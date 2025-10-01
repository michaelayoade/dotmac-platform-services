# Test Fixture Optimization Guide

This guide explains how to use the optimized shared fixtures to reduce duplication and improve test maintainability.

## Overview

The test suite now includes shared fixtures that provide common test objects and mocks. This reduces code duplication and ensures consistency across tests.

## Available Shared Fixtures

### User Authentication Fixtures

```python
# Standard test user with basic permissions
def test_my_endpoint(mock_user_info):
    # mock_user_info provides: user_id, username, email, permissions=["read", "write"]
    pass

# Admin user with elevated permissions
def test_admin_endpoint(admin_user_info):
    # admin_user_info provides: permissions=["admin", "read", "write", "delete"]
    pass

# Read-only user with limited permissions
def test_readonly_endpoint(readonly_user_info):
    # readonly_user_info provides: permissions=["read"]
    pass
```

### Service Mock Fixtures

```python
# Generic async service mock
def test_with_generic_service(mock_async_service):
    mock_async_service.some_method.return_value = "result"
    pass

# Specific service mocks with pre-configured methods
def test_user_operations(mock_user_service):
    # Pre-configured: get_user, create_user, update_user, delete_user, list_users
    mock_user_service.get_user.return_value = user_data
    pass

def test_customer_operations(mock_customer_service):
    # Pre-configured: get_customer, create_customer, update_customer, delete_customer, list_customers
    pass

def test_auth_operations(mock_auth_service):
    # Pre-configured: authenticate, create_token, validate_token, revoke_token
    pass
```

### Database and Storage Fixtures

```python
def test_database_operations(mock_database_manager):
    # Pre-configured: get_session, execute_query, get_connection, close
    pass

def test_redis_operations(mock_redis_client):
    # Pre-configured: get, set, delete, exists, expire, flushdb
    pass

def test_file_operations(mock_file_storage):
    # Pre-configured: upload, download, delete, list_files, get_url
    pass
```

### Configuration and Data Fixtures

```python
def test_with_settings(mock_settings):
    # Pre-configured with test-safe settings
    # Environment: test, debug: True, telemetry disabled
    pass

def test_with_test_ids(test_user_id, test_tenant_id):
    # Provides consistent UUIDs for testing
    pass

def test_with_fixed_time(fixed_datetime):
    # Provides: datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    pass
```

### HTTP and API Fixtures

```python
def test_http_client(mock_http_client):
    # Pre-configured: get, post, put, delete, close
    pass

def test_api_response(sample_api_response):
    # Provides: {"success": True, "data": {...}, "message": "Success"}
    pass

def test_error_response(sample_error_response):
    # Provides: {"success": False, "error": "Not Found", "message": "..."}
    pass
```

### Data Transfer Fixtures (when available)

```python
def test_data_import(transfer_config, import_options):
    # Provides pre-configured TransferConfig and ImportOptions
    pass

def test_data_export(export_options):
    # Provides pre-configured ExportOptions
    pass
```

### Parametrized Fixtures

```python
def test_different_user_roles(user_role):
    # Automatically tests with: "admin", "user", "readonly"
    assert user_role in ["admin", "user", "readonly"]

def test_different_formats(data_format):
    # Automatically tests with: "json", "csv", "xml"
    assert data_format in ["json", "csv", "xml"]
```

## Migration Examples

### Before (Duplicated Fixtures)

```python
# tests/test_my_module.py
@pytest.fixture
def mock_current_user():
    return UserInfo(
        user_id="550e8400-e29b-41d4-a716-446655440000",
        username="testuser",
        email="user@example.com",
        roles=["user"]
    )

@pytest.fixture
def mock_service():
    return AsyncMock()

def test_my_function(mock_current_user, mock_service):
    # test code
    pass
```

### After (Using Shared Fixtures)

```python
# tests/test_my_module.py
# No fixture definitions needed!

def test_my_function(mock_user_info, mock_customer_service):
    # Same test code, but using shared fixtures
    pass
```

