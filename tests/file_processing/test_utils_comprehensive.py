"""
Comprehensive tests for file processing utilities.
Targets uncovered utility functions for file type detection, validation, and manipulation.
"""

import tempfile
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from dotmac.platform.file_processing.base import FileType
from dotmac.platform.file_processing.utils import (
    get_file_type,
    validate_file_size,
    sanitize_filename,
    generate_thumbnail_name,
    get_safe_filename,
    format_file_size,
    is_hidden_file,
    get_file_extension_info,
    validate_file_extension,
)


class TestGetFileType:
    """Test file type detection functionality."""

    def test_get_file_type_image_extensions(self):
        """Test image file type detection by extension."""
        image_files = [
            "photo.jpg",
            "image.jpeg",
            "graphic.png",
            "animated.gif",
            "bitmap.bmp",
            "picture.tiff",
            "web.webp",
            "vector.svg",
            "icon.ico",
            "raw.cr2",
            "nikon.nef",
        ]

        for filename in image_files:
            file_type = get_file_type(filename)
            assert file_type == FileType.IMAGE, f"Failed for {filename}"

    def test_get_file_type_document_extensions(self):
        """Test document file type detection by extension."""
        document_files = [
            "document.pdf",
            "text.doc",
            "modern.docx",
            "spreadsheet.xls",
            "workbook.xlsx",
            "presentation.ppt",
            "slides.pptx",
            "writer.odt",
            "calc.ods",
            "impress.odp",
            "rich.rtf",
            "apple.pages",
            "numbers.numbers",
            "keynote.key",
        ]

        for filename in document_files:
            file_type = get_file_type(filename)
            assert file_type == FileType.DOCUMENT, f"Failed for {filename}"

    def test_get_file_type_video_extensions(self):
        """Test video file type detection by extension."""
        video_files = [
            "movie.mp4",
            "clip.avi",
            "video.mkv",
            "quicktime.mov",
            "windows.wmv",
            "flash.flv",
            "web.webm",
            "mobile.3gp",
            "stream.ts",
            "broadcast.mts",
        ]

        for filename in video_files:
            file_type = get_file_type(filename)
            assert file_type == FileType.VIDEO, f"Failed for {filename}"

    def test_get_file_type_audio_extensions(self):
        """Test audio file type detection by extension."""
        audio_files = [
            "song.mp3",
            "audio.wav",
            "lossless.flac",
            "compressed.aac",
            "open.ogg",
            "windows.wma",
            "apple.m4a",
            "modern.opus",
            "uncompressed.aiff",
        ]

        for filename in audio_files:
            file_type = get_file_type(filename)
            assert file_type == FileType.AUDIO, f"Failed for {filename}"

    def test_get_file_type_archive_extensions(self):
        """Test archive file type detection by extension."""
        archive_files = [
            "package.zip",
            "compressed.rar",
            "archive.7z",
            "bundle.tar",
            "gzipped.gz",
            "compressed.bz2",
            "modern.xz",
            "tarball.tar.gz",
            "backup.tgz",
        ]

        for filename in archive_files:
            file_type = get_file_type(filename)
            assert file_type == FileType.ARCHIVE, f"Failed for {filename}"

    def test_get_file_type_text_extensions(self):
        """Test text file type detection by extension."""
        text_files = [
            "readme.txt",
            "documentation.md",
            "data.csv",
            "config.json",
            "markup.xml",
            "webpage.html",
            "style.css",
            "script.js",
            "program.py",
            "source.java",
            "header.h",
            "settings.yaml",
            "environment.env",
        ]

        for filename in text_files:
            file_type = get_file_type(filename)
            assert file_type == FileType.TEXT, f"Failed for {filename}"

    def test_get_file_type_unknown_extension(self):
        """Test unknown file type detection."""
        unknown_files = [
            "file.unknown",
            "mystery.xyz",
            "strange.weird",
            "no_extension",
        ]

        for filename in unknown_files:
            file_type = get_file_type(filename)
            assert file_type == FileType.UNKNOWN, f"Failed for {filename}"

    def test_get_file_type_case_insensitive(self):
        """Test file type detection is case insensitive."""
        test_cases = [
            ("FILE.JPG", FileType.IMAGE),
            ("DOCUMENT.PDF", FileType.DOCUMENT),
            ("Video.MP4", FileType.VIDEO),
            ("Audio.MP3", FileType.AUDIO),
            ("Archive.ZIP", FileType.ARCHIVE),
            ("Text.TXT", FileType.TEXT),
        ]

        for filename, expected_type in test_cases:
            file_type = get_file_type(filename)
            assert file_type == expected_type, f"Failed for {filename}"

    def test_get_file_type_with_path_object(self):
        """Test file type detection with Path objects."""
        path = Path("documents/report.pdf")
        file_type = get_file_type(path)
        assert file_type == FileType.DOCUMENT

    @patch('mimetypes.guess_type')
    def test_get_file_type_mime_type_fallback(self, mock_guess_type):
        """Test file type detection using MIME type when extension is unknown."""
        # Mock MIME type detection
        mock_guess_type.return_value = ("image/jpeg", None)

        file_type = get_file_type("file.unknown")
        assert file_type == FileType.IMAGE

        # Test other MIME types
        test_cases = [
            ("video/mp4", FileType.VIDEO),
            ("audio/mpeg", FileType.AUDIO),
            ("text/plain", FileType.TEXT),
            ("application/zip", FileType.ARCHIVE),
        ]

        for mime_type, expected_type in test_cases:
            mock_guess_type.return_value = (mime_type, None)
            file_type = get_file_type("file.unknown")
            assert file_type == expected_type


