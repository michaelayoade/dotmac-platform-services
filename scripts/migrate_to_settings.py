#!/usr/bin/env python3
"""Migrate all modules to use centralized settings.py"""

import os
import re
from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).parent.parent

# Patterns to find config imports and usages
CONFIG_PATTERNS = [
    # Direct config class imports
    (r'from \.config import (\w+Config)', 'from dotmac.platform.settings import settings'),
    (r'from \.\.config import (\w+Config)', 'from dotmac.platform.settings import settings'),
    (r'from dotmac\.platform\.\w+\.config import (\w+Config)', 'from dotmac.platform.settings import settings'),

    # Config module imports
    (r'from \. import config', 'from dotmac.platform import settings'),
    (r'from \.\. import config', 'from dotmac.platform import settings'),

    # Auth configs import
    (r'from \.configs import (RBACConfig|SessionConfig|MFAConfig|OAuthConfig)',
     'from dotmac.platform.settings import settings'),
    (r'from dotmac\.platform\.auth\.configs import (RBACConfig|SessionConfig|MFAConfig|OAuthConfig)',
     'from dotmac.platform.settings import settings'),

    # Cache config
    (r'from \.cache_config import CacheConfig', 'from dotmac.platform.settings import settings'),

    # Config instantiation patterns
    (r'(\w+)Config\(\)', r'settings.\1.model_copy()'),
    (r'(\w+)Config\(([^)]+)\)', r'settings.\1.model_copy(update={\2})'),
]

# Mapping old config names to new settings paths
CONFIG_MAPPING = {
    'DatabaseConfig': 'settings.database',
    'RedisConfig': 'settings.redis',
    'JWTConfig': 'settings.jwt',
    'CeleryConfig': 'settings.celery',
    'ObservabilityConfig': 'settings.observability',
    'RateLimitConfig': 'settings.rate_limit',
    'VaultConfig': 'settings.vault',
    'StorageConfig': 'settings.storage',
    'EmailConfig': 'settings.email',
    'WebSocketConfig': 'settings.websocket',
    'RBACConfig': 'settings.features',  # RBAC is now a feature flag
    'SessionConfig': 'settings.redis',  # Sessions use Redis settings
    'MFAConfig': 'settings.features',  # MFA is a feature flag
    'OAuthConfig': 'settings.features',  # OAuth settings merged into features
    'CORSConfig': 'settings.cors',
    'FeatureFlags': 'settings.features',
}

def update_file(filepath: Path) -> bool:
    """Update a single file to use centralized settings."""
    try:
        content = filepath.read_text()
        original_content = content

        # Apply all pattern replacements
        for pattern, replacement in CONFIG_PATTERNS:
            content = re.sub(pattern, replacement, content)

        # Replace config class usage with settings paths
        for old_name, new_path in CONFIG_MAPPING.items():
            # Replace instantiation
            content = re.sub(rf'\b{old_name}\(\)', new_path, content)
            content = re.sub(rf'\b{old_name}\(([^)]+)\)', rf'{new_path}.model_copy(update={{\1}})', content)

            # Replace type hints
            content = re.sub(rf': {old_name}\b', f': type({new_path})', content)
            content = re.sub(rf'\[{old_name}\]', f'[type({new_path})]', content)

        # Write back if changed
        if content != original_content:
            filepath.write_text(content)
            return True
        return False

    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return False

def find_python_files(directory: Path) -> list[Path]:
    """Find all Python files in directory."""
    return list(directory.rglob("*.py"))

def main():
    """Main migration function."""
    src_dir = BASE_DIR / "src" / "dotmac" / "platform"
    tests_dir = BASE_DIR / "tests"

    # Find all Python files
    python_files = find_python_files(src_dir) + find_python_files(tests_dir)

    # Filter out settings.py itself and migration script
    python_files = [
        f for f in python_files
        if f.name != "settings.py" and f.name != "migrate_to_settings.py"
    ]

    print(f"Found {len(python_files)} Python files to check")

    updated_count = 0
    for filepath in python_files:
        if update_file(filepath):
            updated_count += 1
            print(f"Updated: {filepath.relative_to(BASE_DIR)}")

    print(f"\nUpdated {updated_count} files")

    # List config files that can be removed
    config_files = list(src_dir.rglob("*config*.py"))
    config_files = [f for f in config_files if f.name != "settings.py"]

    print(f"\nConfig files that can be removed ({len(config_files)} files):")
    for filepath in config_files:
        print(f"  - {filepath.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    main()