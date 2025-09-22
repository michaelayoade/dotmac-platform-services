"""
Integration tests for critical paths across modules.
Tests the interaction between different components.
"""

import asyncio
import io
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest
from PIL import Image

from dotmac.platform.analytics.base import (
    CounterMetric,
    GaugeMetric,
    MetricRegistry,
)
from dotmac.platform.analytics.service import AnalyticsService
from dotmac.platform.data_transfer.base import (
    DataRecord,
    TransferConfig,
    TransferStatus,
)
from dotmac.platform.data_transfer.exporters import (
    ExportOptions,
    CSVExporter,
    JSONExporter,
)
from dotmac.platform.file_processing.base import (
    ProcessingStatus,
    ProcessingOptions,
    ProcessingResult,
)
from dotmac.platform.file_processing.processors import (
    ImageProcessor,
    DocumentProcessor,
)
from dotmac.platform.file_processing.pipeline import (
    PipelineConfig,
    PipelineStep,
    ProcessingPipeline,
)


class TestAnalyticsDataTransferIntegration:
    """Test integration between analytics and data transfer modules."""

    @pytest.fixture
    def analytics_service(self):
        """Create analytics service."""
        return AnalyticsService()

    @pytest.fixture
    def csv_exporter(self):
        """Create CSV exporter."""
        config = settings.Transfer.model_copy()
        options = ExportOptions()
        return CSVExporter(config=config, options=options)

    async def test_export_analytics_metrics_to_csv(self, analytics_service, csv_exporter):
        """Test exporting analytics metrics to CSV format."""
        # Generate metrics
        metrics = [
            CounterMetric("api_requests", 100, {"endpoint": "/users"}),
            CounterMetric("api_requests", 50, {"endpoint": "/orders"}),
            GaugeMetric("memory_usage", 75.5, {"host": "server1"}),
            GaugeMetric("cpu_usage", 45.2, {"host": "server1"}),
        ]

        # Convert metrics to data records
        records = []
        for metric in metrics:
            record = DataRecord(
                id=f"metric_{len(records)}",
                data={
                    "name": metric.name,
                    "value": metric.value,
                    "type": metric.metric_type.value,
                    "labels": metric.labels,
                    "timestamp": metric.timestamp.isoformat() if metric.timestamp else None
                }
            )
            records.append(record)

        # Export to CSV
        output = io.StringIO()
        result = await csv_exporter.export(records, output)

        assert result.status == TransferStatus.COMPLETED
        assert result.processed_records == 4

        # Verify CSV content
        output.seek(0)
        csv_content = output.read()
        assert "api_requests" in csv_content
        assert "memory_usage" in csv_content
        assert "100" in csv_content
        assert "75.5" in csv_content

    async def test_analytics_metrics_aggregation_export(self, analytics_service):
        """Test aggregating metrics and exporting aggregated data."""
        from dotmac.platform.analytics.aggregators import MetricAggregator

        # Create aggregator
        aggregator = MetricAggregator()

        # Add metrics over time
        for i in range(10):
            metric = CounterMetric(
                "requests",
                value=i * 10,
                labels={"service": "api"},
                timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            aggregator.add_metric(metric)

        # Get aggregated results
        aggregates = aggregator.get_aggregates(aggregation_type="sum")

        # Convert to exportable format
        records = []
        for metric_key, value in aggregates.items():
            record = DataRecord(
                id=f"aggregate_{metric_key}",
                data={
                    "metric": metric_key,
                    "aggregated_value": value,
                    "aggregation_type": "sum",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            records.append(record)

        # Export aggregated data
        config = settings.Transfer.model_copy()
        options = ExportOptions()
        json_exporter = JSONExporter(config=config, options=options)

        output = io.StringIO()
        result = await json_exporter.export(records, output)

        assert result.status == TransferStatus.COMPLETED
        assert len(records) > 0

        # Verify JSON content
        output.seek(0)
        import json
        data = json.loads(output.read())
        assert isinstance(data, list)
        assert data[0]["aggregation_type"] == "sum"


class TestFileProcessingAnalyticsIntegration:
    """Test integration between file processing and analytics."""

    @pytest.fixture
    def image_processor(self):
        """Create image processor."""
        return ImageProcessor()

    @pytest.fixture
    def analytics_service(self):
        """Create analytics service."""
        return AnalyticsService()

    async def test_file_processing_with_metrics_collection(self, image_processor, analytics_service):
        """Test file processing while collecting performance metrics."""
        # Create test image
        img = Image.new('RGB', (200, 200), color='blue')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            tmp.flush()

            try:
                # Process with metrics collection
                start_time = datetime.now(timezone.utc)

                result = await image_processor.process(tmp.name)

                end_time = datetime.now(timezone.utc)
                processing_time = (end_time - start_time).total_seconds()

                # Collect metrics about the processing
                metrics = [
                    CounterMetric(
                        "file_processing_requests",
                        1,
                        {"processor": "image", "status": result.status.value}
                    ),
                    GaugeMetric(
                        "file_processing_duration",
                        processing_time,
                        {"processor": "image", "file_type": "png"}
                    ),
                ]

                if result.metadata:
                    metrics.append(GaugeMetric(
                        "processed_file_size",
                        result.metadata.file_size or 0,
                        {"processor": "image"}
                    ))

                # Register metrics
                registry = MetricRegistry()
                for metric in metrics:
                    registry.register(metric)

                # Verify metrics were collected
                assert len(registry.metrics) >= 2
                processing_metrics = registry.get_by_name("file_processing_requests")
                assert len(processing_metrics) == 1
                assert processing_metrics[0].value == 1

            finally:
                import os
                os.unlink(tmp.name)

    async def test_pipeline_performance_monitoring(self):
        """Test monitoring pipeline performance with analytics."""
        from dotmac.platform.analytics.base import MetricRegistry

        # Create pipeline with performance monitoring
        async def monitored_step(file_path: str, step_name: str, registry: MetricRegistry, **kwargs):
            start_time = datetime.now(timezone.utc)

            # Simulate processing
            await asyncio.sleep(0.1)

            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            # Record performance metric
            metric = GaugeMetric(
                "pipeline_step_duration",
                duration,
                {"step": step_name, "file": Path(file_path).name}
            )
            registry.register(metric)

            return {"step": step_name, "duration": duration}

        config = settings.Pipeline.model_copy(update={
            name="monitored_pipeline",
            steps=["extract", "transform", "analyze"]
        })

        pipeline = ProcessingPipeline(config)
        registry = MetricRegistry()

        # Add monitored steps
        for step_name in ["extract", "transform", "analyze"]:
            def make_monitored_processor(step_name):
                async def processor(fp, **kw):
                    return await monitored_step(fp, step_name, registry, **kw)
                return processor

            pipeline.add_step(PipelineStep(
                name=step_name,
                processor=make_monitored_processor(step_name)
            ))

        # Execute pipeline
        result = await pipeline.execute("/path/to/test_file.txt")

        assert result.status == ProcessingStatus.COMPLETED
        assert len(result.step_results) == 3

        # Check performance metrics
        duration_metrics = registry.get_by_name("pipeline_step_duration")
        assert len(duration_metrics) == 3

        # Verify each step was monitored
        step_names = {m.labels["step"] for m in duration_metrics}
        assert step_names == {"extract", "transform", "analyze"}


class TestDataTransferFileProcessingIntegration:
    """Test integration between data transfer and file processing."""

    async def test_process_and_export_file_metadata(self):
        """Test processing files and exporting their metadata."""
        # Create test files
        test_files = []

        # Text file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
            tmp.write("Sample text content for processing")
            tmp.flush()
            test_files.append(tmp.name)

        # Image file
        img = Image.new('RGB', (100, 100), color='red')
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            tmp.flush()
            test_files.append(tmp.name)

        try:
            # Process files and collect metadata
            processed_data = []

            for file_path in test_files:
                if file_path.endswith('.txt'):
                    processor = DocumentProcessor()
                elif file_path.endswith('.png'):
                    processor = ImageProcessor()
                else:
                    continue

                result = await processor.process(file_path)

                # Convert processing result to exportable data
                file_data = {
                    "file_path": file_path,
                    "file_name": Path(file_path).name,
                    "processing_status": result.status.value,
                    "file_size": result.metadata.file_size if result.metadata else None,
                    "mime_type": result.metadata.mime_type if result.metadata else None,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                }

                if result.metadata:
                    if hasattr(result.metadata, 'width') and result.metadata.width:
                        file_data["width"] = result.metadata.width
                    if hasattr(result.metadata, 'height') and result.metadata.height:
                        file_data["height"] = result.metadata.height

                processed_data.append(file_data)

            # Export metadata to CSV
            records = [
                DataRecord(id=str(i), data=data)
                for i, data in enumerate(processed_data)
            ]

            config = settings.Transfer.model_copy()
            options = ExportOptions()
            exporter = CSVExporter(config=config, options=options)

            output = io.StringIO()
            export_result = await exporter.export(records, output)

            assert export_result.status == TransferStatus.COMPLETED
            assert export_result.processed_records == len(test_files)

            # Verify exported data
            output.seek(0)
            csv_content = output.read()
            assert "file_name" in csv_content
            assert "processing_status" in csv_content
            assert "completed" in csv_content.lower() or "failed" in csv_content.lower()

        finally:
            # Cleanup
            import os
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)

    async def test_batch_file_processing_with_progress_export(self):
        """Test batch file processing with progress data export."""
        from dotmac.platform.data_transfer.progress import ProgressTracker

        # Create multiple test files
        test_files = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as tmp:
                tmp.write(f"Test content for file {i}")
                tmp.flush()
                test_files.append(tmp.name)

        try:
            # Process files with progress tracking
            tracker = ProgressTracker()
            operation_id = "batch_processing_001"

            tracker.start_operation(operation_id)
            tracker.update_progress(operation_id, total=len(test_files))

            processor = DocumentProcessor()
            processed_results = []

            for i, file_path in enumerate(test_files):
                result = await processor.process(file_path)
                processed_results.append(result)

                # Update progress
                tracker.update_progress(
                    operation_id,
                    processed=i + 1,
                    failed=sum(1 for r in processed_results if r.status == ProcessingStatus.FAILED)
                )

            tracker.complete_operation(operation_id)

            # Export progress data
            progress_info = tracker.get_progress(operation_id)

            progress_record = DataRecord(
                id=operation_id,
                data={
                    "operation_id": operation_id,
                    "total_files": len(test_files),
                    "processed_files": progress_info.processed_records,
                    "failed_files": progress_info.failed_records,
                    "status": progress_info.status.value,
                    "completion_percentage": progress_info.progress_percentage,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            )

            # Export progress summary
            config = settings.Transfer.model_copy()
            options = ExportOptions()
            exporter = JSONExporter(config=config, options=options)

            output = io.StringIO()
            export_result = await exporter.export([progress_record], output)

            assert export_result.status == TransferStatus.COMPLETED

            # Verify progress data
            output.seek(0)
            import json
            data = json.loads(output.read())
            assert len(data) == 1
            assert data[0]["total_files"] == 5
            assert data[0]["completion_percentage"] == 100.0
            assert data[0]["status"] == "completed"

        finally:
            # Cleanup
            import os
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)


class TestCrossModuleErrorHandling:
    """Test error handling across module boundaries."""

    async def test_pipeline_with_export_failure_recovery(self):
        """Test pipeline that recovers from export failures."""
        # Create pipeline that processes files and exports results
        processed_results = []

        async def process_step(file_path: str, **kwargs):
            # Simulate file processing
            result = ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                original_file=file_path
            )
            processed_results.append(result)
            return {"processed": True, "file": file_path}

        async def export_step(file_path: str, previous_results=None, **kwargs):
            # Simulate export that might fail
            try:
                # Create data record from processing result
                record = DataRecord(
                    id=Path(file_path).stem,
                    data={
                        "file": file_path,
                        "status": "completed",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )

                # Attempt export
                config = settings.Transfer.model_copy()
                options = ExportOptions()
                exporter = CSVExporter(config=config, options=options)

                output = io.StringIO()
                result = await exporter.export([record], output)

                if result.status == TransferStatus.FAILED:
                    raise Exception("Export failed")

                return {"exported": True, "records": 1}

            except Exception as e:
                # Fallback: store results locally
                return {"exported": False, "error": str(e), "fallback": True}

        config = settings.Pipeline.model_copy(update={
            name="resilient_pipeline",
            steps=["process", "export"],
            continue_on_error=True
        })

        pipeline = ProcessingPipeline(config)

        pipeline.add_step(PipelineStep(
            name="process",
            processor=process_step,
            required=True
        ))

        pipeline.add_step(PipelineStep(
            name="export",
            processor=export_step,
            required=False  # Export is optional
        ))

        # Execute pipeline
        result = await pipeline.execute("/path/to/test_file.txt")

        # Pipeline should complete even if export fails
        assert result.status == ProcessingStatus.COMPLETED
        assert len(result.step_results) == 2

        # Process step should succeed
        process_result = result.step_results[0]
        assert process_result.status == ProcessingStatus.COMPLETED

    async def test_cross_module_validation_chain(self):
        """Test validation chain across modules."""
        from dotmac.platform.data_transfer.base import DataValidationError

        # Define validation pipeline
        validation_errors = []

        async def file_validation_step(file_path: str, **kwargs):
            """Validate file exists and is readable."""
            if not Path(file_path).exists():
                error = "File does not exist"
                validation_errors.append(error)
                raise ProcessingError(error)
            return {"file_valid": True}

        async def data_format_validation_step(file_path: str, **kwargs):
            """Validate data format."""
            # Simulate format validation
            if file_path.endswith('.invalid'):
                error = "Unsupported file format"
                validation_errors.append(error)
                raise DataValidationError(error)
            return {"format_valid": True}

        async def content_validation_step(file_path: str, **kwargs):
            """Validate file content."""
            # Simulate content validation
            if "malicious" in file_path:
                error = "Malicious content detected"
                validation_errors.append(error)
                raise DataValidationError(error)
            return {"content_valid": True}

        config = settings.Pipeline.model_copy(update={
            name="validation_pipeline",
            steps=["file_check", "format_check", "content_check"],
            continue_on_error=False  # Stop on validation failure
        })

        pipeline = ProcessingPipeline(config)

        pipeline.add_step(PipelineStep(
            name="file_check",
            processor=file_validation_step,
            required=True
        ))

        pipeline.add_step(PipelineStep(
            name="format_check",
            processor=data_format_validation_step,
            required=True
        ))

        pipeline.add_step(PipelineStep(
            name="content_check",
            processor=content_validation_step,
            required=True
        ))

        # Test with valid file
        result = await pipeline.execute("/path/to/valid_file.txt")
        assert result.status == ProcessingStatus.COMPLETED
        assert len(validation_errors) == 0

        # Test with invalid format
        validation_errors.clear()
        result = await pipeline.execute("/path/to/file.invalid")
        assert result.status == ProcessingStatus.FAILED
        assert len(validation_errors) > 0
        assert "Unsupported file format" in validation_errors

        # Test with malicious content
        validation_errors.clear()
        result = await pipeline.execute("/path/to/malicious_file.txt")
        assert result.status == ProcessingStatus.FAILED
        assert "Malicious content detected" in validation_errors


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    async def test_complete_file_processing_workflow(self):
        """Test complete workflow from file upload to analytics reporting."""
        # Simulate complete workflow
        workflow_metrics = []

        # Step 1: File upload and validation
        uploaded_files = [
            "/uploads/document1.txt",
            "/uploads/image1.png",
            "/uploads/document2.txt"
        ]

        # Step 2: Process files
        processing_results = []
        for file_path in uploaded_files:
            if file_path.endswith('.txt'):
                processor = DocumentProcessor()
            elif file_path.endswith('.png'):
                processor = ImageProcessor()
            else:
                continue

            # Create mock file for processing
            with tempfile.NamedTemporaryFile(suffix=Path(file_path).suffix, delete=False) as tmp:
                if file_path.endswith('.txt'):
                    tmp.write(b"Sample document content")
                elif file_path.endswith('.png'):
                    img = Image.new('RGB', (100, 100), color='green')
                    img.save(tmp.name)

                tmp.flush()

                try:
                    result = await processor.process(tmp.name)
                    processing_results.append({
                        "original_file": file_path,
                        "temp_file": tmp.name,
                        "result": result
                    })

                    # Collect processing metrics
                    workflow_metrics.append(CounterMetric(
                        "files_processed",
                        1,
                        {
                            "file_type": Path(file_path).suffix[1:],
                            "status": result.status.value
                        }
                    ))

                finally:
                    import os
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)

        # Step 3: Export processing results
        export_records = []
        for proc_result in processing_results:
            record_data = {
                "file_path": proc_result["original_file"],
                "processing_status": proc_result["result"].status.value,
                "file_size": proc_result["result"].metadata.file_size if proc_result["result"].metadata else 0,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }

            export_records.append(DataRecord(
                id=Path(proc_result["original_file"]).stem,
                data=record_data
            ))

        # Export to multiple formats
        config = settings.Transfer.model_copy()

        # CSV export
        csv_exporter = CSVExporter(config=config, options=ExportOptions())
        csv_output = io.StringIO()
        csv_result = await csv_exporter.export(export_records, csv_output)

        # JSON export
        json_exporter = JSONExporter(config=config, options=ExportOptions())
        json_output = io.StringIO()
        json_result = await json_exporter.export(export_records, json_output)

        # Step 4: Generate analytics report
        registry = MetricRegistry()
        for metric in workflow_metrics:
            registry.register(metric)

        # Aggregate metrics
        from dotmac.platform.analytics.aggregators import MetricAggregator
        aggregator = MetricAggregator()
        for metric in workflow_metrics:
            aggregator.add_metric(metric)

        aggregates = aggregator.get_aggregates(aggregation_type="sum")

        # Step 5: Verify complete workflow
        assert len(processing_results) == 3
        assert csv_result.status == TransferStatus.COMPLETED
        assert json_result.status == TransferStatus.COMPLETED
        assert len(workflow_metrics) == 3
        assert len(aggregates) > 0

        # Verify data consistency across formats
        csv_output.seek(0)
        csv_content = csv_output.read()
        assert "document1" in csv_content
        assert "image1" in csv_content

        json_output.seek(0)
        import json
        json_data = json.loads(json_output.read())
        assert len(json_data) == 3

        # Verify metrics
        files_processed = registry.get_by_name("files_processed")
        assert len(files_processed) == 3

    async def test_monitoring_and_alerting_workflow(self):
        """Test monitoring and alerting workflow."""
        from dotmac.platform.analytics.base import MetricRegistry
        from dotmac.platform.analytics.aggregators import MetricAggregator

        # Simulate system metrics collection
        system_metrics = [
            GaugeMetric("cpu_usage", 85.0, {"host": "server1"}),
            GaugeMetric("memory_usage", 92.0, {"host": "server1"}),
            CounterMetric("error_count", 5, {"service": "file_processor"}),
            GaugeMetric("disk_usage", 78.0, {"host": "server1"}),
        ]

        # Register metrics
        registry = MetricRegistry()
        for metric in system_metrics:
            registry.register(metric)

        # Analyze for alerts
        alerts = []

        for metric in system_metrics:
            if metric.name == "cpu_usage" and metric.value > 80:
                alerts.append({
                    "type": "HIGH_CPU",
                    "value": metric.value,
                    "threshold": 80,
                    "host": metric.labels.get("host")
                })
            elif metric.name == "memory_usage" and metric.value > 90:
                alerts.append({
                    "type": "HIGH_MEMORY",
                    "value": metric.value,
                    "threshold": 90,
                    "host": metric.labels.get("host")
                })
            elif metric.name == "error_count" and metric.value > 3:
                alerts.append({
                    "type": "HIGH_ERROR_RATE",
                    "value": metric.value,
                    "threshold": 3,
                    "service": metric.labels.get("service")
                })

        # Export alerts
        alert_records = [
            DataRecord(
                id=f"alert_{i}",
                data={
                    **alert,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "severity": "HIGH" if alert["value"] > alert["threshold"] * 1.5 else "MEDIUM"
                }
            )
            for i, alert in enumerate(alerts)
        ]

        config = settings.Transfer.model_copy()
        exporter = JSONExporter(config=config, options=ExportOptions())
        output = io.StringIO()
        result = await exporter.export(alert_records, output)

        assert result.status == TransferStatus.COMPLETED
        assert len(alerts) >= 2  # Should have CPU and memory alerts

        # Verify alert data
        output.seek(0)
        import json
        alert_data = json.loads(output.read())
        assert any(alert["type"] == "HIGH_CPU" for alert in alert_data)
        assert any(alert["type"] == "HIGH_MEMORY" for alert in alert_data)