"""
Data exporters using pandas for various file formats.
"""

import asyncio
import json
import gzip
import zipfile
import bz2
from pathlib import Path
from typing import AsyncGenerator, Optional
import pandas as pd
import yaml
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .core import (
    BaseExporter,
    DataBatch,
    DataFormat,
    ExportError,
    FormatError,
    TransferConfig,
    ExportOptions,
    ProgressCallback,
    ProgressInfo,
    TransferStatus,
    CompressionType,
)


class CSVExporter(BaseExporter):
    """CSV file exporter using pandas."""

    async def export_to_file(
        self,
        data: AsyncGenerator[DataBatch, None],
        file_path: Path,
    ) -> ProgressInfo:
        """Export data to CSV file."""
        try:
            self._progress.status = TransferStatus.RUNNING

            # Collect data
            all_records = []
            async for batch in data:
                for record in batch.records:
                    all_records.append(record.data)
                self.update_progress(processed=len(batch.records))
                await asyncio.sleep(0)

            # Convert to DataFrame and export
            if all_records:
                df = pd.DataFrame(all_records)
                df.to_csv(
                    file_path,
                    sep=self.options.delimiter,
                    index=False,
                    header=self.options.include_headers,
                    encoding=self.options.encoding,
                    quoting=self.options.quoting,
                )

            self._progress.status = TransferStatus.COMPLETED
            return self._progress
        except Exception as e:
            self._progress.status = TransferStatus.FAILED
            self._progress.error_message = str(e)
            raise ExportError(f"Failed to export CSV: {e}") from e


class JSONExporter(BaseExporter):
    """JSON file exporter using pandas."""

    async def export_to_file(
        self,
        data: AsyncGenerator[DataBatch, None],
        file_path: Path,
    ) -> ProgressInfo:
        """Export data to JSON file."""
        try:
            self._progress.status = TransferStatus.RUNNING

            if self.options.json_lines:
                # Export as JSON Lines
                with open(file_path, 'w', encoding=self.options.encoding) as f:
                    async for batch in data:
                        for record in batch.records:
                            json_line = json.dumps(
                                record.data,
                                ensure_ascii=self.options.json_ensure_ascii,
                                sort_keys=self.options.json_sort_keys,
                            )
                            f.write(json_line + '\n')
                        self.update_progress(processed=len(batch.records))
                        await asyncio.sleep(0)
            else:
                # Export as regular JSON
                all_records = []
                async for batch in data:
                    for record in batch.records:
                        all_records.append(record.data)
                    self.update_progress(processed=len(batch.records))
                    await asyncio.sleep(0)

                if all_records:
                    df = pd.DataFrame(all_records)
                    df.to_json(
                        file_path,
                        orient='records',
                        indent=self.options.json_indent,
                        force_ascii=self.options.json_ensure_ascii,
                    )

            self._progress.status = TransferStatus.COMPLETED
            return self._progress
        except Exception as e:
            self._progress.status = TransferStatus.FAILED
            self._progress.error_message = str(e)
            raise ExportError(f"Failed to export JSON: {e}") from e


class ExcelExporter(BaseExporter):
    """Excel file exporter using pandas."""

    async def export_to_file(
        self,
        data: AsyncGenerator[DataBatch, None],
        file_path: Path,
    ) -> ProgressInfo:
        """Export data to Excel file."""
        try:
            self._progress.status = TransferStatus.RUNNING

            # Collect all data
            all_records = []
            async for batch in data:
                for record in batch.records:
                    all_records.append(record.data)
                self.update_progress(processed=len(batch.records))
                await asyncio.sleep(0)

            # Convert to DataFrame and export
            if all_records:
                df = pd.DataFrame(all_records)

                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    df.to_excel(
                        writer,
                        sheet_name=self.options.sheet_name,
                        index=False,
                        freeze_panes=(1, 0) if self.options.freeze_panes else None,
                    )

                    # Add auto-filter if requested
                    if self.options.auto_filter and all_records:
                        worksheet = writer.sheets[self.options.sheet_name]
                        worksheet.auto_filter.ref = worksheet.dimensions

            self._progress.status = TransferStatus.COMPLETED
            return self._progress
        except Exception as e:
            self._progress.status = TransferStatus.FAILED
            self._progress.error_message = str(e)
            raise ExportError(f"Failed to export Excel: {e}") from e


