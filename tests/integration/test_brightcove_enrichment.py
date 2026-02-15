import asyncio

import pytest

from scripts.enrich_video_metadata import VideoEnricher


class FakeResponse:
    def __init__(self, status_code=200, data=None, text="", headers=None):
        self.status_code = status_code
        self._data = data or {}
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._data


@pytest.mark.asyncio
async def test_brightcove_enrichment_without_credentials(monkeypatch):
    monkeypatch.delenv("BRIGHTCOVE_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("BRIGHTCOVE_CLIENT_ID", raising=False)
    monkeypatch.delenv("BRIGHTCOVE_CLIENT_SECRET", raising=False)

    enricher = VideoEnricher()
    result = await enricher.enrich_brightcove_video(
        "https://players.brightcove.net/123/default_default/index.html?videoId=abc"
    )

    assert result["metadata"].get("credentials_missing") is True
    assert result.get("enrichment_error") is None


@pytest.mark.asyncio
async def test_oauth_token_refresh(monkeypatch):
    monkeypatch.setenv("BRIGHTCOVE_ACCOUNT_ID", "123")
    monkeypatch.setenv("BRIGHTCOVE_CLIENT_ID", "client")
    monkeypatch.setenv("BRIGHTCOVE_CLIENT_SECRET", "secret")

    enricher = VideoEnricher()

    tokens = [
        FakeResponse(200, {"access_token": "token-1", "expires_in": 1}),
        FakeResponse(200, {"access_token": "token-2", "expires_in": 300}),
    ]

    def fake_post(*args, **kwargs):
        return tokens.pop(0)

    enricher.session.post = fake_post

    t1 = await enricher.get_brightcove_access_token(force_refresh=True)
    t2 = await enricher.get_brightcove_access_token(force_refresh=True)

    assert t1 == "token-1"
    assert t2 == "token-2"


@pytest.mark.asyncio
async def test_rate_limit_backoff(monkeypatch):
    monkeypatch.setenv("BRIGHTCOVE_ACCOUNT_ID", "123")
    monkeypatch.setenv("BRIGHTCOVE_CLIENT_ID", "client")
    monkeypatch.setenv("BRIGHTCOVE_CLIENT_SECRET", "secret")

    enricher = VideoEnricher()

    calls = {"count": 0}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return FakeResponse(429, text="rate limited", headers={"Retry-After": "0"})
        return FakeResponse(200, data={"ok": True})

    async def fake_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    enricher.session.get = fake_get

    response = await enricher._brightcove_get_with_retry("https://example.com", headers={"Authorization": "Bearer x"})

    assert response.status_code == 200
    assert calls["count"] == 2
