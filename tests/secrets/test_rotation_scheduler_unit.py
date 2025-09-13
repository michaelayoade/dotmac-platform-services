"""
Unit tests for RotationScheduler with a fake secrets provider.
"""

import pytest

from dotmac.platform.secrets.rotation import (
    RotationResult,
    RotationRule,
    RotationScheduler,
    RotationStatus,
    SecretType,
)


class FakeProvider:
    def __init__(self):
        self.store = {"db/creds/app": {"password": "old", "version": "v1"}}

    async def get_secret(self, path: str):
        return dict(self.store.get(path, {}))

    async def set_secret(self, path: str, data: dict):
        self.store[path] = dict(data)
        return True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rotate_secret_success():
    provider = FakeProvider()
    scheduler = RotationScheduler(provider)
    rule = RotationRule(
        secret_path="db/creds/app",
        secret_type=SecretType.DATABASE_PASSWORD,
        rotation_interval=0,
        max_age=0,
    )
    scheduler.add_rotation_rule(rule)

    result: RotationResult = await scheduler.rotate_secret("db/creds/app", force=True)
    assert result.status == RotationStatus.COMPLETED
    assert provider.store["db/creds/app"]["password"] != "old"
