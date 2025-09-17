"""
File Processing Utilities

Utility functions for file type detection, validation, and name manipulation.
"""

import mimetypes
import os
import re
import unicodedata
from pathlib import Path
from typing import Optional

from .base import FileType


def get_file_type(file_path: str | Path) -> FileType:
    """
    Determine file type based on file extension and MIME type.

    Args:
        file_path: Path to the file

    Returns:
        FileType enum value representing the detected file type
    """
    path = Path(file_path)
    extension = path.suffix.lower()

    # Get MIME type
    mime_type, _ = mimetypes.guess_type(str(path))
    mime_type = mime_type or "application/octet-stream"

    # Image types
    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".svg",
        ".ico",
        ".psd",
        ".raw",
        ".cr2",
        ".nef",
        ".orf",
    }
    if extension in image_extensions or mime_type.startswith("image/"):
        return FileType.IMAGE

    # Document types
    document_extensions = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".ods",
        ".odp",
        ".rtf",
        ".pages",
        ".numbers",
        ".key",
    }
    document_mimes = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.presentation",
        "text/rtf",
    }
    if extension in document_extensions or mime_type in document_mimes:
        return FileType.DOCUMENT

    # Video types
    video_extensions = {
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".3gp",
        ".ogv",
        ".ts",
        ".mts",
        ".m2ts",
    }
    if extension in video_extensions or mime_type.startswith("video/"):
        return FileType.VIDEO

    # Audio types
    audio_extensions = {
        ".mp3",
        ".wav",
        ".flac",
        ".aac",
        ".ogg",
        ".wma",
        ".m4a",
        ".opus",
        ".ape",
        ".ac3",
        ".dts",
        ".aiff",
        ".au",
    }
    if extension in audio_extensions or mime_type.startswith("audio/"):
        return FileType.AUDIO

    # Archive types
    archive_extensions = {
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".tar.gz",
        ".tar.bz2",
        ".tar.xz",
        ".tgz",
        ".tbz2",
    }
    archive_mimes = {
        "application/zip",
        "application/x-rar-compressed",
        "application/x-7z-compressed",
        "application/x-tar",
        "application/gzip",
        "application/x-bzip2",
        "application/x-xz",
    }
    if extension in archive_extensions or mime_type in archive_mimes:
        return FileType.ARCHIVE

    # Text types
    text_extensions = {
        ".txt",
        ".md",
        ".rst",
        ".log",
        ".csv",
        ".tsv",
        ".json",
        ".xml",
        ".html",
        ".htm",
        ".css",
        ".js",
        ".py",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".php",
        ".rb",
        ".go",
        ".rs",
        ".sh",
        ".bat",
        ".ps1",
        ".yaml",
        ".yml",
        ".ini",
        ".cfg",
        ".conf",
        ".toml",
        ".env",
    }
    if extension in text_extensions or mime_type.startswith("text/"):
        return FileType.TEXT

    return FileType.UNKNOWN


def validate_file_size(
    file_path: str | Path,
    max_size_bytes: int = 100 * 1024 * 1024,  # 100MB default
    min_size_bytes: int = 0,
) -> tuple[bool, str]:
    """
    Validate file size against limits.

    Args:
        file_path: Path to the file
        max_size_bytes: Maximum allowed file size in bytes
        min_size_bytes: Minimum allowed file size in bytes

    Returns:
        Tuple of (is_valid, error_message)
        error_message is empty string if valid
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return False, "File does not exist"

        if not path.is_file():
            return False, "Path is not a file"

        file_size = path.stat().st_size

        if file_size < min_size_bytes:
            return False, f"File size {file_size} bytes is below minimum {min_size_bytes} bytes"

        if file_size > max_size_bytes:
            return False, f"File size {file_size} bytes exceeds maximum {max_size_bytes} bytes"

        return True, ""

    except Exception as e:
        return False, f"Error validating file size: {str(e)}"


def sanitize_filename(
    filename: str,
    max_length: int = 255,
    replacement_char: str = "_",
    preserve_extension: bool = True,
) -> str:
    """
    Sanitize a filename for safe filesystem storage.

    Args:
        filename: Original filename
        max_length: Maximum length for the sanitized filename
        replacement_char: Character to replace invalid characters
        preserve_extension: Whether to preserve the file extension

    Returns:
        Sanitized filename safe for filesystem storage
    """
    if not filename:
        return "unnamed_file"

    # Extract extension if preserving
    extension = ""
    name_part = filename
    if preserve_extension:
        path = Path(filename)
        extension = path.suffix
        name_part = path.stem

    # Normalize unicode characters
    name_part = unicodedata.normalize("NFKD", name_part)

    # Remove or replace invalid characters
    # Invalid characters for most filesystems
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    name_part = re.sub(invalid_chars, replacement_char, name_part)

    # Remove leading/trailing dots and spaces
    name_part = name_part.strip(". ")

    # Replace multiple consecutive replacement characters with single one
    if replacement_char:
        pattern = re.escape(replacement_char) + "+"
        name_part = re.sub(pattern, replacement_char, name_part)

    # Remove leading/trailing replacement characters
    name_part = name_part.strip(replacement_char)

    # Ensure we have something left
    if not name_part:
        name_part = "unnamed_file"

    # Handle reserved names (Windows)
    reserved_names = {
        "con",
        "prn",
        "aux",
        "nul",
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
    }
    if name_part.lower() in reserved_names:
        name_part = f"{name_part}_{replacement_char}file"

    # Combine name and extension
    sanitized = name_part + extension

    # Truncate if too long, but preserve extension
    if len(sanitized) > max_length:
        if preserve_extension and extension:
            max_name_length = max_length - len(extension)
            if max_name_length > 0:
                name_part = name_part[:max_name_length]
                sanitized = name_part + extension
            else:
                # Extension is too long, truncate everything
                sanitized = sanitized[:max_length]
        else:
            sanitized = sanitized[:max_length]

    return sanitized


def generate_thumbnail_name(
    original_filename: str,
    size: tuple[int, int],
    suffix: str = "_thumb",
    format_override: Optional[str] = None,
) -> str:
    """
    Generate a thumbnail filename based on original filename and size.

    Args:
        original_filename: Original file name
        size: Thumbnail size as (width, height) tuple
        suffix: Suffix to add before the extension
        format_override: Override file format (e.g., 'jpg', 'png')

    Returns:
        Generated thumbnail filename
    """
    path = Path(original_filename)
    name = path.stem
    extension = path.suffix.lower()

    # Use format override if provided
    if format_override:
        extension = f".{format_override.lower().lstrip('.')}"
    elif not extension:
        extension = ".jpg"  # Default to JPEG for thumbnails

    # Generate size string
    size_str = f"{size[0]}x{size[1]}"

    # Construct thumbnail name
    thumbnail_name = f"{name}{suffix}_{size_str}{extension}"

    # Sanitize the generated name
    return sanitize_filename(thumbnail_name)


def get_safe_filename(base_path: str | Path, desired_name: str, max_attempts: int = 1000) -> str:
    """
    Get a safe filename that doesn't conflict with existing files.

    Args:
        base_path: Directory where the file will be created
        desired_name: Desired filename
        max_attempts: Maximum attempts to find a unique name

    Returns:
        A filename that doesn't exist in the base_path
    """
    base_path = Path(base_path)
    desired_name = sanitize_filename(desired_name)

    # If the desired name doesn't exist, use it
    full_path = base_path / desired_name
    if not full_path.exists():
        return desired_name

    # Extract name and extension
    path = Path(desired_name)
    name = path.stem
    extension = path.suffix

    # Try with numbered suffixes
    for i in range(1, max_attempts + 1):
        candidate_name = f"{name}_{i}{extension}"
        candidate_path = base_path / candidate_name

        if not candidate_path.exists():
            return candidate_name

    # If we couldn't find a unique name, add timestamp
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_{timestamp}{extension}"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Human-readable file size string
    """
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def is_hidden_file(file_path: str | Path) -> bool:
    """
    Check if a file is hidden (starts with dot on Unix-like systems).

    Args:
        file_path: Path to the file

    Returns:
        True if the file is hidden
    """
    path = Path(file_path)
    return path.name.startswith(".")


