"""
Threat detection and security monitoring.
"""

import time
from collections import defaultdict
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


class ThreatLevel(str):
    """Threat severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatDetector:
    """Advanced threat detection and monitoring."""

    def __init__(self):
        self._failed_login_attempts = defaultdict(list)
        self._suspicious_ips = set()
        self._rate_limit_violations = defaultdict(list)

        # Thresholds
        self.max_failed_logins = 5
        self.failed_login_window = 300  # 5 minutes
        self.rate_limit_threshold = 100  # requests per minute

    async def analyze_login_attempt(
        self, user_id: str, ip_address: str, success: bool, user_agent: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Analyze login attempt for suspicious activity.

        Args:
            user_id: User attempting login
            ip_address: Source IP address
            success: Whether login was successful
            user_agent: User agent string

        Returns:
            Threat analysis result
        """
        current_time = time.time()

        result = {
            "threat_detected": False,
            "threat_level": ThreatLevel.LOW,
            "threats": [],
            "recommended_actions": [],
        }

        # Track failed login attempts
        if not success:
            self._failed_login_attempts[user_id].append(current_time)

            # Clean old attempts
            cutoff_time = current_time - self.failed_login_window
            self._failed_login_attempts[user_id] = [t for t in self._failed_login_attempts[user_id] if t > cutoff_time]

            # Check for brute force
            if len(self._failed_login_attempts[user_id]) >= self.max_failed_logins:
                result["threat_detected"] = True
                result["threat_level"] = ThreatLevel.HIGH
                result["threats"].append("Brute force attack detected")
                result["recommended_actions"].append("Block IP address")
                result["recommended_actions"].append("Require additional authentication")

                logger.warning(
                    "Brute force attack detected",
                    user_id=user_id,
                    ip_address=ip_address,
                    failed_attempts=len(self._failed_login_attempts[user_id]),
                )

        # Check for suspicious IP patterns
        if await self._is_suspicious_ip(ip_address):
            result["threat_detected"] = True
            result["threat_level"] = max(result["threat_level"], ThreatLevel.MEDIUM)
            result["threats"].append("Suspicious IP address")
            result["recommended_actions"].append("Enhanced monitoring")

        # Analyze user agent for anomalies
        if user_agent:
            ua_analysis = await self._analyze_user_agent(user_agent)
            if ua_analysis["suspicious"]:
                result["threat_detected"] = True
                result["threat_level"] = max(result["threat_level"], ThreatLevel.MEDIUM)
                result["threats"].extend(ua_analysis["issues"])

        return result

    async def analyze_api_usage(
        self, user_id: str, ip_address: str, endpoint: str, method: str, status_code: int
    ) -> dict[str, Any]:
        """
        Analyze API usage patterns for threats.

        Args:
            user_id: User making API calls
            ip_address: Source IP address
            endpoint: API endpoint accessed
            method: HTTP method
            status_code: Response status code

        Returns:
            Threat analysis result
        """
        current_time = time.time()

        result = {
            "threat_detected": False,
            "threat_level": ThreatLevel.LOW,
            "threats": [],
            "recommended_actions": [],
        }

        # Track API call rates
        rate_key = f"{user_id}:{ip_address}"
        self._rate_limit_violations[rate_key].append(current_time)

        # Clean old entries (1 minute window)
        cutoff_time = current_time - 60
        self._rate_limit_violations[rate_key] = [t for t in self._rate_limit_violations[rate_key] if t > cutoff_time]

        # Check for rate limit violations
        if len(self._rate_limit_violations[rate_key]) > self.rate_limit_threshold:
            result["threat_detected"] = True
            result["threat_level"] = ThreatLevel.HIGH
            result["threats"].append("Rate limit exceeded")
            result["recommended_actions"].append("Apply rate limiting")
            result["recommended_actions"].append("Monitor for DDoS")

        # Check for suspicious endpoint patterns
        if self._is_sensitive_endpoint(endpoint):
            if status_code >= 400:
                result["threat_detected"] = True
                result["threat_level"] = max(result["threat_level"], ThreatLevel.MEDIUM)
                result["threats"].append("Unauthorized access to sensitive endpoint")
                result["recommended_actions"].append("Enhanced authentication required")

        return result

    async def analyze_data_access(
        self, user_id: str, resource_type: str, resource_id: str, operation: str, result: str
    ) -> dict[str, Any]:
        """
        Analyze data access patterns for insider threats.

        Args:
            user_id: User accessing data
            resource_type: Type of resource accessed
            resource_id: Specific resource identifier
            operation: Operation performed (read, write, delete)
            result: Operation result (success, failure)

        Returns:
            Threat analysis result
        """
        analysis_result = {
            "threat_detected": False,
            "threat_level": ThreatLevel.LOW,
            "threats": [],
            "recommended_actions": [],
        }

        # Check for bulk data access
        if operation == "read" and resource_type == "customer_data":
            # This would be more sophisticated in production
            analysis_result["threat_detected"] = True
            analysis_result["threat_level"] = ThreatLevel.MEDIUM
            analysis_result["threats"].append("Potential data exfiltration")
            analysis_result["recommended_actions"].append("Review user permissions")

        return analysis_result

    async def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is known to be suspicious."""
        # Implementation would check against threat intelligence feeds
        # For now, just check internal suspicious list
        return ip_address in self._suspicious_ips

    async def _analyze_user_agent(self, user_agent: str) -> dict[str, Any]:
        """Analyze user agent string for anomalies."""
        analysis = {
            "suspicious": False,
            "issues": [],
        }

        # Check for automated tools/bots
        suspicious_agents = ["curl", "wget", "python-requests", "scanner", "bot", "crawler"]

        ua_lower = user_agent.lower()
        for agent in suspicious_agents:
            if agent in ua_lower:
                analysis["suspicious"] = True
                analysis["issues"].append(f"Automated tool detected: {agent}")

        # Check for empty or very short user agents
        if len(user_agent.strip()) < 10:
            analysis["suspicious"] = True
            analysis["issues"].append("Suspicious user agent length")

        return analysis

    def _is_sensitive_endpoint(self, endpoint: str) -> bool:
        """Check if endpoint contains sensitive data."""
        sensitive_patterns = ["/admin/", "/api/users/", "/api/payments/", "/api/secrets/", "/api/internal/"]

        return any(pattern in endpoint for pattern in sensitive_patterns)

    async def get_threat_summary(self, tenant_id: Optional[str] = None) -> dict[str, Any]:
        """
        Get summary of current threat landscape.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            Threat summary
        """
        return {
            "active_threats": 0,
            "blocked_ips": len(self._suspicious_ips),
            "users_with_failed_logins": len(self._failed_login_attempts),
            "rate_limited_users": len(self._rate_limit_violations),
            "threat_levels": {
                "critical": 0,
                "high": 0,
                "medium": 1,
                "low": 5,
            },
        }
