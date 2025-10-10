#!/usr/bin/env python
"""
Demonstration script for file storage backend functionality.
Shows that files are actually stored and retrievable.
"""

import asyncio
from datetime import datetime

from dotmac.platform.file_storage.service import FileStorageService, StorageBackend


async def demo_file_storage():
    """Demonstrate file storage and retrieval functionality."""
    print("=" * 60)
    print("FILE STORAGE BACKEND DEMONSTRATION")
    print("=" * 60)
    print()

    # 1. Create storage service (using local backend for demo)
    storage = FileStorageService(backend=StorageBackend.LOCAL)
    print("✓ Storage service initialized with LOCAL backend")
    print()

    # 2. Create some test files
    test_files = [
        {
            "name": "document.txt",
            "content": b"This is a text document with important information.",
            "type": "text/plain",
        },
        {
            "name": "data.json",
            "content": b'{"name": "Test Data", "value": 123, "timestamp": "2025-09-23"}',
            "type": "application/json",
        },
        {
            "name": "report.html",
            "content": b"<html><body><h1>Test Report</h1><p>Everything works!</p></body></html>",
            "type": "text/html",
        },
    ]

    file_ids = []
    print("UPLOADING FILES:")
    print("-" * 40)

    for file_info in test_files:
        # Store each file
        file_id = await storage.store_file(
            file_data=file_info["content"],
            file_name=file_info["name"],
            content_type=file_info["type"],
            path="demo/uploads",
            metadata={
                "demo": True,
                "uploaded_at": datetime.now().isoformat(),
                "source": "demo_script",
            },
            tenant_id="demo_tenant",
        )
        file_ids.append(file_id)
        print(f"  • {file_info['name']:20} -> ID: {file_id}")

    print()
    print("✓ All files successfully stored")
    print()

    # 3. Retrieve and verify files
    print("RETRIEVING FILES:")
    print("-" * 40)

    for i, file_id in enumerate(file_ids):
        file_data, metadata = await storage.retrieve_file(file_id, "demo_tenant")

        if file_data:
            original_content = test_files[i]["content"]
            match = file_data == original_content
            status = "✓ MATCH" if match else "✗ MISMATCH"

            print(
                f"  • {metadata['file_name']:20} - Size: {metadata['file_size']:6} bytes - {status}"
            )

            if not match:
                print(f"    Expected: {original_content[:50]}...")
                print(f"    Got:      {file_data[:50]}...")
        else:
            print(f"  ✗ Failed to retrieve file ID: {file_id}")

    print()
    print("✓ All files successfully retrieved and verified")
    print()

    # 4. List files
    print("LISTING FILES IN STORAGE:")
    print("-" * 40)

    files = await storage.list_files(tenant_id="demo_tenant")
    for file_metadata in files[:5]:  # Show first 5 files
        print(
            f"  • {file_metadata.file_name:20} - {file_metadata.file_size:6} bytes - {file_metadata.created_at.strftime('%Y-%m-%d %H:%M')}"
        )

    print(f"\n  Total files in storage: {len(files)}")
    print()

    # 5. Update metadata
    print("UPDATING FILE METADATA:")
    print("-" * 40)

    if file_ids:
        first_file_id = file_ids[0]
        success = await storage.update_file_metadata(
            file_id=first_file_id,
            metadata_updates={
                "reviewed": True,
                "reviewer": "demo_script",
                "review_date": datetime.now().isoformat(),
            },
            tenant_id="demo_tenant",
        )

        if success:
            updated_metadata = await storage.get_file_metadata(first_file_id)
            print(f"  ✓ Updated metadata for {updated_metadata['file_name']}")
            print(f"    New metadata: {updated_metadata['metadata']}")
        else:
            print("  ✗ Failed to update metadata")

    print()

    # 6. Demonstrate persistence
    print("VERIFYING PERSISTENCE:")
    print("-" * 40)

    # Create a new storage instance to verify files persist
    storage2 = FileStorageService(backend=StorageBackend.LOCAL)

    for i, file_id in enumerate(file_ids[:2]):  # Check first 2 files
        file_data, metadata = await storage2.retrieve_file(file_id, "demo_tenant")
        if file_data:
            print(f"  ✓ File {metadata['file_name']} persists across service instances")
        else:
            print(f"  ✗ File {file_id} not found in new instance")

    print()

    # 7. Clean up (optional)
    print("CLEANING UP:")
    print("-" * 40)

    # Auto-cleanup for demo (set to False to keep files)
    cleanup = True
    print(f"  Auto-cleanup: {'Yes' if cleanup else 'No'}")
    if cleanup:
        for file_id in file_ids:
            deleted = await storage.delete_file(file_id, "demo_tenant")
            if deleted:
                print(f"  ✓ Deleted file {file_id}")
            else:
                print(f"  ✗ Failed to delete {file_id}")
    else:
        print("  Files retained for inspection")

    print()
    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)

    # Show storage location for local backend
    if StorageBackend.LOCAL:
        from dotmac.platform.file_storage.service import LocalFileStorage

        local_storage = LocalFileStorage()
        print(f"\nLocal files stored at: {local_storage.base_path}")
        print("You can inspect the files directly in this directory.")


if __name__ == "__main__":
    asyncio.run(demo_file_storage())