class TestValidateFileSize:
    """Test file size validation functionality."""

    def test_validate_file_size_valid_file(self):
        """Test file size validation with valid file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write some content
            content = b"Hello, World!" * 100  # ~1.3KB
            temp_file.write(content)
            temp_file.flush()

            try:
                is_valid, error_msg = validate_file_size(
                    temp_file.name,
                    max_size_bytes=10000,  # 10KB
                    min_size_bytes=100,    # 100B
                )

                assert is_valid is True
                assert error_msg == ""
            finally:
                os.unlink(temp_file.name)

    def test_validate_file_size_file_too_large(self):
        """Test file size validation with file too large."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write large content
            content = b"x" * 2000  # 2KB
            temp_file.write(content)
            temp_file.flush()

            try:
                is_valid, error_msg = validate_file_size(
                    temp_file.name,
                    max_size_bytes=1000,  # 1KB max
                    min_size_bytes=0,
                )

                assert is_valid is False
                assert "exceeds maximum" in error_msg
                assert "2000" in error_msg  # File size
                assert "1000" in error_msg  # Max size
            finally:
                os.unlink(temp_file.name)

    def test_validate_file_size_file_too_small(self):
        """Test file size validation with file too small."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write minimal content
            content = b"x" * 50  # 50B
            temp_file.write(content)
            temp_file.flush()

            try:
                is_valid, error_msg = validate_file_size(
                    temp_file.name,
                    max_size_bytes=10000,
                    min_size_bytes=100,  # 100B min
                )

                assert is_valid is False
                assert "below minimum" in error_msg
                assert "50" in error_msg   # File size
                assert "100" in error_msg  # Min size
            finally:
                os.unlink(temp_file.name)

    def test_validate_file_size_file_does_not_exist(self):
        """Test file size validation with non-existent file."""
        is_valid, error_msg = validate_file_size("/path/to/nonexistent/file.txt")

        assert is_valid is False
        assert "File does not exist" in error_msg

    def test_validate_file_size_path_is_directory(self):
        """Test file size validation with directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            is_valid, error_msg = validate_file_size(temp_dir)

            assert is_valid is False
            assert "Path is not a file" in error_msg

    def test_validate_file_size_default_limits(self):
        """Test file size validation with default limits."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write normal content
            content = b"Hello, World!" * 1000  # ~13KB
            temp_file.write(content)
            temp_file.flush()

            try:
                is_valid, error_msg = validate_file_size(temp_file.name)

                assert is_valid is True
                assert error_msg == ""
            finally:
                os.unlink(temp_file.name)

    def test_validate_file_size_zero_size_file(self):
        """Test file size validation with empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Don't write any content - file will be empty
            temp_file.flush()

            try:
                is_valid, error_msg = validate_file_size(
                    temp_file.name,
                    max_size_bytes=1000,
                    min_size_bytes=0,  # Allow empty files
                )

                assert is_valid is True
                assert error_msg == ""
            finally:
                os.unlink(temp_file.name)

    def test_validate_file_size_with_path_object(self):
        """Test file size validation with Path object."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"test content"
            temp_file.write(content)
            temp_file.flush()

            try:
                path_obj = Path(temp_file.name)
                is_valid, error_msg = validate_file_size(path_obj)

                assert is_valid is True
                assert error_msg == ""
            finally:
                os.unlink(temp_file.name)


class TestSanitizeFilename:
    """Test filename sanitization functionality."""

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        sanitized = sanitize_filename("normal_file.txt")
        assert sanitized == "normal_file.txt"

    def test_sanitize_filename_invalid_characters(self):
        """Test sanitization of invalid characters."""
        test_cases = [
            ("file<name>.txt", "file_name_.txt"),
            ("file>name.txt", "file_name.txt"),
            ("file:name.txt", "file_name.txt"),
            ("file\"name.txt", "file_name.txt"),
            ("file/name.txt", "file_name.txt"),
            ("file\\name.txt", "file_name.txt"),
            ("file|name.txt", "file_name.txt"),
            ("file?name.txt", "file_name.txt"),
            ("file*name.txt", "file_name.txt"),
        ]

        for original, expected in test_cases:
            sanitized = sanitize_filename(original)
            assert sanitized == expected, f"Failed for {original} -> {sanitized} (expected {expected})"

    def test_sanitize_filename_unicode_normalization(self):
        """Test Unicode normalization in filename sanitization."""
        # Test Unicode normalization
        unicode_name = "café_résumé.txt"
        sanitized = sanitize_filename(unicode_name)
        assert len(sanitized) > 0
        assert ".txt" in sanitized

    def test_sanitize_filename_leading_trailing_dots_spaces(self):
        """Test removal of leading/trailing dots and spaces."""
        test_cases = [
            (" file.txt ", "file.txt"),
            ("...file.txt...", "file.txt"),
            (" . file.txt . ", "file.txt"),
            ("  file  .txt  ", "file.txt"),
        ]

        for original, expected in test_cases:
            sanitized = sanitize_filename(original)
            assert sanitized == expected, f"Failed for '{original}' -> '{sanitized}' (expected '{expected}')"

    def test_sanitize_filename_multiple_replacement_chars(self):
        """Test consolidation of multiple replacement characters."""
        sanitized = sanitize_filename("file<<<>>>name.txt", replacement_char="_")
        assert "_" in sanitized
        assert "___" not in sanitized  # Should consolidate multiple underscores

    def test_sanitize_filename_empty_input(self):
        """Test sanitization of empty filename."""
        sanitized = sanitize_filename("")
        assert sanitized == "unnamed_file"

    def test_sanitize_filename_none_input(self):
        """Test sanitization of None input."""
        sanitized = sanitize_filename(None)
        assert sanitized == "unnamed_file"

    def test_sanitize_filename_reserved_names(self):
        """Test handling of reserved Windows filenames."""
        reserved_names = ["con", "prn", "aux", "nul", "com1", "lpt1"]

        for name in reserved_names:
            # Test exact match
            sanitized = sanitize_filename(f"{name}.txt")
            assert sanitized != f"{name}.txt"
            assert "_file.txt" in sanitized

            # Test case insensitive
            sanitized = sanitize_filename(f"{name.upper()}.txt")
            assert sanitized != f"{name.upper()}.txt"

    def test_sanitize_filename_max_length(self):
        """Test filename length limitation."""
        long_name = "a" * 300 + ".txt"
        sanitized = sanitize_filename(long_name, max_length=50)

        assert len(sanitized) <= 50
        assert sanitized.endswith(".txt")  # Extension preserved

    def test_sanitize_filename_preserve_extension_false(self):
        """Test sanitization without preserving extension."""
        long_name = "a" * 300 + ".txt"
        sanitized = sanitize_filename(long_name, max_length=10, preserve_extension=False)

        assert len(sanitized) == 10
        # May or may not contain the extension depending on truncation

    def test_sanitize_filename_custom_replacement_char(self):
        """Test sanitization with custom replacement character."""
        sanitized = sanitize_filename("file<>name.txt", replacement_char="-")
        assert "file--name.txt" == sanitized or "file-name.txt" == sanitized

    def test_sanitize_filename_no_extension(self):
        """Test sanitization of filename without extension."""
        sanitized = sanitize_filename("file<>name")
        assert "_" in sanitized
        assert "file" in sanitized
        assert "name" in sanitized

    def test_sanitize_filename_very_long_extension(self):
        """Test sanitization with very long extension."""
        name_with_long_ext = "file." + "x" * 300
        sanitized = sanitize_filename(name_with_long_ext, max_length=50)

        assert len(sanitized) <= 50


class TestGenerateThumbnailName:
    """Test thumbnail name generation functionality."""

    def test_generate_thumbnail_name_basic(self):
        """Test basic thumbnail name generation."""
        thumbnail = generate_thumbnail_name("photo.jpg", (150, 150))
        assert "photo" in thumbnail
        assert "thumb" in thumbnail
        assert "150x150" in thumbnail
        assert thumbnail.endswith(".jpg")

    def test_generate_thumbnail_name_custom_suffix(self):
        """Test thumbnail name generation with custom suffix."""
        thumbnail = generate_thumbnail_name("image.png", (200, 200), suffix="_small")
        assert "image" in thumbnail
        assert "small" in thumbnail
        assert "200x200" in thumbnail
        assert thumbnail.endswith(".png")

    def test_generate_thumbnail_name_format_override(self):
        """Test thumbnail name generation with format override."""
        thumbnail = generate_thumbnail_name("photo.png", (100, 100), format_override="jpg")
        assert "photo" in thumbnail
        assert "100x100" in thumbnail
        assert thumbnail.endswith(".jpg")  # Overridden format

    def test_generate_thumbnail_name_no_extension(self):
        """Test thumbnail name generation for file without extension."""
        thumbnail = generate_thumbnail_name("photo", (75, 75))
        assert "photo" in thumbnail
        assert "75x75" in thumbnail
        assert thumbnail.endswith(".jpg")  # Default extension

    def test_generate_thumbnail_name_different_sizes(self):
        """Test thumbnail name generation with different sizes."""
        sizes = [(50, 50), (100, 150), (200, 300), (1920, 1080)]

        for width, height in sizes:
            thumbnail = generate_thumbnail_name("test.jpg", (width, height))
            assert f"{width}x{height}" in thumbnail

    def test_generate_thumbnail_name_sanitization(self):
        """Test that generated thumbnail names are sanitized."""
        thumbnail = generate_thumbnail_name("file<>name.jpg", (100, 100))
        # Should be sanitized (no invalid characters)
        assert "<" not in thumbnail
        assert ">" not in thumbnail
        assert "100x100" in thumbnail

    def test_generate_thumbnail_name_format_case_handling(self):
        """Test format override case handling."""
        thumbnail = generate_thumbnail_name("photo.png", (100, 100), format_override="JPG")
        assert thumbnail.endswith(".jpg")  # Should be lowercase

        thumbnail = generate_thumbnail_name("photo.png", (100, 100), format_override=".PNG")
        assert thumbnail.endswith(".png")  # Should handle leading dot


class TestGetSafeFilename:
    """Test safe filename generation functionality."""

    def test_get_safe_filename_no_conflict(self):
        """Test safe filename generation when no conflict exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            safe_name = get_safe_filename(temp_dir, "unique_file.txt")
            assert safe_name == "unique_file.txt"

    def test_get_safe_filename_with_conflict(self):
        """Test safe filename generation when conflict exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file that will cause conflict
            existing_file = Path(temp_dir) / "test_file.txt"
            existing_file.touch()

            safe_name = get_safe_filename(temp_dir, "test_file.txt")
            assert safe_name != "test_file.txt"
            assert "test_file_1.txt" == safe_name

    def test_get_safe_filename_multiple_conflicts(self):
        """Test safe filename generation with multiple conflicts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple conflicting files
            for i in range(5):
                if i == 0:
                    filename = "test.txt"
                else:
                    filename = f"test_{i}.txt"
                conflicting_file = Path(temp_dir) / filename
                conflicting_file.touch()

            safe_name = get_safe_filename(temp_dir, "test.txt")
            assert safe_name == "test_5.txt"

    def test_get_safe_filename_max_attempts_exceeded(self):
        """Test safe filename generation when max attempts exceeded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create many conflicting files
            for i in range(15):
                if i == 0:
                    filename = "test.txt"
                else:
                    filename = f"test_{i}.txt"
                conflicting_file = Path(temp_dir) / filename
                conflicting_file.touch()

            safe_name = get_safe_filename(temp_dir, "test.txt", max_attempts=10)
            # Should use timestamp when max attempts exceeded
            assert "test_" in safe_name
            assert safe_name != "test.txt"

    def test_get_safe_filename_sanitizes_input(self):
        """Test that safe filename generation sanitizes input."""
        with tempfile.TemporaryDirectory() as temp_dir:
            safe_name = get_safe_filename(temp_dir, "file<>name.txt")
            assert "<" not in safe_name
            assert ">" not in safe_name
            assert "file" in safe_name
            assert ".txt" in safe_name

    def test_get_safe_filename_with_path_object(self):
        """Test safe filename generation with Path object."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            safe_name = get_safe_filename(temp_path, "test_file.txt")
            assert safe_name == "test_file.txt"


