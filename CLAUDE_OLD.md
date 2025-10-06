# Claude Effectiveness Guide - DotMac Platform Services

## Project Overview

**DotMac Platform Services** is a unified platform services package providing authentication, secrets management, and observability capabilities. It's built with Python 3.12+ using FastAPI, SQLAlchemy, and integrates with HashiCorp Vault, Redis, and OpenTelemetry.

### Key Technologies
- **Python**: 3.12+ (Poetry managed)
- **Web Framework**: FastAPI with Pydantic v2
- **Database**: SQLAlchemy 2.0+, PostgreSQL, SQLite (dev/test)
- **Auth**: JWT (PyJWT), RBAC, MFA (TOTP), Redis sessions
- **Secrets**: HashiCorp Vault/OpenBao integration
- **Observability**: OpenTelemetry (tracing, metrics, logging)
- **Testing**: pytest with async support, 90% coverage requirement

## Development Environment

### Essential Commands
```bash
# Setup
poetry install --with dev

# Testing (use these specific commands)
make test-fast          # Quick unit tests without coverage
make test-unit          # Unit tests with coverage
make test               # Full test suite
.venv/bin/pytest tests/ --ignore=tests/test_observability.py --ignore=tests/test_real_services.py --ignore=tests/auth/test_mfa_service.py -x

# Code Quality
make format            # Auto-format with black, isort, ruff
make lint              # Check formatting, linting, security
poetry run mypy src    # Type checking
```

### File Structure
```
src/dotmac/platform/
├── auth/              # JWT, RBAC, MFA, sessions
├── secrets/           # Vault integration, encryption
├── observability/     # OpenTelemetry, logging, metrics
├── tenant/            # Multi-tenant support
├── database/          # SQLAlchemy base, sessions
└── tasks/             # Background task decorators
```

## Code Standards & Conventions

### 1. PEP8 & Style Guidelines
**Strictly enforced by CI tools:**
- Line length: 100 characters max
- Black formatting (auto-applied)
- Import organization with isort
- Ruff linting rules (see pyproject.toml:130-158)
- No trailing whitespace, proper indentation

**Key Style Rules:**
```python
# Good - PEP8 compliant
def create_user_token(
    user_id: str,
    permissions: list[str],
    expire_minutes: int = 15,
) -> str:
    """Create JWT token with user permissions."""
    return jwt_service.create_access_token(
        subject=user_id,
        permissions=permissions,
        expire_minutes=expire_minutes,
    )

# Bad - violates line length and formatting
def create_user_token(user_id: str, permissions: list[str], expire_minutes: int = 15) -> str:
    return jwt_service.create_access_token(subject=user_id, permissions=permissions, expire_minutes=expire_minutes)
```

### 2. Pydantic v2 Patterns

**Required usage for ALL data validation:**
```python
from pydantic import BaseModel, Field, field_validator, ConfigDict

class UserClaims(BaseModel):
    """Example following project patterns."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    user_id: str = Field(alias="sub", description="User ID")
    tenant_id: str | None = Field(None, description="Tenant ID") 
    scopes: list[str] = Field(default_factory=list)
    
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("User ID cannot be empty")
        return v.strip()

# Always use for API request/response models
class APIKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
```

**Key Pydantic v2 Features to Use:**
- `Field()` with validation constraints
- `field_validator` for custom validation (replaces v1 validators)
- `model_config = ConfigDict()` (replaces v1 Config class)
- `str | None` union syntax (Python 3.10+ style)
- `model_validate()` method for parsing

### 3. Code Reuse Patterns

**ALWAYS check for existing implementations first:**
```bash
# Before implementing, search for similar patterns
rg "class.*Service" src/                    # Find service classes
rg "async def get_.*secret" src/secrets/    # Find secret retrieval patterns  
rg "def verify_.*token" src/auth/           # Find token verification patterns
rg "BaseModel" src/ --type py               # Find Pydantic models
```

