"""Configuration classes for auth module components."""

from pydantic import BaseModel, Field


class RBACConfig(BaseModel):
    """RBAC configuration."""

    enable_rbac: bool = Field(True, description="Enable RBAC")
    enable_dynamic_permissions: bool = Field(
        False, description="Enable dynamic permission checking"
    )
    cache_ttl: int = Field(300, description="Permission cache TTL in seconds")
    default_role: str = Field("user", description="Default role for new users")
    super_admin_role: str = Field("admin", description="Super admin role name")
    permission_delimiter: str = Field(":", description="Permission string delimiter")
    max_roles_per_user: int = Field(10, description="Maximum roles per user")
    enable_inheritance: bool = Field(True, description="Enable role inheritance")


class SessionConfig(BaseModel):
    """Session management configuration."""

    backend: str = Field("redis", description="Session backend: redis, memory, or database")
    session_key_prefix: str = Field("session:", description="Session key prefix")
    session_ttl: int = Field(86400, description="Session TTL in seconds (24 hours)")
    cookie_name: str = Field("session_id", description="Session cookie name")
    cookie_secure: bool = Field(True, description="Secure cookie flag")
    cookie_httponly: bool = Field(True, description="HTTP-only cookie flag")
    cookie_samesite: str = Field("lax", description="SameSite cookie attribute")
    cookie_domain: str | None = Field(None, description="Cookie domain")
    max_sessions_per_user: int = Field(10, description="Maximum concurrent sessions per user")
    enable_session_extension: bool = Field(True, description="Auto-extend session on activity")


class MFAConfig(BaseModel):
    """Multi-factor authentication configuration."""

    enable_mfa: bool = Field(False, description="Enable MFA globally")
    totp_issuer: str = Field("DotMac Platform", description="TOTP issuer name")
    totp_window: int = Field(1, description="TOTP validation window")
    totp_digits: int = Field(6, description="TOTP code length")
    totp_algorithm: str = Field("SHA1", description="TOTP algorithm")
    totp_interval: int = Field(30, description="TOTP time interval in seconds")
    backup_codes_count: int = Field(10, description="Number of backup codes to generate")
    backup_code_length: int = Field(8, description="Backup code length")
    sms_provider: str | None = Field(None, description="SMS provider: twilio, aws, etc.")
    email_provider: str | None = Field(None, description="Email provider for MFA codes")
    max_attempts: int = Field(3, description="Maximum MFA verification attempts")
    lockout_duration: int = Field(900, description="Account lockout duration in seconds")


class OAuthConfig(BaseModel):
    """OAuth provider configuration."""

    enable_oauth: bool = Field(False, description="Enable OAuth authentication")
    providers: list[str] = Field(default_factory=list, description="Enabled OAuth providers")
    google_client_id: str | None = Field(None, description="Google OAuth client ID")
    google_client_secret: str | None = Field(None, description="Google OAuth client secret")
    github_client_id: str | None = Field(None, description="GitHub OAuth client ID")
    github_client_secret: str | None = Field(None, description="GitHub OAuth client secret")
    microsoft_client_id: str | None = Field(None, description="Microsoft OAuth client ID")
    microsoft_client_secret: str | None = Field(None, description="Microsoft OAuth client secret")
    redirect_uri_base: str = Field("http://localhost:8000", description="OAuth redirect URI base")
    state_ttl: int = Field(600, description="OAuth state parameter TTL in seconds")
    auto_create_users: bool = Field(True, description="Auto-create users on OAuth login")
    require_email_verification: bool = Field(
        False, description="Require email verification for OAuth users"
    )