class TestFormatFileSize:
    """Test file size formatting functionality."""

    def test_format_file_size_bytes(self):
        """Test file size formatting for byte values."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(1) == "1 B"
        assert format_file_size(512) == "512 B"
        assert format_file_size(1023) == "1023 B"

    def test_format_file_size_kilobytes(self):
        """Test file size formatting for kilobyte values."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(2048) == "2.0 KB"
        assert format_file_size(1024 * 1023) == "1023.0 KB"

    def test_format_file_size_megabytes(self):
        """Test file size formatting for megabyte values."""
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 2) == "2.0 MB"
        assert format_file_size(int(1024 * 1024 * 1.5)) == "1.5 MB"

    def test_format_file_size_gigabytes(self):
        """Test file size formatting for gigabyte values."""
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_file_size(int(1024 * 1024 * 1024 * 2.5)) == "2.5 GB"

    def test_format_file_size_terabytes(self):
        """Test file size formatting for terabyte values."""
        assert format_file_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"

    def test_format_file_size_petabytes(self):
        """Test file size formatting for petabyte values."""
        assert format_file_size(1024 * 1024 * 1024 * 1024 * 1024) == "1.0 PB"

    def test_format_file_size_very_large(self):
        """Test file size formatting for extremely large values."""
        # Should stop at PB and not exceed
        huge_size = 1024 * 1024 * 1024 * 1024 * 1024 * 1024
        result = format_file_size(huge_size)
        assert "PB" in result
        assert float(result.split()[0]) >= 1024.0


