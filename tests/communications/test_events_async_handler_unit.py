import asyncio

import pytest

from dotmac.platform.communications.config import EventBusConfig
from dotmac.platform.communications.events import Event, EventBus


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_handler_invoked(monkeypatch):
    bus = EventBus(EventBusConfig(backend="memory"))
    seen = []

    async def ah(e: Event):
        await asyncio.sleep(0)
        seen.append(e.data.get("n"))

    await bus.start()
    try:
        bus.subscribe("a", ah)
        await bus.publish(Event(type="a", data={"n": 7}))
        await asyncio.sleep(0.05)
        assert 7 in seen
    finally:
        await bus.stop()

