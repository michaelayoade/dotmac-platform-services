# Dependency Update Checklist

This checklist ensures critical security updates are tracked and applied promptly.

---

## 🚨 Critical Updates - High Priority

### ⏰ Pending Security Updates

| Package | Current | Target | Priority | Status | Notes |
|---------|---------|--------|----------|--------|-------|
| **pip** | 25.2 | **25.3** | 🔴 HIGH | ⏳ Waiting for release | **CVE-2025-8869**: Tarfile link escape vulnerability. Update IMMEDIATELY when 25.3 is released. See `.pip-audit-ignore.json` and `PIP_AUDIT_SECURITY_ASSESSMENT.md` |

**Action Required**:
```bash
# Check weekly for pip 25.3 release
poetry run pip index versions pip | head -20

# When 25.3 is available, update immediately:
poetry run pip install --upgrade pip
poetry run pip --version  # Verify 25.3+
poetry run pip-audit      # Should clear GHSA-4xh5-x5gv-qwph

# Remove from .pip-audit-ignore.json after update
# Update PIP_AUDIT_SECURITY_ASSESSMENT.md to reflect fix
```

---

## 📋 Regular Dependency Updates

### Weekly Tasks
- [ ] Check for pip 25.3 release (until available)
- [ ] Review GitHub security alerts
- [ ] Check Poetry lock file for outdated critical packages

### Monthly Tasks
- [ ] Run full `poetry update` for non-breaking updates
- [ ] Run `poetry run pip-audit` and review new vulnerabilities
- [ ] Review `.pip-audit-ignore.json` expiration dates
- [ ] Update Python dependencies with security patches

### Quarterly Tasks
- [ ] Review ecdsa usage in codebase (ensure we still don't use ECDSA signing)
- [ ] Check if SendGrid has moved away from ecdsa
- [ ] Audit all cryptographic dependencies
- [ ] Review and update `PIP_AUDIT_SECURITY_ASSESSMENT.md`

---

## 🔄 Update Process

### 1. Pre-Update Assessment
```bash
# Check current vulnerabilities
poetry run pip-audit --desc

# List outdated packages
poetry show --outdated

# Review changelogs for breaking changes
# Check GitHub releases for major version bumps
```

### 2. Apply Updates
```bash
# Update specific package (recommended)
poetry update <package-name>

# Or update all (with caution)
poetry update

# Verify lock file changes
git diff poetry.lock
```

### 3. Testing
```bash
# Run full test suite
make test

# Run security checks
poetry run pip-audit
poetry run bandit -r src/ -ll
poetry run mypy src

# Test in staging environment
# Smoke test critical features
```

### 4. Post-Update Verification
```bash
# Verify no new vulnerabilities introduced
poetry run pip-audit

# Check for dependency conflicts
poetry check

# Update security assessment if needed
vim PIP_AUDIT_SECURITY_ASSESSMENT.md
```

---

## 🛡️ Security Exception Management

### Current Accepted Vulnerabilities

Tracked in `.pip-audit-ignore.json`:

1. **pip 25.2** (GHSA-4xh5-x5gv-qwph)
   - **Expires**: When pip 25.3 is released (or 2025-12-31 hard deadline)
   - **Next Review**: 2025-11-07
   - **Action**: Update to pip 25.3 immediately when available

2. **ecdsa 0.19.1** (GHSA-wj6h-64fc-37mp)
   - **Expires**: No expiration (maintainer won't fix)
   - **Next Review**: 2026-01-07 (quarterly)
   - **Action**: Monitor for SendGrid updates; review if we add ECDSA signing

### Exception Review Process

**When reviewing exceptions**:
1. Check if vulnerability still exists in current version
2. Verify mitigations are still in place
3. Re-assess risk level based on code changes
4. Update `.pip-audit-ignore.json` with new review date
5. Update `PIP_AUDIT_SECURITY_ASSESSMENT.md` if risk changes

**When to remove exceptions**:
- Package is updated to fixed version
- Package is removed from dependencies
- Risk is no longer acceptable (code changes, new attack vectors)
- Exception expiration date is reached

---

## 📊 Dependency Categories

### Critical (Update Immediately)
- Security vulnerabilities with available fixes
- Exploitable bugs in production
- Data loss or corruption issues

### High Priority (Update Within 1 Week)
- Security vulnerabilities with workarounds
- Major bug fixes
- Performance improvements
- Compatibility with new Python versions

### Medium Priority (Monthly Updates)
- Minor bug fixes
- Feature additions
- Non-breaking API changes
- Documentation improvements

### Low Priority (Quarterly Updates)
- Dependency updates without user-facing changes
- Internal refactoring
- Development dependencies

---

## 🚫 Update Restrictions

### DO NOT Update Without Review
- Major version bumps (e.g., 1.x → 2.x)
- Core dependencies: FastAPI, SQLAlchemy, Pydantic
- Authentication libraries: PyJWT, python-multipart
- Database drivers: asyncpg, psycopg2

### Locked Versions (Pinned for Stability)
_Document any intentionally locked versions here_

Current pins:
- None (all managed via poetry.lock)

---

## 🔔 Notification Channels

### Automated Alerts
- [ ] **GitHub Dependabot**: Enabled for security updates
- [ ] **Renovate Bot**: Configure for automated PRs
- [ ] **PyPI Security Advisories**: Subscribe to relevant packages

### Manual Monitoring
- Weekly: Check https://pypi.org/project/pip/#history for pip 25.3
- Monthly: Review GitHub Security tab
- Quarterly: Scan https://github.com/advisories for Python vulnerabilities

---

## 📝 Update Log Template

When performing updates, document them:

```markdown
## [Date] - Dependency Update

**Packages Updated**:
- package-name: old-version → new-version

**Reason**: Security fix / Feature / Bug fix

**Testing**: ✅ All tests pass / ⚠️ Known issues

**Vulnerabilities Fixed**:
- CVE-XXXX-XXXX (if applicable)

**Breaking Changes**: None / List changes

**Rollback Plan**: `poetry install` (uses lock file)
```

---

## 🎯 Goals

- **Security**: Zero HIGH severity vulnerabilities with available fixes
- **Freshness**: Dependencies updated within 30 days of non-breaking releases
- **Stability**: 100% test coverage before and after updates
- **Documentation**: All exceptions and pins documented with rationale

---

## ✅ Quick Reference

```bash
# Daily/Weekly
poetry run pip index versions pip | grep "25.3"  # Check pip 25.3

# Monthly
poetry show --outdated
poetry update
make test
poetry run pip-audit

# Quarterly
vim .pip-audit-ignore.json  # Review exceptions
vim PIP_AUDIT_SECURITY_ASSESSMENT.md  # Update risk assessment
```

---

**Last Updated**: October 7, 2025
**Next Scheduled Review**: November 7, 2025 (pip 25.3 check)
**Owner**: Security Team