class TestIsHiddenFile:
    """Test hidden file detection functionality."""

    def test_is_hidden_file_unix_style(self):
        """Test detection of Unix-style hidden files."""
        assert is_hidden_file(".hidden_file") is True
        assert is_hidden_file(".bashrc") is True
        assert is_hidden_file(".gitignore") is True
        assert is_hidden_file("/.ssh/config") is True

    def test_is_hidden_file_normal_files(self):
        """Test detection returns False for normal files."""
        assert is_hidden_file("normal_file.txt") is False
        assert is_hidden_file("document.pdf") is False
        assert is_hidden_file("/path/to/file.jpg") is False

    def test_is_hidden_file_with_path_object(self):
        """Test hidden file detection with Path objects."""
        assert is_hidden_file(Path(".hidden")) is True
        assert is_hidden_file(Path("visible.txt")) is False

    def test_is_hidden_file_directory_paths(self):
        """Test hidden file detection with directory paths."""
        assert is_hidden_file("/home/user/.config/app") is True
        assert is_hidden_file("/home/user/Documents/file.txt") is False

    def test_is_hidden_file_edge_cases(self):
        """Test hidden file detection edge cases."""
        assert is_hidden_file(".") is True  # Current directory
        assert is_hidden_file("..") is True  # Parent directory
        assert is_hidden_file("...") is True  # Multiple dots
        assert is_hidden_file("file.") is False  # Ends with dot but doesn't start with it


