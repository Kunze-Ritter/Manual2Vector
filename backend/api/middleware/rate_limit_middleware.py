"""Rate limiting middleware utilities using slowapi."""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from config.security_config import get_security_config

logger = logging.getLogger("krai.rate_limit")
_security_config = get_security_config()


def _client_ip(request: Request) -> str:
    """Resolve client IP using forwarded headers fallback to remote address."""
    try:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Safety check for request.client
        if not request.client or not request.client.host:
            return "127.0.0.1"
            
        return get_remote_address(request)
    except Exception:
        return "127.0.0.1"


def _user_or_ip_key(request: Request) -> str:
    """Use authenticated user id when available, otherwise IP."""
    try:
        user = getattr(request.state, "user", None)
        if isinstance(user, dict):
            user_id = user.get("id")
            if user_id:
                return str(user_id)
        return _client_ip(request)
    except Exception:
        return "unknown"


_STORAGE_URI = _security_config.rate_limit_storage_url or "memory://"
limiter = Limiter(
    key_func=_user_or_ip_key,
    storage_uri=_STORAGE_URI,
    headers_enabled=True,
)
limiter.enabled = _security_config.RATE_LIMIT_ENABLED

_WHITELIST = {ip.strip() for ip in _security_config.RATE_LIMIT_WHITELIST if ip.strip()}
_BLACKLIST = {ip.strip() for ip in _security_config.RATE_LIMIT_BLACKLIST if ip.strip()}


def rate_limit_exempt(*args, **kwargs) -> bool:
    """Skip rate limiting for whitelisted IPs or when disabled.

    SlowAPI may invoke request filters without passing a Request object, which
    previously caused a TypeError. We defensively accept arbitrary args/kwargs
    and only apply IP-based whitelisting when a Request is available.
    """

    # Global switch: if rate limiting is disabled, always exempt
    if not _security_config.RATE_LIMIT_ENABLED:
        return True

    # Try to extract Request from positional or keyword arguments
    request: Request | None = None
    if args and isinstance(args[0], Request):
        request = args[0]
    elif isinstance(kwargs.get("request"), Request):
        request = kwargs["request"]

    # Without a concrete Request, we cannot apply whitelist logic safely
    if request is None:
        return False

    return _client_ip(request) in _WHITELIST

# Register the exempt function with the limiter
limiter._request_filters.append(rate_limit_exempt)


class IPFilterMiddleware(BaseHTTPMiddleware):
    """Middleware that blocks blacklisted IPs before hitting routes."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        ip = _client_ip(request)
        if ip in _BLACKLIST:
            logger.warning("Rejected blacklisted IP %s for path %s", ip, request.url.path)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return await call_next(request)


def _rate_limit_value(attr: str) -> str:
    return getattr(_security_config, attr)


def rate_limit_auth() -> str:
    return _rate_limit_value("RATE_LIMIT_AUTH")


def rate_limit_upload() -> str:
    return _rate_limit_value("RATE_LIMIT_UPLOAD")


def rate_limit_search() -> str:
    return _rate_limit_value("RATE_LIMIT_SEARCH")


def rate_limit_standard() -> str:
    return _rate_limit_value("RATE_LIMIT_STANDARD")


def rate_limit_health() -> str:
    return _rate_limit_value("RATE_LIMIT_HEALTH")


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    ip = _client_ip(request)
    limit_desc = getattr(exc, "detail", "Too Many Requests")
    retry_after = getattr(exc, "retry_after", None)
    logger.warning("Rate limit exceeded for IP %s on %s: %s", ip, request.url.path, limit_desc)
    headers = {"Retry-After": str(retry_after)} if retry_after else {}
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded",
            "limit": limit_desc,
            "resource": str(request.url.path),
        },
        headers=headers,
    )
