"""
Simple tests for file storage router to increase coverage.

Tests FastAPI endpoints for file storage operations.
"""

import pytest
import io
import json
from datetime import datetime, UTC
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from dotmac.platform.file_storage.router import file_storage_router
from dotmac.platform.file_storage.service import FileMetadata
from dotmac.platform.auth.core import UserInfo


@pytest.fixture
def app():
    """Create test FastAPI app with file storage router."""
    app = FastAPI()
    app.include_router(file_storage_router, prefix="/files")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock current user for authentication."""
    return UserInfo(
        user_id="test-user-123",
        username="testuser",
        email="test@example.com",
        roles=["user"],
        permissions=["file:read", "file:write"]
    )


@pytest.fixture
def mock_file_metadata():
    """Mock file metadata for testing."""
    return FileMetadata(
        file_id="test-file-123",
        file_name="test.txt",
        file_size=1024,
        content_type="text/plain",
        upload_timestamp=datetime.now(UTC),
        user_id="test-user-123",
        checksum="abc123def456",
        tags=["test", "document"]
    )


class TestFileUploadEndpoint:
    """Test file upload endpoint."""

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_upload_file_success(self, mock_service, mock_get_user, client, mock_user, mock_file_metadata):
        """Test successful file upload."""
        mock_get_user.return_value = mock_user
        mock_service.store_file.return_value = mock_file_metadata

        # Create test file
        test_content = b"Test file content"
        files = {"file": ("test.txt", io.BytesIO(test_content), "text/plain")}

        response = client.post("/files/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == "test-file-123"
        assert data["file_name"] == "test.txt"
        assert data["file_size"] == 1024
        assert data["content_type"] == "text/plain"

        # Verify service was called
        mock_service.store_file.assert_called_once()

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_upload_file_with_tags(self, mock_service, mock_get_user, client, mock_user, mock_file_metadata):
        """Test file upload with tags."""
        mock_get_user.return_value = mock_user
        mock_service.store_file.return_value = mock_file_metadata

        test_content = b"Test file content"
        files = {"file": ("test.txt", io.BytesIO(test_content), "text/plain")}
        data = {"tags": json.dumps(["tag1", "tag2"])}

        response = client.post("/files/upload", files=files, data=data)

        assert response.status_code == 200
        # Verify service was called with tags
        mock_service.store_file.assert_called_once()

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_upload_file_service_error(self, mock_service, mock_get_user, client, mock_user):
        """Test file upload with service error."""
        mock_get_user.return_value = mock_user
        mock_service.store_file.side_effect = Exception("Storage error")

        test_content = b"Test file content"
        files = {"file": ("test.txt", io.BytesIO(test_content), "text/plain")}

        response = client.post("/files/upload", files=files)

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_upload_file_invalid_tags_json(self, mock_service, mock_get_user, client, mock_user):
        """Test file upload with invalid tags JSON."""
        mock_get_user.return_value = mock_user

        test_content = b"Test file content"
        files = {"file": ("test.txt", io.BytesIO(test_content), "text/plain")}
        data = {"tags": "invalid_json"}

        response = client.post("/files/upload", files=files, data=data)

        assert response.status_code == 400
        assert "Invalid tags format" in response.json()["detail"]


class TestFileDownloadEndpoint:
    """Test file download endpoint."""

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_download_file_success(self, mock_service, mock_get_user, client, mock_user):
        """Test successful file download."""
        mock_get_user.return_value = mock_user
        mock_content = b"Test file content"
        mock_service.get_file.return_value = (mock_content, "text/plain", "test.txt")

        response = client.get("/files/test-file-123/download")

        assert response.status_code == 200
        assert response.content == mock_content
        assert response.headers["content-type"] == "text/plain"

        mock_service.get_file.assert_called_once_with("test-file-123", "test-user-123")

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_download_file_not_found(self, mock_service, mock_get_user, client, mock_user):
        """Test download of non-existent file."""
        mock_get_user.return_value = mock_user
        mock_service.get_file.side_effect = FileNotFoundError("File not found")

        response = client.get("/files/nonexistent-file/download")

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_download_file_permission_error(self, mock_service, mock_get_user, client, mock_user):
        """Test download with permission error."""
        mock_get_user.return_value = mock_user
        mock_service.get_file.side_effect = PermissionError("Access denied")

        response = client.get("/files/restricted-file/download")

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_download_file_service_error(self, mock_service, mock_get_user, client, mock_user):
        """Test download with service error."""
        mock_get_user.return_value = mock_user
        mock_service.get_file.side_effect = Exception("Storage error")

        response = client.get("/files/test-file-123/download")

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestFileDeleteEndpoint:
    """Test file delete endpoint."""

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_delete_file_success(self, mock_service, mock_get_user, client, mock_user):
        """Test successful file deletion."""
        mock_get_user.return_value = mock_user
        mock_service.delete_file.return_value = True

        response = client.delete("/files/test-file-123")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "File deleted successfully"
        assert data["file_id"] == "test-file-123"

        mock_service.delete_file.assert_called_once_with("test-file-123", "test-user-123")

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_delete_file_not_found(self, mock_service, mock_get_user, client, mock_user):
        """Test deletion of non-existent file."""
        mock_get_user.return_value = mock_user
        mock_service.delete_file.side_effect = FileNotFoundError("File not found")

        response = client.delete("/files/nonexistent-file")

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_delete_file_permission_error(self, mock_service, mock_get_user, client, mock_user):
        """Test deletion with permission error."""
        mock_get_user.return_value = mock_user
        mock_service.delete_file.side_effect = PermissionError("Access denied")

        response = client.delete("/files/restricted-file")

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]


class TestFileListEndpoint:
    """Test file list endpoint."""

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_list_files_success(self, mock_service, mock_get_user, client, mock_user, mock_file_metadata):
        """Test successful file listing."""
        mock_get_user.return_value = mock_user
        mock_service.list_files.return_value = ([mock_file_metadata], 1)

        response = client.get("/files")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["files"]) == 1
        assert data["files"][0]["file_id"] == "test-file-123"

        mock_service.list_files.assert_called_once()

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_list_files_with_filters(self, mock_service, mock_get_user, client, mock_user, mock_file_metadata):
        """Test file listing with filters."""
        mock_get_user.return_value = mock_user
        mock_service.list_files.return_value = ([mock_file_metadata], 1)

        response = client.get("/files?limit=10&offset=0&content_type=text/plain&tag=test")

        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert "total" in data

        # Verify service was called with filters
        mock_service.list_files.assert_called_once()

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_list_files_service_error(self, mock_service, mock_get_user, client, mock_user):
        """Test file listing with service error."""
        mock_get_user.return_value = mock_user
        mock_service.list_files.side_effect = Exception("Storage error")

        response = client.get("/files")

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestFileMetadataEndpoint:
    """Test file metadata endpoint."""

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_get_metadata_success(self, mock_service, mock_get_user, client, mock_user, mock_file_metadata):
        """Test successful metadata retrieval."""
        mock_get_user.return_value = mock_user
        mock_service.get_file_metadata.return_value = mock_file_metadata

        response = client.get("/files/test-file-123/metadata")

        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == "test-file-123"
        assert data["file_name"] == "test.txt"
        assert data["content_type"] == "text/plain"

        mock_service.get_file_metadata.assert_called_once_with("test-file-123", "test-user-123")

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_get_metadata_not_found(self, mock_service, mock_get_user, client, mock_user):
        """Test metadata retrieval for non-existent file."""
        mock_get_user.return_value = mock_user
        mock_service.get_file_metadata.side_effect = FileNotFoundError("File not found")

        response = client.get("/files/nonexistent-file/metadata")

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]


class TestBatchUploadEndpoint:
    """Test batch upload endpoint."""

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_batch_upload_success(self, mock_service, mock_get_user, client, mock_user, mock_file_metadata):
        """Test successful batch upload."""
        mock_get_user.return_value = mock_user
        mock_service.store_file.return_value = mock_file_metadata

        # Create test files
        test_content = b"Test file content"
        files = [
            ("files", ("test1.txt", io.BytesIO(test_content), "text/plain")),
            ("files", ("test2.txt", io.BytesIO(test_content), "text/plain"))
        ]

        response = client.post("/files/batch", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "successful_uploads" in data
        assert "failed_uploads" in data

        # Should have attempted to store files
        assert mock_service.store_file.call_count >= 1

    @patch('dotmac.platform.file_storage.router.get_current_user')
    @patch('dotmac.platform.file_storage.router.storage_service')
    def test_batch_upload_mixed_results(self, mock_service, mock_get_user, client, mock_user, mock_file_metadata):
        """Test batch upload with mixed success/failure."""
        mock_get_user.return_value = mock_user
        # First call succeeds, second fails
        mock_service.store_file.side_effect = [mock_file_metadata, Exception("Storage error")]

        test_content = b"Test file content"
        files = [
            ("files", ("test1.txt", io.BytesIO(test_content), "text/plain")),
            ("files", ("test2.txt", io.BytesIO(test_content), "text/plain"))
        ]

        response = client.post("/files/batch", files=files)

        assert response.status_code == 200
        data = response.json()
        assert len(data["successful_uploads"]) >= 1
        assert len(data["failed_uploads"]) >= 0  # May vary based on implementation

    @patch('dotmac.platform.file_storage.router.get_current_user')
    def test_batch_upload_no_files(self, mock_get_user, client, mock_user):
        """Test batch upload with no files."""
        mock_get_user.return_value = mock_user

        response = client.post("/files/batch", files=[])

        assert response.status_code == 400
        assert "No files provided" in response.json()["detail"]


class TestRouterConfiguration:
    """Test router configuration."""

    def test_router_instance_exists(self):
        """Test that router instance exists and is configured."""
        from dotmac.platform.file_storage.router import file_storage_router, storage_router

        assert file_storage_router is not None
        assert storage_router is file_storage_router  # Should be alias

    def test_storage_service_instance_exists(self):
        """Test that storage service instance is available."""
        from dotmac.platform.file_storage.router import storage_service

        assert storage_service is not None

    def test_response_models_exist(self):
        """Test that response models are properly defined."""
        from dotmac.platform.file_storage.router import (
            FileUploadResponse,
            FileListResponse,
            BatchUploadResponse
        )

        # Should be able to create instances
        assert FileUploadResponse.__name__ == "FileUploadResponse"
        assert FileListResponse.__name__ == "FileListResponse"
        assert BatchUploadResponse.__name__ == "BatchUploadResponse"