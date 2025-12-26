"""
AWX Client for Ansible automation.

Provides a client for interacting with AWX/Ansible Tower API
for tenant provisioning automation.
"""

import json
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class AWXClientError(Exception):
    """Base exception for AWX client errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AWXAuthenticationError(AWXClientError):
    """Authentication failed with AWX."""

    pass


class AWXNotFoundError(AWXClientError):
    """Resource not found in AWX."""

    pass


class AWXJobError(AWXClientError):
    """Error related to AWX job execution."""

    pass


class AWXClient:
    """AWX API client for Ansible automation."""

    # AWX job status mappings
    JOB_STATUS_SUCCESSFUL = "successful"
    JOB_STATUS_FAILED = "failed"
    JOB_STATUS_ERROR = "error"
    JOB_STATUS_CANCELED = "canceled"
    JOB_STATUS_PENDING = "pending"
    JOB_STATUS_RUNNING = "running"
    JOB_STATUS_WAITING = "waiting"

    TERMINAL_STATUSES = {
        JOB_STATUS_SUCCESSFUL,
        JOB_STATUS_FAILED,
        JOB_STATUS_ERROR,
        JOB_STATUS_CANCELED,
    }

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        verify_ssl: bool = True,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize AWX client.

        Args:
            base_url: AWX server URL (e.g., https://awx.example.com)
            token: Authentication token (preferred over username/password)
            username: AWX username for basic auth
            password: AWX password for basic auth
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/") if base_url else None
        self.token = token
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Determine if properly configured
        has_auth = token is not None or (username is not None and password is not None)
        self._initialized = base_url is not None and has_auth

        # Create HTTP client
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return self._initialized

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            # Build auth headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            auth = None
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            elif self.username and self.password:
                auth = httpx.BasicAuth(self.username, self.password)

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                auth=auth,
                verify=self.verify_ssl,
                timeout=httpx.Timeout(self.timeout),
            )

        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to AWX API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., /api/v2/ping/)
            data: Request body data
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            AWXClientError: On request failure
        """
        client = await self._get_client()

        try:
            response = await client.request(
                method=method,
                url=path,
                json=data,
                params=params,
            )

            # Handle error responses
            if response.status_code == 401:
                raise AWXAuthenticationError(
                    "Authentication failed with AWX",
                    status_code=401,
                )

            if response.status_code == 404:
                raise AWXNotFoundError(
                    f"Resource not found: {path}",
                    status_code=404,
                )

            if response.status_code >= 400:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", str(error_json))
                except Exception:
                    pass

                raise AWXClientError(
                    f"AWX API error: {error_detail}",
                    status_code=response.status_code,
                )

            # Return empty dict for 204 No Content
            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.TimeoutException as e:
            logger.error("AWX request timeout", path=path, error=str(e))
            raise AWXClientError(f"Request timeout: {path}") from e

        except httpx.RequestError as e:
            logger.error("AWX request error", path=path, error=str(e))
            raise AWXClientError(f"Request failed: {str(e)}") from e

    async def health_check(self) -> bool:
        """
        Check if AWX is healthy and accessible.

        Returns:
            True if AWX is accessible and healthy
        """
        if not self.is_configured:
            logger.debug("AWX client not configured")
            return False

        try:
            response = await self._request("GET", "/api/v2/ping/")
            # AWX ping returns instance info if healthy
            return "version" in response or "instances" in response

        except AWXClientError as e:
            logger.warning("AWX health check failed", error=str(e))
            return False

        except Exception as e:
            logger.error("Unexpected error during AWX health check", error=str(e))
            return False

    async def launch_job_template(
        self,
        template_id: int,
        extra_vars: dict[str, Any] | None = None,
        limit: str | None = None,
        tags: str | None = None,
        skip_tags: str | None = None,
    ) -> dict[str, Any]:
        """
        Launch an AWX job template.

        Args:
            template_id: ID of the job template to launch
            extra_vars: Extra variables to pass to the job (will be JSON-encoded)
            limit: Limit hosts for the job
            tags: Tags to run
            skip_tags: Tags to skip

        Returns:
            Job launch response containing job_id and status
        """
        if not self.is_configured:
            logger.warning("AWX client not configured, skipping job launch")
            return {"status": "skipped", "reason": "AWX not configured"}

        logger.info(
            "Launching AWX job template",
            template_id=template_id,
            has_extra_vars=extra_vars is not None,
        )

        # Build request body
        body: dict[str, Any] = {}

        if extra_vars:
            # AWX expects extra_vars as a JSON string
            body["extra_vars"] = json.dumps(extra_vars)

        if limit:
            body["limit"] = limit

        if tags:
            body["job_tags"] = tags

        if skip_tags:
            body["skip_tags"] = skip_tags

        try:
            response = await self._request(
                "POST",
                f"/api/v2/job_templates/{template_id}/launch/",
                data=body,
            )

            job_id = response.get("id") or response.get("job")
            status = response.get("status", "pending")

            logger.info(
                "AWX job launched successfully",
                template_id=template_id,
                job_id=job_id,
                status=status,
            )

            return {
                "status": "launched",
                "template_id": template_id,
                "job_id": job_id,
                "job_status": status,
                "url": response.get("url"),
            }

        except AWXNotFoundError:
            logger.error("Job template not found", template_id=template_id)
            raise AWXJobError(
                f"Job template {template_id} not found",
                status_code=404,
            )

        except AWXClientError as e:
            logger.error(
                "Failed to launch job template",
                template_id=template_id,
                error=str(e),
            )
            raise

    async def get_job_status(self, job_id: int) -> dict[str, Any]:
        """
        Get the status of an AWX job.

        Args:
            job_id: ID of the job to check

        Returns:
            Job status response including status, started, finished, etc.
        """
        if not self.is_configured:
            return {"status": "unknown", "reason": "AWX not configured"}

        try:
            response = await self._request("GET", f"/api/v2/jobs/{job_id}/")

            return {
                "job_id": job_id,
                "status": response.get("status", "unknown"),
                "failed": response.get("failed", False),
                "started": response.get("started"),
                "finished": response.get("finished"),
                "elapsed": response.get("elapsed"),
                "job_type": response.get("job_type"),
                "launch_type": response.get("launch_type"),
                "result_traceback": response.get("result_traceback"),
                "job_explanation": response.get("job_explanation"),
                "is_terminal": response.get("status") in self.TERMINAL_STATUSES,
            }

        except AWXNotFoundError:
            logger.error("Job not found", job_id=job_id)
            return {
                "job_id": job_id,
                "status": "not_found",
                "is_terminal": True,
            }

    async def get_job_stdout(
        self,
        job_id: int,
        format: str = "txt",
    ) -> str:
        """
        Get the stdout output of an AWX job.

        Args:
            job_id: ID of the job
            format: Output format (txt, json, or ansi)

        Returns:
            Job output as string
        """
        if not self.is_configured:
            return ""

        client = await self._get_client()

        try:
            response = await client.get(
                f"/api/v2/jobs/{job_id}/stdout/",
                params={"format": format},
            )

            if response.status_code == 404:
                return ""

            response.raise_for_status()

            # For txt format, return as-is
            if format == "txt":
                return response.text

            # For JSON format
            return response.text

        except Exception as e:
            logger.error("Failed to get job stdout", job_id=job_id, error=str(e))
            return ""

    async def cancel_job(self, job_id: int) -> dict[str, Any]:
        """
        Cancel a running AWX job.

        Args:
            job_id: ID of the job to cancel

        Returns:
            Cancellation response
        """
        if not self.is_configured:
            return {"status": "skipped", "reason": "AWX not configured"}

        try:
            await self._request("POST", f"/api/v2/jobs/{job_id}/cancel/")

            logger.info("AWX job canceled", job_id=job_id)
            return {"status": "canceled", "job_id": job_id}

        except AWXNotFoundError:
            return {"status": "not_found", "job_id": job_id}

        except AWXClientError as e:
            # Job might already be complete
            if e.status_code == 405:
                return {"status": "cannot_cancel", "job_id": job_id}
            raise

    async def list_job_templates(
        self,
        page: int = 1,
        page_size: int = 25,
        search: str | None = None,
    ) -> dict[str, Any]:
        """
        List available job templates.

        Args:
            page: Page number
            page_size: Number of items per page
            search: Search query

        Returns:
            Paginated list of job templates
        """
        if not self.is_configured:
            return {"count": 0, "results": []}

        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }

        if search:
            params["search"] = search

        response = await self._request(
            "GET",
            "/api/v2/job_templates/",
            params=params,
        )

        return {
            "count": response.get("count", 0),
            "next": response.get("next"),
            "previous": response.get("previous"),
            "results": [
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "description": t.get("description"),
                    "job_type": t.get("job_type"),
                    "inventory": t.get("inventory"),
                    "project": t.get("project"),
                    "playbook": t.get("playbook"),
                }
                for t in response.get("results", [])
            ],
        }

    async def get_job_template(self, template_id: int) -> dict[str, Any]:
        """
        Get details of a specific job template.

        Args:
            template_id: ID of the job template

        Returns:
            Job template details
        """
        if not self.is_configured:
            return {}

        response = await self._request(
            "GET",
            f"/api/v2/job_templates/{template_id}/",
        )

        return {
            "id": response.get("id"),
            "name": response.get("name"),
            "description": response.get("description"),
            "job_type": response.get("job_type"),
            "inventory": response.get("inventory"),
            "project": response.get("project"),
            "playbook": response.get("playbook"),
            "extra_vars": response.get("extra_vars"),
            "ask_variables_on_launch": response.get("ask_variables_on_launch"),
            "ask_limit_on_launch": response.get("ask_limit_on_launch"),
            "ask_tags_on_launch": response.get("ask_tags_on_launch"),
        }
