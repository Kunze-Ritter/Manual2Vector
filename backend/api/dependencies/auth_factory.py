"""Factory helpers for creating and registering the AuthService."""
from services.auth_service import AuthService
from services.database_factory import create_database_adapter


def create_auth_service() -> AuthService:
    """Instantiate AuthService using the configured database adapter."""
    adapter = create_database_adapter()
    return AuthService(adapter)
