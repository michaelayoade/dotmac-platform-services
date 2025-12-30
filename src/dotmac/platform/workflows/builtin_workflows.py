"""
Built-in Workflow Definitions.

CRM/customer-specific workflows are removed for the control-plane baseline.
"""

from typing import Any

BUILTIN_WORKFLOWS: dict[str, dict[str, Any]] = {}


def get_all_builtin_workflows() -> list[dict[str, Any]]:
    """
    Get all built-in workflow definitions.

    Returns:
        List of workflow definition dictionaries
    """
    return list(BUILTIN_WORKFLOWS.values())


def get_workflow_by_name(name: str) -> dict[str, Any] | None:
    """
    Get a built-in workflow by name.

    Args:
        name: Workflow name

    Returns:
        Workflow definition dictionary or None
    """
    return BUILTIN_WORKFLOWS.get(name)