def get_file_extension_info(extension: str) -> dict[str, str]:
    """
    Get information about a file extension.

    Args:
        extension: File extension (with or without leading dot)

    Returns:
        Dictionary with extension information
    """
    if not extension.startswith("."):
        extension = f".{extension}"

    extension = extension.lower()

    # Common extension descriptions
    descriptions = {
        # Images
        ".jpg": "JPEG Image",
        ".jpeg": "JPEG Image",
        ".png": "PNG Image",
        ".gif": "GIF Image",
        ".bmp": "Bitmap Image",
        ".tiff": "TIFF Image",
        ".webp": "WebP Image",
        ".svg": "SVG Vector Image",
        # Documents
        ".pdf": "PDF Document",
        ".doc": "Microsoft Word Document",
        ".docx": "Microsoft Word Document",
        ".xls": "Microsoft Excel Spreadsheet",
        ".xlsx": "Microsoft Excel Spreadsheet",
        ".ppt": "Microsoft PowerPoint Presentation",
        ".pptx": "Microsoft PowerPoint Presentation",
        ".txt": "Text Document",
        ".rtf": "Rich Text Format",
        # Audio
        ".mp3": "MP3 Audio",
        ".wav": "WAV Audio",
        ".flac": "FLAC Audio",
        ".aac": "AAC Audio",
        ".ogg": "OGG Audio",
        # Video
        ".mp4": "MP4 Video",
        ".avi": "AVI Video",
        ".mkv": "MKV Video",
        ".mov": "QuickTime Video",
        ".wmv": "Windows Media Video",
        # Archives
        ".zip": "ZIP Archive",
        ".rar": "RAR Archive",
        ".7z": "7-Zip Archive",
        ".tar": "TAR Archive",
        ".gz": "Gzip Archive",
        # Code
        ".py": "Python Script",
        ".js": "JavaScript File",
        ".html": "HTML Document",
        ".css": "CSS Stylesheet",
        ".json": "JSON Data",
        ".xml": "XML Document",
        ".yaml": "YAML Document",
        ".yml": "YAML Document",
    }

    mime_type, _ = mimetypes.guess_type(f"file{extension}")

    return {
        "extension": extension,
        "description": descriptions.get(extension, f"{extension.upper()} File"),
        "mime_type": mime_type or "application/octet-stream",
        "file_type": get_file_type(f"file{extension}").value,
    }


def validate_file_extension(
    filename: str,
    allowed_extensions: Optional[list[str]] = None,
    blocked_extensions: Optional[list[str]] = None,
) -> tuple[bool, str]:
    """
    Validate file extension against allowed/blocked lists.

    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (if None, all are allowed)
        blocked_extensions: List of blocked extensions

    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(filename)
    extension = path.suffix.lower()

    if not extension:
        return False, "File has no extension"

    # Check blocked extensions first
    if blocked_extensions:
        blocked_exts = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in blocked_extensions
        ]
        if extension in blocked_exts:
            return False, f"Extension {extension} is not allowed"

    # Check allowed extensions
    if allowed_extensions:
        allowed_exts = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in allowed_extensions
        ]
        if extension not in allowed_exts:
            return False, f"Extension {extension} is not in the allowed list"

    return True, ""
