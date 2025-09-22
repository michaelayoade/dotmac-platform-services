"""
Simple tests for file processing utilities to improve coverage.
Focuses on actual behavior and edge cases.
"""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch

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

    def test_get_file_type_images(self):
        """Test image file type detection."""
        image_files = ["photo.jpg", "image.png", "graphic.gif", "picture.webp"]
        for filename in image_files:
            assert get_file_type(filename) == FileType.IMAGE

    def test_get_file_type_documents(self):
        """Test document file type detection."""
        doc_files = ["document.pdf", "text.docx", "spreadsheet.xlsx"]
        for filename in doc_files:
            assert get_file_type(filename) == FileType.DOCUMENT

    def test_get_file_type_videos(self):
        """Test video file type detection."""
        video_files = ["movie.mp4", "clip.avi", "video.mkv"]
        for filename in video_files:
            assert get_file_type(filename) == FileType.VIDEO

    def test_get_file_type_audio(self):
        """Test audio file type detection."""
        audio_files = ["song.mp3", "audio.wav", "lossless.flac"]
        for filename in audio_files:
            assert get_file_type(filename) == FileType.AUDIO

    def test_get_file_type_archives(self):
        """Test archive file type detection."""
        archive_files = ["package.zip", "compressed.rar", "archive.7z"]
        for filename in archive_files:
            assert get_file_type(filename) == FileType.ARCHIVE

    def test_get_file_type_text(self):
        """Test text file type detection."""
        text_files = ["readme.txt", "data.csv", "config.json"]
        for filename in text_files:
            assert get_file_type(filename) == FileType.TEXT

    def test_get_file_type_unknown(self):
        """Test unknown file type detection."""
        assert get_file_type("file.unknown") == FileType.UNKNOWN
        assert get_file_type("no_extension") == FileType.UNKNOWN

    def test_get_file_type_case_insensitive(self):
        """Test case insensitive detection."""
        assert get_file_type("FILE.JPG") == FileType.IMAGE
        assert get_file_type("DOCUMENT.PDF") == FileType.DOCUMENT

    def test_get_file_type_with_path(self):
        """Test with Path objects."""
        assert get_file_type(Path("document.pdf")) == FileType.DOCUMENT


class TestValidateFileSize:
    """Test file size validation."""

    def test_validate_file_size_valid(self):
        """Test valid file size."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"Hello, World!" * 100
            temp_file.write(content)
            temp_file.flush()

            try:
                is_valid, error_msg = validate_file_size(temp_file.name, max_size_bytes=10000)
                assert is_valid is True
                assert error_msg == ""
            finally:
                os.unlink(temp_file.name)

    def test_validate_file_size_too_large(self):
        """Test file too large."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"x" * 2000
            temp_file.write(content)
            temp_file.flush()

            try:
                is_valid, error_msg = validate_file_size(temp_file.name, max_size_bytes=1000)
                assert is_valid is False
                assert "exceeds maximum" in error_msg
            finally:
                os.unlink(temp_file.name)

    def test_validate_file_size_too_small(self):
        """Test file too small."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = b"x" * 50
            temp_file.write(content)
            temp_file.flush()

            try:
                is_valid, error_msg = validate_file_size(temp_file.name, min_size_bytes=100)
                assert is_valid is False
                assert "below minimum" in error_msg
            finally:
                os.unlink(temp_file.name)

    def test_validate_file_size_nonexistent(self):
        """Test non-existent file."""
        is_valid, error_msg = validate_file_size("/nonexistent/file.txt")
        assert is_valid is False
        assert "does not exist" in error_msg

    def test_validate_file_size_directory(self):
        """Test directory instead of file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            is_valid, error_msg = validate_file_size(temp_dir)
            assert is_valid is False
            assert "not a file" in error_msg


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_sanitize_filename_basic(self):
        """Test basic sanitization."""
        assert sanitize_filename("normal_file.txt") == "normal_file.txt"

    def test_sanitize_filename_invalid_chars(self):
        """Test sanitization of invalid characters."""
        # Test actual behavior - multiple invalid chars get consolidated
        result = sanitize_filename("file<>name.txt")
        assert "file" in result
        assert "name.txt" in result
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_filename_empty(self):
        """Test empty filename."""
        assert sanitize_filename("") == "unnamed_file"
        assert sanitize_filename(None) == "unnamed_file"

    def test_sanitize_filename_reserved_names(self):
        """Test reserved names."""
        result = sanitize_filename("con.txt")
        assert result != "con.txt"
        assert "file.txt" in result

    def test_sanitize_filename_max_length(self):
        """Test length limitation."""
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name, max_length=50)
        assert len(result) <= 50
        assert result.endswith(".txt")

    def test_sanitize_filename_custom_replacement(self):
        """Test custom replacement character."""
        result = sanitize_filename("file<name.txt", replacement_char="-")
        assert "-" in result
        assert "<" not in result


