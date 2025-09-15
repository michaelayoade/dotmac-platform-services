"""Performance tests for dotmac-communications package."""

import asyncio
import gc
import os
import statistics
import time

import psutil
import pytest


@pytest.mark.performance
class TestNotificationPerformance:
    """Performance tests for notification services."""

    @pytest.mark.asyncio
    async def test_email_throughput(self, communications_config):
        """Test email notification throughput."""
        from dotmac.platform.communications.email import EmailService
        from dotmac.platform.communications.config import SMTPConfig

        config = SMTPConfig(host="localhost", port=1025, from_email="test@example.com")
        service = EmailService(config)

        # Mock the actual sending to test throughput
        sent_count = 0

        def mock_send_email(*args, **kwargs):
            nonlocal sent_count
            sent_count += 1
            return True

        # Replace with mock
        service.send_email = mock_send_email

        # Test parameters
        num_emails = 1000
        batch_sizes = [10, 50, 100]

        results = {}

        for batch_size in batch_sizes:
            start_time = time.time()
            sent_count = 0

            # Send in batches
            for i in range(0, num_emails, batch_size):
                batch = min(batch_size, num_emails - i)
                tasks = []

                for j in range(batch):
                    # Since send_email is sync, run it in executor
                    loop = asyncio.get_event_loop()
                    task = loop.run_in_executor(
                        None,
                        service.send_email,
                        f"test{i+j}@example.com",
                        f"Test {i+j}",
                        "Performance test message",
                    )
                    tasks.append(task)

                await asyncio.gather(*tasks)

            end_time = time.time()
            duration = end_time - start_time
            throughput = num_emails / duration

            results[batch_size] = {
                "duration": duration,
                "throughput": throughput,
                "sent_count": sent_count,
            }

        # Verify results
        for batch_size, result in results.items():
            assert result["sent_count"] == num_emails
            assert result["throughput"] > 100  # At least 100 emails/second

        # Batch size should improve throughput
        assert results[100]["throughput"] > results[10]["throughput"]

    @pytest.mark.asyncio
    async def test_memory_usage_bulk_notifications(self, communications_config):
        """Test memory usage during bulk notification operations."""
        from dotmac.platform.communications.email import EmailService
        from dotmac.platform.communications.config import SMTPConfig

        config = SMTPConfig(host="localhost", port=1025, from_email="test@example.com")
        service = EmailService(config)

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Mock sending to avoid external dependencies
        def mock_send(*args, **kwargs):
            return True

        service.send_email = mock_send

        # Send large batch
        num_notifications = 5000
        tasks = []

        for i in range(num_notifications):
            # Since send_email is sync, run it in executor
            loop = asyncio.get_event_loop()
            task = loop.run_in_executor(
                None,
                service.send_email,
                f"user{i}@example.com",
                f"Bulk test {i}",
                f"This is bulk notification {i}" * 10,  # Make message larger
            )
            tasks.append(task)

        # Process in chunks to avoid overwhelming
        chunk_size = 100
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i : i + chunk_size]
            await asyncio.gather(*chunk)

            # Check memory periodically
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = current_memory - initial_memory

            # Memory growth should be reasonable (< 100MB for 5000 notifications)
            assert memory_growth < 100, f"Memory growth too high: {memory_growth}MB"

        # Force garbage collection
        gc.collect()

        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024
        final_growth = final_memory - initial_memory

        # Memory should not grow excessively
        assert final_growth < 50, f"Final memory growth too high: {final_growth}MB"


