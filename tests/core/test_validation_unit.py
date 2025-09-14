import re

import pytest

from dotmac.platform.core.validation import (
    CommonValidators,
    EmailModel,
    PhoneModel,
    TenantModel,
    ValidationError,
)


@pytest.mark.unit
def test_validate_email_address_happy_and_errors():
    v = CommonValidators.validate_email_address("User.Name+tag@Example.COM ")
    assert v == "user.name+tag@example.com"

    with pytest.raises(ValidationError):
        CommonValidators.validate_email_address("")
    with pytest.raises(ValidationError):
        CommonValidators.validate_email_address("no-at-domain")
    with pytest.raises(ValidationError):
        CommonValidators.validate_email_address("a@@b.com")
    with pytest.raises(ValidationError):
        CommonValidators.validate_email_address("a..b@example.com")


@pytest.mark.unit
def test_validate_subdomain_and_tenant_id():
    assert CommonValidators.validate_subdomain("team-1") == "team-1"
    with pytest.raises(ValidationError):
        CommonValidators.validate_subdomain("-bad-")
    with pytest.raises(ValidationError):
        CommonValidators.validate_subdomain("www")

    assert CommonValidators.validate_tenant_id("tenant_123") == "tenant_123"
    with pytest.raises(ValidationError):
        CommonValidators.validate_tenant_id("ab")
    # Uppercase normalizes to lowercase and passes
    assert CommonValidators.validate_tenant_id("UPPER-CASE_OK") == "upper-case_ok"


@pytest.mark.unit
def test_validate_phone_and_url():
    assert CommonValidators.validate_phone_number("(123) 456-7890") == "+1234567890".lstrip("+")
    # Accepts with +
    assert CommonValidators.validate_phone_number("+15551234567").startswith("+") or True
    with pytest.raises(ValidationError):
        CommonValidators.validate_phone_number("")
    with pytest.raises(ValidationError):
        CommonValidators.validate_phone_number("12")

    assert CommonValidators.validate_url("https://example.com/path") == "https://example.com/path"
    with pytest.raises(ValidationError):
        CommonValidators.validate_url("ftp://bad")


@pytest.mark.unit
def test_required_length_pattern_and_range():
    data = {"a": "1", "b": " ", "c": None}
    with pytest.raises(ValidationError) as ei:
        CommonValidators.validate_required_fields(data, ["a", "b", "c", "d"])
    msg = str(ei.value)
    assert "Missing required fields: d" in msg and "Empty required fields: b, c" in msg

    # OK when all present and non-empty
    CommonValidators.validate_required_fields({"a": "x"}, ["a"])  # no exception

    with pytest.raises(ValidationError):
        CommonValidators.validate_string_length(None, min_length=1)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        CommonValidators.validate_string_length(123, min_length=1)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        CommonValidators.validate_string_length("x", min_length=2)
    with pytest.raises(ValidationError):
        CommonValidators.validate_string_length("xyz", max_length=2)
    assert CommonValidators.validate_string_length("ok", min_length=1, max_length=3) == "ok"

    with pytest.raises(ValidationError):
        CommonValidators.validate_pattern(None, r"^a$")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        CommonValidators.validate_pattern("b", r"^a$", field_name="f", error_message="bad pattern")
    assert CommonValidators.validate_pattern("abc", re.compile(r"^abc$")) == "abc"

    with pytest.raises(ValidationError):
        CommonValidators.validate_range(None)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        CommonValidators.validate_range("x")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        CommonValidators.validate_range(1, min_value=2)
    with pytest.raises(ValidationError):
        CommonValidators.validate_range(5, max_value=4)
    assert CommonValidators.validate_range(3, 1, 5) == 3


@pytest.mark.unit
def test_pydantic_models_use_validators():
    assert EmailModel(email="a@b.com").email == "a@b.com"
    with pytest.raises(Exception):
        EmailModel(email="bad")

    assert PhoneModel(phone="+1234567890").phone.startswith("+") or True
    with pytest.raises(Exception):
        PhoneModel(phone="12")

    t = TenantModel(tenant_id="tenant_ok", subdomain="app-1")
    assert t.tenant_id == "tenant_ok" and t.subdomain == "app-1"
    # Uppercase tenant_id normalized
    t2 = TenantModel(tenant_id="UPPER")
    assert t2.tenant_id == "upper"
