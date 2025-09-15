"""
Test package imports and public API.
"""

import pytest


@pytest.mark.unit
def test_platform_imports():
    """Test that all public API components can be imported."""
    from dotmac.platform import (
        __version__,
    )

    # Test core imports
    from dotmac.platform.core.pagination import Page, PaginationParams
    from dotmac.platform.core.result import Result
    from dotmac.platform.core.utils import generate_id, utcnow
    from dotmac.platform.core.validation import CommonValidators

    # Test auth imports
    from dotmac.platform.auth import (
        __version__ as auth_version,
        initialize_auth_service,
        is_auth_service_available,
    )

    # Test repository imports
    from dotmac.platform.core.repository import (
        AsyncRepository,
        EntityNotFoundError,
        RepositoryError,
    )

    # Test that imports are not None
    assert Page is not None
    assert Result is not None
    assert AsyncRepository is not None

    # Test version
    assert isinstance(__version__, str)


@pytest.mark.unit
def test_result_functionality():
    """Test Result class functionality."""
    from dotmac.platform.core.result import Result

    # Test success result
    success = Result.success("value")
    assert success.is_success is True
    assert success.is_failure is False
    assert success.value == "value"
    assert success.error is None

    # Test failure result
    failure = Result.failure("error")
    assert failure.is_success is False
    assert failure.is_failure is True
    assert isinstance(failure.error, Exception)
    assert str(failure.error) == "error"
    assert failure.value is None


@pytest.mark.unit
def test_pagination_functionality():
    """Test basic pagination functionality."""
    from dotmac.platform.core.pagination import Page, PaginationParams

    # Test pagination params
    params = PaginationParams(page=2, size=10)
    assert params.page == 2
    assert params.size == 10
    assert params.skip == 10  # (page-1) * size
    assert params.limit == 10

    # Test page
    items = list(range(25))
    page = Page.create(items, total=100, page=2, size=10)

    assert page.items == items
    assert page.total == 100
    assert page.page == 2
    assert page.size == 10
    assert page.pages == 10  # 100 / 10
    assert page.has_next is True
    assert page.has_prev is True


@pytest.mark.unit
def test_error_classes():
    """Test error class functionality."""
    from dotmac.platform.core.repository import (
        DuplicateEntityError,
        EntityNotFoundError,
        RepositoryError,
    )

    # Test basic repository error
    error = RepositoryError("Test error")
    assert str(error) == "Test error"

    # Test not found error
    not_found = EntityNotFoundError("User not found")
    assert "User not found" in str(not_found)
    assert isinstance(not_found, RepositoryError)

    # Test duplicate error
    duplicate = DuplicateEntityError("Duplicate email")
    assert "Duplicate email" in str(duplicate)
    assert isinstance(duplicate, RepositoryError)


@pytest.mark.unit
def test_utils_functionality():
    """Test utility functions."""
    from datetime import datetime

    from dotmac.platform.core.utils import generate_id, new_uuid, utcnow

    # Test ID generation
    id1 = generate_id()
    id2 = generate_id()
    assert isinstance(id1, str)
    assert isinstance(id2, str)
    assert id1 != id2

    # Test UUID generation
    uuid1 = new_uuid()
    assert isinstance(uuid1, str)
    assert len(uuid1) == 36  # Standard UUID string length

    # Test UTC now
    now = utcnow()
    assert isinstance(now, datetime)


@pytest.mark.unit
def test_validation_utilities():
    """Test validation utilities."""
    from dotmac.platform.core.validation import CommonValidators, ValidationError

    # Test email validation
    try:
        email = CommonValidators.validate_email_address("test@example.com")
        assert email == "test@example.com"  # Returns normalized email
    except ValidationError:
        assert False, "Valid email should not raise error"

    try:
        CommonValidators.validate_email_address("invalid")
        assert False, "Invalid email should raise error"
    except ValidationError:
        pass  # Expected

    # Test subdomain validation
    try:
        subdomain = CommonValidators.validate_subdomain("valid-subdomain")
        assert subdomain == "valid-subdomain"  # Returns normalized subdomain
    except ValidationError:
        assert False, "Valid subdomain should not raise error"

    try:
        CommonValidators.validate_subdomain("invalid subdomain")
        assert False, "Invalid subdomain should raise error"
    except ValidationError:
        pass  # Expected

    try:
        CommonValidators.validate_subdomain("a")  # Valid - single char is ok
        # No assertion needed, just shouldn't raise
    except ValidationError:
        assert False, "Single char subdomain should be valid"

    # Test phone validation
    try:
        phone = CommonValidators.validate_phone_number("+1234567890")
        assert phone == "+1234567890"  # Returns cleaned phone
    except ValidationError:
        assert False, "Valid phone should not raise error"

    try:
        phone = CommonValidators.validate_phone_number("1234567890")
        assert phone == "1234567890"  # Returns cleaned phone
    except ValidationError:
        assert False, "Valid phone should not raise error"

    try:
        CommonValidators.validate_phone_number("invalid")
        assert False, "Invalid phone should raise error"
    except ValidationError:
        pass  # Expected