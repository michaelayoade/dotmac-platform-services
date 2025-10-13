"""
Tests for file storage service.
"""

import hashlib
import json
from unittest.mock import Mock, patch

import pytest

from dotmac.platform.file_storage.service import (
    FileStorageService,
    LocalFileStorage,
    MemoryFileStorage,
    MinIOFileStorage,
    StorageBackend,
    get_storage_service,
)


class TestMemoryFileStorage:
    """Test in-memory file storage."""

    @pytest.fixture
    def storage(self):
        """Create memory storage instance."""
        return MemoryFileStorage()

    @pytest.mark.asyncio
    async def test_store_file(self, storage):
        """Test storing a file in memory."""
        file_data = b"Test file content"
        file_name = "test.txt"
        content_type = "text/plain"

        file_id = await storage.store(
            file_data=file_data,
            file_name=file_name,
            content_type=content_type,
            path="test/path",
            metadata={"key": "value"},
            tenant_id="tenant1",
        )

        assert file_id is not None
        assert file_id in storage.files
        assert storage.files[file_id] == file_data
        assert file_id in storage.metadata

        metadata = storage.metadata[file_id]
        assert metadata.file_name == file_name
        assert metadata.file_size == len(file_data)
        assert metadata.content_type == content_type
        assert metadata.path == "test/path"
        assert metadata.tenant_id == "tenant1"
        assert metadata.metadata == {"key": "value"}
        assert metadata.checksum == hashlib.sha256(file_data).hexdigest()

    @pytest.mark.asyncio
    async def test_retrieve_file(self, storage):
        """Test retrieving a file from memory."""
        # Store a file first
        file_data = b"Test file content"
        file_id = await storage.store(
            file_data=file_data,
            file_name="test.txt",
            content_type="text/plain",
        )

        # Retrieve the file
        retrieved_data, metadata = await storage.retrieve(file_id)

        assert retrieved_data == file_data
        assert metadata is not None
        assert metadata["file_id"] == file_id
        assert metadata["file_name"] == "test.txt"
        assert metadata["file_size"] == len(file_data)

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_file(self, storage):
        """Test retrieving a non-existent file."""
        file_data, metadata = await storage.retrieve("nonexistent-id")

        assert file_data is None
        assert metadata is None

    @pytest.mark.asyncio
    async def test_delete_file(self, storage):
        """Test deleting a file from memory."""
        # Store a file first
        file_data = b"Test file content"
        file_id = await storage.store(
            file_data=file_data,
            file_name="test.txt",
            content_type="text/plain",
        )

        # Verify it exists
        assert file_id in storage.files

        # Delete the file
        success = await storage.delete(file_id)

        assert success is True
        assert file_id not in storage.files
        assert file_id not in storage.metadata

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, storage):
        """Test deleting a non-existent file."""
        success = await storage.delete("nonexistent-id")

        assert success is False

    @pytest.mark.asyncio
    async def test_list_files(self, storage):
        """Test listing files in memory."""
        # Store multiple files
        file_ids = []
        for i in range(5):
            file_id = await storage.store(
                file_data=f"Content {i}".encode(),
                file_name=f"file{i}.txt",
                content_type="text/plain",
                path=f"path/{i % 2}",  # Alternate between two paths
                tenant_id="tenant1" if i % 2 == 0 else "tenant2",
            )
            file_ids.append(file_id)

        # List all files
        all_files = await storage.list_files()
        assert len(all_files) == 5

        # List files for specific tenant
        tenant1_files = await storage.list_files(tenant_id="tenant1")
        assert len(tenant1_files) == 3  # Files 0, 2, 4

        # List files with specific path
        path0_files = await storage.list_files(path="path/0")
        assert len(path0_files) == 3  # Files 0, 2, 4

        # Test pagination
        page1 = await storage.list_files(limit=2, offset=0)
        assert len(page1) == 2

        page2 = await storage.list_files(limit=2, offset=2)
        assert len(page2) == 2

    @pytest.mark.asyncio
    async def test_get_metadata(self, storage):
        """Test getting file metadata."""
        # Store a file
        file_id = await storage.store(
            file_data=b"Test content",
            file_name="test.txt",
            content_type="text/plain",
            metadata={"custom": "data"},
        )

        # Get metadata
        metadata = await storage.get_metadata(file_id)

        assert metadata is not None
        assert metadata["file_id"] == file_id
        assert metadata["file_name"] == "test.txt"
        assert metadata["metadata"] == {"custom": "data"}

    @pytest.mark.asyncio
    async def test_get_metadata_nonexistent(self, storage):
        """Test getting metadata for non-existent file."""
        metadata = await storage.get_metadata("nonexistent-id")
        assert metadata is None


