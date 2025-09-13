"""
Unit tests for API key rate limit path using a fake DB session.
"""

from datetime import datetime

import pytest

from dotmac.platform.auth.api_keys import (
    APIKey,
    APIKeyRateLimit,
    APIKeyService,
    APIKeyStatus,
    RateLimitWindow,
)
from dotmac.platform.auth.exceptions import RateLimitError


class FakeQuery:
    def __init__(self, model, db):
        self.model = model
        self.db = db
        self._filters = []

    def filter(self, *args, **kwargs):
        # Ignore real conditions; rely on model to dispatch
        return self

    def first(self):
        if self.model is APIKeyRateLimit:
            return self.db._rate_limit
        if self.model is APIKey:
            return self.db._api_key
        return None

    def all(self):
        return []


class FakeDB:
    def __init__(self):
        self._rate_limit = None
        self._api_key = None

    def query(self, model):
        return FakeQuery(model, self)

    def add(self, obj):
        # Capture newly created rate limit
        if isinstance(obj, APIKeyRateLimit):
            self._rate_limit = obj

    async def commit(self):
        return None

    async def refresh(self, obj):
        return None


def make_db_key():
    k = APIKey(
        name="test",
        description=None,
        key_id="kid",
        key_hash="hash",
        key_prefix="dm_",
        user_id="u",
        created_by="u",
        scopes=["read:users"],
        expires_at=None,
        rate_limit_requests=1,
        rate_limit_window=RateLimitWindow.MINUTE.value,
        allowed_ips=[],
        require_https=True,
        tenant_id=None,
        status=APIKeyStatus.ACTIVE,
        created_at=datetime.utcnow(),
    )
    return k


@pytest.mark.unit
@pytest.mark.asyncio
async def test_check_rate_limit_exceeded_raises(monkeypatch):
    svc = APIKeyService(database_session=FakeDB())

    # Inject API key object to be found by query
    db_key = make_db_key()
    svc.db._api_key = db_key

    # Provide an existing rate limit at threshold
    rl = APIKeyRateLimit(
        api_key_id="id",
        window_start=datetime.utcnow(),
        window_type=db_key.rate_limit_window,
        request_count=db_key.rate_limit_requests,
        last_request=None,
    )
    svc.db._rate_limit = rl

    with pytest.raises(RateLimitError):
        await svc._check_rate_limit(db_key, {"ip_address": "1.2.3.4"})  # type: ignore[reportPrivateUsage]
