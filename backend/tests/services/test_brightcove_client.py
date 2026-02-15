from __future__ import annotations

import asyncio

import pytest

from backend.services.brightcove_client import BrightcoveClient


class _FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


@pytest.mark.asyncio
async def test_fetch_video_metadata_requires_credentials():
    client = BrightcoveClient(account_id="", client_id="", client_secret="")
    result = await client.fetch_video_metadata("123")
    assert result["success"] is False
    assert result["error"] == "missing_credentials"


def test_extract_video_id_from_url():
    client = BrightcoveClient(account_id="a", client_id="b", client_secret="c")
    url = "https://players.brightcove.net/123/default_default/index.html?videoId=9876543210"
    assert client.extract_video_id(url) == "9876543210"


@pytest.mark.asyncio
async def test_fetch_video_metadata_success(monkeypatch):
    client = BrightcoveClient(account_id="acc", client_id="id", client_secret="secret")

    async def _inline_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", _inline_to_thread)

    def _fake_post(*args, **kwargs):
        return _FakeResponse(200, {"access_token": "token", "expires_in": 300})

    def _fake_get(*args, **kwargs):
        return _FakeResponse(
            200,
            {
                "id": "999",
                "name": "Test Video",
                "description": "desc",
                "duration": 61000,
                "thumbnail": "https://cdn.example.com/thumb.jpg",
                "published_at": "2025-01-01T00:00:00Z",
                "tags": ["hp", "service"],
            },
        )

    monkeypatch.setattr(client._session, "post", _fake_post)
    monkeypatch.setattr(client._session, "get", _fake_get)

    result = await client.fetch_video_metadata("999")
    assert result["success"] is True
    assert result["title"] == "Test Video"
    assert result["duration"] == 61
    assert result["tags"] == ["hp", "service"]