**Common Reusable Components in Project:**
- `src/dotmac/platform/core/` - Base models, tenant context
- `src/dotmac/platform/auth/exceptions.py` - Standard auth exceptions
- `src/dotmac/platform/secrets/interfaces.py` - Provider interfaces
- `tests/conftest.py` - Test fixtures for DB/Redis/Vault/JWT

**Example: Reusing existing JWT validation:**
```python
# Good - reuse existing service
from dotmac.platform.auth.jwt_service import JWTService
from dotmac.platform.auth.dependencies import get_current_user

# In your FastAPI endpoint
@app.get("/protected")
async def protected_endpoint(
    current_user: UserClaims = Depends(get_current_user)
):
    return {"user_id": current_user.user_id}

# Bad - reimplementing JWT verification
def verify_my_own_token(token: str) -> dict:
    # Don't do this - use existing JWTService
    pass
```

### 4. Validation After Code Changes

**MANDATORY validation sequence after ANY code change:**

```bash
# 1. Format and fix obvious issues
make format

# 2. Run fast tests to catch immediate failures
make test-fast

# 3. Run comprehensive validation
make lint                    # Code quality checks
poetry run mypy src         # Type checking
make test-unit              # Full tests with coverage

# 4. Validate specific test scenarios
.venv/bin/pytest tests/auth/test_jwt_service_comprehensive.py -v
.venv/bin/pytest tests/auth/test_secrets_manager_comprehensive.py -v
```

**Test Validation Patterns (found in project):**
```python
# Follow existing validation test patterns
def test_jwt_token_validation_success(self, jwt_service):
    """Test successful token validation."""
    token = jwt_service.issue_access_token("user123")
    decoded = jwt_service.verify_token(token)
    assert decoded["sub"] == "user123"

def test_jwt_audience_and_issuer_validation(self):
    """Test audience/issuer validation."""
    jwt_service = JWTService(
        algorithm="HS256", 
        secret="test-secret",
        issuer="test-issuer",
        default_audience="test-audience"
    )
    
    token = jwt_service.issue_access_token("user123")
    decoded = jwt_service.verify_token(token)
    assert decoded["iss"] == "test-issuer" 
    assert decoded["aud"] == "test-audience"

# Always test validation failures
def test_validation_failure(self, basic_secrets):
    """Test validation error handling."""
    def failing_validator(secret_data, metadata):
        raise SecretValidationError("Validation failed")
    
    basic_secrets.add_validator("test/path", failing_validator)
    
    with pytest.raises(SecretValidationError):
        await basic_secrets.get_custom_secret("test/path")
```

## Architecture Patterns

### Service Layer Pattern
```python
# Follow existing service patterns
class MyService:
    def __init__(
        self,
        dependency: SomeDependency,
        config: Optional[MyConfig] = None,
    ):
        self._dependency = dependency
        self._config = config or MyConfig()
    
    async def do_something(self, input_data: MyRequest) -> MyResponse:
        # Validate input with Pydantic
        validated_input = MyRequest.model_validate(input_data)
        
        # Business logic
        result = await self._dependency.perform_action(validated_input.field)
        
        # Return validated response
        return MyResponse.model_validate(result)
```

### Error Handling Pattern
```python
# Reuse existing exception classes
from dotmac.platform.auth.exceptions import AuthError, TokenExpired
from dotmac.platform.secrets.exceptions import SecretNotFoundError

# Follow project error handling patterns  
try:
    secret = await secrets_manager.get_custom_secret("path/to/secret")
except SecretNotFoundError:
    logger.warning("Secret not found: path/to/secret")
    raise HTTPException(status_code=404, detail="Secret not found")
except Exception as e:
    logger.error("Unexpected error: %s", e)
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Async/Await Consistency
```python
# All I/O operations must be async - follow project patterns
class MySecretsProvider(SecretsProvider):
    async def get_secret(self, path: str) -> dict[str, Any]:
        # Good - async I/O
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.example.com/{path}") as response:
                return await response.json()
    
    async def set_secret(self, path: str, secret_data: dict[str, Any]) -> None:
        # Follow interface pattern
        pass
