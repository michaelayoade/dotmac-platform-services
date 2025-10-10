#!/usr/bin/env python3
"""
Validate API router tags follow Title Case convention.

This script validates that all API router tags (used in FastAPI @router decorators
and APIRouter() constructors) follow the Title Case with Spaces convention.

Internal tags (cache keys, plugin metadata) are excluded from validation.
"""

import re
import subprocess
import sys


def get_api_router_tags():
    """Extract tags from APIRouter() declarations and @router decorator endpoints."""
    # Find tags in APIRouter declarations
    result = subprocess.run(
        [
            "rg",
            r"(router|APIRouter)\(.*tags=\[",
            "src/dotmac/platform",
            "--type",
            "py",
            "-A",
            "0",
        ],
        capture_output=True,
        text=True,
    )

    # Also find tags in @router.* endpoint decorators
    result2 = subprocess.run(
        [
            "rg",
            r"@router\.(get|post|put|patch|delete)\(.*tags=\[",
            "src/dotmac/platform",
            "--type",
            "py",
            "-A",
            "0",
        ],
        capture_output=True,
        text=True,
    )

    tags = set()
    for line in result.stdout.split("\n") + result2.stdout.split("\n"):
        # Extract tags from the line
        match = re.search(r"tags=\[(.*?)\]", line)
        if match:
            tag_content = match.group(1)
            # Extract individual tags from the list
            for tag in re.findall(r'"([^"]+)"', tag_content):
                # Exclude internal tags (cache keys, plugin metadata)
                if not _is_internal_tag(tag):
                    tags.add(tag)

    return tags


def _is_internal_tag(tag: str) -> bool:
    """Check if a tag is an internal tag (cache key, plugin metadata)."""
    # Cache key patterns
    if ":" in tag:  # e.g., "tenant:{tenant_id}", "product:{product_id}"
        return True
    if "{" in tag:  # e.g., f-string cache keys
        return True

    # Internal lowercase tags used in cache/plugins
    internal_tags = {
        "pricing_rules",
        "product_list",
        # Plugin metadata tags
        "messaging",
        "whatsapp",
        "notifications",
        "meta",
        "business-api",
    }

    return tag in internal_tags


def validate_tag_format(tag: str) -> tuple[bool, str]:
    """
    Validate a single tag follows Title Case convention.

    Returns:
        (is_valid, error_message)
    """
    # Allow hierarchical tags with " - " separator
    parts = tag.split(" - ")

    for part in parts:
        # Check if part is Title Case
        words = part.split()
        for word in words:
            # Skip acronyms (all uppercase)
            if word.isupper() and len(word) > 1:
                continue

            # Check first character is uppercase
            if not word[0].isupper():
                return (
                    False,
                    f"'{tag}' is not Title Case (word '{word}' should start with uppercase)",
                )

            # Check remaining characters follow title case
            # (lowercase, except for acronyms/names like "API", "ID", etc.)
            if len(word) > 1 and word[1:].isupper() and len(word) > 3:
                # Probably not an intentional acronym if > 3 chars
                return False, f"'{tag}' has word '{word}' in all caps (should be Title Case)"

        # Check for kebab-case
        if "-" in part and " - " not in tag:
            return False, f"'{tag}' uses kebab-case (should use Title Case with spaces)"

        # Check for snake_case
        if "_" in part:
            return False, f"'{tag}' uses snake_case (should use Title Case with spaces)"

    return True, ""


def main():
    """Main validation logic."""
    print("=" * 70)
    print("API Router Tag Validation")
    print("=" * 70)

    # Get all API router tags
    tags = get_api_router_tags()

    print(f"\nFound {len(tags)} API router tags\n")

    # Validate each tag
    invalid_tags = []
    for tag in sorted(tags):
        is_valid, error_msg = validate_tag_format(tag)
        if not is_valid:
            invalid_tags.append((tag, error_msg))

    # Report results
    if invalid_tags:
        print("❌ VALIDATION FAILED\n")
        print(f"Found {len(invalid_tags)} invalid tag(s):\n")
        for tag, error in invalid_tags:
            print(f"  • {error}")
        print("\n" + "=" * 70)
        sys.exit(1)
    else:
        print("✅ ALL API ROUTER TAGS VALID\n")
        print("All tags follow Title Case with Spaces convention:")
        for tag in sorted(tags):
            print(f"  • {tag}")
        print("\n" + "=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()