class XMLExporter(BaseExporter):
    """XML file exporter."""

    async def export_to_file(
        self,
        data: AsyncGenerator[DataBatch, None],
        file_path: Path,
    ) -> ProgressInfo:
        """Export data to XML file."""
        try:
            self._progress.status = TransferStatus.RUNNING

            # Create root element
            root = ET.Element(self.options.xml_root_element)

            # Add records
            async for batch in data:
                for record in batch.records:
                    record_elem = ET.SubElement(root, self.options.xml_record_element)
                    self._dict_to_xml(record.data, record_elem)
                self.update_progress(processed=len(batch.records))
                await asyncio.sleep(0)

            # Write to file
            if self.options.xml_pretty_print:
                xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
                with open(file_path, 'w', encoding=self.options.encoding) as f:
                    f.write(xml_str)
            else:
                tree = ET.ElementTree(root)
                tree.write(file_path, encoding=self.options.encoding, xml_declaration=True)

            self._progress.status = TransferStatus.COMPLETED
            return self._progress
        except Exception as e:
            self._progress.status = TransferStatus.FAILED
            self._progress.error_message = str(e)
            raise ExportError(f"Failed to export XML: {e}") from e

    def _dict_to_xml(self, data: dict, parent: ET.Element):
        """Convert dictionary to XML elements."""
        for key, value in data.items():
            if isinstance(value, dict):
                child = ET.SubElement(parent, str(key))
                self._dict_to_xml(value, child)
            elif isinstance(value, list):
                for item in value:
                    child = ET.SubElement(parent, str(key))
                    if isinstance(item, dict):
                        self._dict_to_xml(item, child)
                    else:
                        child.text = str(item)
            else:
                child = ET.SubElement(parent, str(key))
                child.text = str(value) if value is not None else ""


class YAMLExporter(BaseExporter):
    """YAML file exporter."""

    async def export_to_file(
        self,
        data: AsyncGenerator[DataBatch, None],
        file_path: Path,
    ) -> ProgressInfo:
        """Export data to YAML file."""
        try:
            self._progress.status = TransferStatus.RUNNING

            # Collect all data
            all_records = []
            async for batch in data:
                for record in batch.records:
                    all_records.append(record.data)
                self.update_progress(processed=len(batch.records))
                await asyncio.sleep(0)

            # Export to YAML
            with open(file_path, 'w', encoding=self.options.encoding) as f:
                yaml.dump(
                    all_records,
                    f,
                    default_flow_style=False,
                    sort_keys=self.options.json_sort_keys,
                    allow_unicode=True,
                )

            self._progress.status = TransferStatus.COMPLETED
            return self._progress
        except Exception as e:
            self._progress.status = TransferStatus.FAILED
            self._progress.error_message = str(e)
            raise ExportError(f"Failed to export YAML: {e}") from e


def create_exporter(
    format: DataFormat,
    config: TransferConfig,
    options: Optional[ExportOptions] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> BaseExporter:
    """Create an exporter for the specified format."""
    options = options or ExportOptions()

    exporters = {
        DataFormat.CSV: CSVExporter,
        DataFormat.JSON: JSONExporter,
        DataFormat.JSONL: JSONExporter,
        DataFormat.EXCEL: ExcelExporter,
        DataFormat.XML: XMLExporter,
        DataFormat.YAML: YAMLExporter,
    }

    if format == DataFormat.JSONL:
        options.json_lines = True

    exporter_class = exporters.get(format)
    if not exporter_class:
        raise FormatError(f"No exporter available for format: {format}")

    return exporter_class(config, options, progress_callback)


async def export_data(
    data: AsyncGenerator[DataBatch, None],
    file_path: str,
    format: Optional[DataFormat] = None,
    config: Optional[TransferConfig] = None,
    options: Optional[ExportOptions] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> ProgressInfo:
    """Export data to a file."""
    path = Path(file_path)

    if format is None:
        format = detect_format(path)

    config = config or None
    exporter = create_exporter(format, config, options, progress_callback)

    return await exporter.export_to_file(data, path)


def detect_format(file_path: Path) -> DataFormat:
    """Detect file format from extension."""
    extension_map = {
        ".csv": DataFormat.CSV,
        ".json": DataFormat.JSON,
        ".jsonl": DataFormat.JSONL,
        ".xlsx": DataFormat.EXCEL,
        ".xls": DataFormat.EXCEL,
        ".xml": DataFormat.XML,
        ".yaml": DataFormat.YAML,
        ".yml": DataFormat.YAML,
    }

    ext = file_path.suffix.lower()
    if ext in extension_map:
        return extension_map[ext]

    raise FormatError(f"Unsupported file format: {ext}")


def compress_file(
    file_path: Path,
    compression: CompressionType,
    delete_original: bool = False,
) -> Path:
    """Compress a file using the specified compression type."""
    if compression == CompressionType.NONE:
        return file_path

    compressed_path = None

    try:
        if compression == CompressionType.GZIP:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)

        elif compression == CompressionType.ZIP:
            compressed_path = file_path.with_suffix('.zip')
            with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_path, file_path.name)

        elif compression == CompressionType.BZIP2:
            compressed_path = file_path.with_suffix(file_path.suffix + '.bz2')
            with open(file_path, 'rb') as f_in:
                with bz2.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)

        else:
            raise ExportError(f"Unsupported compression type: {compression}")

        if delete_original and compressed_path:
            file_path.unlink()

        return compressed_path

    except Exception as e:
        if compressed_path and compressed_path.exists():
            compressed_path.unlink()
        raise ExportError(f"Failed to compress file: {e}") from e