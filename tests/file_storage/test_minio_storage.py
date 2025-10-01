"""Tests for simplified MinIO storage."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO
from datetime import datetime
from pathlib import Path

from dotmac.platform.file_storage import MinIOStorage, FileInfo, get_storage
from minio.error import S3Error


class TestMinIOStorage:
    """Test MinIO storage functionality."""

    @pytest.fixture
    def mock_minio_client(self):
        """Create a mock Minio client."""
        with patch('dotmac.platform.file_storage.minio_storage.Minio') as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def storage(self, mock_minio_client):
        """Create MinIO storage with mocked client."""
        with patch('dotmac.platform.file_storage.minio_storage.Minio') as mock:
            mock.return_value = mock_minio_client
            mock_minio_client.bucket_exists.return_value = True
            storage = MinIOStorage()
            storage.client = mock_minio_client
            return storage

    def test_init_creates_bucket_if_not_exists(self):
        """Test that initialization creates bucket if it doesn't exist."""
        with patch('dotmac.platform.file_storage.minio_storage.Minio') as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            mock_client.bucket_exists.return_value = False

            storage = MinIOStorage()

            mock_client.bucket_exists.assert_called_once()
            mock_client.make_bucket.assert_called_once()

    def test_init_handles_http_endpoint(self):
        """Test initialization with http:// endpoint."""
        with patch('dotmac.platform.file_storage.minio_storage.Minio') as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            mock_client.bucket_exists.return_value = True

            storage = MinIOStorage(endpoint="http://localhost:9000")

            mock.assert_called_with(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin123",
                secure=False,
            )

    def test_init_handles_https_endpoint(self):
        """Test initialization with https:// endpoint."""
        with patch('dotmac.platform.file_storage.minio_storage.Minio') as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            mock_client.bucket_exists.return_value = True

            storage = MinIOStorage(endpoint="https://minio.example.com")

            mock.assert_called_with(
                endpoint="minio.example.com",
                access_key="minioadmin",
                secret_key="minioadmin123",
                secure=True,
            )

    def test_save_file(self, storage):
        """Test saving a file to MinIO."""
        content = BytesIO(b"test content")
        tenant_id = "tenant-123"

        result = storage.save_file("test.txt", content, tenant_id)

        assert result == "tenant-123/test.txt"
        storage.client.put_object.assert_called_once()
        call_args = storage.client.put_object.call_args
        assert call_args[0][0] == "dotmac"  # bucket
        assert call_args[0][1] == "tenant-123/test.txt"  # object name

    def test_save_file_handles_error(self, storage):
        """Test save_file error handling."""
        storage.client.put_object.side_effect = S3Error(
            "PutObject", "500", "Internal Server Error", "", "", ""
        )

        with pytest.raises(S3Error):
            content = BytesIO(b"test")
            storage.save_file("test.txt", content, "tenant-123")

    def test_get_file(self, storage):
        """Test getting a file from MinIO."""
        mock_response = Mock()
        mock_response.read.return_value = b"file content"
        storage.client.get_object.return_value = mock_response

        data = storage.get_file("test.txt", "tenant-123")

        assert data == b"file content"
        storage.client.get_object.assert_called_once_with(
            "dotmac", "tenant-123/test.txt"
        )
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()

    def test_get_file_not_found(self, storage):
        """Test getting a non-existent file."""
        error = S3Error("GetObject", "NoSuchKey", "Not Found", "", "", "")
        storage.client.get_object.side_effect = error

        with pytest.raises(FileNotFoundError) as exc:
            storage.get_file("missing.txt", "tenant-123")

        assert "tenant-123/missing.txt" in str(exc.value)

    def test_delete_file(self, storage):
        """Test deleting a file from MinIO."""
        result = storage.delete_file("test.txt", "tenant-123")

        assert result is True
        storage.client.remove_object.assert_called_once_with(
            "dotmac", "tenant-123/test.txt"
        )

    def test_delete_file_not_found(self, storage):
        """Test deleting a non-existent file."""
        error = S3Error("RemoveObject", "NoSuchKey", "Not Found", "", "", "")
        storage.client.remove_object.side_effect = error

        result = storage.delete_file("missing.txt", "tenant-123")

        assert result is False

    def test_file_exists_true(self, storage):
        """Test checking if a file exists (true case)."""
        storage.client.stat_object.return_value = Mock()

        exists = storage.file_exists("test.txt", "tenant-123")

        assert exists is True
        storage.client.stat_object.assert_called_once_with(
            "dotmac", "tenant-123/test.txt"
        )

    def test_file_exists_false(self, storage):
        """Test checking if a file exists (false case)."""
        error = S3Error("StatObject", "NoSuchKey", "Not Found", "", "", "")
        storage.client.stat_object.side_effect = error

        exists = storage.file_exists("missing.txt", "tenant-123")

        assert exists is False

    def test_list_files(self, storage):
        """Test listing files from MinIO."""
        mock_obj1 = Mock()
        mock_obj1.object_name = "tenant-123/file1.txt"
        mock_obj1.size = 100
        mock_obj1.content_type = "text/plain"
        mock_obj1.last_modified = datetime.now()

        mock_obj2 = Mock()
        mock_obj2.object_name = "tenant-123/file2.pdf"
        mock_obj2.size = 200
        mock_obj2.content_type = "application/pdf"
        mock_obj2.last_modified = datetime.now()

        storage.client.list_objects.return_value = [mock_obj1, mock_obj2]

        files = storage.list_files(tenant_id="tenant-123")

        assert len(files) == 2
        assert files[0].filename == "file1.txt"
        assert files[0].path == "file1.txt"
        assert files[0].size == 100
        assert files[1].filename == "file2.pdf"
        assert files[1].path == "file2.pdf"

    def test_list_files_with_limit(self, storage):
        """Test listing files with a limit."""
        mock_objs = []
        for i in range(5):
            obj = Mock()
            obj.object_name = f"tenant-123/file{i}.txt"
            obj.size = 100
            obj.content_type = "text/plain"
            obj.last_modified = datetime.now()
            mock_objs.append(obj)

        storage.client.list_objects.return_value = mock_objs

        files = storage.list_files(tenant_id="tenant-123", limit=3)

        assert len(files) == 3

    def test_list_files_skips_invalid(self, storage):
        """Test list_files skips objects with missing fields."""
        mock_obj1 = Mock()
        mock_obj1.object_name = "tenant-123/valid.txt"
        mock_obj1.size = 100
        mock_obj1.content_type = "text/plain"
        mock_obj1.last_modified = datetime.now()

        mock_obj2 = Mock()
        mock_obj2.object_name = None  # Missing object name
        mock_obj2.size = 200
        mock_obj2.content_type = "text/plain"
        mock_obj2.last_modified = datetime.now()

        mock_obj3 = Mock()
        mock_obj3.object_name = "tenant-123/no-size.txt"
        mock_obj3.size = None  # Missing size
        mock_obj3.content_type = "text/plain"
        mock_obj3.last_modified = datetime.now()

        storage.client.list_objects.return_value = [mock_obj1, mock_obj2, mock_obj3]

        files = storage.list_files(tenant_id="tenant-123")

        assert len(files) == 1
        assert files[0].filename == "valid.txt"

    def test_save_file_from_path(self, storage):
        """Test uploading a file from local filesystem."""
        result = storage.save_file_from_path(
            "/local/file.pdf", "documents/file.pdf", "tenant-123"
        )

        assert result == "tenant-123/documents/file.pdf"
        storage.client.fput_object.assert_called_once_with(
            "dotmac", "tenant-123/documents/file.pdf", "/local/file.pdf"
        )

    def test_get_file_to_path(self, storage):
        """Test downloading a file to local filesystem."""
        result = storage.get_file_to_path(
            "documents/file.pdf", "/local/download.pdf", "tenant-123"
        )

        assert result == "/local/download.pdf"
        storage.client.fget_object.assert_called_once_with(
            "dotmac", "tenant-123/documents/file.pdf", "/local/download.pdf"
        )

    def test_get_file_to_path_not_found(self, storage):
        """Test downloading a non-existent file."""
        error = S3Error("GetObject", "NoSuchKey", "Not Found", "", "", "")
        storage.client.fget_object.side_effect = error

        with pytest.raises(FileNotFoundError):
            storage.get_file_to_path(
                "missing.pdf", "/local/file.pdf", "tenant-123"
            )

    def test_get_object_name(self, storage):
        """Test object name generation with tenant prefix."""
        name = storage._get_object_name("path/to/file.txt", "tenant-123")
        assert name == "tenant-123/path/to/file.txt"

        # Test with leading slash
        name = storage._get_object_name("/path/to/file.txt", "tenant-123")
        assert name == "tenant-123/path/to/file.txt"


class TestFileInfo:
    """Test FileInfo dataclass."""

    def test_file_info_creation(self):
        """Test creating FileInfo instance."""
        info = FileInfo(
            filename="test.txt",
            path="path/to/test.txt",
            size=1024,
            content_type="text/plain",
            modified_at=datetime.now(),
            tenant_id="tenant-123"
        )

        assert info.filename == "test.txt"
        assert info.path == "path/to/test.txt"
        assert info.size == 1024
        assert info.content_type == "text/plain"
        assert info.tenant_id == "tenant-123"


class TestGlobalStorage:
    """Test global storage singleton."""

    def test_get_storage_singleton(self):
        """Test that get_storage returns a singleton."""
        with patch('dotmac.platform.file_storage.minio_storage.MinIOStorage') as mock:
            mock_instance = Mock()
            mock.return_value = mock_instance

            # Clear any existing instance
            import dotmac.platform.file_storage.minio_storage as mod
            mod._storage = None

            storage1 = get_storage()
            storage2 = get_storage()

            assert storage1 is storage2
            mock.assert_called_once()  # Only initialized once