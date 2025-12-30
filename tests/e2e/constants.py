"""Shared constants for E2E tests.

Centralizes test data to avoid hard-coded values scattered across test files.
"""

# =============================================================================
# Test Credentials
# =============================================================================

TEST_PASSWORD = "TestPassword123!"
TEST_PASSWORD_WEAK = "weak"
TEST_PASSWORD_NEW = "NewSecurePassword456!"

# =============================================================================
# Test User Data
# =============================================================================

TEST_USER_EMAIL = "e2e-test@example.com"
TEST_USER_USERNAME = "e2e-test-user"
TEST_ADMIN_EMAIL = "platform-admin@example.com"

# =============================================================================
# Test Tenant Data
# =============================================================================

TEST_TENANT_ID = "e2e-test-tenant"
TEST_TENANT_NAME = "E2E Test Tenant"

# =============================================================================
# JWT Configuration
# =============================================================================

TEST_JWT_SECRET = "test-secret-key-for-e2e-tests"
TEST_JWT_ALGORITHM = "HS256"

# =============================================================================
# API Endpoints
# =============================================================================

class Endpoints:
    """API endpoint paths for E2E tests."""

    # Auth
    AUTH_LOGIN = "/api/v1/auth/login"
    AUTH_REGISTER = "/api/v1/auth/register"
    AUTH_LOGOUT = "/api/v1/auth/logout"
    AUTH_REFRESH = "/api/v1/auth/refresh"
    AUTH_ME = "/api/v1/auth/me"
    AUTH_PASSWORD_RESET = "/api/v1/auth/password-reset"
    AUTH_PASSWORD_RESET_CONFIRM = "/api/v1/auth/password-reset/confirm"
    AUTH_VERIFY_EMAIL = "/api/v1/auth/verify-email"
    AUTH_2FA_SETUP = "/api/v1/auth/2fa/setup"
    AUTH_2FA_VERIFY = "/api/v1/auth/2fa/verify"

    # Users
    USERS = "/api/v1/users"
    USERS_ME = "/api/v1/users/me"
    USERS_BULK = "/api/v1/users/bulk"

    # Tenants
    TENANTS = "/api/v1/tenants"
    TENANT_SETTINGS = "/api/v1/tenant/settings"
    TENANT_INVITATIONS = "/api/v1/tenant/invitations"

    # Billing
    BILLING_PRODUCTS = "/api/v1/billing/products"
    BILLING_PRICES = "/api/v1/billing/prices"
    BILLING_SUBSCRIPTIONS = "/api/v1/billing/subscriptions"
    BILLING_INVOICES = "/api/v1/billing/invoices"
    BILLING_USAGE = "/api/v1/billing/usage"

    # Platform Admin
    PLATFORM_HEALTH = "/api/v1/platform/health"
    PLATFORM_TENANTS = "/api/v1/platform/tenants"
    PLATFORM_STATS = "/api/v1/platform/stats"

    # Onboarding
    ONBOARDING_START = "/api/v1/onboarding/start"
    ONBOARDING_SIGNUP = "/api/v1/onboarding/public/signup"

# =============================================================================
# HTTP Status Code Groups (for clear test assertions)
# =============================================================================

class StatusCodes:
    """Expected status code constants for clearer assertions."""

    SUCCESS = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE = 422
    INTERNAL_ERROR = 500

# =============================================================================
# Test Data Generators
# =============================================================================

def unique_email(prefix: str = "test") -> str:
    """Generate a unique email for testing."""
    import uuid
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"

def unique_username(prefix: str = "user") -> str:
    """Generate a unique username for testing."""
    import uuid
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def unique_tenant_name(prefix: str = "tenant") -> str:
    """Generate a unique tenant name for testing."""
    import uuid
    return f"{prefix}-{uuid.uuid4().hex[:8]}"