class TestGetFileExtensionInfo:
    """Test file extension information functionality."""

    def test_get_file_extension_info_common_extensions(self):
        """Test file extension info for common extensions."""
        test_cases = [
            (".jpg", "JPEG Image", "image/jpeg"),
            (".pdf", "PDF Document", "application/pdf"),
            (".mp3", "MP3 Audio", "audio/mpeg"),
            (".mp4", "MP4 Video", "video/mp4"),
            (".txt", "Text Document", "text/plain"),
            (".zip", "ZIP Archive", "application/zip"),
        ]

        for ext, expected_desc, expected_mime in test_cases:
            info = get_file_extension_info(ext)
            assert info["extension"] == ext
            assert info["description"] == expected_desc
            assert expected_mime in info["mime_type"] or info["mime_type"] == expected_mime

    def test_get_file_extension_info_without_leading_dot(self):
        """Test file extension info without leading dot."""
        info = get_file_extension_info("jpg")
        assert info["extension"] == ".jpg"
        assert "JPEG" in info["description"]

    def test_get_file_extension_info_case_insensitive(self):
        """Test file extension info is case insensitive."""
        info_lower = get_file_extension_info(".jpg")
        info_upper = get_file_extension_info(".JPG")

        assert info_lower["extension"] == info_upper["extension"]
        assert info_lower["description"] == info_upper["description"]

    def test_get_file_extension_info_unknown_extension(self):
        """Test file extension info for unknown extensions."""
        info = get_file_extension_info(".xyz")
        assert info["extension"] == ".xyz"
        assert info["description"] == ".XYZ File"
        assert "application/octet-stream" in info["mime_type"]

    def test_get_file_extension_info_file_type_mapping(self):
        """Test that file type is correctly mapped."""
        test_cases = [
            (".jpg", "image"),
            (".pdf", "document"),
            (".mp3", "audio"),
            (".mp4", "video"),
            (".zip", "archive"),
            (".txt", "text"),
        ]

        for ext, expected_type in test_cases:
            info = get_file_extension_info(ext)
            assert info["file_type"] == expected_type

    def test_get_file_extension_info_programming_languages(self):
        """Test file extension info for programming languages."""
        programming_extensions = [
            (".py", "Python Script"),
            (".js", "JavaScript File"),
            (".html", "HTML Document"),
            (".css", "CSS Stylesheet"),
            (".json", "JSON Data"),
            (".xml", "XML Document"),
        ]

        for ext, expected_desc in programming_extensions:
            info = get_file_extension_info(ext)
            assert info["description"] == expected_desc


