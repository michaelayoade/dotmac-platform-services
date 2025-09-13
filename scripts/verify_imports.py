"""
Verify that platform modules import correctly under the current interpreter.

Usage:
  PYTHONPATH=dotmac-platform-services/src python3 scripts/verify_imports.py

This script checks Python version (>=3.12 recommended per pyproject.toml) and
attempts to import high-level modules, printing a summary with failures.
"""

import importlib
import sys

REQUIRED_MAJOR = 3
REQUIRED_MINOR = 12

MODULES = [
    "dotmac.platform",
    "dotmac.platform.auth",
    "dotmac.platform.secrets",
    "dotmac.platform.observability",
    "dotmac.platform.monitoring.integrations",
    "dotmac.platform.monitoring.benchmarks",
    "dotmac.platform.database.session",
    "dotmac.platform.database.base",
    "dotmac.platform.tasks.decorators",
    "dotmac.platform.tenant.middleware",
    "dotmac.platform.tenant.identity",
]


def main() -> int:
    major, minor = sys.version_info[:2]
    ok = True

    if (major, minor) < (REQUIRED_MAJOR, REQUIRED_MINOR):
        print(
            f"WARNING: Python {major}.{minor} detected; project targets >= {REQUIRED_MAJOR}.{REQUIRED_MINOR}.\n"
            "Some imports may fail due to modern typing (PEP 604 | unions)."
        )

    for mod in MODULES:
        try:
            importlib.import_module(mod)
            print(f"OK   {mod}")
        except Exception as e:
            ok = False
            print(f"FAIL {mod}: {type(e).__name__}: {e}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
