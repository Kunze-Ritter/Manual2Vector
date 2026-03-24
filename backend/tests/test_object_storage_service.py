from __future__ import annotations

import json

import pytest

from backend.services.object_storage_service import ObjectStorageService


class FakeS3Client:
    def __init__(self) -> None:
        self.head_bucket_calls: list[str] = []
        self.policy_calls: list[tuple[str, str]] = []

    def head_bucket(self, Bucket: str) -> None:
        self.head_bucket_calls.append(Bucket)

    def put_bucket_policy(self, Bucket: str, Policy: str) -> None:
        self.policy_calls.append((Bucket, Policy))


@pytest.mark.asyncio
async def test_connect_applies_public_read_policy_for_buckets_with_public_urls(monkeypatch: pytest.MonkeyPatch):
    fake_client = FakeS3Client()

    service = ObjectStorageService(
        access_key_id="key",
        secret_access_key="secret",
        endpoint_url="http://minio:9000",
        public_url_documents="http://localhost:9000/documents",
        public_url_error="",
        public_url_parts="",
        public_url_images="",
        use_ssl=False,
        bucket_documents="documents",
        bucket_images="images",
    )

    monkeypatch.setattr("backend.services.object_storage_service.BOTO3_AVAILABLE", True)
    monkeypatch.setattr(
        "backend.services.object_storage_service.boto3.client",
        lambda *args, **kwargs: fake_client,
    )

    await service.connect()

    assert "documents" in fake_client.head_bucket_calls
    assert tuple(call[0] for call in fake_client.policy_calls) == ("documents",)

    bucket_name, policy_json = fake_client.policy_calls[0]
    assert bucket_name == "documents"
    policy = json.loads(policy_json)
    assert policy["Statement"][0]["Action"] == ["s3:GetObject"]
    assert policy["Statement"][0]["Resource"] == ["arn:aws:s3:::documents/*"]
