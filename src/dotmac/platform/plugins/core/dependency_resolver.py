"""
Plugin dependency resolution system.

Handles dependency ordering, circular dependency detection, and dependency validation.
"""


from collections import deque
from dataclasses import dataclass
from typing import Any

from .exceptions import PluginDependencyError
from .plugin_base import PluginMetadata

from dotmac.platform.observability.unified_logging import get_logger
@dataclass
class DependencyNode:
    """Represents a plugin in the dependency graph."""

    plugin_key: str
    dependencies: set[str]
    optional_dependencies: set[str]
    dependents: set[str]

    # Resolution state
    visited: bool = False
    in_stack: bool = False
    resolved: bool = False

class DependencyGraph:
    """
    Dependency graph for plugin resolution.

    Manages the plugin dependency relationships and provides topological sorting.
    """

    def __init__(self):
        self.nodes: dict[str, DependencyNode] = {}
        self._logger = get_logger("plugins.dependency_graph")

    def add_plugin(self, plugin_key: str, metadata: PluginMetadata) -> None:
        """Add a plugin to the dependency graph."""
        dependencies = set(metadata.dependencies)
        optional_dependencies = set(metadata.optional_dependencies)

        # Create or update node
        if plugin_key in self.nodes:
            node = self.nodes[plugin_key]
            node.dependencies = dependencies
            node.optional_dependencies = optional_dependencies
        else:
            node = DependencyNode(
                plugin_key=plugin_key,
                dependencies=dependencies,
                optional_dependencies=optional_dependencies,
                dependents=set(),
            )
            self.nodes[plugin_key] = node

        # Update reverse dependencies
        for dep_key in dependencies | optional_dependencies:
            if dep_key not in self.nodes:
                # Create placeholder node for dependency
                self.nodes[dep_key] = DependencyNode(
                    plugin_key=dep_key,
                    dependencies=set(),
                    optional_dependencies=set(),
                    dependents=set(),
                )

            self.nodes[dep_key].dependents.add(plugin_key)

    def remove_plugin(self, plugin_key: str) -> None:
        """Remove a plugin from the dependency graph."""
        if plugin_key not in self.nodes:
            return

        node = self.nodes[plugin_key]

        # Remove from dependents
        for dep_key in node.dependencies | node.optional_dependencies:
            if dep_key in self.nodes:
                self.nodes[dep_key].dependents.discard(plugin_key)

        # Remove from dependencies
        for dependent_key in node.dependents:
            if dependent_key in self.nodes:
                dependent = self.nodes[dependent_key]
                dependent.dependencies.discard(plugin_key)
                dependent.optional_dependencies.discard(plugin_key)

        del self.nodes[plugin_key]

    def get_missing_dependencies(self, available_plugins: set[str]) -> dict[str, list[str]]:
        """Get missing required dependencies for each plugin."""
        missing_deps = {}

        for plugin_key, node in self.nodes.items():
            if plugin_key not in available_plugins:
                continue

            missing = []
            for dep_key in node.dependencies:
                if dep_key not in available_plugins:
                    missing.append(dep_key)

            if missing:
                missing_deps[plugin_key] = missing

        return missing_deps

    def detect_circular_dependencies(self) -> list[list[str]]:
        """Detect circular dependency chains."""
        cycles = []

        # Reset visit state
        for node in self.nodes.values():
            node.visited = False
            node.in_stack = False

        def dfs_cycle_detection(plugin_key: str, path: list[str]) -> None:
            if plugin_key not in self.nodes:
                return

            node = self.nodes[plugin_key]

            if node.in_stack:
                # Found a cycle - extract the cycle from the path
                cycle_start = path.index(plugin_key)
                cycle = path[cycle_start:] + [plugin_key]
                cycles.append(cycle)
                return

            if node.visited:
                return

            node.visited = True
            node.in_stack = True

            # Check dependencies (not optional dependencies for cycles)
            for dep_key in node.dependencies:
                dfs_cycle_detection(dep_key, path + [plugin_key])

            node.in_stack = False

        # Run DFS from each unvisited node
        for plugin_key in self.nodes:
            if not self.nodes[plugin_key].visited:
                dfs_cycle_detection(plugin_key, [])

        return cycles

    def topological_sort(self, available_plugins: set[str]) -> list[str]:
        """
        Perform topological sort of plugins considering dependencies.

        Returns plugins in dependency order (dependencies before dependents).
        """
        # Filter to only include available plugins
        filtered_nodes = {key: node for key, node in self.nodes.items() if key in available_plugins}

        # Calculate in-degrees (number of dependencies)
        in_degrees = {}
        for plugin_key in filtered_nodes:
            in_degrees[plugin_key] = len(
                [dep for dep in filtered_nodes[plugin_key].dependencies if dep in available_plugins]
            )

        # Initialize queue with plugins that have no dependencies
        queue = deque([plugin_key for plugin_key, degree in in_degrees.items() if degree == 0])

        sorted_plugins = []

        while queue:
            current = queue.popleft()
            sorted_plugins.append(current)

            # Update in-degrees for dependents
            if current in filtered_nodes:
                for dependent in filtered_nodes[current].dependents:
                    if dependent in in_degrees:
                        in_degrees[dependent] -= 1
                        if in_degrees[dependent] == 0:
                            queue.append(dependent)

        # Check if all plugins were sorted (no cycles)
        if len(sorted_plugins) != len(filtered_nodes):
            unsorted = set(filtered_nodes.keys()) - set(sorted_plugins)
            raise PluginDependencyError("multiple_plugins", [], list(unsorted))

        return sorted_plugins

    def get_plugin_order_groups(self, available_plugins: set[str]) -> list[list[str]]:
        """
        Get plugins grouped by dependency level.

        Plugins in the same group can be loaded in parallel.
        """
        sorted_plugins = self.topological_sort(available_plugins)

        # Group plugins by dependency level
        levels = {}
        max_level = 0

        def calculate_level(plugin_key: str) -> int:
            if plugin_key in levels:
                return levels[plugin_key]

            if plugin_key not in self.nodes:
                levels[plugin_key] = 0
                return 0

            node = self.nodes[plugin_key]
            max_dep_level = -1

            for dep_key in node.dependencies:
                if dep_key in available_plugins:
                    dep_level = calculate_level(dep_key)
                    max_dep_level = max(max_dep_level, dep_level)

            level = max_dep_level + 1
            levels[plugin_key] = level
            return level

        # Calculate levels for all plugins
        for plugin_key in sorted_plugins:
            level = calculate_level(plugin_key)
            max_level = max(max_level, level)

        # Group plugins by level
        groups = [[] for _ in range(max_level + 1)]
        for plugin_key in sorted_plugins:
            groups[levels[plugin_key]].append(plugin_key)

        return [group for group in groups if group]

