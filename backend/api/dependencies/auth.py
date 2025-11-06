"""Auth-related dependency helpers."""
from typing import Optional

from backend.services.auth_service import AuthService

_auth_service: Optional[AuthService] = None


def set_auth_service(service: AuthService) -> None:
    """Register the singleton AuthService used across the API."""
    global _auth_service
    _auth_service = service


def get_auth_service() -> AuthService:
    """Provide the configured AuthService instance or raise if missing."""
    if _auth_service is None:
        raise RuntimeError("Authentication service has not been initialized")
    return _auth_service
