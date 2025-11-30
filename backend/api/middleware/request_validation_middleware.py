"""Request validation middleware for size, content-type, and upload checks."""

from __future__ import annotations

import json
import logging
import re
from io import BytesIO
from typing import Any, Dict, Iterable

import magic
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from config.security_config import get_security_config

logger = logging.getLogger("krai.request_validation")
_sql_pattern = re.compile(r"(;\s*drop|union\s+select|--|/\*|\*/|exec\s|xp_)", re.I)
_xss_pattern = re.compile(r"(<script|javascript:|onerror=|onload=|onclick=)", re.I)

ALLOWED_CONTENT_TYPES = {
    "application/json",
    "multipart/form-data",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _sanitize_filename(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return sanitized[:255]


def _is_disallowed_path(name: str) -> bool:
    lowered = name.lower()
    return ".." in lowered or lowered.startswith(("/", "\\"))


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware that validates request size, headers, and uploads."""

    def __init__(self, app):
        super().__init__(app)
        self.config = get_security_config()
        self.max_request_bytes = self.config.MAX_REQUEST_SIZE_MB * 1024 * 1024
        self.max_file_bytes = self.config.MAX_FILE_SIZE_MB * 1024 * 1024
        self.allowed_extensions = set(self.config.ALLOWED_FILE_TYPES)
        self.enabled = self.config.REQUEST_VALIDATION_ENABLED

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            return await call_next(request)

        if _is_whitelisted_content_type(request.headers.get("content-type")):
            pass

        enforce_size = self._check_content_length(request)
        if enforce_size is not None:
            return enforce_size

        enforce_blacklist = self._check_blacklist(request)
        if enforce_blacklist is not None:
            return enforce_blacklist

        if request.method in {"POST", "PUT", "PATCH"}:
            validation_response = await self._validate_body(request)
            if validation_response is not None:
                return validation_response

        return await call_next(request)

    def _check_content_length(self, request: Request) -> Response | None:
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit():
            size = int(content_length)
            if size > self.max_request_bytes:
                logger.warning("Request too large from %s: %s bytes", request.client, size)
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "detail": "Request payload too large",
                        "limit_mb": self.config.MAX_REQUEST_SIZE_MB,
                    },
                )
        return None

    def _check_blacklist(self, request: Request) -> Response | None:
        suspicious_headers = [
            value for header, value in request.headers.items() if _sql_pattern.search(value or "")
        ]
        if suspicious_headers:
            logger.warning("Suspicious headers detected from %s", request.client)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Suspicious input detected"},
            )
        return None

    async def _validate_body(self, request: Request) -> Response | None:
        content_type = request.headers.get("content-type", "").lower()
        if "multipart/form-data" in content_type:
            return await self._validate_multipart(request)
        if "application/json" in content_type:
            return await self._validate_json(request)
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            return JSONResponse(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                content={
                    "detail": "Unsupported Content-Type",
                    "allowed": list(ALLOWED_CONTENT_TYPES),
                },
            )
        return None

    async def _validate_json(self, request: Request) -> Response | None:
        body = await request.body()
        if len(body) > self.max_request_bytes:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "JSON payload too large"},
            )
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Invalid JSON"})
        suspicious = self._scan_payload(data)
        if suspicious:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Suspicious content detected", "fields": suspicious},
            )
        request._body = body  # type: ignore[attr-defined]
        return None

    async def _validate_multipart(self, request: Request) -> Response | None:
        form = await request.form()
        for key, value in form.multi_items():
            if hasattr(value, "filename"):
                response = self._validate_upload(value.filename, value.content_type, await value.read())
                if response:
                    return response
                value.file.seek(0)
            elif isinstance(value, str):
                if _sql_pattern.search(value) or _xss_pattern.search(value):
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": f"Field {key} contains forbidden content"},
                    )
        return None

    def _validate_upload(self, filename: str, content_type: str, data: bytes) -> Response | None:
        if not filename:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Filename required"})
        if _is_disallowed_path(filename):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid filename"},
            )
        sanitized = _sanitize_filename(filename)
        ext = f".{sanitized.split('.')[-1].lower()}" if "." in sanitized else ""
        if ext not in self.allowed_extensions:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Unsupported file type", "allowed": list(self.allowed_extensions)},
            )
        if len(data) > self.max_file_bytes:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "File too large", "limit_mb": self.config.MAX_FILE_SIZE_MB},
            )
        mime = magic.from_buffer(data[:2048], mime=True)
        if not mime:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Unable to detect file type"})
        if mime != content_type:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Mismatched file type", "detected": mime, "provided": content_type},
            )
        return None

    def _scan_payload(self, data: Any, path: str = "") -> Iterable[str]:
        suspicious_fields = []
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                suspicious_fields.extend(self._scan_payload(value, new_path))
        elif isinstance(data, list):
            for idx, value in enumerate(data):
                new_path = f"{path}[{idx}]"
                suspicious_fields.extend(self._scan_payload(value, new_path))
        elif isinstance(data, str):
            if _sql_pattern.search(data) or _xss_pattern.search(data):
                suspicious_fields.append(path)
        return suspicious_fields


def _is_whitelisted_content_type(content_type: str | None) -> bool:
    return content_type is None
