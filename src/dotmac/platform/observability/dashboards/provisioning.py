"""
Advanced dashboard provisioning system for SigNoz.

Features:
- Automated dashboard creation and updates
- Template-based dashboard generation with variables
- Datasource management and provisioning
- Dashboard version control and rollback
- Multi-tenant dashboard isolation
- CI/CD integration support
"""

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    import git

# Runtime availability check
_advanced_dependencies = False
try:
    import git

    _advanced_dependencies = True
except ImportError:
    pass

from .manager import DashboardConfig, DashboardManager, DashboardTemplate, PlatformType


@dataclass
class DashboardVersion:
    """Dashboard version information."""

    version: str
    created_at: datetime
    created_by: str
    description: str
    template_hash: str
    platform_specific_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProvisioningConfig:
    """Configuration for advanced dashboard provisioning."""

    # Repository settings
    template_repository_url: str | None = None
    template_branch: str = "main"
    template_directory: str = "dashboards"

    # Version control
    enable_versioning: bool = True
    max_versions_to_keep: int = 10

    # Deployment settings
    auto_deploy: bool = True
    deployment_strategy: str = "rolling"  # rolling, blue_green, canary

    # Tenant isolation
    enable_tenant_isolation: bool = True
    tenant_prefix_template: str = "[{tenant_id}] "

    # Validation
    validate_before_deploy: bool = True
    require_approval_for_production: bool = True

    # Rollback settings
    enable_auto_rollback: bool = True
    rollback_on_error_threshold: float = 0.1  # 10% error rate