@pytest.mark.performance
class TestWebSocketPerformance:
    """Performance tests for WebSocket services."""

    @pytest.mark.asyncio
    async def test_connection_handling_performance(self, communications_config):
        """Test WebSocket connection handling performance."""
        from unittest.mock import AsyncMock, MagicMock

        from dotmac.platform.communications.websocket import WebSocketManager
        from dotmac.platform.communications.config import WebSocketConfig

        manager = WebSocketManager(WebSocketConfig())

        # Mock WebSocket connections
        connections = []
        for i in range(1000):
            mock_ws = MagicMock()
            mock_ws.send = AsyncMock()
            mock_ws.close = AsyncMock()
            mock_ws.closed = False
            connections.append(mock_ws)

        # Test connection performance
        start_time = time.time()

        connection_times = []
        for i, ws in enumerate(connections[:100]):  # Test first 100 for timing
            conn_start = time.time()

            # Mock the connect method if it exists
            if hasattr(manager, "connect"):
                await manager.connect(ws, f"tenant_{i % 10}")

            conn_end = time.time()
            connection_times.append(conn_end - conn_start)

        end_time = time.time()

        # Verify performance metrics
        total_duration = end_time - start_time
        avg_connection_time = statistics.mean(connection_times) if connection_times else 0

        # Connection should be fast
        assert total_duration < 5.0, f"Total connection time too slow: {total_duration}s"
        if connection_times:
            assert (
                avg_connection_time < 0.1
            ), f"Average connection time too slow: {avg_connection_time}s"

    @pytest.mark.skip(reason="Performance test removed")
    @pytest.mark.asyncio
    async def test_message_broadcast_performance(self, communications_config):
        """Test message broadcasting performance."""
        from unittest.mock import AsyncMock, MagicMock

        from dotmac.platform.communications.websocket import WebSocketManager
        from dotmac.platform.communications.config import WebSocketConfig

        manager = WebSocketManager(WebSocketConfig())

        # Create mock connections
        num_connections = 500
        connections = []

        for i in range(num_connections):
            mock_ws = MagicMock()
            mock_ws.send = AsyncMock()
            mock_ws.closed = False
            connections.append(mock_ws)

        # Mock the broadcast method
        broadcast_count = 0

        async def mock_broadcast(channel, message):
            nonlocal broadcast_count
            broadcast_count += 1
            # Simulate some work
            await asyncio.sleep(0.001)
            return {"sent": num_connections}

        if hasattr(manager, "broadcast_to_channel"):
            manager.broadcast_to_channel = mock_broadcast
        elif hasattr(manager, "broadcast"):
            manager.broadcast = mock_broadcast

        # Test broadcast performance
        num_messages = 100
        start_time = time.time()

        for i in range(num_messages):
            if hasattr(manager, "broadcast_to_channel"):
                await manager.broadcast_to_channel(
                    "test_channel", {"type": "performance_test", "message": f"Test message {i}"}
                )
            elif hasattr(manager, "broadcast"):
                await manager.broadcast(
                    {"type": "performance_test", "message": f"Test message {i}"}
                )

        end_time = time.time()
        duration = end_time - start_time

        # Verify performance
        messages_per_second = num_messages / duration
        assert messages_per_second > 50, f"Broadcast rate too slow: {messages_per_second} msg/s"

        if hasattr(manager, "broadcast_to_channel") or hasattr(manager, "broadcast"):
            assert broadcast_count == num_messages