class TestLocalFileStorage:
    """Test local filesystem storage."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for testing."""
        return tmp_path / "test_storage"

    @pytest.fixture
    def storage(self, temp_dir):
        """Create local storage instance."""
        return LocalFileStorage(base_path=str(temp_dir))

    @pytest.mark.asyncio
    async def test_store_file_locally(self, storage, temp_dir):
        """Test storing a file on local filesystem."""
        file_data = b"Local test file content"
        file_name = "local_test.txt"
        content_type = "text/plain"

        file_id = await storage.store(
            file_data=file_data,
            file_name=file_name,
            content_type=content_type,
            path="local/test",
            tenant_id="tenant1",
        )

        # Verify file exists on disk
        file_path = temp_dir / "tenant1" / file_id
        assert file_path.exists()
        assert file_path.read_bytes() == file_data

        # Verify metadata exists
        metadata_path = temp_dir / ".metadata" / f"{file_id}.json"
        assert metadata_path.exists()

        with open(metadata_path) as f:
            metadata = json.load(f)
            assert metadata["file_name"] == file_name
            assert metadata["file_size"] == len(file_data)

    @pytest.mark.asyncio
    async def test_retrieve_file_locally(self, storage, temp_dir):
        """Test retrieving a file from local filesystem."""
        # Store a file first
        file_data = b"Local test content"
        file_id = await storage.store(
            file_data=file_data,
            file_name="test.txt",
            content_type="text/plain",
            tenant_id="tenant1",
        )

        # Retrieve the file
        retrieved_data, metadata = await storage.retrieve(file_id, "tenant1")

        assert retrieved_data == file_data
        assert metadata is not None
        assert metadata["file_id"] == file_id

    @pytest.mark.asyncio
    async def test_delete_file_locally(self, storage, temp_dir):
        """Test deleting a file from local filesystem."""
        # Store a file
        file_data = b"Delete test content"
        file_id = await storage.store(
            file_data=file_data,
            file_name="delete.txt",
            content_type="text/plain",
            tenant_id="tenant1",
        )

        file_path = temp_dir / "tenant1" / file_id
        metadata_path = temp_dir / ".metadata" / f"{file_id}.json"

        # Verify files exist
        assert file_path.exists()
        assert metadata_path.exists()

        # Delete the file
        success = await storage.delete(file_id, "tenant1")

        assert success is True
        assert not file_path.exists()
        assert not metadata_path.exists()

    @pytest.mark.asyncio
    async def test_list_files_locally(self, storage):
        """Test listing files from local filesystem."""
        # Store multiple files
        for i in range(3):
            await storage.store(
                file_data=f"Content {i}".encode(),
                file_name=f"file{i}.txt",
                content_type="text/plain",
                path=f"path/{i}",
                tenant_id="tenant1",
            )

        # List all files
        files = await storage.list_files()
        assert len(files) == 3

        # List with tenant filter
        tenant_files = await storage.list_files(tenant_id="tenant1")
        assert len(tenant_files) == 3

        # List with path filter
        path_files = await storage.list_files(path="path/0")
        assert len(path_files) == 1