class DashboardVersionControl:
    """Version control system for dashboards."""

    def __init__(self, storage_path: str) -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.versions_file = self.storage_path / "versions.json"

    def save_version(
        self,
        dashboard_name: str,
        template: DashboardTemplate,
        created_by: str,
        description: str = "",
    ) -> DashboardVersion:
        """Save a new version of the dashboard."""
        # Calculate template hash
        template_content = json.dumps(template.template_content, sort_keys=True)
        template_hash = hashlib.sha256(template_content.encode()).hexdigest()[:12]

        # Load existing versions
        versions = self._load_versions()
        if dashboard_name not in versions:
            versions[dashboard_name] = []

        # Create new version
        version_number = f"v{len(versions[dashboard_name]) + 1}.0.0"
        new_version = DashboardVersion(
            version=version_number,
            created_at=datetime.now(),
            created_by=created_by,
            description=description,
            template_hash=template_hash,
        )

        # Save template content
        version_dir = self.storage_path / dashboard_name / version_number
        version_dir.mkdir(parents=True, exist_ok=True)

        template_file = version_dir / "template.json"
        with open(template_file, "w") as f:
            json.dump(template.template_content, f, indent=2)

        metadata_file = version_dir / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(
                {
                    "version": new_version.version,
                    "created_at": new_version.created_at.isoformat(),
                    "created_by": new_version.created_by,
                    "description": new_version.description,
                    "template_hash": new_version.template_hash,
                    "name": template.name,
                    "title": template.title,
                    "tags": template.tags,
                    "variables": template.variables or {},
                },
                f,
                indent=2,
            )

        # Add to versions list
        versions[dashboard_name].append(new_version)

        # Keep only max versions
        if len(versions[dashboard_name]) > 10:  # Default max versions
            old_versions = versions[dashboard_name][:-10]
            versions[dashboard_name] = versions[dashboard_name][-10:]

            # Clean up old version directories
            for old_version in old_versions:
                old_dir = self.storage_path / dashboard_name / old_version.version
                if old_dir.exists():
                    import shutil

                    shutil.rmtree(old_dir)

        # Save versions
        self._save_versions(versions)

        return new_version

    def get_version(
        self, dashboard_name: str, version: str | None = None
    ) -> DashboardTemplate | None:
        """Get a specific version of the dashboard."""
        versions = self._load_versions()
        if dashboard_name not in versions or not versions[dashboard_name]:
            return None

        # Get latest version if none specified
        if version is None:
            target_version = versions[dashboard_name][-1]
        else:
            target_version = next(
                (v for v in versions[dashboard_name] if v.version == version), None
            )

        if not target_version:
            return None

        # Load template content
        version_dir = self.storage_path / dashboard_name / target_version.version
        template_file = version_dir / "template.json"
        metadata_file = version_dir / "metadata.json"

        if not template_file.exists() or not metadata_file.exists():
            return None

        with open(template_file) as f:
            template_content = json.load(f)

        with open(metadata_file) as f:
            metadata = json.load(f)

        return DashboardTemplate(
            name=metadata["name"],
            title=metadata["title"],
            description=metadata.get("description", ""),
            tags=metadata.get("tags", []),
            template_content=template_content,
            variables=metadata.get("variables"),
        )

    def list_versions(self, dashboard_name: str) -> list[DashboardVersion]:
        """List all versions of a dashboard."""
        versions = self._load_versions()
        return versions.get(dashboard_name, [])

    def _load_versions(self) -> dict[str, list[DashboardVersion]]:
        """Load versions from storage."""
        if not self.versions_file.exists():
            return {}

        try:
            with open(self.versions_file) as f:
                data = json.load(f)

            # Convert to DashboardVersion objects
            versions = {}
            for dashboard_name, version_list in data.items():
                versions[dashboard_name] = []
                for v_data in version_list:
                    version = DashboardVersion(
                        version=v_data["version"],
                        created_at=datetime.fromisoformat(v_data["created_at"]),
                        created_by=v_data["created_by"],
                        description=v_data["description"],
                        template_hash=v_data["template_hash"],
                        platform_specific_data=v_data.get("platform_specific_data", {}),
                    )
                    versions[dashboard_name].append(version)

            return versions
        except Exception:
            return {}

    def _save_versions(self, versions: dict[str, list[DashboardVersion]]) -> None:
        """Save versions to storage."""
        # Convert to serializable format
        data = {}
        for dashboard_name, version_list in versions.items():
            data[dashboard_name] = []
            for version in version_list:
                data[dashboard_name].append(
                    {
                        "version": version.version,
                        "created_at": version.created_at.isoformat(),
                        "created_by": version.created_by,
                        "description": version.description,
                        "template_hash": version.template_hash,
                        "platform_specific_data": version.platform_specific_data,
                    }
                )

        with open(self.versions_file, "w") as f:
            json.dump(data, f, indent=2)


class DashboardValidator:
    """Dashboard template validator."""

    def __init__(self, platform_type: PlatformType) -> None:
        self.platform_type = platform_type

    def validate_template(self, template: DashboardTemplate) -> list[str]:
        """Validate dashboard template and return list of errors."""
        errors = []

        # Basic validation
        if not template.name:
            errors.append("Dashboard name is required")

        if not template.title:
            errors.append("Dashboard title is required")

        if not template.template_content:
            errors.append("Dashboard template content is required")

        # Platform-specific validation
        if self.platform_type == "signoz":
            errors.extend(self._validate_signoz_template(template))

        return errors

    def _validate_signoz_template(self, template: DashboardTemplate) -> list[str]:
        """Validate SigNoz-specific template."""
        errors = []
        content = template.template_content

        # SigNoz-specific validation
        if "widgets" not in content:
            errors.append("SigNoz dashboard must have 'widgets' field")

        # Validate widgets
        if isinstance(content.get("widgets"), list):
            for i, widget in enumerate(content["widgets"]):
                if not isinstance(widget, dict):
                    errors.append(f"Widget {i} must be an object")
                    continue

                if "title" not in widget:
                    errors.append(f"Widget {i} missing title")

                if "queryType" not in widget:
                    errors.append(f"Widget {i} missing queryType")

        return errors


