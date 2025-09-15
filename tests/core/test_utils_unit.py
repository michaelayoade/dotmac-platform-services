import re
from datetime import datetime, timezone, timedelta

import pytest

from dotmac.platform.core.utils import (
    ensure_in,
    ensure_range,
    generate_id,
    hash_dict,
    hash_string,
    truncate,
    isoformat,
    is_email,
    is_url,
    is_uuid,
    new_uuid,
    new_uuid_hex,
    sanitize_text,
    slugify,
    timestamp,
    to_utc,
    utcnow,
)


@pytest.mark.unit
def test_uuid_helpers_and_generate_id():
    u1 = new_uuid()
    u2 = new_uuid()
    assert is_uuid(u1)
    assert is_uuid(u2)
    assert u1 != u2

    hx = new_uuid_hex()
    assert re.fullmatch(r"[0-9a-f]{32}", hx)

    gid = generate_id("x-")
    assert gid.startswith("x-") and len(gid) > 2 and is_uuid(gid.split("x-")[-1])


@pytest.mark.unit
def test_time_helpers():
    now = utcnow()
    assert now.tzinfo is timezone.utc

    # to_utc converts naive to aware (assume naive is UTC)
    naive = datetime(2024, 1, 1, 12, 0, 0)
    aware = to_utc(naive)
    assert aware.tzinfo is timezone.utc
    assert aware.replace(tzinfo=None) == naive

    # isoformat returns ISO string with timezone
    iso = isoformat()
    assert "+00:00" in iso

    t1 = timestamp()
    t2 = timestamp()
    assert t2 >= t1


@pytest.mark.unit
def test_string_helpers():
    assert slugify("Hello World_test--OK!") == "hello-world-test-ok"
    assert slugify("  MULTI   Spaces__Here  ") == "multi-spaces-here"

    assert truncate("short", 10) == "short"
    assert truncate("exact", 5) == "exact"
    assert truncate("long-text", 4) == "l..."
    # Edge where max_length <= len(suffix)
    assert truncate("abcdef", 3, suffix="....") == "abc"

    dirty = "\x00Hello\n\tWorld\r  !  "
    # Control chars are removed, remaining whitespace normalized
    assert sanitize_text(dirty) == "HelloWorld !"


@pytest.mark.unit
def test_hash_and_validation_helpers():
    # Hash lengths and determinism
    assert len(hash_string("abc", "sha256")) == 64
    assert len(hash_string("abc", "sha512")) == 128
    assert hash_string("abc", "sha256") == hash_string("abc", "sha256")

    # hash_dict stable across key order
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2, "a": 1}
    assert hash_dict(d1) == hash_dict(d2)

    # Validators
    assert is_uuid(new_uuid())
    assert not is_uuid("not-a-uuid")

    assert is_email("user@example.com")
    assert not is_email("user@@example..com")

    assert is_url("http://localhost:8000")
    assert is_url("https://1.2.3.4/path")
    assert not is_url("ftp://example.com")

    # Range utilities
    assert ensure_range(5, min_value=10) == 10
    assert ensure_range(50, max_value=10) == 10
    assert ensure_range(5, 0, 10) == 5

    assert ensure_in("x", ["a", "x", "b"]) == "x"
    with pytest.raises(ValueError):
        ensure_in("z", ["a", "x", "b"])
