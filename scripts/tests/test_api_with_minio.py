#!/usr/bin/env python
"""
Test the platform API with MinIO backend.
"""

import os
import asyncio
import httpx
import json
from datetime import datetime

# Set environment for MinIO
os.environ['STORAGE__PROVIDER'] = 'minio'
os.environ['STORAGE__ENDPOINT'] = 'localhost:9000'
os.environ['STORAGE__ACCESS_KEY'] = 'minioadmin'
os.environ['STORAGE__SECRET_KEY'] = 'minioadmin123'
os.environ['STORAGE__BUCKET'] = 'dotmac'
os.environ['STORAGE__USE_SSL'] = 'false'
os.environ['FEATURES__STORAGE_MINIO_ENABLED'] = 'true'

BASE_URL = "http://localhost:8001"

# Test user token (you may need to adjust this)
TEST_TOKEN = "Bearer test-token-123"


async def test_api_with_minio():
    """Test file storage API endpoints with MinIO backend."""
    print("=" * 70)
    print("TESTING PLATFORM API WITH MINIO BACKEND")
    print("=" * 70)
    print()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Upload a file
        print("1. UPLOADING FILE VIA API:")
        print("-" * 50)

        files = {
            'file': ('test_document.pdf', b'PDF content for MinIO test via API', 'application/pdf')
        }

        response = await client.post(
            "/api/v1/files/storage/upload",
            files=files,
            headers={"Authorization": TEST_TOKEN}
        )

        if response.status_code == 200:
            upload_response = response.json()
            file_id = upload_response.get('file_id')
            print(f"  ✅ File uploaded successfully!")
            print(f"     File ID: {file_id}")
            print(f"     Response: {json.dumps(upload_response, indent=2)}")
        else:
            print(f"  ❌ Upload failed: {response.status_code}")
            print(f"     Error: {response.text}")
            return

        print()

        # 2. List files
        print("2. LISTING FILES VIA API:")
        print("-" * 50)

        response = await client.get(
            "/api/v1/files/storage",
            headers={"Authorization": TEST_TOKEN}
        )

        if response.status_code == 200:
            files = response.json()
            print(f"  ✅ Found {len(files)} file(s):")
            for f in files[:5]:
                print(f"     • {f.get('file_name', 'N/A'):20} - {f.get('file_size', 0):6} bytes")
        else:
            print(f"  ❌ List failed: {response.status_code}")
            print(f"     Error: {response.text}")

        print()

        # 3. Get file metadata
        print("3. GETTING FILE METADATA VIA API:")
        print("-" * 50)

        response = await client.get(
            f"/api/v1/files/storage/{file_id}",
            headers={"Authorization": TEST_TOKEN}
        )

        if response.status_code == 200:
            metadata = response.json()
            print(f"  ✅ File metadata retrieved:")
            print(f"     Name: {metadata.get('file_name')}")
            print(f"     Size: {metadata.get('file_size')} bytes")
            print(f"     Type: {metadata.get('content_type')}")
            print(f"     Path: {metadata.get('file_path')}")
            print(f"     Checksum: {metadata.get('checksum', 'N/A')[:16]}...")
        else:
            print(f"  ❌ Get metadata failed: {response.status_code}")
            print(f"     Error: {response.text}")

        print()

        # 4. Download file
        print("4. DOWNLOADING FILE VIA API:")
        print("-" * 50)

        response = await client.get(
            f"/api/v1/files/storage/{file_id}/download",
            headers={"Authorization": TEST_TOKEN}
        )

        if response.status_code == 200:
            content = response.content
            expected = b'PDF content for MinIO test via API'
            if content == expected:
                print(f"  ✅ File downloaded successfully!")
                print(f"     Content matches: {len(content)} bytes")
            else:
                print(f"  ⚠️  File downloaded but content differs")
                print(f"     Expected: {expected[:50]}")
                print(f"     Got: {content[:50]}")
        else:
            print(f"  ❌ Download failed: {response.status_code}")
            print(f"     Error: {response.text}")

        print()

        # 5. Delete file
        print("5. DELETING FILE VIA API:")
        print("-" * 50)

        response = await client.delete(
            f"/api/v1/files/storage/{file_id}",
            headers={"Authorization": TEST_TOKEN}
        )

        if response.status_code == 200:
            print(f"  ✅ File deleted successfully!")
        else:
            print(f"  ❌ Delete failed: {response.status_code}")
            print(f"     Error: {response.text}")

        print()

    print("=" * 70)
    print("✅ API TESTING COMPLETE")
    print("=" * 70)
    print()
    print("MinIO Console: http://localhost:9001")
    print("Credentials: minioadmin / minioadmin123")
    print()


if __name__ == "__main__":
    print("Note: Make sure the platform API is running with MinIO configuration")
    print("Run: STORAGE__PROVIDER=minio uvicorn dotmac.platform.main:app --reload --port 8001")
    print()
    asyncio.run(test_api_with_minio())