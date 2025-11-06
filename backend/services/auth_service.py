"""
Authentication Service
Handles all authentication logic, user validation, and token management
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from passlib.context import CryptContext

# Import models and config
from models.user import (
    UserCreate, UserLogin, UserUpdate, UserResponse, UserListResponse,
    Token, TokenPayload, AuthResponse, UserRole, UserStatus,
    generate_user_id, generate_jti
)
from config.auth_config import (
    get_jwt_config, get_jwt_validator, ACCESS_TOKEN, REFRESH_TOKEN,
    CLAIM_USER_ID, CLAIM_EMAIL, CLAIM_ROLE, CLAIM_TOKEN_TYPE, CLAIM_JTI
)

# Import database service
from services.database_service import DatabaseService

# Setup logging
logger = logging.getLogger("krai.auth.service")


# Permission matrix -------------------------------------------------------
PERMISSIONS: Dict[str, str] = {
    "documents:read": "Read access to documents",
    "documents:write": "Create or update documents",
    "documents:delete": "Delete documents",
    "products:read": "Read access to products",
    "products:write": "Create or update products",
    "products:delete": "Delete products",
    "products:stats": "View product statistics",
    "error_codes:read": "Read access to error codes",
    "error_codes:write": "Create or update error codes",
    "error_codes:delete": "Delete error codes",
    "videos:read": "Read access to videos",
    "videos:write": "Create or update videos",
    "videos:delete": "Delete videos",
    "images:read": "Read access to images",
    "images:write": "Create or update images",
    "images:delete": "Delete images",
    "monitoring:read": "Read access to monitoring data and metrics",
    "monitoring:write": "Manage alerts and alert rules",
    "alerts:read": "Read access to alerts",
    "alerts:write": "Acknowledge and dismiss alerts",
    "alerts:manage": "Manage alert rules (Admin only)",
    "batch:read": "View batch operations and task status",
    "batch:update": "Execute batch create/update/status-change operations",
    "batch:delete": "Execute batch delete operations and cancel tasks",
    "batch:rollback": "Trigger compensating rollbacks for batch operations",
    "users:manage": "Manage user accounts and permissions",
    "tokens:revoke": "Revoke authentication tokens",
}

ROLE_PERMISSIONS: Dict[UserRole, List[str]] = {
    UserRole.ADMIN: list(PERMISSIONS.keys()),
    UserRole.EDITOR: [
        "documents:read",
        "documents:write",
        "products:read",
        "products:write",
        "products:stats",
        "error_codes:read",
        "error_codes:write",
        "videos:read",
        "videos:write",
        "images:read",
        "images:write",
        "monitoring:read",
        "alerts:read",
        "alerts:write",
        "batch:read",
        "batch:update",
    ],
    UserRole.VIEWER: [
        "documents:read",
        "products:read",
        "products:stats",
        "error_codes:read",
        "videos:read",
        "images:read",
        "monitoring:read",
        "alerts:read",
        "batch:read",
    ],
    UserRole.API_USER: [
        "documents:read",
        "products:read",
        "error_codes:read",
        "videos:read",
        "images:read",
    ],
}

class AuthenticationError(Exception):
    """Authentication exception"""
    pass

class AuthorizationError(Exception):
    """Authorization exception"""
    pass

class RateLimitError(Exception):
    """Rate limiting exception"""
    pass

class AuthService:
    """Authentication service with comprehensive security features"""
    
    def __init__(self, database_service: DatabaseService):
        self.db = database_service
        self.jwt_config = get_jwt_config()
        self.jwt_validator = get_jwt_validator()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Rate limiting
        self.login_attempts = {}  # ip -> [timestamps]
        self.max_login_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
    
    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def _is_rate_limited(self, identifier: str) -> bool:
        """Check if identifier is rate limited"""
        now = datetime.now(timezone.utc)
        if identifier not in self.login_attempts:
            self.login_attempts[identifier] = []
        
        # Remove old attempts
        cutoff = now - self.lockout_duration
        self.login_attempts[identifier] = [
            attempt for attempt in self.login_attempts[identifier] 
            if attempt > cutoff
        ]
        
        # Check if exceeded limit
        return len(self.login_attempts[identifier]) >= self.max_login_attempts
    
    def _record_login_attempt(self, identifier: str):
        """Record a login attempt"""
        now = datetime.now(timezone.utc)
        if identifier not in self.login_attempts:
            self.login_attempts[identifier] = []
        
        self.login_attempts[identifier].append(now)
    
    def _reset_login_attempts(self, identifier: str):
        """Reset login attempts after successful login"""
        if identifier in self.login_attempts:
            self.login_attempts[identifier] = []
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create new user with validation"""
        try:
            # Validate input
            if user_data.password != user_data.confirm_password:
                raise AuthenticationError("Passwords do not match")
            
            # Check if username or email already exists
            if await self._user_exists(user_data.username, user_data.email):
                raise AuthenticationError("Username or email already exists")
            
            # Hash password
            password_hash = self.hash_password(user_data.password)
            
            # Create user data
            user_id = generate_user_id()
            now = datetime.now(timezone.utc)
            
            # Get default status
            status = UserStatus.ACTIVE
            if user_data.role == UserRole.ADMIN:
                status = UserStatus.PENDING  # Admin needs approval
            
            # Prepare user data
            user_record = {
                "id": user_id,
                "email": user_data.email,
                "username": user_data.username,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "password_hash": password_hash,
                "role": user_data.role.value,
                "status": status.value,
                "is_active": user_data.is_active,
                "is_verified": user_data.is_verified,
                "login_count": 0,
                "failed_login_attempts": 0,
                "created_at": now,
                "updated_at": now
            }
            
            # Insert into database
            query = """
                INSERT INTO krai_users.users (
                    id, email, username, first_name, last_name,
                    password_hash, role, status, is_active,
                    is_verified, login_count, failed_login_attempts,
                    created_at, updated_at
                ) VALUES (
                    :id, :email, :username, :first_name, :last_name,
                    :password_hash, :role, :status, :is_active,
                    :is_verified, :login_count, :failed_login_attempts,
                    :created_at, :updated_at
                )
            """
            
            await self.db.execute_query(query, user_record)
            
            # Return user response
            return await self._get_user_by_id(user_id)
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Create user error: {e}")
            raise AuthenticationError("Failed to create user")
    
    async def _user_exists(self, username: str, email: str) -> bool:
        """Check if user exists"""
        try:
            query = "SELECT COUNT(*) FROM krai_users.users WHERE username = :username OR email = :email"
            result = await self.db.fetch_one(query, {"username": username, "email": email})
            return result[0] > 0 if result else False
        except Exception as e:
            logger.error(f"Check user exists error: {e}")
            return True  # Assume exists to be safe
    
    async def _get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID"""
        try:
            query = """
                SELECT id, email, username, first_name, last_name, role, status,
                       is_active, is_verified, last_login, login_count, failed_login_attempts,
                       created_at, updated_at, locked_until, permissions
                FROM krai_users.users WHERE id = :user_id
            """
            result = await self.db.fetch_one(query, {"user_id": user_id})
            
            if not result:
                return None
            
            # Convert to UserResponse
            user_dict = dict(result)
            user_dict["locked_until"] = user_dict.get("locked_until")
            permissions = user_dict.get("permissions")
            if permissions is None:
                user_dict["permissions"] = self._get_default_permissions(user_dict.get("role"))
            
            return UserResponse(**user_dict)
            
        except Exception as e:
            logger.error(f"Get user by ID error: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Retrieve user details by email address."""
        try:
            query = """
                SELECT id, email, username, first_name, last_name, role, status,
                       is_active, is_verified, last_login, login_count, failed_login_attempts,
                       created_at, updated_at, locked_until, permissions
                FROM krai_users.users
                WHERE email = :email
            """
            result = await self.db.fetch_one(query, {"email": email})

            if not result:
                return None

            user_dict = dict(result)
            if not user_dict.get("permissions"):
                user_dict["permissions"] = self._get_default_permissions(user_dict.get("role"))

            return UserResponse(**user_dict)

        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            raise AuthenticationError("Error fetching user information")

    async def promote_user_to_admin(
        self,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> UserResponse:
        """Elevate an existing account to admin with verified, active status."""
        try:
            now = datetime.now(timezone.utc)
            query = """
                UPDATE krai_users.users
                SET role = :role,
                    status = :status,
                    is_active = TRUE,
                    is_verified = TRUE,
                    first_name = COALESCE(:first_name, first_name),
                    last_name = COALESCE(:last_name, last_name),
                    updated_at = :now
                WHERE id = :user_id
                RETURNING id, email, username, first_name, last_name, role, status,
                          is_active, is_verified, last_login, login_count, failed_login_attempts,
                          created_at, updated_at, locked_until, permissions
            """

            params = {
                "user_id": user_id,
                "role": UserRole.ADMIN.value,
                "status": UserStatus.ACTIVE.value,
                "first_name": first_name,
                "last_name": last_name,
                "now": now
            }

            result = await self.db.fetch_one(query, params)
            if not result:
                raise AuthenticationError("Failed to promote user to admin")

            user_dict = dict(result)
            if not user_dict.get("permissions"):
                user_dict["permissions"] = self._get_default_permissions(user_dict.get("role"))

            return UserResponse(**user_dict)

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Promote user to admin error: {e}")
            raise AuthenticationError("Failed to promote user to admin")

    async def ensure_default_admin(
        self,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        password: Optional[str] = None
    ) -> UserResponse:
        """Ensure a default admin account exists and is configured correctly."""
        try:
            try:
                existing_user = await self.get_user_by_email(email)
            except AuthenticationError:
                existing_user = None

            if existing_user:
                needs_update = any([
                    existing_user.role != UserRole.ADMIN,
                    existing_user.status != UserStatus.ACTIVE,
                    not existing_user.is_active,
                    not existing_user.is_verified,
                    (first_name and (existing_user.first_name or "") != first_name),
                    (last_name and (existing_user.last_name or "") != last_name)
                ])

                if needs_update:
                    return await self.promote_user_to_admin(
                        user_id=existing_user.id,
                        first_name=first_name,
                        last_name=last_name
                    )

                return existing_user

            if not password:
                raise AuthenticationError("Default admin password not provided")

            admin_payload = UserCreate(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                confirm_password=password,
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )

            created_user = await self.create_user(admin_payload)
            return await self.promote_user_to_admin(
                user_id=created_user.id,
                first_name=first_name,
                last_name=last_name
            )

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Ensure default admin error: {e}")
            raise AuthenticationError("Failed to ensure default admin user")

    async def authenticate_user(self, login_data: UserLogin, client_ip: str = None) -> AuthResponse:
        """Authenticate user with rate limiting and security checks"""
        try:
            # Rate limiting check
            identifier = client_ip or login_data.username
            if self._is_rate_limited(identifier):
                raise RateLimitError("Too many login attempts. Please try again later.")
            
            # Get user from database
            user = await self._get_user_by_username(login_data.username)
            if not user:
                self._record_login_attempt(identifier)
                raise AuthenticationError("Invalid credentials")
            
            # Check if user is active
            if not user.is_active or user.status != UserStatus.ACTIVE:
                self._record_login_attempt(identifier)
                raise AuthenticationError("Account is not active")
            
            # Get full user record for password verification
            user_record = await self._get_user_record_by_username(login_data.username)
            if not user_record:
                self._record_login_attempt(identifier)
                raise AuthenticationError("Invalid credentials")
            
            # Check if account is locked
            if user_record.get("locked_until") and user_record["locked_until"] > datetime.now(timezone.utc):
                self._record_login_attempt(identifier)
                raise AuthenticationError("Account is temporarily locked")
            
            # Verify password
            if not self.verify_password(login_data.password, user_record["password_hash"]):
                # Increment failed attempts
                await self._increment_failed_attempts(user_record["id"], identifier)
                raise AuthenticationError("Invalid credentials")
            
            # Successful login - reset failed attempts and update login info
            await self._successful_login(user_record["id"], identifier, login_data.remember_me)
            
            # Generate tokens
            tokens = await self._generate_tokens(user_record, login_data.remember_me)
            
            # Return auth response
            return AuthResponse(
                success=True,
                message="Login successful",
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token"),
                token_type="bearer",
                expires_in=tokens["expires_in"],
                user=user
            )
            
        except (AuthenticationError, RateLimitError):
            raise
        except Exception as e:
            logger.error(f"Authenticate user error: {e}")
            raise AuthenticationError("Authentication failed")
    
    # ====== User Management Methods ======
    
    async def _get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """Get user by username"""
        try:
            query = """
                SELECT id, email, username, first_name, last_name, role, status,
                       is_active, is_verified, last_login, login_count, failed_login_attempts,
                       created_at, updated_at, locked_until, permissions
                FROM krai_users.users WHERE username = :username
            """
            result = await self.db.fetch_one(query, {"username": username})
            
            if not result:
                return None
                
            # Convert to dict and handle permissions
            user_dict = dict(result)
            if 'permissions' not in user_dict or not user_dict['permissions']:
                # Set default permissions based on role if none exist
                user_dict['permissions'] = self._get_default_permissions(user_dict.get('role'))
            
            return UserResponse(**user_dict)
            
        except Exception as e:
            logger.error(f"Error fetching user by username {username}: {str(e)}")
            raise AuthenticationError("Error fetching user information")

    def _get_default_permissions(self, role: str) -> List[str]:
        """Get default permissions for a role"""
        if not role:
            return []
        try:
            user_role = UserRole(role)
            return ROLE_PERMISSIONS.get(user_role, [])
        except ValueError:
            return []
    
    # ====== Permission Methods ======
    
    async def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission"""
        if not user_id or not permission:
            return False
            
        # Get user with permissions
        user = await self._get_user_by_id(user_id)
        if not user or not user.is_active or user.status != UserStatus.ACTIVE:
            return False
            
        # Admins have all permissions
        if user.role == UserRole.ADMIN:
            return True
            
        # Check if permission exists in user's permissions or role permissions
        user_perms = getattr(user, 'permissions', []) or []
        role_perms = ROLE_PERMISSIONS.get(user.role, [])
        
        return permission in user_perms or permission in role_perms
    
    async def check_permission(self, user_id: str, permission: str) -> bool:
        """Check permission and raise AuthorizationError if not authorized"""
        if not await self.has_permission(user_id, permission):
            raise AuthorizationError(f"Insufficient permissions: {permission}")
        return True
    
    # ====== Token Blacklist ======
    
    async def add_to_blacklist(self, jti: str, user_id: str, token_type: str, expires_at: datetime) -> bool:
        """Add token to blacklist"""
        try:
            query = """
                INSERT INTO krai_users.token_blacklist (jti, user_id, token_type, expires_at, blacklisted_at)
                VALUES (:jti, :user_id, :token_type, :expires_at, :blacklisted_at)
            """
            await self.db.execute_query(query, {
                'jti': jti,
                'user_id': user_id,
                'token_type': token_type,
                'expires_at': expires_at,
                'blacklisted_at': datetime.now(timezone.utc)
            })
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        try:
            query = "SELECT 1 FROM krai_users.token_blacklist WHERE jti = :jti AND (expires_at IS NULL OR expires_at > :now)"
            result = await self.db.fetch_one(query, {
                'jti': jti,
                'now': datetime.now(timezone.utc)
            })
            return result is not None
        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return True  # Fail safe - block token if we can't verify
    
    async def revoke_token(self, jti: str, user_id: str = None) -> bool:
        """Revoke a specific token by jti"""
        try:
            query = """
                UPDATE krai_users.token_blacklist 
                SET expires_at = :now 
                WHERE jti = :jti 
                AND (expires_at IS NULL OR expires_at > :now)
            """
            params = {'jti': jti, 'now': datetime.now(timezone.utc)}
            
            if user_id:
                query += " AND user_id = :user_id"
                params['user_id'] = user_id
                
            result = await self.db.execute_query(query, params)
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user"""
        try:
            query = """
                UPDATE krai_users.token_blacklist 
                SET expires_at = :now 
                WHERE user_id = :user_id 
                AND (expires_at IS NULL OR expires_at > :now)
            """
            result = await self.db.execute_query(query, {
                'user_id': user_id,
                'now': datetime.now(timezone.utc)
            })
            return result.rowcount
        except Exception as e:
            logger.error(f"Error revoking user tokens: {e}")
            return 0
    
    # ====== User Management ======
    
    async def update_user(self, user_id: str, update_data: UserUpdate, current_user_id: str = None) -> UserResponse:
        """Update user information"""
        try:
            # Check if user exists
            existing_user = await self._get_user_by_id(user_id)
            if not existing_user:
                raise AuthenticationError("User not found")
                
            # Only allow users to update their own profile unless they have users:manage permission
            if user_id != current_user_id:
                await self.check_permission(current_user_id, "users:manage")
            
            # Prepare update fields
            update_fields = {}
            if update_data.email is not None:
                update_fields['email'] = update_data.email
            if update_data.first_name is not None:
                update_fields['first_name'] = update_data.first_name
            if update_data.last_name is not None:
                update_fields['last_name'] = update_data.last_name
            if update_data.is_active is not None and current_user_id != user_id:  # Don't allow self-deactivation
                update_fields['is_active'] = update_data.is_active
            if update_data.is_verified is not None and current_user_id != user_id:
                await self.check_permission(current_user_id, "users:manage")
                update_fields['is_verified'] = update_data.is_verified
            if update_data.role is not None and current_user_id != user_id:  # Don't allow self-role change
                await self.check_permission(current_user_id, "users:manage")
                update_fields['role'] = update_data.role.value
            
            # Handle password change
            if update_data.current_password and update_data.new_password:
                if user_id != current_user_id:
                    raise AuthorizationError("Cannot change another user's password")
                    
                # Verify current password
                user_record = await self._get_user_record_by_id(user_id)
                if not self.verify_password(update_data.current_password, user_record['password_hash']):
                    raise AuthenticationError("Current password is incorrect")
                    
                # Update password
                update_fields['password_hash'] = self.hash_password(update_data.new_password)
            
            # Update user in database
            if update_fields:
                update_fields['updated_at'] = datetime.now(timezone.utc)
                set_clause = ", ".join([f"{k} = :{k}" for k in update_fields.keys()])
                
                query = f"""
                    UPDATE krai_users.users 
                SET {set_clause}
                WHERE id = :user_id
                RETURNING *
                """
                
                params = {"user_id": user_id, **update_fields}
                result = await self.db.fetch_one(query, params)
                
                if not result:
                    raise Exception("Failed to update user")
            
            # Return updated user
            return await self._get_user_by_id(user_id)
            
        except (AuthenticationError, AuthorizationError):
            raise
        except Exception as e:
            logger.error(f"Update user error: {e}")
            raise AuthenticationError("Failed to update user")
    
    async def list_users(self, current_user_id: str, page: int = 1, page_size: int = 10) -> UserListResponse:
        """List users with pagination (admin only)"""
        try:
            # Check permissions
            await self.check_permission(current_user_id, "users:manage")
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Get total count
            count_query = "SELECT COUNT(*) FROM krai_users.users"
            total_count_result = await self.db.fetch_one(count_query)
            total_count = total_count_result[0] if total_count_result else 0
            
            # Get paginated users
            query = """
                SELECT id, email, username, first_name, last_name, role, status,
                       is_active, is_verified, last_login, login_count, created_at, updated_at
                FROM krai_users.users
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            users = await self.db.fetch_all(query, {"limit": page_size, "offset": offset})
            
            # Convert to UserResponse list
            user_list = [UserResponse(**dict(user)) for user in users]
            
            return UserListResponse(
                items=user_list,
                total=total_count,
                page=page,
                page_size=page_size,
                total_pages=(total_count + page_size - 1) // page_size
            )
            
        except (AuthenticationError, AuthorizationError):
            raise
        except Exception as e:
            logger.error(f"List users error: {e}")
            raise AuthenticationError("Failed to list users")
    
    async def delete_user(self, user_id: str, current_user_id: str) -> bool:
        """Delete a user (soft delete)"""
        try:
            # Check permissions
            await self.check_permission(current_user_id, "users:manage")
            
            # Don't allow self-deletion
            if user_id == current_user_id:
                raise AuthorizationError("Cannot delete your own account")
            
            # Soft delete user
            query = """
                UPDATE krai_users.users 
                SET is_active = false, 
                    status = :status,
                    updated_at = :now
                WHERE id = :user_id
                RETURNING 1
            """
            
            result = await self.db.execute_query(query, {
                'user_id': user_id,
                'status': UserStatus.DELETED.value,
                'now': datetime.now(timezone.utc)
            })
            
            # Revoke all user tokens
            await self.revoke_all_user_tokens(user_id)
            
            return result.rowcount > 0
            
        except (AuthenticationError, AuthorizationError):
            raise
        except Exception as e:
            logger.error(f"Delete user error: {e}")
            raise AuthenticationError("Failed to delete user")
    
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for a user (combined role and user-specific permissions)"""
        try:
            # Get user with permissions
            user = await self._get_user_by_id(user_id)
            if not user or not user.is_active or user.status != UserStatus.ACTIVE:
                return []
                
            # Start with role permissions
            permissions = set(ROLE_PERMISSIONS.get(user.role, []))
            
            # Add user-specific permissions if any
            user_perms = getattr(user, 'permissions', []) or []
            permissions.update(user_perms)
            
            return list(permissions)
            
        except Exception as e:
            logger.error(f"Get user permissions error: {e}")
            return []
    
    async def update_user_permissions(self, user_id: str, permissions: List[str], current_user_id: str) -> bool:
        """Update user-specific permissions"""
        try:
            # Check permissions
            await self.check_permission(current_user_id, "users:manage")
            
            # Validate permissions
            invalid_perms = [p for p in permissions if p not in PERMISSIONS]
            if invalid_perms:
                raise ValueError(f"Invalid permissions: {', '.join(invalid_perms)}")
            
            # Update user permissions
            query = """
                UPDATE krai_users.users 
                SET permissions = :permissions,
                    updated_at = :now
                WHERE id = :user_id
            """
            
            result = await self.db.execute_query(query, {
                'user_id': user_id,
                'permissions': permissions,
                'now': datetime.now(timezone.utc)
            })
            
            return result.rowcount > 0
            
        except (AuthenticationError, AuthorizationError, ValueError):
            raise
        except Exception as e:
            logger.error(f"Update user permissions error: {e}")
            raise AuthenticationError("Failed to update user permissions")

    async def _get_user_record_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get full user record by ID including password hash."""
        try:
            query = """
                SELECT id, email, username, password_hash, role, status, is_active,
                       login_count, failed_login_attempts, locked_until
                FROM krai_users.users WHERE id = :user_id
            """
            result = await self.db.fetch_one(query, {"user_id": user_id})
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Get user record by id error: {e}")
            return None
    
    async def _get_user_record_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get full user record including password"""
        try:
            query = """
                SELECT id, email, username, password_hash, role, status, is_active,
                       login_count, failed_login_attempts, locked_until
                FROM krai_users.users WHERE username = :username
            """
            result = await self.db.fetch_one(query, {"username": username})
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Get user record error: {e}")
            return None
    
    async def _increment_failed_attempts(self, user_id: str, identifier: str):
        """Increment failed login attempts"""
        try:
            now = datetime.now(timezone.utc)
            
            # Check if should lock account
            lock_account = False
            if await self._should_lock_account(user_id):
                lock_account = True
            
            # Update failed attempts
            query = """
                UPDATE krai_users.users 
                SET failed_login_attempts = failed_login_attempts + 1,
                    locked_until = CASE WHEN :lock_account THEN :lockout_time ELSE locked_until END,
                    updated_at = :now
                WHERE id = :user_id
            """
            
            await self.db.execute_query(query, {
                "user_id": user_id,
                "lock_account": lock_account,
                "lockout_time": now + self.lockout_duration if lock_account else None,
                "now": now
            })
            
            self._record_login_attempt(identifier)
            
        except Exception as e:
            logger.error(f"Increment failed attempts error: {e}")
    
    async def _should_lock_account(self, user_id: str) -> bool:
        """Check if account should be locked"""
        try:
            query = "SELECT failed_login_attempts FROM krai_users.users WHERE id = :user_id"
            result = await self.db.fetch_one(query, {"user_id": user_id})
            
            if not result:
                return False
            
            failed_attempts = result[0]
            return failed_attempts >= self.max_login_attempts - 1
            
        except Exception as e:
            logger.error(f"Check should lock account error: {e}")
            return False
    
    async def _successful_login(self, user_id: str, identifier: str, remember_me: bool):
        """Update user after successful login"""
        try:
            now = datetime.now(timezone.utc)
            
            query = """
                UPDATE krai_users.users 
                SET last_login = :now,
                    login_count = login_count + 1,
                    failed_login_attempts = 0,
                    locked_until = NULL,
                    updated_at = :now
                WHERE id = :user_id
            """
            
            await self.db.execute_query(query, {
                "user_id": user_id,
                "now": now
            })
            
            self._reset_login_attempts(identifier)
            
        except Exception as e:
            logger.error(f"Successful login update error: {e}")
    
    async def _generate_tokens(self, user_record: Dict[str, Any], remember_me: bool = False) -> Dict[str, str]:
        """Generate access and refresh tokens"""
        try:
            user_id = user_record["id"]
            email = user_record["email"]
            role = user_record["role"]
            
            # Generate token IDs
            access_jti = generate_jti()
            refresh_jti = generate_jti() if remember_me else None
            
            # Create access token payload
            access_payload = {
                CLAIM_USER_ID: user_id,
                CLAIM_EMAIL: email,
                CLAIM_ROLE: role,
                CLAIM_TOKEN_TYPE: ACCESS_TOKEN,
                CLAIM_JTI: access_jti
            }
            
            # Generate access token
            access_token = self.jwt_validator.encode_token(access_payload, ACCESS_TOKEN)
            
            # Calculate expiry
            access_expires_in = int(self.jwt_config.access_token_expire.total_seconds())
            
            result = {
                "access_token": access_token,
                "expires_in": access_expires_in
            }
            
            # Generate refresh token if requested
            if remember_me:
                refresh_payload = {
                    CLAIM_USER_ID: user_id,
                    CLAIM_EMAIL: email,
                    CLAIM_ROLE: role,
                    CLAIM_TOKEN_TYPE: REFRESH_TOKEN,
                    CLAIM_JTI: refresh_jti
                }
                
                refresh_token = self.jwt_validator.encode_token(refresh_payload, REFRESH_TOKEN)
                result["refresh_token"] = refresh_token
            
            return result
            
        except Exception as e:
            logger.error(f"Generate tokens error: {e}")
            raise AuthenticationError("Failed to generate tokens")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            # Validate refresh token
            payload = self.jwt_validator.decode_token(refresh_token)
            if not payload:
                raise AuthenticationError("Invalid refresh token")
            
            if payload.get(CLAIM_TOKEN_TYPE) != REFRESH_TOKEN:
                raise AuthenticationError("Invalid token type")
            
            # Get user from database
            user = await self._get_user_by_id(payload[CLAIM_USER_ID])
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            # Get user record for token generation
            user_record = await self._get_user_record_by_username(user.username)
            if not user_record:
                raise AuthenticationError("User record not found")
            
            # Generate new access token
            tokens = await self._generate_tokens(user_record, remember_me=False)
            
            return {
                "access_token": tokens["access_token"],
                "expires_in": tokens["expires_in"],
                "token_type": "bearer"
            }
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Refresh token error: {e}")
            raise AuthenticationError("Failed to refresh token")
    
    async def decode_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode access token and verify it is not blacklisted."""
        try:
            payload = self.jwt_validator.decode_token(token)
            if not payload:
                return None
            
            if payload.get(CLAIM_TOKEN_TYPE) != ACCESS_TOKEN:
                return None
            
            jti = payload.get(CLAIM_JTI)
            if jti and await self.is_token_blacklisted(jti):
                logger.warning("Access token is blacklisted")
                return None
            
            return payload
            
        except Exception as e:
            logger.error(f"Decode access token error: {e}")
            return None

# Authentication decorator for protected endpoints
def require_auth(service: AuthService = None):
    """Decorator for requiring authentication"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract token from request (this would be handled by middleware)
            # For now, this is a placeholder
            pass
        return wrapper
    return decorator
