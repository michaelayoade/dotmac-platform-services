import asyncio

import pytest

from dotmac.platform.communications.config import EventBusConfig
from dotmac.platform.communications.events import Event, EventBus


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handler_exception_does_not_stop_processing():
    bus = EventBus(EventBusConfig(backend="memory"))
    got = []

    def bad_handler(e: Event):
        raise RuntimeError("boom")

    def good_handler(e: Event):
        got.append(e.data.get("v"))

    await bus.start()
    try:
        bus.subscribe("evt", bad_handler)
        bus.subscribe("evt", good_handler)
        await bus.publish(Event(type="evt", data={"v": 1}))
        await asyncio.sleep(0.1)
        assert 1 in got
        # Unsubscribe non-existing handler is a no-op
        bus.unsubscribe("evt", lambda e: None)
    finally:
        await bus.stop()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_wait_for_event_timeout_returns_none():
    bus = EventBus(EventBusConfig(backend="memory"))
    await bus.start()
    try:
        res = await bus.wait_for_event("never", timeout=0.05)
        assert res is None
    finally:
        await bus.stop()

