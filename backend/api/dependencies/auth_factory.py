"""Factory helpers for creating and registering the AuthService."""
from services.auth_service import AuthService
from services.database_service import DatabaseService


def create_auth_service() -> AuthService:
    """Instantiate AuthService using the configured database service."""
    db_service = DatabaseService()
    return AuthService(db_service)


async def create_and_initialize_auth_service() -> AuthService:
    """Create and initialize AuthService with database connection."""
    auth_service = create_auth_service()
    await auth_service.initialize()
    return auth_service
