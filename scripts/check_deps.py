"""
Check for required Python packages.

Usage:
  poetry run python scripts/check_deps.py runtime
  poetry run python scripts/check_deps.py dev

runtime: required deps must exist, exit nonzero if missing
dev: dev/test deps; print warnings if missing
"""

import importlib
import sys

RUNTIME = [
    "pydantic",
    "fastapi",
    "httpx",
    "sqlalchemy",
    "aiohttp",
    "opentelemetry.sdk",
    "structlog",
    "jwt",  # PyJWT is installed as 'jwt'
    "cryptography",
]

DEV = [
    "pytest",
    "pytest_asyncio",
    "pytest_cov",
    "ruff",
    "black",
    "mypy",
    "bandit",
]

OPTIONAL = ["fakeredis", "mutmut", "pip_audit"]


def check(mods: list[str], strict: bool) -> int:
    ok = True
    for m in mods:
        try:
            importlib.import_module(m)
            print(f"✓ {m}")
        except Exception as e:
            ok = False
            msg = f"Missing or failing import: {m}: {type(e).__name__}: {e}"
            if strict:
                print(msg)
            else:
                print(f"! {msg}")
    return 0 if ok or not strict else 1


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {"runtime", "dev"}:
        print("Usage: python scripts/check_deps.py [runtime|dev]")
        return 2

    mode = sys.argv[1]
    if mode == "runtime":
        rc = check(RUNTIME, strict=True)
        return rc
    else:
        _ = check(DEV, strict=False)
        print("Optional (skipped if missing):")
        _ = check(OPTIONAL, strict=False)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