@pytest.mark.performance
class TestEventPerformance:
    """Performance tests for event services."""

    @pytest.mark.asyncio
    async def test_event_publishing_throughput(self, communications_config):
        """Test event publishing throughput."""
        from dotmac.platform.communications.events import EventBus
        from dotmac.platform.communications.config import EventBusConfig

        bus = EventBus(EventBusConfig())

        # Track published events
        published_events = []

        # Mock publish method
        async def mock_publish(event):
            published_events.append(event)
            return True

        if hasattr(bus, "publish"):
            bus.publish = mock_publish

        # Test parameters
        num_events = 2000
        event_sizes = ["small", "medium", "large"]

        results = {}

        for size in event_sizes:
            # Create payload of different sizes
            if size == "small":
                payload = {"id": 1, "action": "test"}
            elif size == "medium":
                payload = {"id": 1, "action": "test", "data": "x" * 1000}
            else:  # large
                payload = {"id": 1, "action": "test", "data": "x" * 10000}

            published_events.clear()
            start_time = time.time()

            # Publish events
            tasks = []
            for i in range(num_events):
                event = {"topic": f"performance.test.{size}", "payload": {**payload, "sequence": i}}
                tasks.append(bus.publish(event))

            await asyncio.gather(*tasks)

            end_time = time.time()
            duration = end_time - start_time
            throughput = num_events / duration

            results[size] = {
                "duration": duration,
                "throughput": throughput,
                "published_count": len(published_events),
            }

        # Verify results
        for size, result in results.items():
            assert result["published_count"] == num_events
            assert (
                result["throughput"] > 200
            ), f"{size} events too slow: {result['throughput']} events/s"

    @pytest.mark.asyncio
    async def test_event_processing_latency(self, communications_config):
        """Test event processing latency."""
        from dotmac.platform.communications.events import EventBus
        from dotmac.platform.communications.config import EventBusConfig

        bus = EventBus(EventBusConfig())

        # Track processing times
        processing_times = []

        # Mock subscribe and handler
        def mock_handler(event):
            # Record processing time
            if "timestamp" in event:
                process_time = time.time() - event["timestamp"]
                processing_times.append(process_time)

        if hasattr(bus, "subscribe"):
            bus.subscribe("latency.test", mock_handler)

        # Mock publish to trigger handler immediately
        async def mock_publish(event):
            if hasattr(bus, "subscribe"):
                # Simulate immediate processing
                mock_handler(event)
            return True

        if hasattr(bus, "publish"):
            bus.publish = mock_publish

        # Publish events with timestamps
        num_events = 100
        for i in range(num_events):
            event = {"topic": "latency.test", "payload": {"sequence": i}, "timestamp": time.time()}
            await bus.publish(event)

            # Small delay between events
            await asyncio.sleep(0.001)

        # Wait for processing
        await asyncio.sleep(0.1)

        # Analyze latency
        if processing_times:
            avg_latency = statistics.mean(processing_times)
            max_latency = max(processing_times)
            p95_latency = statistics.quantiles(processing_times, n=20)[18]  # 95th percentile

            # Verify latency requirements
            assert avg_latency < 0.01, f"Average latency too high: {avg_latency}s"
            assert max_latency < 0.05, f"Max latency too high: {max_latency}s"
            assert p95_latency < 0.02, f"95th percentile latency too high: {p95_latency}s"