class DependencyResolver:
    """
    Advanced dependency resolution system.

    Provides dependency validation, resolution ordering, and conflict detection.
    """

    def __init__(self):
        self.graph = DependencyGraph()
        self._logger = get_logger("plugins.dependency_resolver")

    def add_plugin(self, plugin_key: str, metadata: PluginMetadata) -> None:
        """Add a plugin to the dependency resolver."""
        self.graph.add_plugin(plugin_key, metadata)
        self._logger.debug(
            f"Added plugin {plugin_key} with {len(metadata.dependencies)} dependencies"
        )

    def remove_plugin(self, plugin_key: str) -> None:
        """Remove a plugin from the dependency resolver."""
        self.graph.remove_plugin(plugin_key)
        self._logger.debug(f"Removed plugin {plugin_key}")

    def validate_dependencies(self, available_plugins: set[str]) -> dict[str, Any]:
        """
        Validate all plugin dependencies.

        Returns:
            Dict with validation results including missing deps and circular deps
        """
        validation_result = {
            "valid": True,
            "missing_dependencies": {},
            "circular_dependencies": [],
            "warnings": [],
        }

        # Check for missing dependencies
        missing_deps = self.graph.get_missing_dependencies(available_plugins)
        if missing_deps:
            validation_result["valid"] = False
            validation_result["missing_dependencies"] = missing_deps

        # Check for circular dependencies
        circular_deps = self.graph.detect_circular_dependencies()
        if circular_deps:
            validation_result["valid"] = False
            validation_result["circular_dependencies"] = circular_deps

        # Check for optional dependencies that are missing
        for plugin_key in available_plugins:
            if plugin_key not in self.graph.nodes:
                continue

            node = self.graph.nodes[plugin_key]
            missing_optional = [
                dep for dep in node.optional_dependencies if dep not in available_plugins
            ]

            if missing_optional:
                validation_result["warnings"].append(
                    {
                        "plugin": plugin_key,
                        "type": "missing_optional_dependencies",
                        "dependencies": missing_optional,
                    }
                )

        return validation_result

    def resolve_load_order(self, plugin_keys: set[str]) -> list[str]:
        """
        Resolve the order in which plugins should be loaded.

        Args:
            plugin_keys: Set of plugin keys to resolve order for

        Returns:
            List of plugin keys in dependency order

        Raises:
            PluginDependencyError: If dependencies cannot be resolved
        """
        self._logger.info(f"Resolving load order for {len(plugin_keys)} plugins")

        # Validate dependencies first
        validation = self.validate_dependencies(plugin_keys)

        if not validation["valid"]:
            error_msg = "Dependency validation failed"

            if validation["missing_dependencies"]:
                missing = validation["missing_dependencies"]
                error_msg += f". Missing dependencies: {missing}"

            if validation["circular_dependencies"]:
                circular = validation["circular_dependencies"]
                error_msg += f". Circular dependencies: {circular}"

            raise PluginDependencyError(
                "dependency_resolution",
                list(validation.get("missing_dependencies", {}).keys()),
                [cycle[0] for cycle in validation.get("circular_dependencies", [])],
            )

        # Perform topological sort
        try:
            load_order = self.graph.topological_sort(plugin_keys)
            self._logger.info(f"Resolved load order: {load_order}")
            return load_order

        except Exception as e:
            raise PluginDependencyError("topological_sort", [], []) from e

    def get_parallel_load_groups(self, plugin_keys: set[str]) -> list[list[str]]:
        """
        Get plugins grouped for parallel loading.

        Plugins in the same group have no dependencies on each other
        and can be loaded simultaneously.

        Args:
            plugin_keys: Set of plugin keys to group

        Returns:
            List of groups, where each group is a list of plugin keys
        """
        self._logger.info(f"Creating parallel load groups for {len(plugin_keys)} plugins")

        groups = self.graph.get_plugin_order_groups(plugin_keys)

        self._logger.info(f"Created {len(groups)} parallel load groups")
        for i, group in enumerate(groups):
            self._logger.debug(f"Group {i}: {group}")

        return groups

    def get_shutdown_order(self, plugin_keys: set[str]) -> list[str]:
        """
        Get the order in which plugins should be shut down.

        This is the reverse of the load order to ensure dependencies
        are shut down before their dependents.

        Args:
            plugin_keys: Set of plugin keys to order for shutdown

        Returns:
            List of plugin keys in shutdown order
        """
        load_order = self.resolve_load_order(plugin_keys)
        shutdown_order = list(reversed(load_order))

        self._logger.info(f"Resolved shutdown order: {shutdown_order}")
        return shutdown_order

    def get_dependencies(self, plugin_key: str, recursive: bool = False) -> set[str]:
        """
        Get dependencies for a plugin.

        Args:
            plugin_key: Plugin to get dependencies for
            recursive: Whether to include transitive dependencies

        Returns:
            Set of dependency plugin keys
        """
        if plugin_key not in self.graph.nodes:
            return set()

        if not recursive:
            return self.graph.nodes[plugin_key].dependencies.copy()

        # Get transitive dependencies
        visited = set()
        to_visit = deque([plugin_key])

        while to_visit:
            current = to_visit.popleft()
            if current in visited or current not in self.graph.nodes:
                continue

            visited.add(current)
            node = self.graph.nodes[current]

            for dep in node.dependencies:
                if dep not in visited:
                    to_visit.append(dep)

        # Remove the original plugin from dependencies
        visited.discard(plugin_key)
        return visited

    def get_dependents(self, plugin_key: str, recursive: bool = False) -> set[str]:
        """
        Get dependents for a plugin.

        Args:
            plugin_key: Plugin to get dependents for
            recursive: Whether to include transitive dependents

        Returns:
            Set of dependent plugin keys
        """
        if plugin_key not in self.graph.nodes:
            return set()

        if not recursive:
            return self.graph.nodes[plugin_key].dependents.copy()

        # Get transitive dependents
        visited = set()
        to_visit = deque([plugin_key])

        while to_visit:
            current = to_visit.popleft()
            if current in visited or current not in self.graph.nodes:
                continue

            visited.add(current)
            node = self.graph.nodes[current]

            for dependent in node.dependents:
                if dependent not in visited:
                    to_visit.append(dependent)

        # Remove the original plugin from dependents
        visited.discard(plugin_key)
        return visited

    def can_unload_plugin(
        self, plugin_key: str, active_plugins: set[str]
    ) -> tuple[bool, list[str]]:
        """
        Check if a plugin can be safely unloaded.

        Args:
            plugin_key: Plugin to check for unloading
            active_plugins: Set of currently active plugin keys

        Returns:
            Tuple of (can_unload, blocking_dependents)
        """
        if plugin_key not in self.graph.nodes:
            return True, []

        # Get active dependents
        node = self.graph.nodes[plugin_key]
        active_dependents = [dep for dep in node.dependents if dep in active_plugins]

        # Check if any active dependents have this as a required dependency
        blocking_dependents = []
        for dependent in active_dependents:
            if dependent in self.graph.nodes:
                dep_node = self.graph.nodes[dependent]
                if plugin_key in dep_node.dependencies:  # Required dependency
                    blocking_dependents.append(dependent)

        can_unload = len(blocking_dependents) == 0
        return can_unload, blocking_dependents

    def get_dependency_stats(self) -> dict[str, Any]:
        """Get statistics about the dependency graph."""
        total_nodes = len(self.graph.nodes)
        total_edges = sum(len(node.dependencies) for node in self.graph.nodes.values())

        # Calculate dependency distribution
        dep_counts = [len(node.dependencies) for node in self.graph.nodes.values()]
        dependent_counts = [len(node.dependents) for node in self.graph.nodes.values()]

        return {
            "total_plugins": total_nodes,
            "total_dependencies": total_edges,
            "avg_dependencies_per_plugin": (total_edges / total_nodes if total_nodes > 0 else 0),
            "max_dependencies": max(dep_counts) if dep_counts else 0,
            "max_dependents": max(dependent_counts) if dependent_counts else 0,
            "plugins_with_no_dependencies": sum(1 for count in dep_counts if count == 0),
            "plugins_with_no_dependents": sum(1 for count in dependent_counts if count == 0),
        }
