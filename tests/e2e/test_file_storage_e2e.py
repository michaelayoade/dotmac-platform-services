"""
End-to-End tests for File Storage API.

Tests complete workflows through the API router, covering:
- File upload/download
- File deletion
- File metadata management
- File listing
- Batch operations
- Integration with storage backends

This E2E test suite covers the following modules:
- src/dotmac/platform/file_storage/router.py (router)
- src/dotmac/platform/file_storage/service.py (service)
- src/dotmac/platform/file_storage/minio_storage.py (storage backend)
"""

import io
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# Pytest marker for E2E tests
pytestmark = pytest.mark.e2e


@pytest.fixture
async def file_storage_app():
    """Create FastAPI app with file storage router for E2E testing."""
    from dotmac.platform.auth.core import UserInfo
    from dotmac.platform.auth.dependencies import get_current_user
    from dotmac.platform.file_storage.router import file_storage_router

    app = FastAPI(title="File Storage E2E Test App")
    app.include_router(file_storage_router, prefix="/api/v1/files/storage", tags=["File Storage"])

    # Override auth dependency
    async def override_get_current_user():
        return UserInfo(
            user_id="test-user-123",
            username="testuser",
            email="test@example.com",
            permissions=["read", "write"],
            roles=["user"],
            tenant_id="test-tenant",
        )

    app.dependency_overrides[get_current_user] = override_get_current_user

    return app


