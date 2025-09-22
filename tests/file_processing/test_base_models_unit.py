"""Targeted coverage for file processing base primitives."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from dotmac.platform.file_processing.base import (
    FileMetadata,
    FileProcessor,
    FileType,
    ProcessingError,
    ProcessingOptions,
    ProcessingResult,
    ProcessingStatus,
)


def test_file_metadata_from_file(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("hello world", encoding="utf-8")

    metadata = FileMetadata.from_file(str(sample))

    assert metadata.file_type is FileType.TEXT
    assert metadata.file_size == sample.stat().st_size
    assert metadata.format == "TXT"
    assert metadata.file_hash
    assert metadata.file_name == "sample.txt"


def test_file_metadata_type_detection(tmp_path: Path) -> None:
    cases = {
        "clip.mp4": FileType.VIDEO,
        "song.wav": FileType.AUDIO,
        "report.pdf": FileType.DOCUMENT,
        "archive.zip": FileType.ARCHIVE,
    }

    for filename, expected in cases.items():
        path = tmp_path / filename
        path.write_bytes(b"data")
        detected = FileMetadata.from_file(str(path))
        assert detected.file_type is expected


def test_processing_result_helpers() -> None:
    result = ProcessingResult(status=ProcessingStatus.PROCESSING, original_file="input.txt")

    result.add_warning("low confidence")
    assert result.warnings == ["low confidence"]

    result.add_processed_file("output.txt")
    assert result.processed_file == "output.txt"

    result.add_thumbnail("output_thumb.png")
    assert "output_thumb.png" in result.thumbnails

    result.add_error("conversion failed")
    assert result.status is ProcessingStatus.FAILED
    assert not result.success


class DummyProcessor(FileProcessor):
    async def process(self, file_path: str, options: ProcessingOptions | None = None) -> ProcessingResult:
        opts = self.resolve_options(options)
        if opts.output_format == "invalid":  # pragma: no cover - defensive
            raise ProcessingError("Invalid format")

        metadata = await self.extract_basic_metadata(file_path)
        result = ProcessingResult(status=ProcessingStatus.COMPLETED, original_file=file_path, metadata=metadata)
        return result


@pytest.mark.asyncio
async def test_file_processor_utilities(tmp_path: Path) -> None:
    base_file = tmp_path / "document.md"
    base_file.write_text("# Title", encoding="utf-8")

    processor = DummyProcessor(ProcessingOptions(output_format="pdf", quality=70))
    override = ProcessingOptions(quality=90, generate_thumbnails=True)
    merged = processor.resolve_options(override)
    assert merged.quality == 90 and merged.generate_thumbnails is True

    metadata = await processor.extract_basic_metadata(str(base_file))
    assert metadata.file_name == "document.md"

    result = await processor.process(str(base_file), ProcessingOptions())
    assert result.status is ProcessingStatus.COMPLETED
    assert result.metadata is not None


@pytest.mark.asyncio
async def test_file_processor_validation_rules(tmp_path: Path) -> None:
    validator_opts = ProcessingOptions(
        allowed_extensions=[".txt"],
        blocked_extensions=[".bin"],
        max_file_size=4,
        allowed_mime_types=["text/plain"],
    )
    processor = DummyProcessor(validator_opts)

    valid_file = tmp_path / "valid.txt"
    valid_file.write_text("ok", encoding="utf-8")
    assert await processor.validate(str(valid_file))

    blocked = tmp_path / "payload.bin"
    blocked.write_bytes(b"abcd")
    assert not await processor.validate(str(blocked))

    oversized = tmp_path / "oversize.txt"
    oversized.write_bytes(b"012345")
    assert not await processor.validate(str(oversized))

    wrong_ext = tmp_path / "note.md"
    wrong_ext.write_text("# heading", encoding="utf-8")
    assert not await processor.validate(str(wrong_ext))

    processor.options.allowed_mime_types = ["application/json"]
    assert not await processor.validate(str(valid_file))

    # Ensure resolve_options without override returns base instance
    assert processor.resolve_options() is processor.options
