"""Lightweight smoke tests for key file processing flows."""

from __future__ import annotations

import asyncio
import types
from pathlib import Path
from typing import Any

import sys

import pytest
from PIL import Image
from PyPDF2 import PdfWriter

from dotmac.platform.file_processing import processors
from dotmac.platform.file_processing.base import (
    ProcessingError,
    ProcessingOptions,
    ProcessingStatus,
)


class _StubStream:
    def __init__(self, path: str) -> None:
        self.path = path

    def filter(self, *_args: Any, **_kwargs: Any) -> "_StubStream":
        return self

    def output(self, *_args: Any, **_kwargs: Any) -> "_StubStream":
        return self

    def overwrite_output(self) -> "_StubStream":
        return self

    def run(self, *_, **__) -> None:  # pragma: no cover - deterministic stub
        return None


class _StubFfmpeg:
    def probe(self, path: str) -> dict[str, Any]:
        if path.endswith(".mp4"):
            return {
                "format": {"duration": "1", "bit_rate": "1000"},
                "streams": [
                    {
                        "codec_type": "video",
                        "width": 320,
                        "height": 180,
                        "codec_name": "h264",
                        "r_frame_rate": "30/1",
                    }
                ],
            }
        return {
            "format": {"duration": "2", "bit_rate": "640"},
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "44100",
                    "channels": 2,
                }
            ],
        }

    def input(self, path: str, **_kwargs: Any) -> _StubStream:
        return _StubStream(path)


@pytest.mark.asyncio
async def test_image_processor_watermark(tmp_path: Path) -> None:
    image_path = tmp_path / "image.png"
    Image.new("RGB", (32, 32), color="black").save(image_path)

    processor = processors.ImageProcessor()
    options = ProcessingOptions(
        watermark_text="CONFIDENTIAL",
        generate_thumbnails=True,
        thumbnail_sizes=[(16, 16)],
    )

    result = await processor.process(str(image_path), options)
    assert result.status is ProcessingStatus.COMPLETED
    assert result.metadata and result.metadata.width == 32
    assert result.thumbnails  # thumbnail created


# Additional coverage for watermark path handling.
@pytest.mark.asyncio
async def test_image_processor_watermark_file(tmp_path: Path) -> None:
    base_image = tmp_path / "photo.png"
    Image.new("RGB", (24, 24), color="blue").save(base_image)

    watermark = tmp_path / "stamp.png"
    Image.new("RGBA", (8, 8), color=(255, 0, 0, 128)).save(watermark)

    processor = processors.ImageProcessor()
    options = ProcessingOptions(watermark_path=str(watermark))

    result = await processor.process(str(base_image), options)
    assert result.status is ProcessingStatus.COMPLETED
    assert result.processed_file is not None