class TestMinIOFileStorage:
    """Test MinIO storage backend."""

    @pytest.fixture
    def mock_minio_client(self):
        """Create mock MinIO client."""
        client = Mock()
        client.save_file = Mock(return_value="tenant1/test-path/object-name")
        client.get_file = Mock(return_value=b"MinIO test content")
        client.delete_file = Mock(return_value=True)
        return client

    @pytest.fixture
    def storage(self, mock_minio_client):
        """Create MinIO storage instance."""
        return MinIOFileStorage(minio_client=mock_minio_client)

    @pytest.mark.asyncio
    async def test_store_file_minio(self, storage, mock_minio_client):
        """Test storing a file in MinIO."""
        file_data = b"MinIO test content"
        file_name = "minio_test.txt"
        content_type = "text/plain"

        file_id = await storage.store(
            file_data=file_data,
            file_name=file_name,
            content_type=content_type,
            path="test/path",
            tenant_id="tenant1",
        )

        assert file_id is not None
        assert mock_minio_client.save_file.called

        # Verify metadata stored
        assert file_id in storage.metadata_store
        metadata = storage.metadata_store[file_id]
        assert metadata.file_name == file_name

    @pytest.mark.asyncio
    async def test_retrieve_file_minio(self, storage, mock_minio_client):
        """Test retrieving a file from MinIO."""
        # Store a file first
        file_data = b"MinIO test content"
        file_id = await storage.store(
            file_data=file_data,
            file_name="test.txt",
            content_type="text/plain",
            tenant_id="tenant1",
        )

        # Retrieve the file
        retrieved_data, metadata = await storage.retrieve(file_id, "tenant1")

        assert retrieved_data == b"MinIO test content"  # From mock
        assert metadata is not None
        assert mock_minio_client.get_file.called

    @pytest.mark.asyncio
    async def test_delete_file_minio(self, storage, mock_minio_client):
        """Test deleting a file from MinIO."""
        # Store a file first
        file_id = await storage.store(
            file_data=b"Delete test",
            file_name="delete.txt",
            content_type="text/plain",
            tenant_id="tenant1",
        )

        # Delete the file
        success = await storage.delete(file_id, "tenant1")

        assert success is True
        assert mock_minio_client.delete_file.called
        assert file_id not in storage.metadata_store