## Factory Functions

For dynamic test data creation:

```python
def test_with_dynamic_service():
    # Create a service mock with specific methods
    service = create_mock_service("my_service", ["method1", "method2"])
    assert service.name == "my_service"
    service.method1.return_value = "test"

def test_with_dynamic_data():
    # Create test data for different model types
    user_data = create_test_data("user", email="custom@example.com")
    customer_data = create_test_data("customer", name="Custom Customer")
```

## Best Practices

### 1. Use Specific Fixtures When Available

```python
# Good - uses specific fixture
def test_customer_crud(mock_customer_service):
    pass

# Less ideal - uses generic fixture
def test_customer_crud(mock_async_service):
    pass
```

### 2. Combine Fixtures for Complex Scenarios

```python
def test_authenticated_customer_operation(mock_user_info, mock_customer_service, mock_settings):
    # Test with authenticated user, customer service, and test settings
    pass
```

### 3. Use Parametrized Fixtures for Multiple Test Cases

```python
def test_user_permissions(user_role, mock_user_info):
    # This test will run 3 times: admin, user, readonly
    if user_role == "admin":
        # admin-specific assertions
        pass
```

### 4. Clean Up Resources

```python
def test_file_operations(cleanup_temp_files):
    temp_file = "/tmp/test_file.txt"
    cleanup_temp_files(temp_file)  # Will be cleaned up automatically

    # Create and use temp file
    with open(temp_file, 'w') as f:
        f.write("test content")
```

## Adding New Shared Fixtures

When adding new shared fixtures to `tests/shared_fixtures.py`:

1. **Follow the existing patterns**:
   ```python
   @pytest.fixture
   def my_new_fixture() -> MyType:
       """Description of what this fixture provides."""
       return MyType(...)
   ```

2. **Add to the appropriate section** (User, Service, Database, etc.)

3. **Update the `__all__` list** or the dynamic `_all_fixtures` list

4. **Handle optional dependencies** gracefully:
   ```python
   if HAS_MY_DEPENDENCY:
       @pytest.fixture
       def my_conditional_fixture():
           # fixture implementation
           pass
   ```

5. **Document in this guide** with usage examples

## Troubleshooting

### ImportError: module has no attribute 'fixture_name'

The fixture might be conditionally defined. Check if the required dependencies are available:

```python
# In shared_fixtures.py
try:
    from dotmac.platform.some_module import SomeModel
    HAS_SOME_MODEL = True
except ImportError:
    HAS_SOME_MODEL = False

if HAS_SOME_MODEL:
    @pytest.fixture
    def some_model_fixture():
        return SomeModel(...)
```

### Validation Errors

Ensure shared fixtures use the correct model fields:

```python
# Check the actual model definition
from dotmac.platform.auth.core import UserInfo
# UserInfo expects: user_id, email, username, roles, permissions, tenant_id
```

### Fixture Conflicts

If you need a different configuration, create a test-specific fixture:

```python
@pytest.fixture
def custom_user_info():
    """Custom user info for this specific test."""
    return UserInfo(
        user_id="custom-user-id",
        username="custom",
        # ... other fields
    )

def test_with_custom_user(custom_user_info):
    # Uses your custom fixture instead of shared one
    pass
```

## Benefits

1. **Reduced Duplication**: No more copy-paste fixture definitions
2. **Consistency**: Same test data across all tests
3. **Maintenance**: Change fixture in one place, affects all tests
4. **Discoverability**: All fixtures documented and available in IDE
5. **Type Safety**: Fixtures are properly typed
6. **Test Speed**: Shared fixtures can be cached/reused

## Migration Checklist

- [ ] Identify duplicate fixtures in your test files
- [ ] Replace with appropriate shared fixtures
- [ ] Remove local fixture definitions
- [ ] Run tests to ensure compatibility
- [ ] Update test documentation if needed