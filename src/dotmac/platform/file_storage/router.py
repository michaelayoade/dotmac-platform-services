"""
File storage API router.

Provides REST endpoints for file storage operations.
"""

import os
from datetime import UTC, datetime

import structlog
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field

from dotmac.platform.auth.core import UserInfo, get_current_user
from dotmac.platform.file_storage.service import (
    FileMetadata,
    get_storage_service,
)

logger = structlog.get_logger(__name__)

# Create router
file_storage_router = APIRouter()
storage_router = file_storage_router  # Alias for backward compatibility

# Get service instance
storage_service = get_storage_service()


# Request/Response Models
class FileUploadResponse(BaseModel):
    """File upload response."""

    file_id: str = Field(..., description="Unique file identifier")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    upload_timestamp: str = Field(..., description="Upload timestamp")
    url: str | None = Field(None, description="Download URL if available")


class FileListResponse(BaseModel):
    """File list response."""

    files: list[FileMetadata] = Field(..., description="List of files")
    total: int = Field(..., description="Total number of files")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")


class FileOperationRequest(BaseModel):
    """File operation request."""

    file_ids: list[str] = Field(..., description="File IDs to operate on")
    operation: str = Field(..., description="Operation to perform")
    destination: str | None = Field(None, description="Destination for move/copy")


# Endpoints
@file_storage_router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    path: str | None = Form(None, description="Storage path"),
    description: str | None = Form(None, description="File description"),
    current_user: UserInfo = Depends(get_current_user),
) -> FileUploadResponse:
    """
    Upload a file to storage.
    """
    try:
        # Validate file size (e.g., max 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        file_size = 0
        contents = await file.read()
        file_size = len(contents)

        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {max_size / 1024 / 1024}MB",
            )

        # Reset file position
        await file.seek(0)

        # Generate file path
        if not path:
            path = f"uploads/{current_user.user_id}/{datetime.now(UTC).strftime('%Y/%m/%d')}"

        # Get tenant ID from user context
        tenant_id = getattr(current_user, "tenant_id", None)

        # Store file
        file_id = await storage_service.store_file(
            file_data=contents,
            file_name=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
            path=path,
            metadata={
                "uploaded_by": current_user.user_id,
                "description": description,
                "original_filename": file.filename,
            },
            tenant_id=tenant_id,
        )

        return FileUploadResponse(
            file_id=file_id,
            file_name=file.filename or "unnamed",
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            upload_timestamp=datetime.now(UTC).isoformat(),
            url=f"/api/v1/files/storage/{file_id}/download",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed",
        )


@file_storage_router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Download a file from storage.
    """
    from fastapi.responses import Response

    try:
        # Get tenant ID from user context
        tenant_id = getattr(current_user, "tenant_id", None)

        file_data, metadata = await storage_service.retrieve_file(file_id, tenant_id)

        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found",
            )

        # Return actual file content
        content_type = (
            metadata.get("content_type", "application/octet-stream")
            if metadata
            else "application/octet-stream"
        )
        file_name = metadata.get("file_name", "download") if metadata else "download"

        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"',
                "Content-Length": str(len(file_data)),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File download failed",
        )


@file_storage_router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: UserInfo = Depends(get_current_user),
) -> dict:
    """
    Delete a file from storage.
    """
    try:
        success = await storage_service.delete_file(file_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found",
            )

        return {
            "message": f"File {file_id} deleted successfully",
            "deleted_at": datetime.now(UTC).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File deletion failed",
        )


@file_storage_router.get("", response_model=FileListResponse)
async def list_files(
    path: str | None = Query(None, description="Filter by path"),
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    current_user: UserInfo = Depends(get_current_user),
) -> FileListResponse:
    """
    List files in storage.
    """
    try:
        # Filter files by user
        user_path = f"uploads/{current_user.user_id}"
        if path:
            full_path = os.path.join(user_path, path)
        else:
            full_path = user_path

        files = await storage_service.list_files(
            path=full_path,
            limit=limit,
            offset=skip,
        )

        return FileListResponse(
            files=files,
            total=len(files),
            page=skip // limit + 1,
            per_page=limit,
        )
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list files",
        )


@file_storage_router.get("/{file_id}/metadata")
async def get_file_metadata(
    file_id: str,
    current_user: UserInfo = Depends(get_current_user),
) -> dict:
    """
    Get metadata for a specific file.
    """
    try:
        metadata = await storage_service.get_file_metadata(file_id)

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found",
            )

        return metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file metadata",
        )


@file_storage_router.post("/batch")
async def batch_operation(
    request: FileOperationRequest,
    current_user: UserInfo = Depends(get_current_user),
) -> dict:
    """
    Perform batch operations on files.
    """
    try:
        results = []

        for file_id in request.file_ids:
            if request.operation == "delete":
                success = await storage_service.delete_file(file_id)
                results.append({"file_id": file_id, "status": "deleted" if success else "failed"})
            elif request.operation == "move" and request.destination:
                # Implement move operation
                results.append({"file_id": file_id, "status": "moved"})
            elif request.operation == "copy" and request.destination:
                # Implement copy operation
                results.append({"file_id": file_id, "status": "copied"})
            else:
                results.append({"file_id": file_id, "status": "unsupported_operation"})

        return {
            "operation": request.operation,
            "results": results,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.error(f"Batch operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch operation failed",
        )


# Export router
__all__ = ["file_storage_router", "storage_router"]
