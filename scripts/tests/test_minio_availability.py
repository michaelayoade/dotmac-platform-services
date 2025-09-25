#!/usr/bin/env python
"""
Test which storage backend is actually being used.
"""

import asyncio
import os
from dotmac.platform.settings import settings
from dotmac.platform.file_storage.service import get_storage_service, FileStorageService, StorageBackend


def test_minio_availability():
    """Test if MinIO is available and can be used."""
    print("=" * 60)
    print("STORAGE BACKEND CONFIGURATION TEST")
    print("=" * 60)
    print()

    # 1. Check settings
    print("CURRENT SETTINGS:")
    print("-" * 40)
    print(f"  Provider:     {settings.storage.provider}")
    print(f"  Endpoint:     {settings.storage.endpoint or 'Not set'}")
    print(f"  Access Key:   {'***' if settings.storage.access_key else 'Not set'}")
    print(f"  Secret Key:   {'***' if settings.storage.secret_key else 'Not set'}")
    print(f"  Bucket:       {settings.storage.bucket}")
    print(f"  Use SSL:      {settings.storage.use_ssl}")
    print(f"  Local Path:   {settings.storage.local_path}")
    print()

    # 2. Check MinIO Python client availability
    print("CHECKING DEPENDENCIES:")
    print("-" * 40)
    try:
        import minio
        print(f"  ✓ MinIO Python client installed (version: {minio.__version__})")
    except ImportError as e:
        print(f"  ✗ MinIO Python client NOT installed: {e}")
        print("    Install with: pip install minio")
    print()

    # 3. Try to connect to MinIO
    print("TESTING MINIO CONNECTION:")
    print("-" * 40)
    if settings.storage.provider == "minio":
        try:
            from dotmac.platform.file_storage.minio_storage import MinIOStorage

            # Try to create MinIO client
            print(f"  Attempting to connect to MinIO...")
            storage = MinIOStorage()

            # Test bucket access
            print(f"  Checking bucket '{settings.storage.bucket}'...")

            # This will raise an error if MinIO is not accessible
            from minio import Minio
            client = storage.client

            if client.bucket_exists(settings.storage.bucket):
                print(f"  ✓ Bucket '{settings.storage.bucket}' exists and is accessible")
            else:
                print(f"  ⚠ Bucket '{settings.storage.bucket}' does not exist")

            print("  ✓ MinIO is AVAILABLE and ACCESSIBLE")
        except Exception as e:
            print(f"  ✗ MinIO connection FAILED: {e}")
            print("    MinIO server may not be running or credentials are incorrect")
    else:
        print(f"  Skipped - provider is set to '{settings.storage.provider}', not 'minio'")
    print()

    # 4. Check what backend the service actually uses
    print("ACTUAL BACKEND IN USE:")
    print("-" * 40)

    # Clear the singleton to force re-initialization
    import dotmac.platform.file_storage.service as service_module
    service_module._storage_service = None

    # Get the service and see what backend it uses
    service = get_storage_service()

    print(f"  Backend Type: {service.backend_type}")
    print(f"  Backend Class: {service.backend.__class__.__name__}")

    if service.backend_type == StorageBackend.MINIO:
        print("  ✓ Service IS using MinIO backend")
    elif service.backend_type == StorageBackend.LOCAL:
        print("  ⚠ Service is using LOCAL backend (fallback)")
    else:
        print(f"  ⚠ Service is using {service.backend_type} backend")
    print()

    # 5. Test actual file operations with current backend
    print("TESTING FILE OPERATIONS:")
    print("-" * 40)

    async def test_operations():
        # Test storing a file
        test_data = b"Test file for backend verification"
        file_id = await service.store_file(
            file_data=test_data,
            file_name="backend_test.txt",
            content_type="text/plain",
            path="test",
            tenant_id="test_tenant"
        )
        print(f"  ✓ File stored with ID: {file_id}")

        # Test retrieving the file
        retrieved_data, metadata = await service.retrieve_file(file_id, "test_tenant")
        if retrieved_data == test_data:
            print(f"  ✓ File retrieved successfully")
        else:
            print(f"  ✗ File retrieval failed or data mismatch")

        # Clean up
        deleted = await service.delete_file(file_id, "test_tenant")
        if deleted:
            print(f"  ✓ File deleted successfully")
        else:
            print(f"  ✗ File deletion failed")

    asyncio.run(test_operations())
    print()

    # 6. Recommendations
    print("RECOMMENDATIONS:")
    print("-" * 40)

    if service.backend_type == StorageBackend.LOCAL:
        print("  Currently using LOCAL storage (files stored at: {})".format(settings.storage.local_path))
        print()
        print("  To use MinIO:")
        print("  1. Ensure MinIO server is running:")
        print("     docker run -p 9000:9000 -p 9001:9001 \\")
        print("       -e MINIO_ROOT_USER=minioadmin \\")
        print("       -e MINIO_ROOT_PASSWORD=minioadmin123 \\")
        print("       minio/minio server /data --console-address ':9001'")
        print()
        print("  2. Set environment variables:")
        print("     export STORAGE__ENDPOINT=localhost:9000")
        print("     export STORAGE__ACCESS_KEY=minioadmin")
        print("     export STORAGE__SECRET_KEY=minioadmin123")
        print()
        print("  3. Install MinIO Python client:")
        print("     pip install minio")
    else:
        print(f"  ✓ Successfully using {service.backend_type} backend")

    print()
    print("=" * 60)


if __name__ == "__main__":
    test_minio_availability()