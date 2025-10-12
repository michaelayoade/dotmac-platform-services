#!/usr/bin/env python3
"""
Validate Pydantic models across the codebase.

Checks for:
- Pydantic v2 compliance (ConfigDict usage)
- Required imports (BaseModel, Field, ConfigDict, field_validator)
- Proper field validators using @field_validator decorator
- Model configuration best practices
- Type annotations
"""

import ast
import sys
from pathlib import Path


class PydanticModelValidator(ast.NodeVisitor):
    """AST visitor to validate Pydantic models."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.has_basemodel_import = False
        self.has_field_import = False
        self.has_configdict_import = False
        self.has_field_validator_import = False
        self.current_class: str | None = None
        self.models_found = 0

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check Pydantic imports."""
        if node.module == "pydantic":
            for alias in node.names:
                if alias.name == "BaseModel":
                    self.has_basemodel_import = True
                elif alias.name == "Field":
                    self.has_field_import = True
                elif alias.name == "ConfigDict":
                    self.has_configdict_import = True
                elif alias.name == "field_validator":
                    self.has_field_validator_import = True
        # Also accept imports from core.models (project pattern)
        elif node.module and ("core.models" in node.module or node.module.endswith(".core.models")):
            for alias in node.names:
                if alias.name == "BaseModel":
                    self.has_basemodel_import = True
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check class definitions for Pydantic models."""
        # Check if this is a Pydantic model (inherits from BaseModel)
        is_pydantic_model = any(
            (isinstance(base, ast.Name) and base.id == "BaseModel") for base in node.bases
        )

        if is_pydantic_model:
            self.models_found += 1
            self.current_class = node.name
            self._validate_model(node)

        self.generic_visit(node)
        self.current_class = None

    def _validate_model(self, node: ast.ClassDef) -> None:
        """Validate a Pydantic model class."""
        has_model_config = False
        uses_config_dict = False
        has_old_config = False
        field_validators: list[str] = []

        for item in node.body:
            # Check for model_config
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                if item.target.id == "model_config":
                    has_model_config = True
                    # Check if it uses ConfigDict
                    if isinstance(item.value, ast.Call):
                        if isinstance(item.value.func, ast.Name):
                            if item.value.func.id == "ConfigDict":
                                uses_config_dict = True
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "model_config":
                        has_model_config = True
                        if isinstance(item.value, ast.Call):
                            if isinstance(item.value.func, ast.Name):
                                if item.value.func.id == "ConfigDict":
                                    uses_config_dict = True

            # Check for old Config class (Pydantic v1 pattern)
            if isinstance(item, ast.ClassDef) and item.name == "Config":
                has_old_config = True
                self.errors.append(
                    f"{self.filepath}:{node.lineno}: {node.name} uses old Pydantic v1 "
                    f"'Config' class. Use 'model_config = ConfigDict(...)' instead"
                )

            # Check for field validators
            if isinstance(item, ast.FunctionDef) and hasattr(item, "decorator_list"):
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "field_validator":
                        field_validators.append(item.name)
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            if decorator.func.id == "field_validator":
                                field_validators.append(item.name)
                                # Check for @classmethod
                                has_classmethod = any(
                                    isinstance(d, ast.Name) and d.id == "classmethod"
                                    for d in item.decorator_list
                                )
                                if not has_classmethod:
                                    self.warnings.append(
                                        f"{self.filepath}:{item.lineno}: {node.name}.{item.name} "
                                        f"should use @classmethod with @field_validator"
                                    )
                            # Check for old v1 validators
                            elif decorator.func.id == "validator":
                                self.errors.append(
                                    f"{self.filepath}:{item.lineno}: {node.name}.{item.name} "
                                    f"uses old Pydantic v1 @validator. Use @field_validator instead"
                                )

        # Recommendations
        if not has_model_config and not has_old_config:
            self.warnings.append(
                f"{self.filepath}:{node.lineno}: {node.name} has no model_config. "
                f"Consider adding ConfigDict for validation settings"
            )
        elif has_model_config and not uses_config_dict:
            self.warnings.append(
                f"{self.filepath}:{node.lineno}: {node.name} has model_config but "
                f"doesn't use ConfigDict"
            )


def validate_file(filepath: Path) -> tuple[list[str], list[str]]:
    """Validate a single Python file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=str(filepath))
        validator = PydanticModelValidator(filepath)
        validator.visit(tree)

        # Check imports if models were found
        if validator.models_found > 0:
            if not validator.has_basemodel_import:
                validator.errors.append(
                    f"{filepath}:1: File has Pydantic models but doesn't import BaseModel"
                )
            if not validator.has_configdict_import:
                validator.warnings.append(
                    f"{filepath}:1: File has Pydantic models but doesn't import ConfigDict. "
                    f"Consider adding it for model configuration"
                )

        return validator.errors, validator.warnings

    except Exception as e:
        return [f"{filepath}: Error parsing file: {e}"], []


def main() -> int:
    """Main validation function."""
    # Find all Python files in src/
    root = Path(__file__).parent.parent
    src_dir = root / "src"

    all_errors: list[str] = []
    all_warnings: list[str] = []
    files_checked = 0
    models_checked = 0

    print("Validating Pydantic models...")
    print(f"Scanning: {src_dir}")
    print()

    for py_file in src_dir.rglob("*.py"):
        # Skip __pycache__ and similar
        if "__pycache__" in str(py_file) or ".pyc" in str(py_file):
            continue

        files_checked += 1
        errors, warnings = validate_file(py_file)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

        # Count models
        try:
            with open(py_file, encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if any(
                        isinstance(base, ast.Name) and base.id == "BaseModel" for base in node.bases
                    ):
                        models_checked += 1
        except Exception:
            pass

    # Print results
    print(f"Files checked: {files_checked}")
    print(f"Pydantic models found: {models_checked}")
    print()

    if all_errors:
        print(f"❌ ERRORS ({len(all_errors)}):")
        for error in all_errors:
            print(f"  {error}")
        print()

    if all_warnings:
        print(f"⚠️  WARNINGS ({len(all_warnings)}):")
        for warning in all_warnings:
            print(f"  {warning}")
        print()

    if not all_errors and not all_warnings:
        print("✅ All Pydantic models are valid!")
        return 0
    elif not all_errors:
        print(f"✅ No errors found, but {len(all_warnings)} warnings")
        return 0
    else:
        print(f"❌ Found {len(all_errors)} errors and {len(all_warnings)} warnings")
        return 1


if __name__ == "__main__":
    sys.exit(main())
