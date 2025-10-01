# Security Extension Points

This boilerplate provides foundational security patterns with clear extension points for production use.

## 🔐 Authentication & Authorization

### JWT Token Management
- **Current**: Basic JWT generation/verification with JTI (unique token ID)
- **Extension Point**: Token revocation blacklist in `src/dotmac/platform/auth/core.py:200-204`
- **Pattern**: Use Redis to store revoked JTIs until expiry

```python
# Example: Enable token revocation
async def revoke_token(jti: str, exp: datetime):
    ttl = (exp - datetime.now(UTC)).total_seconds()
    await redis_client.setex(f"blacklist:{jti}", ttl, "1")
```

### Session Management
- **Current**: Redis-based session storage with user data
- **Extension Point**: Add device tracking and concurrent session limits
- **Location**: `src/dotmac/platform/auth/core.py` - SessionManager class

### Password Security
- **Current**: Bcrypt hashing via passlib (consistent across all components)
- **Extension Point**: Add password policy enforcement in UserService
- **Location**: `src/dotmac/platform/user_management/service.py`

## 🚦 Rate Limiting

### Current Setup
- **Infrastructure**: SlowAPI configured with Redis backend
- **Status**: ✅ Connected to FastAPI app in `main.py`
- **Usage**: Apply `@rate_limit("5/minute")` decorator to endpoints

### Extension Points
```python
# Example: Protect auth endpoints
from dotmac.platform.rate_limiting import rate_limit

@rate_limit("5/minute")  # Prevent brute force
async def login(request: LoginRequest): ...

@rate_limit("3/minute")  # Prevent reset spam
async def request_password_reset(request: PasswordResetRequest): ...
```

## 🔍 Audit & Compliance

### User Lifecycle
- **Current**: Basic CRUD operations with structured logging
- **Extension Points**:
  - Add audit trail table for user changes
  - Implement soft deletes (add `deleted_at` field)
  - Track admin actions with `performed_by` field

### Compliance Patterns
```python
# Example: Add audit logging
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    action = Column(String)  # CREATE, UPDATE, DELETE, LOGIN
    changes = Column(JSON)   # Before/after values
    performed_by = Column(UUID)  # Admin who made change
    ip_address = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
```

## 🛡️ Security Headers & Middleware

### Current Middleware
- CORS (configurable)
- GZip compression
- Rate limiting (configured)

### Extension Points
Add security headers middleware:

```python
# Example: Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## 🔧 Production Hardening Checklist

### Immediate (Pre-Production)
- [ ] Enable rate limiting on auth endpoints
- [ ] Add security headers middleware
- [ ] Configure HTTPS/TLS certificates
- [ ] Set up environment-specific secrets management

### Short-term (Production Ready)
- [ ] Implement token revocation blacklist
- [ ] Add audit logging for user changes
- [ ] Configure session timeout policies
- [ ] Set up monitoring and alerting

### Compliance (As Needed)
- [ ] **GDPR**: Add consent tracking, data retention policies
- [ ] **SOC2**: Comprehensive audit trails, access logging
- [ ] **HIPAA**: PHI access controls, encryption at rest
- [ ] **PCI DSS**: Payment data tokenization (if applicable)

## 📊 Observability

### Security Monitoring
- **Current**: Structured logging with user actions
- **Extension Point**: Add security event tracking
- **Location**: Throughout auth and user management modules

### Metrics to Track
- Failed login attempts per user/IP
- Password reset requests frequency
- Token generation/verification rates
- API endpoint usage patterns

## 🚀 Production Deployment

### Environment Variables
```bash
# Security Configuration
JWT_SECRET=your-strong-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
REDIS_CACHE_URL=redis://localhost:6379/1

# CORS (restrict in production)
CORS_ORIGINS=["https://yourdomain.com"]
```

### Security Best Practices
1. **Secrets Management**: Use environment variables or Vault
2. **Database**: Enable SSL, use connection pooling
3. **Redis**: Enable AUTH, use SSL in production
4. **Monitoring**: Set up alerts for security events
5. **Backups**: Regular database backups with encryption

## 🔗 External Dependencies

### Security-Related Libraries
- `passlib[bcrypt]` - Password hashing
- `python-jose[cryptography]` - JWT handling
- `slowapi` - Rate limiting
- `structlog` - Security event logging

### Integration Points
- **Email Service**: Password reset, welcome emails
- **Redis**: Session storage, rate limiting
- **Vault**: Secrets management (configured but optional)

This boilerplate provides a solid security foundation that can be extended based on your specific compliance and operational requirements.