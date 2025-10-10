import types
from urllib.parse import urlencode

import pytest
from fastapi import Request
from starlette.datastructures import Headers

from dotmac.platform.tenant.tenant import TenantIdentityResolver

pytestmark = pytest.mark.asyncio


def make_request(headers=None, query=None, state_dict=None) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "headers": Headers(headers or {}).raw,
        "query_string": urlencode(query or {}).encode("utf-8"),
    }
    req = Request(scope)
    if state_dict is not None:
        # request.state is a SimpleNamespace-like; we mimic by setting __dict__
        ns = types.SimpleNamespace()
        ns.__dict__.update(state_dict)
        object.__setattr__(req, "_state", ns)
    return req


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_prefers_header_then_query_then_state():
    from dotmac.platform.tenant.config import TenantConfiguration, TenantMode

    # Create a multi-tenant config for this test
    config = TenantConfiguration(mode=TenantMode.MULTI)
    r = TenantIdentityResolver(config=config)

    # Header wins
    req = make_request(
        headers={"X-Tenant-ID": "H"}, query={"tenant_id": "Q"}, state_dict={"tenant_id": "S"}
    )
    assert await r.resolve(req) == "H"

    # Query used when header missing
    req2 = make_request(headers={}, query={"tenant_id": "Q"}, state_dict={"tenant_id": "S"})
    assert await r.resolve(req2) == "Q"

    # State used when others missing
    req3 = make_request(headers={}, query={}, state_dict={"tenant_id": "S"})
    assert await r.resolve(req3) == "S"

    # None when not present
    req4 = make_request(headers={}, query={})
    assert await r.resolve(req4) is None
