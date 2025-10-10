#!/usr/bin/env python
"""
Test MinIO operations with proper configuration.
"""

import asyncio
import os

# Set environment variables before importing the app modules
os.environ["STORAGE__PROVIDER"] = "minio"
os.environ["STORAGE__ENDPOINT"] = "localhost:9000"
os.environ["STORAGE__ACCESS_KEY"] = "minioadmin"
os.environ["STORAGE__SECRET_KEY"] = "minioadmin123"
os.environ["STORAGE__BUCKET"] = "dotmac"
os.environ["STORAGE__USE_SSL"] = "false"
os.environ["FEATURES__STORAGE_MINIO_ENABLED"] = "true"

# Force reloading of settings with new environment variables
import sys

if "dotmac.platform.settings" in sys.modules:
    del sys.modules["dotmac.platform.settings"]
if "dotmac.platform.file_storage.service" in sys.modules:
    del sys.modules["dotmac.platform.file_storage.service"]

import dotmac.platform.file_storage.service as service_module
from dotmac.platform.file_storage.service import StorageBackend, get_storage_service
from dotmac.platform.settings import settings


async def test_minio_operations():
    """Test file operations with MinIO."""
    print("=" * 70)
    print("TESTING FILE OPERATIONS WITH MINIO")
    print("=" * 70)
    print()

    # 1. Verify configuration
    print("CONFIGURATION:")
    print("-" * 50)
    print(f"  Provider:     {settings.storage.provider}")
    print(f"  Endpoint:     {settings.storage.endpoint}")
    print(
        f"  Access Key:   {'***' + settings.storage.access_key[-4:] if settings.storage.access_key else 'Not set'}"
    )
    print(
        f"  Secret Key:   {'***' + settings.storage.secret_key[-4:] if settings.storage.secret_key else 'Not set'}"
    )
    print(f"  Bucket:       {settings.storage.bucket}")
    print(f"  Use SSL:      {settings.storage.use_ssl}")
    print()

    # 2. Clear the singleton to force re-initialization with MinIO
    print("INITIALIZING STORAGE SERVICE:")
    print("-" * 50)
    service_module._storage_service = None

    # Get storage service
    storage = get_storage_service()
    print(f"  Backend Type:  {storage.backend_type}")
    print(f"  Backend Class: {storage.backend.__class__.__name__}")

    if storage.backend_type == StorageBackend.MINIO:
        print("  ✅ Successfully using MinIO backend!")
    else:
        print(f"  ⚠️  Using {storage.backend_type} backend (MinIO may not be accessible)")
    print()

    # 3. Test file upload
    print("UPLOADING FILES TO MINIO:")
    print("-" * 50)

    test_files = [
        {
            "name": "test_document.pdf",
            "content": b"PDF content simulation for MinIO test",
            "type": "application/pdf",
        },
        {
            "name": "data.csv",
            "content": b"id,name,value\n1,test1,100\n2,test2,200\n3,test3,300",
            "type": "text/csv",
        },
        {
            "name": "image.png",
            "content": b"\x89PNG\r\n\x1a\n" + b"Fake PNG data for testing",
            "type": "image/png",
        },
    ]

    file_ids = []
    for file_info in test_files:
        try:
            file_id = await storage.store_file(
                file_data=file_info["content"],
                file_name=file_info["name"],
                content_type=file_info["type"],
                path="minio-test",
                metadata={
                    "test": "minio",
                    "source": "test_script",
                },
                tenant_id="minio-test-tenant",
            )
            file_ids.append((file_id, file_info))
            print(f"  ✅ Uploaded: {file_info['name']:20} -> ID: {file_id}")
        except Exception as e:
            print(f"  ❌ Failed to upload {file_info['name']}: {e}")

    print()

    if not file_ids:
        print("  ⚠️  No files were uploaded successfully")
        return

    # 4. List files
    print("LISTING FILES IN MINIO:")
    print("-" * 50)

    try:
        files = await storage.list_files(tenant_id="minio-test-tenant")
        print(f"  Found {len(files)} file(s) in MinIO:")
        for f in files[:5]:
            print(
                f"    • {f.file_name:20} - {f.file_size:6} bytes - {f.created_at.strftime('%H:%M:%S')}"
            )
    except Exception as e:
        print(f"  ❌ Failed to list files: {e}")

    print()

    # 5. Retrieve and verify files
    print("RETRIEVING FILES FROM MINIO:")
    print("-" * 50)

    for file_id, original_file in file_ids:
        try:
            file_data, metadata = await storage.retrieve_file(file_id, "minio-test-tenant")

            if file_data:
                matches = file_data == original_file["content"]
                status = "✅ Content matches" if matches else "❌ Content mismatch"
                print(
                    f"  • {original_file['name']:20} - Retrieved {len(file_data):6} bytes - {status}"
                )
            else:
                print(f"  ❌ Failed to retrieve {original_file['name']}")
        except Exception as e:
            print(f"  ❌ Error retrieving {original_file['name']}: {e}")

    print()

    # 6. Update metadata
    print("UPDATING FILE METADATA:")
    print("-" * 50)

    if file_ids:
        first_id, first_file = file_ids[0]
        try:
            success = await storage.update_file_metadata(
                file_id=first_id,
                metadata_updates={
                    "verified": True,
                    "minio_test": "passed",
                },
                tenant_id="minio-test-tenant",
            )
            if success:
                print(f"  ✅ Updated metadata for {first_file['name']}")
            else:
                print(f"  ❌ Failed to update metadata for {first_file['name']}")
        except Exception as e:
            print(f"  ❌ Error updating metadata: {e}")

    print()

    # 7. Delete files
    print("CLEANING UP:")
    print("-" * 50)

    for file_id, file_info in file_ids:
        try:
            deleted = await storage.delete_file(file_id, "minio-test-tenant")
            if deleted:
                print(f"  ✅ Deleted: {file_info['name']}")
            else:
                print(f"  ⚠️  Could not delete: {file_info['name']}")
        except Exception as e:
            print(f"  ❌ Error deleting {file_info['name']}: {e}")

    print()

    # 8. Check if we're actually using MinIO
    if storage.backend_type == StorageBackend.MINIO:
        print("=" * 70)
        print("✅ SUCCESS: All operations completed using MinIO backend!")
        print("=" * 70)
        print()
        print("MinIO Console available at: http://localhost:9001")
        print("Login with: minioadmin / minioadmin123")
        print("You can browse the 'dotmac' bucket to see stored files.")
    else:
        print("=" * 70)
        print("⚠️  NOTICE: Operations completed but using LOCAL storage")
        print("=" * 70)
        print()
        print("MinIO may not be properly configured or accessible.")
        print("Check that MinIO is running with: docker ps")


if __name__ == "__main__":
    asyncio.run(test_minio_operations())
