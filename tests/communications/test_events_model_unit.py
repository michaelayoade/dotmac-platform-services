import pytest

from dotmac.platform.communications.events import Event


@pytest.mark.unit
def test_event_json_roundtrip_and_defaults():
    e = Event(type="t", data={"a": 1}, metadata={"m": 2}, source="s", correlation_id="c")
    js = e.to_json()
    e2 = Event.from_json(js)
    assert e2.type == "t" and e2.data == {"a": 1} and e2.metadata == {"m": 2}
    assert e2.source == "s" and e2.correlation_id == "c" and isinstance(e2.timestamp, float)
    # id preserved
    assert e2.id == e.id