@pytest.mark.asyncio
async def test_image_processor_invalid_image(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.jpg"
    corrupt.write_bytes(b"not-a-real-image")

    processor = processors.ImageProcessor()
    assert await processor.validate(str(corrupt)) is False

    result = await processor.process(str(corrupt))
    assert result.status is ProcessingStatus.FAILED
    assert result.errors


@pytest.mark.asyncio
async def test_document_processor_text(tmp_path: Path) -> None:
    doc_path = tmp_path / "note.txt"
    doc_path.write_text("Line one\nLine two", encoding="utf-8")

    processor = processors.DocumentProcessor()
    result = await processor.process(str(doc_path))

    assert result.status is ProcessingStatus.COMPLETED
    assert result.extracted_text and "Line one" in result.extracted_text


@pytest.mark.asyncio
async def test_document_processor_split_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with pdf_path.open("wb") as handle:
        writer.write(handle)

    out_dir = tmp_path / "pages"
    processor = processors.DocumentProcessor()
    options = ProcessingOptions(split_pages=True, output_directory=str(out_dir))
    result = await processor.process(str(pdf_path), options)

    assert result.status is ProcessingStatus.COMPLETED
    assert result.metadata and result.metadata.page_count == 1


@pytest.mark.asyncio
async def test_document_processor_missing_file() -> None:
    processor = processors.DocumentProcessor()
    result = await processor.process("missing.pdf")
    assert result.status is ProcessingStatus.FAILED
    assert result.errors


@pytest.mark.asyncio
async def test_document_processor_docx_branch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_document(_path: str):
        return types.SimpleNamespace(
            paragraphs=[types.SimpleNamespace(text="First paragraph")],
            element=types.SimpleNamespace(body=[object(), object(), object()]),
            core_properties=types.SimpleNamespace(title="Doc", author="Tester"),
        )

    monkeypatch.setattr(processors, "docx", types.SimpleNamespace(Document=fake_document))

    doc_path = tmp_path / "draft.docx"
    doc_path.write_bytes(b"fake")

    processor = processors.DocumentProcessor()
    options = ProcessingOptions()
    result = await processor.process(str(doc_path), options)

    assert result.status is ProcessingStatus.COMPLETED
    assert result.metadata and result.metadata.title == "Doc"
    assert "First paragraph" in (result.extracted_text or "")


@pytest.mark.asyncio
async def test_document_processor_excel_branch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class FakeCell:
        def __init__(self, value: Any, data_type: str) -> None:
            self.value = value
            self.data_type = data_type

    class FakeSheet:
        title = "Sheet1"
        max_row = 2
        max_column = 2

        def iter_rows(self, values_only: bool = False):
            if values_only:
                return [(1, 2), (3, 4)]
            return [[FakeCell("=SUM(A1:A2)", "f"), FakeCell(5, "n")]]

    class FakeWorkbook:
        def __init__(self) -> None:
            self.sheetnames = ["Sheet1"]
            self.worksheets = [FakeSheet()]

        def __getitem__(self, name: str) -> FakeSheet:
            return self.worksheets[0]

    fake_workbook = FakeWorkbook()

    def load_workbook(*_args, **_kwargs):
        return fake_workbook

    monkeypatch.setattr(processors, "openpyxl", types.SimpleNamespace(load_workbook=load_workbook))

    xlsx_path = tmp_path / "table.xlsx"
    xlsx_path.write_bytes(b"excel")

    processor = processors.DocumentProcessor()
    options = ProcessingOptions(extract_formulas=True)
    result = await processor.process(str(xlsx_path), options)

    assert result.status is ProcessingStatus.COMPLETED
    assert result.metadata and result.metadata.sheet_count == 1
    assert result.extracted_text and "Sheet: Sheet1" in result.extracted_text


@pytest.mark.asyncio
async def test_document_processor_invalid_extension(tmp_path: Path) -> None:
    bad = tmp_path / "payload.xyz"
    bad.write_text("data", encoding="utf-8")

    processor = processors.DocumentProcessor()
    result = await processor.process(str(bad))
    assert result.status is ProcessingStatus.FAILED
    assert result.errors


@pytest.mark.asyncio
async def test_document_processor_ocr(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "ocr.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with pdf_path.open("wb") as handle:
        writer.write(handle)

    stub_images = [Image.new("RGB", (16, 16), color="white")]

    monkeypatch.setitem(sys.modules, "pdf2image", types.SimpleNamespace(convert_from_path=lambda _p: stub_images))
    monkeypatch.setitem(sys.modules, "pytesseract", types.SimpleNamespace(image_to_string=lambda _img: "OCR"))

    processor = processors.DocumentProcessor()
    result = await processor.process(str(pdf_path), ProcessingOptions(ocr_enabled=True))

    assert result.status is ProcessingStatus.COMPLETED
    assert "OCR" in (result.extracted_text or "")


@pytest.mark.asyncio
async def test_document_processor_validation_failure(tmp_path: Path) -> None:
    empty = tmp_path / "blank.txt"
    empty.write_text("", encoding="utf-8")

    processor = processors.DocumentProcessor(ProcessingOptions(validate_content=True))
    result = await processor.process(str(empty))

    assert result.status is ProcessingStatus.FAILED
    assert result.errors and "validation" in result.errors[0].lower()


@pytest.mark.asyncio
async def test_spreadsheet_processor_excel_formulas(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class FakeCell:
        def __init__(self, value: Any, data_type: str) -> None:
            self.value = value
            self.data_type = data_type

    class FakeSheet:
        title = "Sheet1"
        max_row = 2
        max_column = 2

        def iter_rows(self, values_only: bool = False):
            if values_only:
                yield (1, 2)
                yield (3, 4)
            else:
                yield [FakeCell("=SUM(A1:A2)", "f"), FakeCell(5, "n")]

    class FakeWorkbook:
        def __init__(self) -> None:
            self.sheetnames = ["Sheet1"]
            self.worksheets = [FakeSheet()]

        def __getitem__(self, name: str) -> FakeSheet:
            return self.worksheets[0]

    monkeypatch.setattr(
        processors,
        "openpyxl",
        types.SimpleNamespace(load_workbook=lambda *_args, **_kwargs: FakeWorkbook()),
    )

    path = tmp_path / "sheet.xlsx"
    path.write_bytes(b"excel")

    processor = processors.SpreadsheetProcessor()
    result = await processor.process(str(path), ProcessingOptions(extract_formulas=True))

    assert result.status is ProcessingStatus.COMPLETED
    assert result.formulas and "SUM" in result.formulas[0]
    assert result.extracted_data["Sheet1"][0][0] == "=SUM(A1:A2)"


@pytest.mark.asyncio
async def test_spreadsheet_processor_unsupported_extension(tmp_path: Path) -> None:
    processor = processors.SpreadsheetProcessor()
    result = await processor.process(str(tmp_path / "data.txt"))
    assert result.status is ProcessingStatus.FAILED
    assert result.errors


@pytest.mark.asyncio
async def test_spreadsheet_processor_csv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("col1,col2\n1,2\n3,4\n", encoding="utf-8")

    class _DummyFrame:
        shape = (2, 2)
        columns = ["col1", "col2"]
        dtypes = {"col1": "int64", "col2": "int64"}

        def to_dict(self) -> dict[str, list[int]]:
            return {"col1": [1, 3], "col2": [2, 4]}

    dummy_module = types.SimpleNamespace(read_csv=lambda path: _DummyFrame())
    monkeypatch.setitem(sys.modules, "pandas", dummy_module)

    processor = processors.SpreadsheetProcessor()
    result = await processor.process(str(csv_path))

    assert result.status is ProcessingStatus.COMPLETED
    assert result.metadata and result.metadata.total_rows == 2
    assert result.extracted_data["col1"] == [1, 3]


@pytest.mark.asyncio
async def test_presentation_processor_success(tmp_path: Path) -> None:
    deck = tmp_path / "deck.pptx"
    deck.write_bytes(b"ppt")

    processor = processors.PresentationProcessor()
    result = await processor.process(str(deck))

    assert result.status is ProcessingStatus.COMPLETED
    assert result.metadata and result.metadata.file_name == "deck.pptx"


@pytest.mark.asyncio
async def test_presentation_processor_missing() -> None:
    processor = processors.PresentationProcessor()
    result = await processor.process("missing.pptx")

    assert result.status is ProcessingStatus.FAILED
    assert result.errors


@pytest.mark.asyncio
async def test_video_processor_stubbed_ffmpeg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    video_path = tmp_path / "clip.mp4"
    video_path.write_bytes(b"video")

    monkeypatch.setattr(processors, "ffmpeg", _StubFfmpeg())

    processor = processors.VideoProcessor()
    options = ProcessingOptions(
        generate_thumbnail=True,
        extract_frames=True,
        frame_interval=0.5,
        transcode=True,
        output_format="mp4",
        video_codec="libx264",
    )

    result = await processor.process(str(video_path), options)

    assert result.status is ProcessingStatus.COMPLETED
    assert result.metadata and result.metadata.width == 320
    assert result.thumbnails  # thumbnail path recorded


@pytest.mark.asyncio
async def test_video_processor_missing_file() -> None:
    processor = processors.VideoProcessor()
    result = await processor.process("missing.mp4")
    assert result.status is ProcessingStatus.FAILED
    assert result.errors


@pytest.mark.asyncio
async def test_video_processor_invalid_extension(tmp_path: Path) -> None:
    wrong = tmp_path / "video.txt"
    wrong.write_bytes(b"vid")

    processor = processors.VideoProcessor()
    result = await processor.process(str(wrong))
    assert result.status is ProcessingStatus.FAILED
    assert result.errors


@pytest.mark.asyncio
async def test_video_processor_metadata_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    video_path = tmp_path / "broken.mp4"
    video_path.write_bytes(b"vid")

    class BrokenFfmpeg:
        def probe(self, _path: str):
            raise RuntimeError("ffmpeg failure")

        def input(self, path: str, **_kwargs: Any) -> _StubStream:
            return _StubStream(path)

    monkeypatch.setattr(processors, "ffmpeg", BrokenFfmpeg())

    processor = processors.VideoProcessor()
    metadata = await processor.extract_metadata(str(video_path))
    assert "metadata_error" in metadata.extra_metadata


@pytest.mark.asyncio
async def test_audio_processor_stubbed_ffmpeg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    audio_path = tmp_path / "sound.mp3"
    audio_path.write_bytes(b"audio")

    monkeypatch.setattr(processors, "ffmpeg", _StubFfmpeg())

    processor = processors.AudioProcessor()
    result = await processor.process(str(audio_path), ProcessingOptions(generate_waveform=True))

    assert result.status is ProcessingStatus.COMPLETED
    assert result.metadata and result.metadata.audio_codec == "aac"


@pytest.mark.asyncio
async def test_audio_processor_missing_file() -> None:
    processor = processors.AudioProcessor()
    result = await processor.process("missing.mp3")
    assert result.status is ProcessingStatus.FAILED
    assert result.errors