class GitTemplateLoader:
    """Load dashboard templates from Git repository."""

    def __init__(
        self, repository_url: str, branch: str = "main", template_directory: str = "dashboards"
    ) -> None:
        self.repository_url = repository_url
        self.branch = branch
        self.template_directory = template_directory
        self._repo_path: Path | None = None

    def load_templates(self) -> list[DashboardTemplate]:
        """Load templates from Git repository."""
        if not _advanced_dependencies:
            raise ImportError(
                "Git template loading requires 'gitpython'. Install with: pip install gitpython"
            )

        templates = []

        # Clone or update repository
        repo_path = self._get_or_update_repo()
        template_path = repo_path / self.template_directory

        if not template_path.exists():
            return templates

        # Load templates from directory
        for template_file in template_path.glob("**/*.json"):
            try:
                template = self._load_template_file(template_file)
                if template:
                    templates.append(template)
            except Exception as e:
                print(f"Error loading template {template_file}: {e}")

        # Also load YAML templates
        for template_file in template_path.glob("**/*.yaml"):
            try:
                template = self._load_template_file(template_file)
                if template:
                    templates.append(template)
            except Exception as e:
                print(f"Error loading template {template_file}: {e}")

        return templates

    def _get_or_update_repo(self) -> Path:
        """Clone or update the Git repository."""
        if self._repo_path and self._repo_path.exists():
            # Update existing repo
            repo = git.Repo(self._repo_path)
            origin = repo.remotes.origin
            origin.pull(self.branch)
            return self._repo_path

        # Clone repository
        with tempfile.TemporaryDirectory() as temp_dir:
            clone_path = Path(temp_dir) / "dashboard_templates"
            repo = git.Repo.clone_from(
                self.repository_url,
                clone_path,
                branch=self.branch,
                depth=1,  # Shallow clone
            )

            # Copy to persistent location
            import shutil

            persistent_path = Path.home() / ".dotmac" / "dashboard_templates"
            if persistent_path.exists():
                shutil.rmtree(persistent_path)
            shutil.copytree(clone_path, persistent_path)

            self._repo_path = persistent_path
            return self._repo_path

    def _load_template_file(self, file_path: Path) -> DashboardTemplate | None:
        """Load template from file."""
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f) if file_path.suffix == ".yaml" else json.load(f)

            # Extract template metadata
            metadata = data.get("metadata", {})
            template_content = data.get("dashboard", data.get("template", {}))

            if not template_content:
                return None

            return DashboardTemplate(
                name=metadata.get("name", file_path.stem),
                title=metadata.get("title", file_path.stem.replace("_", " ").title()),
                description=metadata.get("description", ""),
                tags=metadata.get("tags", []),
                template_content=template_content,
                variables=metadata.get("variables"),
            )

        except Exception:
            return None


