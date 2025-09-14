import asyncio

import pytest

from dotmac.platform.communications.config import EventBusConfig
from dotmac.platform.communications.events import Event, EventBus


@pytest.mark.unit
@pytest.mark.asyncio
async def test_eventbus_publish_subscribe_wait_memory_backend():
    bus = EventBus(EventBusConfig(backend="memory"))
    received = []

    def handler(e: Event):
        received.append((e.type, e.data.get("x")))

    await bus.start()
    try:
        bus.subscribe("demo", handler)

        evt = Event(type="demo", data={"x": 1}, source="test")
        await bus.publish(evt)

        # Also test wait_for_event with filter
        waiter = asyncio.create_task(bus.wait_for_event("demo", timeout=2.0, filter_func=lambda e: e.data.get("x") == 2))
        await bus.publish(Event(type="demo", data={"x": 2}))
        awaited = await waiter

        # Give the consumer loop a chance to handle
        await asyncio.sleep(0.1)

        assert ("demo", 1) in received
        assert awaited and awaited.data["x"] == 2

        # Unsubscribe cleans up without error
        bus.unsubscribe("demo", handler)

        # Test emit helper schedules publish
        bus.emit("demo", {"x": 3})
        await asyncio.sleep(0.1)
    finally:
        await bus.stop()