class TestFileStorageService:
    """Test unified file storage service."""

    @pytest.mark.asyncio
    async def test_service_with_memory_backend(self):
        """Test service with memory backend."""
        service = FileStorageService(backend=StorageBackend.MEMORY)

        # Store a file
        file_id = await service.store_file(
            file_data=b"Service test content",
            file_name="service_test.txt",
            content_type="text/plain",
            metadata={"source": "test"},
        )

        assert file_id is not None

        # Retrieve the file
        file_data, metadata = await service.retrieve_file(file_id)

        assert file_data == b"Service test content"
        assert metadata is not None

        # Delete the file
        success = await service.delete_file(file_id)
        assert success is True

    @pytest.mark.asyncio
    async def test_service_with_local_backend(self, tmp_path):
        """Test service with local backend."""
        with patch("dotmac.platform.file_storage.service.settings") as mock_settings:
            mock_settings.storage.local_path = str(tmp_path)

            service = FileStorageService(backend=StorageBackend.LOCAL)

            # Store a file
            file_id = await service.store_file(
                file_data=b"Local service test",
                file_name="local_test.txt",
                content_type="text/plain",
            )

            # Verify file exists on disk
            assert (tmp_path / file_id).exists()

            # Retrieve the file
            file_data, metadata = await service.retrieve_file(file_id)
            assert file_data == b"Local service test"

    @pytest.mark.asyncio
    async def test_list_files(self):
        """Test listing files through service."""
        service = FileStorageService(backend=StorageBackend.MEMORY)

        # Store multiple files
        file_ids = []
        for i in range(3):
            file_id = await service.store_file(
                file_data=f"Content {i}".encode(),
                file_name=f"file{i}.txt",
                content_type="text/plain",
                path=f"path{i}",
                tenant_id="tenant1",
            )
            file_ids.append(file_id)

        # List files
        files = await service.list_files(tenant_id="tenant1")
        assert len(files) == 3

    @pytest.mark.asyncio
    async def test_update_file_metadata(self):
        """Test updating file metadata."""
        service = FileStorageService(backend=StorageBackend.MEMORY)

        # Store a file
        file_id = await service.store_file(
            file_data=b"Test content",
            file_name="test.txt",
            content_type="text/plain",
            metadata={"version": "1.0"},
        )

        # Update metadata
        success = await service.update_file_metadata(
            file_id=file_id,
            metadata_updates={"version": "2.0", "updated_by": "test"},
        )

        assert success is True

        # Verify metadata was updated
        metadata = await service.get_file_metadata(file_id)
        assert metadata is not None
        assert metadata["metadata"]["version"] == "2.0"
        assert metadata["metadata"]["updated_by"] == "test"

    def test_get_storage_service_singleton(self):
        """Test that get_storage_service returns singleton."""
        service1 = get_storage_service()
        service2 = get_storage_service()

        assert service1 is service2

    @pytest.mark.asyncio
    async def test_service_handles_errors(self):
        """Test service error handling."""
        from uuid import uuid4

        service = FileStorageService(backend=StorageBackend.MEMORY)

        # Try to retrieve non-existent file (must be valid UUID)
        nonexistent_id = str(uuid4())
        file_data, metadata = await service.retrieve_file(nonexistent_id)
        assert file_data is None
        assert metadata is None

        # Try to delete non-existent file (must be valid UUID)
        success = await service.delete_file(nonexistent_id)
        assert success is False


class TestEndToEndFileOperations:
    """End-to-end tests for file operations."""

    @pytest.mark.asyncio
    async def test_complete_file_lifecycle(self, tmp_path):
        """Test complete file lifecycle: upload, retrieve, update, delete."""
        with patch("dotmac.platform.file_storage.service.settings") as mock_settings:
            mock_settings.storage.local_path = str(tmp_path)
            mock_settings.storage.backend = StorageBackend.LOCAL

            service = FileStorageService(backend=StorageBackend.LOCAL)

            # 1. Upload a file
            test_content = b"This is a test file for end-to-end testing"
            file_id = await service.store_file(
                file_data=test_content,
                file_name="e2e_test.txt",
                content_type="text/plain",
                path="e2e/test",
                metadata={
                    "author": "test_user",
                    "purpose": "testing",
                },
                tenant_id="test_tenant",
            )

            assert file_id is not None
            print(f"✓ File uploaded: {file_id}")

            # 2. Retrieve the file
            retrieved_data, metadata = await service.retrieve_file(file_id, "test_tenant")

            assert retrieved_data == test_content
            assert metadata is not None
            assert metadata["file_name"] == "e2e_test.txt"
            assert metadata["content_type"] == "text/plain"
            assert metadata["metadata"]["author"] == "test_user"
            print("✓ File retrieved successfully")

            # 3. Update metadata
            success = await service.update_file_metadata(
                file_id=file_id,
                metadata_updates={
                    "status": "verified",
                    "reviewed_by": "admin",
                },
                tenant_id="test_tenant",
            )

            assert success is True
            print("✓ Metadata updated")

            # 4. List files
            files = await service.list_files(tenant_id="test_tenant")
            assert len(files) >= 1
            assert any(f.file_id == file_id for f in files)
            print("✓ File listed in storage")

            # 5. Delete the file
            deleted = await service.delete_file(file_id, "test_tenant")
            assert deleted is True
            print("✓ File deleted")

            # 6. Verify deletion
            retrieved_after_delete, _ = await service.retrieve_file(file_id, "test_tenant")
            assert retrieved_after_delete is None
            print("✓ File no longer accessible after deletion")

            print("\n✅ Complete file lifecycle test passed!")
