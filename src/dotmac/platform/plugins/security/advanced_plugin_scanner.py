"""
Production-grade plugin security scanner with comprehensive threat detection.
Leverages existing DRY patterns and security frameworks.
"""

import ast
import hashlib

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from dotmac.platform.core.decorators import standard_exception_handler
from dotmac.platform.core.enhanced.exceptions import ValidationError
from dotmac.security.audit import get_audit_logger
from dotmac.platform.plugins.security.audit_monitor import UnifiedAuditMonitor

from ..core.exceptions import PluginSecurityError
from .plugin_sandbox import SecurityScanner

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger("plugins.security.scanner")
audit_logger = get_audit_logger()

@dataclass
class SecurityThreat:
    """Represents a security threat found in plugin code."""

    threat_type: str
    severity: str  # "critical", "high", "medium", "low"
    description: str
    location: str
    line_number: Optional[int] = None
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    cve_references: list[str] = field(default_factory=list)

@dataclass
class PluginSecurityReport:
    """Comprehensive security scan report."""

    plugin_id: str
    scan_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # File analysis
    file_hash: str = ""
    file_size: int = 0
    line_count: int = 0

    # Security assessment
    threats: list[SecurityThreat] = field(default_factory=list)
    risk_score: int = 0  # 0-100
    security_level: str = "unknown"  # "safe", "low", "medium", "high", "critical"

    # Code quality metrics
    complexity_score: int = 0
    dependency_count: int = 0
    api_calls: list[str] = field(default_factory=list)

    # Compliance
    passes_validation: bool = False
    certification_eligible: bool = False

    # Recommendations
    recommendations: list[str] = field(default_factory=list)
    required_permissions: list[str] = field(default_factory=list)

