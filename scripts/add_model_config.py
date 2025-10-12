"""Utility script to add ConfigDict definitions to Pydantic models.

This script scans Python files and ensures that every class inheriting from
``pydantic.BaseModel`` defines ``model_config = ConfigDict()``. When a file
uses ``BaseModel`` but does not import ``ConfigDict``, the import is added as
needed. The goal is to bring the codebase in line with Pydantic v2 expectations
so validation behaviour is explicit.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import libcst as cst


class ConfigDictAdder(cst.CSTTransformer):
    """Transformer that injects ``model_config = ConfigDict()`` into models."""

    def __init__(self) -> None:
        self.base_model_names: set[str] = set()
        self.pydantic_module_aliases: set[str] = set()
        self.configdict_imported: bool = False
        self.configdict_alias: str = "ConfigDict"
        self.need_configdict_import: bool = False
        self.import_updated: bool = False
        self.modified: bool = False

    def visit_Import(self, node: cst.Import) -> bool:
        for alias in node.names:
            name_value = self._name_value(alias.name)
            alias_name = alias.asname.name.value if alias.asname else name_value
            if name_value == "pydantic":
                self.pydantic_module_aliases.add(alias_name)
        return True

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        module_name = self._module_name(node.module)
        if module_name == "pydantic":
            names = self._extract_import_aliases(node.names)
            for alias in names:
                original = alias.name
                alias_name = alias.asname.name.value if alias.asname else self._name_value(original)
                original_name = self._name_value(original)
                if original_name == "BaseModel":
                    self.base_model_names.add(alias_name)
                if original_name == "ConfigDict":
                    self.configdict_imported = True
                    self.configdict_alias = alias_name
        elif module_name and module_name.endswith("core.models"):
            names = self._extract_import_aliases(node.names)
            for alias in names:
                original_name = self._name_value(alias.name)
                if original_name == "BaseModel":
                    alias_name = alias.asname.name.value if alias.asname else original_name
                    self.base_model_names.add(alias_name)
        return True

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        if node.name.value.endswith("BaseModel"):
            for base in node.bases:
                if self._is_pydantic_base_expr(base.value):
                    self.base_model_names.add(node.name.value)
                    break
        elif node.name.value == "BaseModel":
            for base in node.bases:
                if self._is_pydantic_base_expr(base.value):
                    self.base_model_names.add(node.name.value)
                    break
        return True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        if not self._inherits_pydantic_base(updated_node):
            return updated_node

        if self._has_model_config(updated_node):
            return updated_node

        assign_stmt = self._build_model_config_assignment()
        body_statements = list(updated_node.body.body)
        insert_at = 0

        if body_statements and self._is_docstring(body_statements[0]):
            insert_at = 1

        if insert_at == 1:
            assign_stmt = assign_stmt.with_changes(leading_lines=(cst.EmptyLine(),))

        body_statements.insert(insert_at, assign_stmt)
        self.need_configdict_import = True
        self.modified = True

        new_body = updated_node.body.with_changes(body=tuple(body_statements))
        return updated_node.with_changes(body=new_body)

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        if not self.modified:
            return updated_node

        if self.need_configdict_import and not self.configdict_imported:
            updated_node = self._ensure_configdict_import(updated_node)

        return updated_node

    def _ensure_configdict_import(self, module: cst.Module) -> cst.Module:
        body = list(module.body)

        for idx, stmt in enumerate(body):
            if not isinstance(stmt, cst.SimpleStatementLine):
                continue

            if len(stmt.body) != 1 or not isinstance(stmt.body[0], cst.ImportFrom):
                continue

            import_from = stmt.body[0]
            if not (
                isinstance(import_from.module, cst.Name) and import_from.module.value == "pydantic"
            ):
                continue

            names = list(self._extract_import_aliases(import_from.names))
            if any(self._name_value(alias.name) == "ConfigDict" for alias in names):
                self.configdict_imported = True
                return module

            names.append(cst.ImportAlias(name=cst.Name("ConfigDict")))
            new_import = import_from.with_changes(names=tuple(names))
            body[idx] = stmt.with_changes(body=(new_import,))
            self.configdict_imported = True
            self.import_updated = True
            return module.with_changes(body=tuple(body))

        import_stmt = cst.SimpleStatementLine(
            body=(
                cst.ImportFrom(
                    module=cst.Name("pydantic"),
                    names=(cst.ImportAlias(name=cst.Name("ConfigDict")),),
                ),
            )
        )

        insert_at = self._find_import_insertion_index(body)
        body.insert(insert_at, import_stmt)
        self.configdict_imported = True
        self.import_updated = True
        return module.with_changes(body=tuple(body))

    def _find_import_insertion_index(self, statements: list[cst.CSTNode]) -> int:
        idx = 0
        if idx < len(statements) and self._is_docstring(statements[idx]):
            idx += 1

        while idx < len(statements):
            stmt = statements[idx]
            if not isinstance(stmt, cst.SimpleStatementLine):
                break
            if not stmt.body or not isinstance(stmt.body[0], (cst.Import, cst.ImportFrom)):
                break
            idx += 1
        return idx

    def _extract_import_aliases(
        self, names: cst.ImportAlias | cst.ImportStar | tuple[cst.ImportAlias, ...]
    ) -> tuple[cst.ImportAlias, ...]:
        if isinstance(names, tuple):
            return names
        if isinstance(names, cst.ImportAlias):
            return (names,)
        return ()

    def _inherits_pydantic_base(self, node: cst.ClassDef) -> bool:
        for base in node.bases:
            if self._is_pydantic_base_expr(base.value):
                return True
        return False

    def _is_pydantic_base_expr(self, expr: cst.BaseExpression) -> bool:
        if isinstance(expr, cst.Name):
            return expr.value in self.base_model_names

        if isinstance(expr, cst.Attribute) and isinstance(expr.value, cst.Name):
            module_name = expr.value.value
            return module_name in self.pydantic_module_aliases and expr.attr.value == "BaseModel"

        return False

    def _has_model_config(self, node: cst.ClassDef) -> bool:
        for stmt in node.body.body:
            if not isinstance(stmt, cst.SimpleStatementLine):
                continue
            for small_stmt in stmt.body:
                if not isinstance(small_stmt, cst.Assign):
                    continue
                for target in small_stmt.targets:
                    if (
                        isinstance(target.target, cst.Name)
                        and target.target.value == "model_config"
                    ):
                        return True
        return False

    def _build_model_config_assignment(self) -> cst.SimpleStatementLine:
        return cst.SimpleStatementLine(
            body=(
                cst.Assign(
                    targets=(cst.AssignTarget(target=cst.Name("model_config")),),
                    value=cst.Call(func=cst.Name(self.configdict_alias)),
                ),
            )
        )

    def _is_docstring(self, node: cst.CSTNode) -> bool:
        if not isinstance(node, cst.SimpleStatementLine):
            return False
        if len(node.body) != 1:
            return False
        only_stmt = node.body[0]
        return isinstance(only_stmt, cst.Expr) and isinstance(only_stmt.value, cst.SimpleString)

    def _name_value(self, node: cst.CSTNode) -> str:
        if isinstance(node, cst.Name):
            return node.value
        if isinstance(node, cst.Attribute):
            return node.attr.value
        return ""

    def _module_name(self, module: cst.BaseExpression | None) -> str | None:
        if module is None:
            return None
        if isinstance(module, cst.Name):
            return module.value

        if isinstance(module, cst.Attribute):
            parts: list[str] = []
            current: cst.BaseExpression | None = module
            while isinstance(current, cst.Attribute):
                parts.append(current.attr.value)
                current = current.value
            if isinstance(current, cst.Name):
                parts.append(current.value)
            parts.reverse()
            return ".".join(parts)

        return None


def update_file(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    module = cst.parse_module(source)
    transformer = ConfigDictAdder()
    updated_module = module.visit(transformer)
    if transformer.modified:
        path.write_text(updated_module.code, encoding="utf-8")
        return True
    return False


def iter_python_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*.py") if not path.name.endswith("_backup.py")]


def main() -> None:
    parser = argparse.ArgumentParser(description="Add ConfigDict to Pydantic BaseModel subclasses.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("src")],
        help="Files or directories to process (defaults to src/).",
    )
    args = parser.parse_args()

    files: list[Path] = []
    for path in args.paths:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(iter_python_files(path))

    files = sorted(set(files))
    updated_files = 0

    for file_path in files:
        if update_file(file_path):
            updated_files += 1

    print(f"Updated {updated_files} file(s).")


if __name__ == "__main__":
    main()