```

## Testing Requirements & Patterns

### Coverage Standards (Enforced by CI)
- **Line coverage**: 85% baseline (realistic with full test suite)
- **Diff coverage**: 95% required for new code changes
- **Branch coverage**: Enabled via `--cov-branch`
- Use markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`

**Note**: CI runs full test suite excluding integration/slow tests (~6,146 tests) to achieve comprehensive coverage while maintaining fast feedback.

### Validation Test Patterns
```python
# Follow project validation testing patterns
class TestJWTServiceValidation:
    def test_jwt_token_validation_success(self, jwt_service):
        """Test successful validation - positive case."""
        token = jwt_service.issue_access_token("user123")
        decoded = jwt_service.verify_token(token) 
        assert decoded["sub"] == "user123"
    
    def test_jwt_token_validation_failure_expired(self, jwt_service):
        """Test validation failure - negative case."""
        # Create expired token
        with patch('time.time', return_value=time.time() - 3600):
            token = jwt_service.issue_access_token("user123")
        
        with pytest.raises(TokenExpired):
            jwt_service.verify_token(token)
    
    def test_jwt_audience_and_issuer_validation(self):
        """Test specific validation rules."""
        service = JWTService(
            algorithm="HS256",
            secret="test-secret", 
            issuer="correct-issuer",
            default_audience="correct-audience"
        )
        
        token = service.issue_access_token("user123")
        decoded = service.verify_token(token)
        
        # Validate required claims
        assert decoded["iss"] == "correct-issuer"
        assert decoded["aud"] == "correct-audience"
```

### Pydantic Validation Testing
```python
def test_user_claims_validation():
    """Test Pydantic model validation."""
    # Valid data
    claims = UserClaims(sub="user123", scopes=["read", "write"])
    assert claims.user_id == "user123"
    assert claims.scopes == ["read", "write"]
    
    # Invalid data - test validation failures
    with pytest.raises(ValidationError):
        UserClaims(sub="")  # Empty user_id should fail
        
    with pytest.raises(ValidationError):
        UserClaims(sub="user123", invalid_field="value")  # Extra fields forbidden
```

## Key Workflow

### 1. Before Making Changes
```bash
# Understand existing patterns
rg "similar_function_name" src/
read existing_similar_file.py
check tests/test_similar_functionality.py
```

### 2. During Development  
- Use Pydantic v2 for ALL data validation
- Follow PEP8 (enforced by tools)
- Reuse existing services, exceptions, patterns
- Write tests alongside code (TDD approach)

### 3. After Each Change
```bash
make format              # Fix formatting
make test-fast          # Quick validation  
make lint               # Code quality
poetry run mypy src     # Type checking
```

### 4. Before Committing
```bash
make test-unit          # Full test suite with coverage
# Ensure all tests pass and coverage ≥85%
# New code should achieve ≥95% diff coverage
```

## Quick Reference

| Task | Command | Notes |
|------|---------|-------|
| Find similar code | `rg "pattern" src/` | Always check first |
| Run fast tests | `make test-fast` | Quick feedback |  
| Full validation | `make test-unit` | Required for PRs |
| Format code | `make format` | Auto-fixes most style issues |
| Type check | `poetry run mypy src` | Required passing |
| Find models | `rg "class.*BaseModel" src/` | Pydantic v2 patterns |
| Check validators | `rg "field_validator" src/` | Validation patterns |

## Common Pitfalls to Avoid

❌ **Don't reimplement existing functionality**
✅ **Always search and reuse existing code patterns**

❌ **Don't skip Pydantic validation** 
✅ **Use BaseModel for all data structures**

❌ **Don't ignore formatting/linting**
✅ **Run `make format` and `make lint` frequently**

❌ **Don't write code without tests**
✅ **Follow TDD - write tests first or alongside code**

❌ **Don't commit without validation**
✅ **Always run full test suite with coverage checks**

This guide emphasizes the project's commitment to code quality, proper validation, and systematic reuse of existing patterns.