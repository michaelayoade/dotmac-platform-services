#!/usr/bin/env python3
"""Migrate observability and audit imports to use standard libraries directly."""

import re
from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).parent.parent

# Import replacement patterns
REPLACEMENTS = [
    # Replace unified_logging imports with our new simple logging
    (r'from dotmac\.platform\.observability\.unified_logging import get_logger',
     'from dotmac.platform.logging import get_logger'),
    (r'from \.\.observability\.unified_logging import get_logger',
     'from dotmac.platform.logging import get_logger'),
    (r'from \.\.\.observability\.unified_logging import get_logger',
     'from dotmac.platform.logging import get_logger'),

    # Replace audit_trail imports with logging
    (r'from dotmac\.platform\.audit_trail import .*',
     'from dotmac.platform.logging import log_audit_event'),
    (r'from \.\.audit_trail import .*',
     'from dotmac.platform.logging import log_audit_event'),

    # Replace observability imports with telemetry/logging
    (r'from dotmac\.platform\.observability import (\w+)',
     lambda m: f'# TODO: Update {m.group(1)} to use telemetry or logging directly'),

    # Replace AuditAggregator usage
    (r'AuditAggregator',
     '# AuditAggregator removed - use log_audit_event'),
    (r'get_audit_aggregator',
     '# get_audit_aggregator removed - use log_audit_event'),

    # Replace audit event logging
    (r'audit_aggregator\.log_event\(',
     'log_audit_event('),
    (r'self\.audit\.log_event\(',
     'log_audit_event('),
]

def update_file(filepath: Path) -> bool:
    """Update a single file with new imports."""
    try:
        content = filepath.read_text()
        original_content = content

        for pattern, replacement in REPLACEMENTS:
            if callable(replacement):
                content = re.sub(pattern, replacement, content)
            else:
                content = re.sub(pattern, replacement, content)

        if content != original_content:
            filepath.write_text(content)
            return True
        return False

    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return False

def main():
    """Main migration function."""
    src_dir = BASE_DIR / "src" / "dotmac" / "platform"
    tests_dir = BASE_DIR / "tests"

    # Find all Python files
    python_files = list(src_dir.rglob("*.py")) + list(tests_dir.rglob("*.py"))

    # Filter out our new files
    python_files = [
        f for f in python_files
        if f.name not in ["telemetry.py", "logging.py", "migrate_observability.py"]
    ]

    print(f"Found {len(python_files)} Python files to check")

    updated_count = 0
    for filepath in python_files:
        if update_file(filepath):
            updated_count += 1
            print(f"Updated: {filepath.relative_to(BASE_DIR)}")

    print(f"\nUpdated {updated_count} files")

if __name__ == "__main__":
    main()