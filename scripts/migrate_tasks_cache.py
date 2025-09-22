#!/usr/bin/env python3
"""Migrate tasks and cache imports to use standard libraries directly."""

import re
from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).parent.parent

# Import replacement patterns
REPLACEMENTS = [
    # Replace tasks imports
    (r'from dotmac\.platform\.tasks import .*',
     'from dotmac.platform.tasks_simple import app as celery_app'),
    (r'from \.\.tasks import .*',
     'from dotmac.platform.tasks_simple import app as celery_app'),
    (r'from \.tasks import .*',
     'from dotmac.platform.tasks_simple import app as celery_app'),

    # Replace cache imports
    (r'from dotmac\.platform\.cache import .*',
     'from dotmac.platform.caching import cache_get, cache_set, cache_delete, redis_cache'),
    (r'from \.\.cache import .*',
     'from dotmac.platform.caching import cache_get, cache_set, cache_delete, redis_cache'),
    (r'from \.cache import .*',
     'from dotmac.platform.caching import cache_get, cache_set, cache_delete, redis_cache'),

    # Replace CacheService usage
    (r'CacheService',
     '# CacheService removed - use cache functions directly'),
    (r'create_cache_service',
     '# create_cache_service removed - use cache functions directly'),
    (r'InMemoryCache',
     'TTLCache  # from cachetools'),
    (r'RedisCache',
     'redis_client  # from caching module'),

    # Replace task decorators
    (r'@background_task',
     '@celery_app.task'),
    (r'@task',
     '@celery_app.task'),
]

def update_file(filepath: Path) -> bool:
    """Update a single file with new imports."""
    try:
        content = filepath.read_text()
        original_content = content

        for pattern, replacement in REPLACEMENTS:
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

    # Filter out our new files and old modules
    python_files = [
        f for f in python_files
        if f.name not in ["tasks_simple.py", "caching.py", "migrate_tasks_cache.py"]
        and "tasks_old_to_delete" not in str(f)
        and "cache_old_to_delete" not in str(f)
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