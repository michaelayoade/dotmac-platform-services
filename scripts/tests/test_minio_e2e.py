#!/usr/bin/env python
"""
Complete end-to-end test of file storage with MinIO.
"""

import os
import asyncio
import tempfile
from pathlib import Path

# Set MinIO configuration
os.environ['STORAGE__PROVIDER'] = 'minio'
os.environ['STORAGE__ENDPOINT'] = 'localhost:9000'
os.environ['STORAGE__ACCESS_KEY'] = 'minioadmin'
os.environ['STORAGE__SECRET_KEY'] = 'minioadmin123'
os.environ['STORAGE__BUCKET'] = 'dotmac'
os.environ['STORAGE__USE_SSL'] = 'false'
os.environ['FEATURES__STORAGE_MINIO_ENABLED'] = 'true'

# Force reload of settings
import sys
if 'dotmac.platform.settings' in sys.modules:
    del sys.modules['dotmac.platform.settings']
if 'dotmac.platform.file_storage.service' in sys.modules:
    del sys.modules['dotmac.platform.file_storage.service']

from dotmac.platform.settings import settings
from dotmac.platform.file_storage.service import get_storage_service, StorageBackend


async def main():
    """Run complete end-to-end test."""
    print("=" * 70)
    print("COMPLETE END-TO-END TEST WITH MINIO")
    print("=" * 70)
    print()

    # 1. Verify configuration
    print("1. VERIFYING CONFIGURATION:")
    print("-" * 50)
    print(f"  Provider:     {settings.storage.provider}")
    print(f"  Endpoint:     {settings.storage.endpoint}")
    print(f"  Bucket:       {settings.storage.bucket}")
    print()

    # 2. Initialize storage service
    print("2. INITIALIZING STORAGE SERVICE:")
    print("-" * 50)
    storage = get_storage_service()
    print(f"  Backend Type: {storage.backend_type}")
    print(f"  Backend Class: {storage.backend.__class__.__name__}")

    if storage.backend_type == StorageBackend.MINIO:
        print("  ✅ Successfully using MinIO backend!")
    else:
        print(f"  ⚠️ Using {storage.backend_type} backend instead of MinIO")
        return
    print()

    # 3. Create test files
    print("3. CREATING TEST FILES:")
    print("-" * 50)

    test_files = [
        {
            "name": "report.pdf",
            "content": b"Annual Report 2024 - Complete financial data and analysis",
            "type": "application/pdf",
            "size": 58
        },
        {
            "name": "dataset.csv",
            "content": b"id,product,price,quantity\n1,Widget A,19.99,100\n2,Widget B,29.99,75\n3,Widget C,39.99,50",
            "type": "text/csv",
            "size": 87
        },
        {
            "name": "logo.png",
            "content": b"\x89PNG\r\n\x1a\n" + b"Company logo image data here",
            "type": "image/png",
            "size": 36
        }
    ]

    uploaded_files = []

    for file_data in test_files:
        try:
            file_id = await storage.store_file(
                file_data=file_data["content"],
                file_name=file_data["name"],
                content_type=file_data["type"],
                path="production/documents",
                metadata={
                    "environment": "production",
                    "test": "minio-e2e",
                    "uploaded_from": "test_script"
                },
                tenant_id="tenant-001"
            )
            uploaded_files.append({
                "id": file_id,
                "name": file_data["name"],
                "original_content": file_data["content"]
            })
            print(f"  ✅ Uploaded: {file_data['name']:15} -> {file_id}")
        except Exception as e:
            print(f"  ❌ Failed to upload {file_data['name']}: {e}")

    print()

    if not uploaded_files:
        print("  ⚠️ No files uploaded successfully")
        return

    # 4. List all files
    print("4. LISTING ALL FILES:")
    print("-" * 50)

    try:
        all_files = await storage.list_files(tenant_id="tenant-001")
        print(f"  Found {len(all_files)} file(s) in MinIO:")
        for f in all_files:
            print(f"    • {f.file_name:15} - {f.file_size:6} bytes - {f.file_id}")
    except Exception as e:
        print(f"  ❌ Failed to list files: {e}")

    print()

    # 5. Retrieve and verify each file
    print("5. RETRIEVING AND VERIFYING FILES:")
    print("-" * 50)

    for file_info in uploaded_files:
        try:
            retrieved_data, metadata = await storage.retrieve_file(
                file_info["id"],
                "tenant-001"
            )

            if retrieved_data:
                matches = retrieved_data == file_info["original_content"]
                status = "✅ Content verified" if matches else "❌ Content mismatch"
                print(f"  • {file_info['name']:15} - {status}")

                if metadata:
                    print(f"    Metadata: {metadata}")
            else:
                print(f"  ❌ Failed to retrieve {file_info['name']}")
        except Exception as e:
            print(f"  ❌ Error retrieving {file_info['name']}: {e}")

    print()

    # 6. Search for files
    print("6. SEARCHING FILES:")
    print("-" * 50)

    try:
        # Search by path
        path_results = await storage.list_files(
            path="production/documents",
            tenant_id="tenant-001"
        )
        print(f"  Files in 'production/documents': {len(path_results)}")

        # Search by content type
        csv_files = [f for f in all_files if f.content_type == "text/csv"]
        print(f"  CSV files: {len(csv_files)}")

        # Search by metadata (if supported)
        prod_files = [f for f in all_files
                     if f.metadata and f.metadata.get("environment") == "production"]
        print(f"  Production files: {len(prod_files)}")
    except Exception as e:
        print(f"  ⚠️ Search operations partially failed: {e}")

    print()

    # 7. Update metadata
    print("7. UPDATING METADATA:")
    print("-" * 50)

    if uploaded_files:
        first_file = uploaded_files[0]
        try:
            success = await storage.update_file_metadata(
                file_id=first_file["id"],
                metadata_updates={
                    "status": "approved",
                    "reviewed_by": "admin",
                    "review_date": "2025-09-23"
                },
                tenant_id="tenant-001"
            )
            if success:
                print(f"  ✅ Updated metadata for {first_file['name']}")

                # Verify the update
                _, updated_metadata = await storage.retrieve_file(
                    first_file["id"],
                    "tenant-001"
                )
                print(f"    New metadata: {updated_metadata}")
            else:
                print(f"  ❌ Failed to update metadata")
        except Exception as e:
            print(f"  ❌ Error updating metadata: {e}")

    print()

    # 8. Clean up
    print("8. CLEANING UP:")
    print("-" * 50)

    for file_info in uploaded_files:
        try:
            deleted = await storage.delete_file(file_info["id"], "tenant-001")
            if deleted:
                print(f"  ✅ Deleted: {file_info['name']}")
            else:
                print(f"  ⚠️ Could not delete: {file_info['name']}")
        except Exception as e:
            print(f"  ❌ Error deleting {file_info['name']}: {e}")

    print()

    # 9. Verify cleanup
    print("9. VERIFYING CLEANUP:")
    print("-" * 50)

    try:
        remaining_files = await storage.list_files(tenant_id="tenant-001")
        if len(remaining_files) == 0:
            print("  ✅ All test files successfully deleted")
        else:
            print(f"  ⚠️ {len(remaining_files)} file(s) still remain")
    except Exception as e:
        print(f"  ❌ Error checking remaining files: {e}")

    print()
    print("=" * 70)
    print("✅ END-TO-END TEST COMPLETE")
    print("=" * 70)
    print()
    print("MinIO Console: http://localhost:9001")
    print("Login: minioadmin / minioadmin123")
    print("Check the 'dotmac' bucket to see file operations")
    print()


if __name__ == "__main__":
    asyncio.run(main())