class AdvancedPluginSecurityScanner:
    """
    Production-grade plugin security scanner with comprehensive threat detection.
    """

    def __init__(self, audit_monitor: Optional[UnifiedAuditMonitor] = None):
        self.audit_monitor = audit_monitor  # Optional audit monitor, can be None
        self.security_manager = SecurityScanner()

        # Threat detection patterns
        self._threat_patterns = self._initialize_threat_patterns()
        self._dependency_allowlist = self._load_dependency_allowlist()
        self._api_patterns = self._initialize_api_patterns()

        # Security thresholds
        self.risk_thresholds = {"safe": 20, "low": 40, "medium": 60, "high": 80, "critical": 100}

    def _initialize_threat_patterns(self) -> dict[str, dict[str, Any]]:
        """Initialize threat detection patterns."""
        return {
            "dangerous_imports": {
                "pattern": r"import\s+(os|subprocess|sys|ctypes|socket|urllib|requests)",
                "severity": "high",
                "description": "Potentially dangerous system imports detected",
            },
            "eval_usage": {
                "pattern": r"\b(eval|exec|compile)\s*\(",
                "severity": "critical",
                "description": "Dynamic code execution functions detected",
            },
            "file_system_access": {
                "pattern": r"open\s*\(|pathlib|glob\.glob|os\.path",
                "severity": "medium",
                "description": "File system access detected",
            },
            "network_calls": {
                "pattern": r"(urllib|requests|socket|http)\.",
                "severity": "medium",
                "description": "Network communication detected",
            },
            "shell_commands": {
                "pattern": r"subprocess\.(run|call|Popen|check_output)",
                "severity": "critical",
                "description": "Shell command execution detected",
            },
            "environment_access": {
                "pattern": r"os\.environ|getenv",
                "severity": "medium",
                "description": "Environment variable access detected",
            },
            "pickle_usage": {
                "pattern": r"import\s+pickle|pickle\.",
                "severity": "high",
                "description": "Pickle deserialization vulnerability risk",
            },
            "sql_injection": {
                "pattern": r"execute\s*\(\s*[\"'].*%|format\s*\(.*\+",
                "severity": "high",
                "description": "Potential SQL injection vulnerability",
            },
        }

    def _load_dependency_allowlist(self) -> set[str]:
        """Load allowed dependencies."""
        return {
            "fastapi",
            "pydantic",
            "sqlalchemy",
            "httpx",
            "asyncio",
            "datetime",
            "json",
            "typing",
            "uuid",
            "logging",
            "dataclasses",
            "pathlib",
            "re",
            "hashlib",
            "base64",
        }

    def _initialize_api_patterns(self) -> dict[str, str]:
        """Initialize API call patterns for detection."""
        return {
            "database_access": r"(session\.|db\.|query\(|execute\()",
            "auth_bypass": r"(bypass|skip|ignore).*auth",
            "privilege_escalation": r"(admin|root|sudo|elevated)",
            "data_exfiltration": r"(send|post|upload|export).*data",
        }

    @standard_exception_handler
    async def scan_plugin(self, plugin_code: str, metadata: dict[str, Any]) -> PluginSecurityReport:
        """
        Perform comprehensive security scan of plugin code.
        """
        plugin_id = metadata.get("id", "unknown")

        # Initialize report
        report = PluginSecurityReport(plugin_id=plugin_id)

        # Basic file analysis
        report.file_hash = hashlib.sha256(plugin_code.encode()).hexdigest()
        report.file_size = len(plugin_code.encode())
        report.line_count = len(plugin_code.splitlines())

        if audit_logger:
            audit_logger.info(
                "Starting plugin security scan",
                extra={
                    "plugin_id": plugin_id,
                    "scan_id": report.scan_id,
                    "file_size": report.file_size,
                    "line_count": report.line_count,
                },
            )

        try:
            # Parse code to AST for deep analysis
            tree = ast.parse(plugin_code)

            # Run comprehensive security checks
            await self._analyze_code_patterns(plugin_code, report)
            await self._analyze_ast_structure(tree, report)
            await self._analyze_dependencies(tree, plugin_code, report)
            await self._analyze_api_usage(plugin_code, report)
            await self._check_compliance_requirements(plugin_code, metadata, report)

            # Calculate risk score and security level
            self._calculate_risk_assessment(report)

            # Generate recommendations
            self._generate_security_recommendations(report)

            # Log scan completion
            if audit_logger:
                audit_logger.info(
                    "Plugin security scan completed",
                    extra={
                        "plugin_id": plugin_id,
                        "scan_id": report.scan_id,
                        "risk_score": report.risk_score,
                        "security_level": report.security_level,
                        "threat_count": len(report.threats),
                    },
                )

        except SyntaxError as e:
            threat = SecurityThreat(
                threat_type="syntax_error",
                severity="critical",
                description=f"Code syntax error: {e}",
                location="global",
                line_number=e.lineno,
            )
            report.threats.append(threat)
            report.risk_score = 100
            report.security_level = "critical"

        except Exception as e:
            logger.error(f"Scanner error for plugin {plugin_id}: {e}")
            raise PluginSecurityError(f"Security scan failed: {e}") from e

        return report

    async def _analyze_code_patterns(self, code: str, report: PluginSecurityReport) -> None:
        """Analyze code for threat patterns using regex."""
        for threat_name, config in self._threat_patterns.items():
            matches = re.finditer(config["pattern"], code, re.MULTILINE | re.IGNORECASE)

            for match in matches:
                line_number = code[: match.start()].count("\n") + 1

                threat = SecurityThreat(
                    threat_type=threat_name,
                    severity=config["severity"],
                    description=config["description"],
                    location=f"line {line_number}",
                    line_number=line_number,
                    evidence=match.group(0),
                    remediation=self._get_remediation(threat_name),
                )
                report.threats.append(threat)

    async def _analyze_ast_structure(self, tree: ast.AST, report: PluginSecurityReport) -> None:
        """Deep AST analysis for security issues."""

        class SecurityAnalyzer(ast.NodeVisitor):
            def __init__(self, report: PluginSecurityReport):
                self.report = report
                self.complexity = 0

            def visit_FunctionDef(self, node):
                # Analyze function complexity
                self.complexity += len(node.body)

                # Check for suspicious function names
                suspicious_names = ["backdoor", "bypass", "exploit", "hack"]
                if any(name in node.name.lower() for name in suspicious_names):
                    threat = SecurityThreat(
                        threat_type="suspicious_function",
                        severity="high",
                        description=f"Suspicious function name: {node.name}",
                        location=f"line {node.lineno}",
                        line_number=node.lineno,
                    )
                    self.report.threats.append(threat)

                self.generic_visit(node)

            def visit_Call(self, node):
                # Track API calls
                if isinstance(node.func, ast.Attribute):
                    call_name = f"{ast.unparse(node.func.value)}.{node.func.attr}"
                    self.report.api_calls.append(call_name)
                elif isinstance(node.func, ast.Name):
                    self.report.api_calls.append(node.func.id)

                self.generic_visit(node)

            def visit_Import(self, node):
                for alias in node.names:
                    if alias.name not in self._dependency_allowlist:
                        threat = SecurityThreat(
                            threat_type="unauthorized_import",
                            severity="medium",
                            description=f"Non-whitelisted import: {alias.name}",
                            location=f"line {node.lineno}",
                            line_number=node.lineno,
                            remediation="Use only approved dependencies",
                        )
                        self.report.threats.append(threat)

                self.generic_visit(node)

        analyzer = SecurityAnalyzer(report)
        analyzer.visit(tree)
        report.complexity_score = analyzer.complexity

    async def _analyze_dependencies(
        self, tree: ast.AST, code: str, report: PluginSecurityReport
    ) -> None:
        """Analyze plugin dependencies for security risks."""
        dependencies = set()

        # Extract imports from AST
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.add(node.module.split(".")[0])

        report.dependency_count = len(dependencies)

        # Check for high-risk dependencies
        high_risk_deps = {
            "subprocess": "System command execution",
            "os": "Operating system access",
            "socket": "Network socket access",
            "ctypes": "Low-level system access",
            "pickle": "Unsafe deserialization",
        }

        for dep in dependencies:
            if dep in high_risk_deps:
                threat = SecurityThreat(
                    threat_type="high_risk_dependency",
                    severity="high",
                    description=f"High-risk dependency: {dep} - {high_risk_deps[dep]}",
                    location="imports",
                    remediation="Consider safer alternatives",
                )
                report.threats.append(threat)

    async def _analyze_api_usage(self, code: str, report: PluginSecurityReport) -> None:
        """Analyze API usage patterns for security concerns."""
        for pattern_name, pattern in self._api_patterns.items():
            matches = re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE)

            for match in matches:
                line_number = code[: match.start()].count("\n") + 1

                threat = SecurityThreat(
                    threat_type=f"suspicious_api_{pattern_name}",
                    severity="medium",
                    description=f"Suspicious API pattern detected: {pattern_name}",
                    location=f"line {line_number}",
                    line_number=line_number,
                    evidence=match.group(0),
                )
                report.threats.append(threat)

    async def _check_compliance_requirements(
        self, code: str, metadata: dict[str, Any], report: PluginSecurityReport
    ) -> None:
        """Check compliance with enterprise security requirements."""
        compliance_checks = [
            self._check_data_privacy_compliance,
            self._check_access_control_compliance,
            self._check_logging_compliance,
            self._check_error_handling_compliance,
        ]

        for check in compliance_checks:
            await check(code, metadata, report)

    async def _check_data_privacy_compliance(
        self, code: str, metadata: dict[str, Any], report: PluginSecurityReport
    ) -> None:
        """Check data privacy compliance."""
        # Look for PII handling patterns
        pii_patterns = [
            r"(ssn|social.security|passport|license)",
            r"(email|phone|address|credit.card)",
            r"(password|secret|key|token)",
        ]

        for pattern in pii_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                threat = SecurityThreat(
                    threat_type="pii_handling",
                    severity="high",
                    description="Potential PII handling without proper safeguards",
                    location="code analysis",
                    remediation="Implement data anonymization and encryption",
                )
                report.threats.append(threat)

    async def _check_access_control_compliance(
        self, code: str, metadata: dict[str, Any], report: PluginSecurityReport
    ) -> None:
        """Check access control implementation."""
        if "auth" in code.lower() or "permission" in code.lower():
            # Require explicit permission declarations
            if not metadata.get("required_permissions"):
                threat = SecurityThreat(
                    threat_type="missing_permission_declaration",
                    severity="medium",
                    description="Plugin handles auth but doesn't declare required permissions",
                    location="metadata",
                    remediation="Declare all required permissions in plugin metadata",
                )
                report.threats.append(threat)

    async def _check_logging_compliance(
        self, code: str, metadata: dict[str, Any], report: PluginSecurityReport
    ) -> None:
        """Check audit logging compliance."""
        if not re.search(r"log(ger|ging)", code, re.IGNORECASE):
            report.recommendations.append("Consider adding audit logging for security events")

    async def _check_error_handling_compliance(
        self, code: str, metadata: dict[str, Any], report: PluginSecurityReport
    ) -> None:
        """Check error handling compliance."""
        if "except:" in code or "except Exception:" in code:
            threat = SecurityThreat(
                threat_type="broad_exception_handling",
                severity="low",
                description="Overly broad exception handling may hide security issues",
                location="error handling",
                remediation="Use specific exception types",
            )
            report.threats.append(threat)

    def _calculate_risk_assessment(self, report: PluginSecurityReport) -> None:
        """Calculate overall risk score and security level."""
        severity_weights = {"critical": 30, "high": 15, "medium": 7, "low": 2}

        risk_score = 0
        for threat in report.threats:
            risk_score += severity_weights.get(threat.severity, 0)

        # Additional risk factors
        if report.complexity_score > 50:
            risk_score += 10

        if report.dependency_count > 10:
            risk_score += 5

        # Cap at 100
        report.risk_score = min(risk_score, 100)

        # Determine security level
        for level, threshold in sorted(self.risk_thresholds.items(), key=lambda x: x[1]):
            if report.risk_score <= threshold:
                report.security_level = level
                break
        else:
            report.security_level = "critical"

        # Set validation and certification flags
        report.passes_validation = report.security_level in ["safe", "low"]
        report.certification_eligible = (
            report.security_level == "safe"
            and len([t for t in report.threats if t.severity in ["critical", "high"]]) == 0
        )

    def _generate_security_recommendations(self, report: PluginSecurityReport) -> None:
        """Generate security recommendations based on findings."""
        if report.risk_score > 60:
            report.recommendations.append("Consider code review by security team")

        if any(t.threat_type == "dangerous_imports" for t in report.threats):
            report.recommendations.append("Replace dangerous imports with safer alternatives")

        if report.complexity_score > 50:
            report.recommendations.append("Reduce code complexity for better security analysis")

        if not report.passes_validation:
            report.recommendations.append(
                "Address high and critical security issues before deployment"
            )

        # Generate required permissions based on threats
        permission_mapping = {
            "file_system_access": "filesystem:read",
            "network_calls": "network:http",
            "database_access": "database:read",
            "environment_access": "system:environment",
        }

        for threat in report.threats:
            if threat.threat_type in permission_mapping:
                perm = permission_mapping[threat.threat_type]
                if perm not in report.required_permissions:
                    report.required_permissions.append(perm)

    def _get_remediation(self, threat_type: str) -> str:
        """Get remediation advice for specific threat types."""
        remediations = {
            "dangerous_imports": "Use safer alternatives or request specific permissions",
            "eval_usage": "Replace with safer parsing methods like json.loads()",
            "shell_commands": "Use platform-specific APIs instead of shell commands",
            "sql_injection": "Use parameterized queries or ORM methods",
            "pickle_usage": "Use JSON or other safe serialization formats",
        }
        return remediations.get(threat_type, "Review and mitigate security risk")

    @standard_exception_handler
    async def scan_plugin_file(
        self, file_path: Path, metadata: Optional[dict[str, Any]] = None
    ) -> PluginSecurityReport:
        """Scan plugin file for security issues."""
        if not file_path.exists():
            raise ValidationError(f"Plugin file not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                code = f.read()

            plugin_metadata = metadata or {"id": file_path.stem, "name": file_path.name}
            return await self.scan_plugin(code, plugin_metadata)

        except Exception as e:
            logger.error(f"Failed to scan plugin file {file_path}: {e}")
            raise PluginSecurityError(f"File scan failed: {e}") from e

    @standard_exception_handler
    async def batch_scan_directory(
        self, directory: Path, pattern: str = "*.py"
    ) -> list[PluginSecurityReport]:
        """Scan all plugins in a directory."""
        if not directory.exists():
            raise ValidationError(f"Directory not found: {directory}")

        reports = []
        plugin_files = list(directory.glob(pattern))

        logger.info(f"Starting batch scan of {len(plugin_files)} files in {directory}")

        for file_path in plugin_files:
            try:
                report = await self.scan_plugin_file(file_path)
                reports.append(report)

                logger.info(
                    f"Scanned {file_path.name}: {report.security_level} risk ({report.risk_score} score)"
                )

            except Exception as e:
                logger.error(f"Failed to scan {file_path.name}: {e}")
                # Create error report
                error_report = PluginSecurityReport(
                    plugin_id=file_path.stem, security_level="unknown", risk_score=100
                )
                error_report.threats.append(
                    SecurityThreat(
                        threat_type="scan_error",
                        severity="critical",
                        description=f"Scan failed: {e}",
                        location="scanner",
                    )
                )
                reports.append(error_report)

        return reports

# Factory function for dependency injection
def create_advanced_plugin_scanner(
    audit_monitor: Optional[UnifiedAuditMonitor] = None,
) -> AdvancedPluginSecurityScanner:
    """Create advanced plugin security scanner instance."""
    return AdvancedPluginSecurityScanner(audit_monitor)

__all__ = [
    "SecurityThreat",
    "PluginSecurityReport",
    "AdvancedPluginSecurityScanner",
    "create_advanced_plugin_scanner",
]