class TestGenerateThumbnailName:
    """Test thumbnail name generation."""

    def test_generate_thumbnail_name_basic(self):
        """Test basic thumbnail generation."""
        result = generate_thumbnail_name("photo.jpg", (150, 150))
        assert "photo" in result
        assert "thumb" in result
        assert "150x150" in result
        assert result.endswith(".jpg")

    def test_generate_thumbnail_name_custom_suffix(self):
        """Test custom suffix."""
        result = generate_thumbnail_name("image.png", (100, 100), suffix="_small")
        assert "small" in result
        assert "100x100" in result

    def test_generate_thumbnail_name_format_override(self):
        """Test format override."""
        result = generate_thumbnail_name("photo.png", (100, 100), format_override="jpg")
        assert result.endswith(".jpg")

    def test_generate_thumbnail_name_no_extension(self):
        """Test file without extension."""
        result = generate_thumbnail_name("photo", (75, 75))
        assert "photo" in result
        assert result.endswith(".jpg")  # Default


class TestGetSafeFilename:
    """Test safe filename generation."""

    def test_get_safe_filename_no_conflict(self):
        """Test when no conflict exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = get_safe_filename(temp_dir, "unique_file.txt")
            assert result == "unique_file.txt"

    def test_get_safe_filename_with_conflict(self):
        """Test when conflict exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_file = Path(temp_dir) / "test_file.txt"
            existing_file.touch()

            result = get_safe_filename(temp_dir, "test_file.txt")
            assert result == "test_file_1.txt"

    def test_get_safe_filename_multiple_conflicts(self):
        """Test multiple conflicts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            for i in range(3):
                if i == 0:
                    filename = "test.txt"
                else:
                    filename = f"test_{i}.txt"
                conflicting_file = Path(temp_dir) / filename
                conflicting_file.touch()

            result = get_safe_filename(temp_dir, "test.txt")
            assert result == "test_3.txt"


class TestFormatFileSize:
    """Test file size formatting."""

    def test_format_file_size_bytes(self):
        """Test byte formatting."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512 B"
        assert format_file_size(1023) == "1023 B"

    def test_format_file_size_kilobytes(self):
        """Test kilobyte formatting."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"

    def test_format_file_size_megabytes(self):
        """Test megabyte formatting."""
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(int(1024 * 1024 * 1.5)) == "1.5 MB"

    def test_format_file_size_gigabytes(self):
        """Test gigabyte formatting."""
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"

    def test_format_file_size_large(self):
        """Test very large sizes."""
        tb_size = 1024 * 1024 * 1024 * 1024
        result = format_file_size(tb_size)
        assert "TB" in result


class TestIsHiddenFile:
    """Test hidden file detection."""

    def test_is_hidden_file_unix_style(self):
        """Test Unix-style hidden files."""
        assert is_hidden_file(".hidden_file") is True
        assert is_hidden_file(".bashrc") is True

    def test_is_hidden_file_normal(self):
        """Test normal files."""
        assert is_hidden_file("normal_file.txt") is False
        assert is_hidden_file("document.pdf") is False

    def test_is_hidden_file_paths(self):
        """Test with paths."""
        assert is_hidden_file("/home/user/.config") is True
        assert is_hidden_file("/home/user/Documents/file.txt") is False

    def test_is_hidden_file_edge_cases(self):
        """Test edge cases."""
        assert is_hidden_file(".") is False  # Single dot is not considered hidden
        assert is_hidden_file("..") is True  # Double dot is considered hidden
        assert is_hidden_file("file.") is False  # Ends with dot but doesn't start with it


class TestGetFileExtensionInfo:
    """Test file extension information."""

    def test_get_file_extension_info_common(self):
        """Test common extensions."""
        info = get_file_extension_info(".jpg")
        assert info["extension"] == ".jpg"
        assert "JPEG" in info["description"]
        assert "image" in info["mime_type"] or info["file_type"] == "image"

    def test_get_file_extension_info_without_dot(self):
        """Test without leading dot."""
        info = get_file_extension_info("pdf")
        assert info["extension"] == ".pdf"
        assert "PDF" in info["description"]

    def test_get_file_extension_info_case_insensitive(self):
        """Test case insensitivity."""
        info_lower = get_file_extension_info(".jpg")
        info_upper = get_file_extension_info(".JPG")
        assert info_lower["extension"] == info_upper["extension"]

    def test_get_file_extension_info_unknown(self):
        """Test unknown extension."""
        info = get_file_extension_info(".xyz")
        assert info["extension"] == ".xyz"
        assert ".XYZ" in info["description"]


class TestValidateFileExtension:
    """Test file extension validation."""

    def test_validate_file_extension_allowed(self):
        """Test with allowed list."""
        allowed = [".jpg", ".png", ".gif"]

        is_valid, msg = validate_file_extension("photo.jpg", allowed_extensions=allowed)
        assert is_valid is True
        assert msg == ""

        is_valid, msg = validate_file_extension("doc.pdf", allowed_extensions=allowed)
        assert is_valid is False
        assert "not in the allowed list" in msg

    def test_validate_file_extension_blocked(self):
        """Test with blocked list."""
        blocked = [".exe", ".bat"]

        is_valid, msg = validate_file_extension("doc.pdf", blocked_extensions=blocked)
        assert is_valid is True

        is_valid, msg = validate_file_extension("prog.exe", blocked_extensions=blocked)
        assert is_valid is False
        assert "not allowed" in msg

    def test_validate_file_extension_no_extension(self):
        """Test file without extension."""
        is_valid, msg = validate_file_extension("README")
        assert is_valid is False
        assert "no extension" in msg

    def test_validate_file_extension_case_insensitive(self):
        """Test case insensitivity."""
        allowed = [".JPG"]
        is_valid, msg = validate_file_extension("photo.jpg", allowed_extensions=allowed)
        assert is_valid is True

    def test_validate_file_extension_no_restrictions(self):
        """Test with no restrictions."""
        is_valid, msg = validate_file_extension("any_file.xyz")
        assert is_valid is True
        assert msg == ""


class TestUtilsEdgeCases:
    """Test edge cases and error handling."""

    def test_get_file_type_empty(self):
        """Test empty filename."""
        assert get_file_type("") == FileType.UNKNOWN

    @patch('pathlib.Path.stat')
    def test_validate_file_size_permission_error(self, mock_stat):
        """Test permission error handling."""
        mock_stat.side_effect = PermissionError("Access denied")
        is_valid, error_msg = validate_file_size("/protected/file.txt")
        assert is_valid is False
        assert "Error validating file size" in error_msg

    def test_sanitize_filename_only_invalid(self):
        """Test filename with only invalid characters."""
        result = sanitize_filename("<>:\"/\\|?*")
        assert result == "unnamed_file"

    def test_generate_thumbnail_name_extreme_sizes(self):
        """Test extreme thumbnail sizes."""
        result = generate_thumbnail_name("photo.jpg", (0, 0))
        assert "0x0" in result

        result = generate_thumbnail_name("photo.jpg", (9999, 9999))
        assert "9999x9999" in result

    def test_format_file_size_edge_cases(self):
        """Test file size formatting edge cases."""
        # Test negative (implementation dependent)
        result = format_file_size(-1024)
        assert isinstance(result, str)

    def test_get_safe_filename_timestamp_fallback(self):
        """Test timestamp fallback when max attempts exceeded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create many files to force timestamp usage
            for i in range(1005):
                if i == 0:
                    filename = "test.txt"
                else:
                    filename = f"test_{i}.txt"
                conflicting_file = Path(temp_dir) / filename
                conflicting_file.touch()

            result = get_safe_filename(temp_dir, "test.txt", max_attempts=1000)
            # Should use timestamp when max attempts exceeded
            assert "test_" in result
            assert result != "test.txt"


class TestMimeTypeFallback:
    """Test MIME type fallback in file type detection."""

    @patch('mimetypes.guess_type')
    def test_mime_type_detection(self, mock_guess_type):
        """Test MIME type fallback."""
        # Test image MIME type
        mock_guess_type.return_value = ("image/jpeg", None)
        assert get_file_type("unknown.file") == FileType.IMAGE

        # Test video MIME type
        mock_guess_type.return_value = ("video/mp4", None)
        assert get_file_type("unknown.file") == FileType.VIDEO

        # Test audio MIME type
        mock_guess_type.return_value = ("audio/mpeg", None)
        assert get_file_type("unknown.file") == FileType.AUDIO

        # Test text MIME type
        mock_guess_type.return_value = ("text/plain", None)
        assert get_file_type("unknown.file") == FileType.TEXT

        # Test archive MIME type
        mock_guess_type.return_value = ("application/zip", None)
        assert get_file_type("unknown.file") == FileType.ARCHIVE