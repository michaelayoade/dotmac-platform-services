import json
import ast
from pathlib import Path
from collections import defaultdict
import os

# Generate coverage json (ignore exit code)
os.system("poetry run coverage json 2>/dev/null")

with open("coverage.json") as f:
    coverage_data = json.load(f)

# Group by module
modules = defaultdict(lambda: {"total": 0, "untested": 0, "partial": 0})

for file_path, file_data in coverage_data["files"].items():
    if not file_path.startswith("src/dotmac/platform/"):
        continue
    
    # Get module name
    module = file_path.replace("src/dotmac/platform/", "").split("/")[0]
    
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())
        
        executed_lines = set(file_data.get("executed_lines", []))
        missing_lines = set(file_data.get("missing_lines", []))
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    continue
                    
                func_lines = set(range(node.lineno, node.end_lineno + 1) if hasattr(node, 'end_lineno') else [node.lineno])
                func_executed = func_lines & executed_lines
                func_missing = func_lines & missing_lines
                
                modules[module]["total"] += 1
                
                if not func_executed:
                    modules[module]["untested"] += 1
                elif func_missing:
                    modules[module]["partial"] += 1
    except:
        pass

# Print summary
print("=== FUNCTIONS BY MODULE ===")
print(f"{'Module':<20} {'Total':>8} {'Untested':>10} {'Partial':>8} {'Tested':>8} {'Coverage':>10}")
print("-" * 70)

total_all = sum(m["total"] for m in modules.values())
untested_all = sum(m["untested"] for m in modules.values())
partial_all = sum(m["partial"] for m in modules.values())

for module, stats in sorted(modules.items()):
    tested = stats["total"] - stats["untested"] - stats["partial"]
    coverage = (tested / stats["total"] * 100) if stats["total"] > 0 else 0
    print(f"{module:<20} {stats['total']:>8} {stats['untested']:>10} {stats['partial']:>8} {tested:>8} {coverage:>9.1f}%")

print("-" * 70)
tested_all = total_all - untested_all - partial_all
print(f"{'TOTAL':<20} {total_all:>8} {untested_all:>10} {partial_all:>8} {tested_all:>8} {tested_all/total_all*100 if total_all > 0 else 0:>9.1f}%")
print()
print(f"🔴 Untested functions: {untested_all} ({untested_all/total_all*100:.1f}%)")
print(f"🟡 Partially tested: {partial_all} ({partial_all/total_all*100:.1f}%)")
print(f"🟢 Fully tested: {tested_all} ({tested_all/total_all*100:.1f}%)")