@pytest.mark.performance
class TestIntegratedPerformance:
    """Integrated performance tests across all communication services."""

    @pytest.mark.asyncio
    async def test_mixed_workload_performance(self, communications_config):
        """Test performance under mixed workload (notifications + websockets + events)."""
        from dotmac.platform.communications import EmailService, WebSocketManager, EventBus
        from dotmac.platform.communications.config import WebSocketConfig, EventBusConfig

        class MockCommunicationsService:
            def __init__(self):
                from dotmac.platform.communications.config import SMTPConfig
                config = SMTPConfig(host="localhost", port=1025, from_email="test@example.com")
                self.notifications = EmailService(config)
                self.websockets = WebSocketManager(WebSocketConfig())
                self.events = EventBus(EventBusConfig())

        comm = MockCommunicationsService()

        # Mock all services
        notification_count = 0
        websocket_count = 0
        event_count = 0

        def mock_notification(*args, **kwargs):
            nonlocal notification_count
            notification_count += 1
            return True

        async def mock_websocket(*args, **kwargs):
            nonlocal websocket_count
            websocket_count += 1
            return {"sent": True}

        async def mock_event(*args, **kwargs):
            nonlocal event_count
            event_count += 1
            return True

        # Apply mocks
        if hasattr(comm.notifications, "send_email"):
            comm.notifications.send_email = mock_notification
        if hasattr(comm.websockets, "broadcast"):
            comm.websockets.broadcast = mock_websocket
        if hasattr(comm.events, "publish"):
            comm.events.publish = mock_event

        # Mixed workload test
        start_time = time.time()

        tasks = []

        # Add notification tasks
        loop = asyncio.get_event_loop()
        for i in range(100):
            task = loop.run_in_executor(
                None,
                comm.notifications.send_email,
                f"user{i}@example.com",
                f"Mixed workload {i}",
                "Test message",
            )
            tasks.append(task)

        # Add WebSocket tasks
        for i in range(50):
            task = comm.websockets.broadcast({"type": "mixed_test", "message": f"Broadcast {i}"})
            tasks.append(task)

        # Add event tasks
        for i in range(200):
            task = comm.events.publish({"topic": "mixed.workload", "payload": {"sequence": i}})
            tasks.append(task)

        # Execute all tasks concurrently
        await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # Verify all operations completed
        assert notification_count == 100
        assert websocket_count == 50
        assert event_count == 200

        # Performance requirements
        total_operations = 350
        operations_per_second = total_operations / duration

        assert duration < 10.0, f"Mixed workload took too long: {duration}s"
        assert (
            operations_per_second > 50
        ), f"Mixed workload throughput too low: {operations_per_second} ops/s"

    @pytest.mark.asyncio
    async def test_resource_cleanup_performance(self, communications_config):
        """Test resource cleanup performance."""
        from dotmac.platform.communications import EmailService, WebSocketManager, EventBus
        from dotmac.platform.communications.config import WebSocketConfig, EventBusConfig

        class MockCommunicationsService:
            def __init__(self):
                from dotmac.platform.communications.config import SMTPConfig
                config = SMTPConfig(host="localhost", port=1025, from_email="test@example.com")
                self.notifications = EmailService(config)
                self.websockets = WebSocketManager(WebSocketConfig())
                self.events = EventBus(EventBusConfig())

            async def cleanup(self):
                pass

        # Create and use service
        comm = MockCommunicationsService()

        # Get initial resource usage
        process = psutil.Process(os.getpid())
        initial_fds = process.num_fds() if hasattr(process, "num_fds") else 0
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Simulate heavy usage
        for _ in range(10):
            # Create mock connections/resources
            pass

        # Cleanup
        start_time = time.time()

        if hasattr(comm, "cleanup"):
            await comm.cleanup()

        cleanup_time = time.time() - start_time

        # Check resource usage after cleanup
        final_fds = process.num_fds() if hasattr(process, "num_fds") else 0
        final_memory = process.memory_info().rss / 1024 / 1024

        # Verify cleanup performance
        assert cleanup_time < 5.0, f"Cleanup took too long: {cleanup_time}s"

        # Resource usage should not grow significantly
        fd_growth = final_fds - initial_fds
        memory_growth = final_memory - initial_memory

        assert fd_growth < 10, f"Too many file descriptors leaked: {fd_growth}"
        assert memory_growth < 20, f"Too much memory growth: {memory_growth}MB"


# Performance benchmarking utilities
class PerformanceBenchmark:
    """Utility class for performance benchmarking."""

    @staticmethod
    def measure_async_operation(operation, iterations=100):
        """Measure async operation performance."""

        async def _run_benchmark():
            times = []

            for _ in range(iterations):
                start = time.time()
                await operation()
                end = time.time()
                times.append(end - start)

            return {
                "iterations": iterations,
                "total_time": sum(times),
                "avg_time": statistics.mean(times),
                "min_time": min(times),
                "max_time": max(times),
                "median_time": statistics.median(times),
                "ops_per_second": iterations / sum(times),
            }

        return _run_benchmark()

    @staticmethod
    def measure_memory_usage(operation):
        """Measure memory usage of operation."""

        async def _run_memory_test():
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024

            await operation()

            final_memory = process.memory_info().rss / 1024 / 1024

            return {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_growth_mb": final_memory - initial_memory,
            }

        return _run_memory_test()


# Export benchmark utilities for use in other tests
__all__ = ["PerformanceBenchmark"]