class TestValidateFileExtension:
    """Test file extension validation functionality."""

    def test_validate_file_extension_allowed_list(self):
        """Test file extension validation with allowed list."""
        allowed = [".jpg", ".png", ".gif"]

        # Valid extensions
        is_valid, msg = validate_file_extension("photo.jpg", allowed_extensions=allowed)
        assert is_valid is True
        assert msg == ""

        is_valid, msg = validate_file_extension("image.PNG", allowed_extensions=allowed)
        assert is_valid is True
        assert msg == ""

        # Invalid extension
        is_valid, msg = validate_file_extension("document.pdf", allowed_extensions=allowed)
        assert is_valid is False
        assert "not in the allowed list" in msg

    def test_validate_file_extension_blocked_list(self):
        """Test file extension validation with blocked list."""
        blocked = [".exe", ".bat", ".sh"]

        # Safe extension
        is_valid, msg = validate_file_extension("document.pdf", blocked_extensions=blocked)
        assert is_valid is True
        assert msg == ""

        # Blocked extension
        is_valid, msg = validate_file_extension("program.exe", blocked_extensions=blocked)
        assert is_valid is False
        assert "not allowed" in msg

    def test_validate_file_extension_combined_lists(self):
        """Test file extension validation with both allowed and blocked lists."""
        allowed = [".jpg", ".png", ".gif", ".exe"]
        blocked = [".exe", ".bat"]

        # Allowed but also blocked - should be blocked
        is_valid, msg = validate_file_extension("program.exe", allowed_extensions=allowed, blocked_extensions=blocked)
        assert is_valid is False
        assert "not allowed" in msg

        # Allowed and not blocked
        is_valid, msg = validate_file_extension("photo.jpg", allowed_extensions=allowed, blocked_extensions=blocked)
        assert is_valid is True
        assert msg == ""

    def test_validate_file_extension_no_extension(self):
        """Test file extension validation for files without extension."""
        is_valid, msg = validate_file_extension("README")
        assert is_valid is False
        assert "no extension" in msg

    def test_validate_file_extension_case_insensitive(self):
        """Test file extension validation is case insensitive."""
        allowed = [".JPG", ".png"]

        is_valid, msg = validate_file_extension("photo.jpg", allowed_extensions=allowed)
        assert is_valid is True

        is_valid, msg = validate_file_extension("image.PNG", allowed_extensions=allowed)
        assert is_valid is True

    def test_validate_file_extension_extensions_without_dots(self):
        """Test file extension validation with extensions without leading dots."""
        allowed = ["jpg", "png"]  # No leading dots
        blocked = ["exe", "bat"]  # No leading dots

        is_valid, msg = validate_file_extension("photo.jpg", allowed_extensions=allowed)
        assert is_valid is True

        is_valid, msg = validate_file_extension("program.exe", blocked_extensions=blocked)
        assert is_valid is False

    def test_validate_file_extension_none_lists(self):
        """Test file extension validation with None lists."""
        # No restrictions
        is_valid, msg = validate_file_extension("any_file.xyz")
        assert is_valid is True
        assert msg == ""

    def test_validate_file_extension_empty_lists(self):
        """Test file extension validation with empty lists."""
        is_valid, msg = validate_file_extension("file.txt", allowed_extensions=[], blocked_extensions=[])
        assert is_valid is False  # Empty allowed list means nothing is allowed
        assert "not in the allowed list" in msg


