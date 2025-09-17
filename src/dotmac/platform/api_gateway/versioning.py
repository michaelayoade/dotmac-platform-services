"""
API versioning strategies using platform services.
"""


from typing import Optional, Dict, Any
from fastapi import Request, Response

from .interfaces import VersionStrategy

from dotmac.platform.observability.unified_logging import get_logger
logger = get_logger(__name__)

class HeaderVersioning(VersionStrategy):
    """API versioning through headers (e.g., X-API-Version: v1)."""

    def __init__(
        self,
        header_name: str = "X-API-Version",
        supported_versions: Optional[list[str]] = None,
        current_version: str = "v1",
        min_version: str = "v1",
    ):
        self.header_name = header_name
        self.supported_versions = supported_versions or ["v1", "v2"]
        self.current_version = current_version
        self.min_version = min_version

    def extract_version(self, request: Request) -> Optional[str]:
        """Extract API version from request headers."""
        return request.headers.get(self.header_name)

    def inject_version(self, response: Response, version: str) -> None:
        """Inject version information into response headers."""
        response.headers[self.header_name] = version
        response.headers["X-API-Current-Version"] = self.current_version
        response.headers["X-API-Min-Version"] = self.min_version

    def is_supported(self, version: str) -> bool:
        """Check if version is supported."""
        supported = version in self.supported_versions
        if not supported:
            logger.warning(f"Unsupported API version requested: {version}")
        return supported

    def get_deprecation_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get deprecation information for a version."""
        if version < self.min_version:
            return {
                "deprecated": True,
                "message": f"Version {version} is deprecated. Minimum supported version is {self.min_version}",
                "sunset_date": None,  # Could be configured
            }
        return None

class PathVersioning(VersionStrategy):
    """API versioning through URL path (e.g., /api/v1/users)."""

    def __init__(
        self,
        path_prefix: str = "/api",
        supported_versions: Optional[list[str]] = None,
        current_version: str = "v1",
    ):
        self.path_prefix = path_prefix
        self.supported_versions = supported_versions or ["v1", "v2"]
        self.current_version = current_version

    def extract_version(self, request: Request) -> Optional[str]:
        """Extract API version from URL path."""
        path = request.url.path
        if path.startswith(self.path_prefix):
            # Extract version from path like /api/v1/...
            parts = path[len(self.path_prefix) :].strip("/").split("/")
            if parts and parts[0].startswith("v"):
                return parts[0]
        return None

    def inject_version(self, response: Response, version: str) -> None:
        """Inject version information into response."""
        response.headers["X-API-Version"] = version

    def is_supported(self, version: str) -> bool:
        """Check if version is supported."""
        supported = version in self.supported_versions
        if not supported:
            logger.warning(f"Unsupported API version requested: {version}")
        return supported

    def get_deprecation_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get deprecation information for a version."""
        # Could check against a deprecation schedule
        return None

class QueryVersioning(VersionStrategy):
    """API versioning through query parameters (e.g., ?version=v1)."""

    def __init__(
        self,
        param_name: str = "version",
        supported_versions: Optional[list[str]] = None,
        current_version: str = "v1",
        default_version: str = "v1",
    ):
        self.param_name = param_name
        self.supported_versions = supported_versions or ["v1", "v2"]
        self.current_version = current_version
        self.default_version = default_version

    def extract_version(self, request: Request) -> Optional[str]:
        """Extract API version from query parameters."""
        return request.query_params.get(self.param_name, self.default_version)

    def inject_version(self, response: Response, version: str) -> None:
        """Inject version information into response."""
        response.headers["X-API-Version"] = version

    def is_supported(self, version: str) -> bool:
        """Check if version is supported."""
        supported = version in self.supported_versions
        if not supported:
            logger.warning(f"Unsupported API version requested: {version}")
        return supported

    def get_deprecation_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get deprecation information for a version."""
        return None

class AcceptHeaderVersioning(VersionStrategy):
    """API versioning through Accept header (e.g., Accept: application/vnd.api+json;version=1)."""

    def __init__(
        self,
        media_type: str = "application/vnd.api+json",
        supported_versions: Optional[list[str]] = None,
        current_version: str = "1",
    ):
        self.media_type = media_type
        self.supported_versions = supported_versions or ["1", "2"]
        self.current_version = current_version

    def extract_version(self, request: Request) -> Optional[str]:
        """Extract API version from Accept header."""
        accept_header = request.headers.get("Accept", "")
        if self.media_type in accept_header:
            # Parse version from media type parameters
            parts = accept_header.split(";")
            for part in parts:
                if "version=" in part:
                    return part.split("=")[1].strip()
        return None

    def inject_version(self, response: Response, version: str) -> None:
        """Inject version information into response."""
        response.headers["Content-Type"] = f"{self.media_type};version={version}"

    def is_supported(self, version: str) -> bool:
        """Check if version is supported."""
        supported = version in self.supported_versions
        if not supported:
            logger.warning(f"Unsupported API version requested: {version}")
        return supported

    def get_deprecation_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get deprecation information for a version."""
        return None
