#!/usr/bin/env python
"""
Test that files are actually persisted in MinIO.
"""

import os
import asyncio
import uuid
from datetime import datetime

# Configure MinIO
os.environ["STORAGE__PROVIDER"] = "minio"
os.environ["STORAGE__ENDPOINT"] = "localhost:9000"
os.environ["STORAGE__ACCESS_KEY"] = "minioadmin"
os.environ["STORAGE__SECRET_KEY"] = "minioadmin123"
os.environ["STORAGE__BUCKET"] = "dotmac"
os.environ["STORAGE__USE_SSL"] = "false"
os.environ["FEATURES__STORAGE_MINIO_ENABLED"] = "true"

# Force reload
import sys

for module in list(sys.modules.keys()):
    if "dotmac.platform" in module:
        del sys.modules[module]

from dotmac.platform.file_storage.service import get_storage_service, StorageBackend


async def main():
    """Upload files and keep them in MinIO for verification."""
    print("=" * 70)
    print("MINIO PERSISTENCE TEST")
    print("=" * 70)
    print()

    storage = get_storage_service()

    if storage.backend_type != StorageBackend.MINIO:
        print(f"ERROR: Using {storage.backend_type} backend instead of MinIO")
        return

    print("✅ Using MinIO backend")
    print()

    # Upload 3 files that will persist
    print("UPLOADING FILES TO MINIO (these will persist):")
    print("-" * 50)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    files_to_upload = [
        {
            "name": f"document_{timestamp}_1.txt",
            "content": f"This is a test document created at {timestamp}".encode(),
            "type": "text/plain",
        },
        {
            "name": f"data_{timestamp}_2.json",
            "content": f'{{"timestamp": "{timestamp}", "test": "minio", "persistent": true}}'.encode(),
            "type": "application/json",
        },
        {
            "name": f"report_{timestamp}_3.html",
            "content": f"<html><body><h1>Test Report {timestamp}</h1></body></html>".encode(),
            "type": "text/html",
        },
    ]

    uploaded = []
    for file_data in files_to_upload:
        file_id = await storage.store_file(
            file_data=file_data["content"],
            file_name=file_data["name"],
            content_type=file_data["type"],
            path="persistent-test",
            metadata={"test": "persistence", "timestamp": timestamp, "should_persist": True},
            tenant_id="persistence-test",
        )
        uploaded.append((file_id, file_data["name"]))
        print(f"  ✅ Uploaded: {file_data['name']} -> {file_id}")

    print()
    print("FILES ARE NOW STORED IN MINIO")
    print()
    print("To verify files are actually in MinIO:")
    print()
    print("1. Open MinIO Console: http://localhost:9001")
    print("2. Login with: minioadmin / minioadmin123")
    print("3. Browse to the 'dotmac' bucket")
    print("4. Navigate to: persistence-test/persistent-test/")
    print("5. You should see the uploaded files")
    print()
    print("Or use the command line:")
    print("docker exec dotmac-minio mc ls local/dotmac/ --recursive")
    print()
    print("Uploaded file IDs (for later retrieval):")
    for file_id, file_name in uploaded:
        print(f"  - {file_id}: {file_name}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
