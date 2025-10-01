"""Test fixtures for partner management tests."""

import pytest
from uuid import uuid4


@pytest.fixture
def test_tenant_id():
    """Generate a test tenant ID."""
    return uuid4()