class TestUtilsEdgeCases:
    """Test edge cases and error handling in utility functions."""

    def test_get_file_type_empty_string(self):
        """Test file type detection with empty string."""
        file_type = get_file_type("")
        assert file_type == FileType.UNKNOWN

    def test_validate_file_size_permission_error(self):
        """Test file size validation with permission errors."""
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.side_effect = PermissionError("Access denied")

            is_valid, error_msg = validate_file_size("/some/protected/file.txt")
            assert is_valid is False
            assert "Error validating file size" in error_msg

    def test_sanitize_filename_only_invalid_chars(self):
        """Test sanitizing filename with only invalid characters."""
        sanitized = sanitize_filename("<>:\"/\\|?*")
        assert sanitized == "unnamed_file"

    def test_generate_thumbnail_name_extreme_sizes(self):
        """Test thumbnail name generation with extreme sizes."""
        thumbnail = generate_thumbnail_name("photo.jpg", (0, 0))
        assert "0x0" in thumbnail

        thumbnail = generate_thumbnail_name("photo.jpg", (9999, 9999))
        assert "9999x9999" in thumbnail

    def test_format_file_size_negative_input(self):
        """Test file size formatting with negative input."""
        # Should handle gracefully (implementation dependent)
        result = format_file_size(-1024)
        assert isinstance(result, str)

    @patch('datetime.datetime')
    def test_get_safe_filename_timestamp_fallback(self, mock_datetime):
        """Test safe filename generation timestamp fallback."""
        mock_now = MagicMock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create many conflicting files to force timestamp usage
            for i in range(1005):  # Exceed max_attempts default
                if i == 0:
                    filename = "test.txt"
                else:
                    filename = f"test_{i}.txt"
                conflicting_file = Path(temp_dir) / filename
                conflicting_file.touch()

            safe_name = get_safe_filename(temp_dir, "test.txt", max_attempts=1000)
            assert "20240101_120000" in safe_name

    def test_validate_file_extension_mixed_case_lists(self):
        """Test file extension validation with mixed case in lists."""
        allowed = [".JPG", ".png", ".GIF"]
        blocked = [".EXE", ".bat"]

        is_valid, msg = validate_file_extension("photo.jpg", allowed_extensions=allowed, blocked_extensions=blocked)
        assert is_valid is True

        is_valid, msg = validate_file_extension("program.exe", allowed_extensions=allowed, blocked_extensions=blocked)
        assert is_valid is False