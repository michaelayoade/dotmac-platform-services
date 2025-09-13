"""
Additional unit tests for JWTService configuration and factory.
"""

import pytest

from dotmac.platform.auth.exceptions import ConfigurationError, InvalidAlgorithm
from dotmac.platform.auth.jwt_service import JWTService, create_jwt_service_from_config


@pytest.mark.unit
def test_invalid_algorithm_raises():
    with pytest.raises(InvalidAlgorithm):
        JWTService(algorithm="HS999")


@pytest.mark.unit
def test_hs256_requires_secret():
    with pytest.raises(ConfigurationError):
        JWTService(algorithm="HS256", secret=None)


@pytest.mark.unit
def test_rs256_requires_keys():
    # Neither private nor public key provided
    with pytest.raises(ConfigurationError):
        JWTService(algorithm="RS256", private_key=None, public_key=None)


@pytest.mark.unit
def test_create_from_config_builds_service():
    svc = create_jwt_service_from_config({"algorithm": "HS256", "secret": "s"})
    assert isinstance(svc, JWTService)
    assert svc.algorithm == "HS256"