@pytest.fixture
async def client(file_storage_app):
    """Async HTTP client for E2E testing."""
    transport = ASGITransport(app=file_storage_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def mock_storage_service():
    """Mock storage service for testing."""
    with patch("dotmac.platform.file_storage.router.storage_service") as mock_service:
        # Configure mock service methods
        mock_service.store_file = AsyncMock()
        mock_service.retrieve_file = AsyncMock()
        mock_service.delete_file = AsyncMock()
        mock_service.list_files = AsyncMock()
        mock_service.get_file_metadata = AsyncMock()
        yield mock_service


# ============================================================================
# File Upload E2E Tests
# ============================================================================


class TestFileUploadE2E:
    """E2E tests for file upload workflows."""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, client, mock_storage_service):
        """Test successful file upload."""
        # Setup mock
        file_id = str(uuid4())
        mock_storage_service.store_file.return_value = file_id

        # Create test file
        file_content = b"Test file content"
        files = {
            "file": ("test.txt", io.BytesIO(file_content), "text/plain"),
        }
        data = {
            "path": "documents/test",
            "description": "Test file upload",
        }

        # Upload file
        response = await client.post(
            "/api/v1/files/storage/upload",
            files=files,
            data=data,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["file_id"] == file_id
        assert result["file_name"] == "test.txt"
        assert result["file_size"] == len(file_content)
        assert result["content_type"] == "text/plain"
        assert "upload_timestamp" in result
        assert result["url"] == f"/api/v1/files/storage/{file_id}/download"

        # Verify service was called correctly
        mock_storage_service.store_file.assert_called_once()
        call_args = mock_storage_service.store_file.call_args
        assert call_args.kwargs["file_name"] == "test.txt"
        assert call_args.kwargs["content_type"] == "text/plain"
        assert call_args.kwargs["path"] == "documents/test"
        assert call_args.kwargs["tenant_id"] == "test-tenant"
        assert call_args.kwargs["metadata"]["uploaded_by"] == "test-user-123"

    @pytest.mark.asyncio
    async def test_upload_file_without_path(self, client, mock_storage_service):
        """Test upload without specifying path (auto-generated)."""
        file_id = str(uuid4())
        mock_storage_service.store_file.return_value = file_id

        files = {
            "file": ("document.pdf", io.BytesIO(b"PDF content"), "application/pdf"),
        }

        response = await client.post(
            "/api/v1/files/storage/upload",
            files=files,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["file_id"] == file_id

        # Verify auto-generated path includes user_id and date
        call_args = mock_storage_service.store_file.call_args
        path = call_args.kwargs["path"]
        assert "uploads/test-user-123" in path
        assert datetime.now(UTC).strftime("%Y/%m/%d") in path

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, client, mock_storage_service):
        """Test upload fails for files exceeding size limit."""
        # Create file larger than 100MB
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        files = {
            "file": ("large.bin", io.BytesIO(large_content), "application/octet-stream"),
        }

        response = await client.post(
            "/api/v1/files/storage/upload",
            files=files,
        )

        assert response.status_code == 413
        data = response.json()
        assert "File too large" in data["detail"]

        # Verify service was NOT called
        mock_storage_service.store_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_file_storage_error(self, client, mock_storage_service):
        """Test error handling when storage fails."""
        mock_storage_service.store_file.side_effect = Exception("Storage unavailable")

        files = {
            "file": ("test.txt", io.BytesIO(b"content"), "text/plain"),
        }

        response = await client.post(
            "/api/v1/files/storage/upload",
            files=files,
        )

        assert response.status_code == 500
        data = response.json()
        assert "File upload failed" in data["detail"]

    @pytest.mark.asyncio
    async def test_upload_binary_file(self, client, mock_storage_service):
        """Test uploading binary files (images, etc.)."""
        file_id = str(uuid4())
        mock_storage_service.store_file.return_value = file_id

        # Simulate image upload
        image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # PNG header + data
        files = {
            "file": ("photo.png", io.BytesIO(image_bytes), "image/png"),
        }

        response = await client.post(
            "/api/v1/files/storage/upload",
            files=files,
            data={"description": "Profile photo"},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["content_type"] == "image/png"
        assert result["file_name"] == "photo.png"


# ============================================================================
# File Download E2E Tests
# ============================================================================


class TestFileDownloadE2E:
    """E2E tests for file download workflows."""

    @pytest.mark.asyncio
    async def test_download_file_success(self, client, mock_storage_service):
        """Test successful file download."""
        file_id = str(uuid4())
        file_content = b"Downloaded file content"
        metadata = {
            "file_name": "downloaded.txt",
            "content_type": "text/plain",
            "file_size": len(file_content),
        }

        mock_storage_service.retrieve_file.return_value = (file_content, metadata)

        response = await client.get(f"/api/v1/files/storage/{file_id}/download")

        assert response.status_code == 200
        assert response.content == file_content
        assert "text/plain" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        assert "downloaded.txt" in response.headers["content-disposition"]
        assert response.headers["content-length"] == str(len(file_content))

        # Verify service was called correctly
        mock_storage_service.retrieve_file.assert_called_once_with(file_id, "test-tenant")

    @pytest.mark.asyncio
    async def test_download_file_not_found(self, client, mock_storage_service):
        """Test download fails for non-existent file."""
        file_id = str(uuid4())
        mock_storage_service.retrieve_file.return_value = (None, None)

        response = await client.get(f"/api/v1/files/storage/{file_id}/download")

        assert response.status_code == 404
        data = response.json()
        assert file_id in data["detail"]
        assert "not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_download_file_storage_error(self, client, mock_storage_service):
        """Test error handling when download fails."""
        file_id = str(uuid4())
        mock_storage_service.retrieve_file.side_effect = Exception("Storage error")

        response = await client.get(f"/api/v1/files/storage/{file_id}/download")

        assert response.status_code == 500
        data = response.json()
        assert "File download failed" in data["detail"]

    @pytest.mark.asyncio
    async def test_download_binary_file(self, client, mock_storage_service):
        """Test downloading binary files."""
        file_id = str(uuid4())
        image_bytes = b"\xFF\xD8\xFF" + b"\x00" * 100  # JPEG header + data
        metadata = {
            "file_name": "image.jpg",
            "content_type": "image/jpeg",
        }

        mock_storage_service.retrieve_file.return_value = (image_bytes, metadata)

        response = await client.get(f"/api/v1/files/storage/{file_id}/download")

        assert response.status_code == 200
        assert response.content == image_bytes
        assert response.headers["content-type"] == "image/jpeg"


# ============================================================================
# File Deletion E2E Tests
# ============================================================================


class TestFileDeleteE2E:
    """E2E tests for file deletion workflows."""

    @pytest.mark.asyncio
    async def test_delete_file_success(self, client, mock_storage_service):
        """Test successful file deletion."""
        file_id = str(uuid4())
        mock_storage_service.delete_file.return_value = True

        response = await client.delete(f"/api/v1/files/storage/{file_id}")

        assert response.status_code == 200
        data = response.json()
        assert file_id in data["message"]
        assert "deleted successfully" in data["message"]
        assert "deleted_at" in data

        # Verify service was called
        mock_storage_service.delete_file.assert_called_once_with(file_id)

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, client, mock_storage_service):
        """Test deletion fails for non-existent file."""
        file_id = str(uuid4())
        mock_storage_service.delete_file.return_value = False

        response = await client.delete(f"/api/v1/files/storage/{file_id}")

        assert response.status_code == 404
        data = response.json()
        assert file_id in data["detail"]
        assert "not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_delete_file_storage_error(self, client, mock_storage_service):
        """Test error handling when deletion fails."""
        file_id = str(uuid4())
        mock_storage_service.delete_file.side_effect = Exception("Delete error")

        response = await client.delete(f"/api/v1/files/storage/{file_id}")

        assert response.status_code == 500
        data = response.json()
        assert "File deletion failed" in data["detail"]


# ============================================================================
# File Listing E2E Tests
# ============================================================================


class TestFileListE2E:
    """E2E tests for file listing workflows."""

    @pytest.mark.asyncio
    async def test_list_files_success(self, client, mock_storage_service):
        """Test successful file listing."""
        from dotmac.platform.file_storage.service import FileMetadata

        files = [
            FileMetadata(
                file_id=str(uuid4()),
                file_name="file1.txt",
                file_size=100,
                content_type="text/plain",
                created_at=datetime.now(UTC),
                path="uploads/test-user-123/documents",
            ),
            FileMetadata(
                file_id=str(uuid4()),
                file_name="file2.pdf",
                file_size=200,
                content_type="application/pdf",
                created_at=datetime.now(UTC),
                path="uploads/test-user-123/documents",
            ),
        ]

        mock_storage_service.list_files.return_value = files

        response = await client.get("/api/v1/files/storage")

        assert response.status_code == 200
        data = response.json()
        assert len(data["files"]) == 2
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["per_page"] == 100

        # Verify first file
        assert data["files"][0]["file_name"] == "file1.txt"
        assert data["files"][0]["file_size"] == 100

    @pytest.mark.asyncio
    async def test_list_files_with_pagination(self, client, mock_storage_service):
        """Test file listing with pagination."""
        mock_storage_service.list_files.return_value = []

        response = await client.get("/api/v1/files/storage?skip=20&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 3  # (20 / 10) + 1
        assert data["per_page"] == 10

        # Verify service was called with correct pagination
        call_args = mock_storage_service.list_files.call_args
        assert call_args.kwargs["offset"] == 20
        assert call_args.kwargs["limit"] == 10

    @pytest.mark.asyncio
    async def test_list_files_with_path_filter(self, client, mock_storage_service):
        """Test listing files with path filter."""
        mock_storage_service.list_files.return_value = []

        response = await client.get("/api/v1/files/storage?path=documents/2024")

        assert response.status_code == 200

        # Verify path filter was applied
        call_args = mock_storage_service.list_files.call_args
        path = call_args.kwargs["path"]
        assert "uploads/test-user-123" in path
        assert "documents/2024" in path

    @pytest.mark.asyncio
    async def test_list_files_empty(self, client, mock_storage_service):
        """Test listing when no files exist."""
        mock_storage_service.list_files.return_value = []

        response = await client.get("/api/v1/files/storage")

        assert response.status_code == 200
        data = response.json()
        assert data["files"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_files_error(self, client, mock_storage_service):
        """Test error handling when listing fails."""
        mock_storage_service.list_files.side_effect = Exception("List error")

        response = await client.get("/api/v1/files/storage")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to list files" in data["detail"]


# ============================================================================
# File Metadata E2E Tests
# ============================================================================


class TestFileMetadataE2E:
    """E2E tests for file metadata operations."""

    @pytest.mark.asyncio
    async def test_get_metadata_success(self, client, mock_storage_service):
        """Test successful metadata retrieval."""
        file_id = str(uuid4())
        metadata = {
            "file_id": file_id,
            "file_name": "document.pdf",
            "file_size": 1024,
            "content_type": "application/pdf",
            "created_at": datetime.now(UTC).isoformat(),
            "checksum": "abc123def456",
            "custom_field": "custom_value",
        }

        mock_storage_service.get_file_metadata.return_value = metadata

        response = await client.get(f"/api/v1/files/storage/{file_id}/metadata")

        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == file_id
        assert data["file_name"] == "document.pdf"
        assert data["checksum"] == "abc123def456"
        assert data["custom_field"] == "custom_value"

    @pytest.mark.asyncio
    async def test_get_metadata_not_found(self, client, mock_storage_service):
        """Test metadata retrieval for non-existent file."""
        file_id = str(uuid4())
        mock_storage_service.get_file_metadata.return_value = None

        response = await client.get(f"/api/v1/files/storage/{file_id}/metadata")

        assert response.status_code == 404
        data = response.json()
        assert file_id in data["detail"]

    @pytest.mark.asyncio
    async def test_get_metadata_error(self, client, mock_storage_service):
        """Test error handling when metadata retrieval fails."""
        file_id = str(uuid4())
        mock_storage_service.get_file_metadata.side_effect = Exception("Metadata error")

        response = await client.get(f"/api/v1/files/storage/{file_id}/metadata")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to get file metadata" in data["detail"]


# ============================================================================
# Batch Operations E2E Tests
# ============================================================================


class TestBatchOperationsE2E:
    """E2E tests for batch file operations."""

    @pytest.mark.asyncio
    async def test_batch_delete_success(self, client, mock_storage_service):
        """Test batch deletion of multiple files."""
        file_ids = [str(uuid4()), str(uuid4()), str(uuid4())]
        mock_storage_service.delete_file.return_value = True

        response = await client.post(
            "/api/v1/files/storage/batch",
            json={
                "file_ids": file_ids,
                "operation": "delete",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "delete"
        assert len(data["results"]) == 3
        assert all(r["status"] == "deleted" for r in data["results"])

        # Verify all deletes were called
        assert mock_storage_service.delete_file.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_delete_partial_failure(self, client, mock_storage_service):
        """Test batch deletion with some failures."""
        file_ids = [str(uuid4()), str(uuid4())]
        # First succeeds, second fails
        mock_storage_service.delete_file.side_effect = [True, False]

        response = await client.post(
            "/api/v1/files/storage/batch",
            json={
                "file_ids": file_ids,
                "operation": "delete",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["results"][0]["status"] == "deleted"
        assert data["results"][1]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_batch_move_operation(self, client, mock_storage_service):
        """Test batch move operation."""
        file_ids = [str(uuid4()), str(uuid4())]

        response = await client.post(
            "/api/v1/files/storage/batch",
            json={
                "file_ids": file_ids,
                "operation": "move",
                "destination": "archive/2024",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "move"
        assert all(r["status"] == "moved" for r in data["results"])

    @pytest.mark.asyncio
    async def test_batch_unsupported_operation(self, client, mock_storage_service):
        """Test batch operation with unsupported operation type."""
        file_ids = [str(uuid4())]

        response = await client.post(
            "/api/v1/files/storage/batch",
            json={
                "file_ids": file_ids,
                "operation": "compress",  # Not supported
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["status"] == "unsupported_operation"

    @pytest.mark.asyncio
    async def test_batch_operation_error(self, client, mock_storage_service):
        """Test error handling in batch operations."""
        mock_storage_service.delete_file.side_effect = Exception("Batch error")

        response = await client.post(
            "/api/v1/files/storage/batch",
            json={
                "file_ids": [str(uuid4())],
                "operation": "delete",
            },
        )

        assert response.status_code == 500
        data = response.json()
        assert "Batch operation failed" in data["detail"]


# ============================================================================
# Complete Workflow E2E Tests
# ============================================================================


class TestCompleteWorkflowE2E:
    """E2E tests for complete file lifecycle workflows."""

    @pytest.mark.asyncio
    async def test_complete_file_lifecycle(self, client, mock_storage_service):
        """Test complete workflow: upload → metadata → download → delete."""
        file_id = str(uuid4())
        file_content = b"Complete lifecycle test content"

        # 1. Upload file
        mock_storage_service.store_file.return_value = file_id
        upload_response = await client.post(
            "/api/v1/files/storage/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
            data={"description": "Lifecycle test"},
        )
        assert upload_response.status_code == 200
        assert upload_response.json()["file_id"] == file_id

        # 2. Get metadata
        mock_storage_service.get_file_metadata.return_value = {
            "file_id": file_id,
            "file_name": "test.txt",
            "file_size": len(file_content),
        }
        metadata_response = await client.get(f"/api/v1/files/storage/{file_id}/metadata")
        assert metadata_response.status_code == 200
        assert metadata_response.json()["file_id"] == file_id

        # 3. Download file
        mock_storage_service.retrieve_file.return_value = (
            file_content,
            {"file_name": "test.txt", "content_type": "text/plain"},
        )
        download_response = await client.get(f"/api/v1/files/storage/{file_id}/download")
        assert download_response.status_code == 200
        assert download_response.content == file_content

        # 4. Delete file
        mock_storage_service.delete_file.return_value = True
        delete_response = await client.delete(f"/api/v1/files/storage/{file_id}")
        assert delete_response.status_code == 200

    @pytest.mark.asyncio
    async def test_multi_file_upload_and_list(self, client, mock_storage_service):
        """Test uploading multiple files and listing them."""
        from dotmac.platform.file_storage.service import FileMetadata

        file_ids = [str(uuid4()), str(uuid4()), str(uuid4())]
        mock_storage_service.store_file.side_effect = file_ids

        # Upload 3 files
        for i, file_id in enumerate(file_ids):
            response = await client.post(
                "/api/v1/files/storage/upload",
                files={
                    "file": (
                        f"file{i}.txt",
                        io.BytesIO(f"Content {i}".encode()),
                        "text/plain",
                    )
                },
            )
            assert response.status_code == 200

        # List files
        mock_storage_service.list_files.return_value = [
            FileMetadata(
                file_id=fid,
                file_name=f"file{i}.txt",
                file_size=10,
                content_type="text/plain",
                created_at=datetime.now(UTC),
            )
            for i, fid in enumerate(file_ids)
        ]

        list_response = await client.get("/api/v1/files/storage")
        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data["files"]) == 3