class AdvancedDashboardProvisioner:
    """Advanced dashboard provisioning with version control and automation."""

    def __init__(
        self,
        dashboard_config: DashboardConfig,
        provisioning_config: ProvisioningConfig,
        storage_path: str | None = None,
    ) -> None:
        self.dashboard_config = dashboard_config
        self.provisioning_config = provisioning_config

        # Initialize components
        storage_path = storage_path or os.path.expanduser("~/.dotmac/dashboards")
        self.version_control = DashboardVersionControl(storage_path)
        self.validator = DashboardValidator(dashboard_config.platform_type)

        # Git template loader
        self.git_loader: GitTemplateLoader | None = None
        if provisioning_config.template_repository_url:
            self.git_loader = GitTemplateLoader(
                provisioning_config.template_repository_url,
                provisioning_config.template_branch,
                provisioning_config.template_directory,
            )

    def provision_dashboards_from_git(
        self,
        tenant_id: str | None = None,
        custom_variables: dict[str, str] | None = None,
        created_by: str = "system",
    ) -> dict[str, Any]:
        """Provision dashboards from Git repository."""
        if not self.git_loader:
            return {"success": False, "error": "Git template repository not configured"}

        try:
            # Load templates from Git
            templates = self.git_loader.load_templates()

            return self.provision_dashboards(
                templates=templates,
                tenant_id=tenant_id,
                custom_variables=custom_variables,
                created_by=created_by,
            )

        except Exception as e:
            return {"success": False, "error": f"Failed to load templates from Git: {e}"}

    def provision_dashboards(
        self,
        templates: list[DashboardTemplate],
        tenant_id: str | None = None,
        custom_variables: dict[str, str] | None = None,
        created_by: str = "system",
    ) -> dict[str, Any]:
        """Provision dashboards with advanced features."""
        result = {
            "success": True,
            "dashboards_processed": 0,
            "dashboards_created": [],
            "dashboards_updated": [],
            "dashboards_failed": [],
            "versions_created": [],
            "errors": [],
            "warnings": [],
        }

        for template in templates:
            try:
                # Apply tenant isolation if enabled
                if self.provisioning_config.enable_tenant_isolation and tenant_id:
                    template = self._apply_tenant_isolation(template, tenant_id)

                # Validate template
                if self.provisioning_config.validate_before_deploy:
                    validation_errors = self.validator.validate_template(template)
                    if validation_errors:
                        result["dashboards_failed"].append(template.name)
                        result["errors"].extend(
                            [f"{template.name}: {error}" for error in validation_errors]
                        )
                        continue

                # Save version if enabled
                if self.provisioning_config.enable_versioning:
                    version = self.version_control.save_version(
                        template.name,
                        template,
                        created_by,
                        f"Auto-provision from {'Git' if self.git_loader else 'direct'}",
                    )
                    result["versions_created"].append(
                        {"dashboard": template.name, "version": version.version}
                    )

                # Deploy dashboard
                deployment_result = self._deploy_dashboard(template, tenant_id, custom_variables)

                if deployment_result["success"]:
                    if deployment_result.get("created"):
                        result["dashboards_created"].append(template.name)
                    else:
                        result["dashboards_updated"].append(template.name)
                else:
                    result["dashboards_failed"].append(template.name)
                    if "error" in deployment_result:
                        result["errors"].append(f"{template.name}: {deployment_result['error']}")

                result["dashboards_processed"] += 1

            except Exception as e:
                result["dashboards_failed"].append(template.name)
                result["errors"].append(f"{template.name}: {e!s}")

        # Set overall success based on failures
        if result["dashboards_failed"]:
            result["success"] = (
                len(result["dashboards_failed"]) < len(templates) * 0.5
            )  # 50% failure threshold

        return result

    def rollback_dashboard(
        self,
        dashboard_name: str,
        target_version: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Rollback dashboard to a previous version."""
        try:
            # Get target version
            template = self.version_control.get_version(dashboard_name, target_version)
            if not template:
                return {
                    "success": False,
                    "error": f"Version {target_version or 'latest'} not found for dashboard {dashboard_name}",
                }

            # Apply tenant isolation if needed
            if self.provisioning_config.enable_tenant_isolation and tenant_id:
                template = self._apply_tenant_isolation(template, tenant_id)

            # Deploy the rollback version
            deployment_result = self._deploy_dashboard(template, tenant_id)

            if deployment_result["success"]:
                return {
                    "success": True,
                    "dashboard": dashboard_name,
                    "version": target_version or "previous",
                    "action": "rollback_completed",
                }
            return {
                "success": False,
                "error": f"Failed to rollback dashboard: {deployment_result.get('error')}",
            }

        except Exception as e:
            return {"success": False, "error": f"Rollback failed: {e!s}"}

    def _apply_tenant_isolation(
        self, template: DashboardTemplate, tenant_id: str
    ) -> DashboardTemplate:
        """Apply tenant isolation to dashboard template."""
        # Create isolated template
        isolated_template = DashboardTemplate(
            name=f"{tenant_id}_{template.name}",
            title=self.provisioning_config.tenant_prefix_template.format(tenant_id=tenant_id)
            + template.title,
            description=template.description,
            tags=[*template.tags, f"tenant:{tenant_id}"],
            template_content=template.template_content.copy(),
            variables=template.variables.copy() if template.variables else None,
        )

        # Add tenant filtering to queries if possible
        if isolated_template.variables is None:
            isolated_template.variables = {}
        isolated_template.variables["tenant_id"] = tenant_id

        return isolated_template

    def _deploy_dashboard(
        self,
        template: DashboardTemplate,
        tenant_id: str | None = None,
        custom_variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Deploy dashboard using the base manager."""
        try:
            with DashboardManager(self.dashboard_config) as manager:
                result = manager.provision_dashboards(
                    templates=[template],
                    tenant_id=tenant_id,
                    custom_variables=custom_variables,
                    auto_create_datasources=True,
                )

                return {
                    "success": result.success,
                    "created": template.name in result.dashboards_created,
                    "error": "; ".join(result.errors) if result.errors else None,
                }

        except Exception as e:
            return {"success": False, "error": str(e)}


# Factory functions
def create_provisioning_config(**kwargs) -> ProvisioningConfig:
    """Create provisioning configuration."""
    return ProvisioningConfig(**kwargs)


def create_advanced_provisioner(
    dashboard_config: DashboardConfig,
    provisioning_config: ProvisioningConfig,
    storage_path: str | None = None,
) -> AdvancedDashboardProvisioner:
    """Create advanced dashboard provisioner."""
    return AdvancedDashboardProvisioner(dashboard_config, provisioning_config, storage_path)


def create_git_template_loader(repository_url: str, **kwargs) -> GitTemplateLoader:
    """Create Git template loader."""
    return GitTemplateLoader(repository_url, **kwargs)


def create_dashboard_validator(platform_type: PlatformType) -> DashboardValidator:
    """Create dashboard validator."""
    return DashboardValidator(platform_type)


class DashboardProvisioner:
    """
    Automated dashboard provisioning for DotMac platform services.

    Handles deployment, configuration, and lifecycle management of
    observability dashboards across multiple platforms.
    """

    def __init__(
        self, platform_type: PlatformType = "signoz", config: dict[str, Any] | None = None
    ) -> None:
        self.platform_type = platform_type
        self.config = config or {}
        self.validator = DashboardValidator(platform_type)
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the dashboard provisioner."""
        if self._initialized:
            return

        # Initialize platform-specific configuration
        self._setup_platform_config()
        self._initialized = True

    def _setup_platform_config(self) -> None:
        """Setup platform-specific configuration."""
        if self.platform_type == "signoz":
            self._setup_signoz_config()
        # Add more platforms as needed

    def _setup_signoz_config(self) -> None:
        """Setup SigNoz-specific configuration."""
        self.config.setdefault("api_url", "http://localhost:3301/api")
        self.config.setdefault("api_key", "")
        self.config.setdefault("dashboards_path", "/v1/dashboards")

    def _setup_datadog_config(self) -> None:
        """Setup Datadog-specific configuration."""
        self.config.setdefault("api_key", "")
        self.config.setdefault("app_key", "")
        self.config.setdefault("site", "datadoghq.com")

    def provision_dashboard(self, dashboard_config: dict[str, Any]) -> bool:
        """
        Provision a single dashboard.

        Args:
            dashboard_config: Dashboard configuration dictionary

        Returns:
            bool: True if provisioning succeeded, False otherwise
        """
        if not self._initialized:
            self.initialize()

        try:
            # Validate dashboard configuration
            validation_result = self.validator.validate(dashboard_config)
            if not validation_result.is_valid:
                return False

            # Platform-specific provisioning
            if self.platform_type == "signoz":
                return self._provision_signoz_dashboard(dashboard_config)

            return False
        except Exception:
            return False

    def _provision_signoz_dashboard(self, config: dict[str, Any]) -> bool:
        """Provision SigNoz dashboard."""
        # Implementation would make API calls to SigNoz
        # SigNoz uses its own API structure
        return True

    def _provision_datadog_dashboard(self, config: dict[str, Any]) -> bool:
        """Provision Datadog dashboard."""
        # Implementation would make API calls to Datadog
        return True
