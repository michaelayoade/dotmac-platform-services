#!/usr/bin/env python3
"""
Convert Radix UI Select components to native HTML select elements
"""

import re
import sys


def convert_selects(content):
    """Convert Select components to native select elements"""

    # Pattern to match complete Select component blocks
    # Matches: <Select ...>...</Select>
    pattern = r"<Select\s+([^>]*?)>(.*?)</Select>"

    def replace_select(match):
        props = match.group(1)
        inner_content = match.group(2)

        # Extract props using regex
        value_match = re.search(r"value=\{([^}]+)\}", props)
        onchange_match = re.search(r"onValueChange=\{([^}]+)\}", props)
        disabled_match = re.search(r"disabled=\{([^}]+)\}", props)

        if not value_match or not onchange_match:
            print("⚠️  Skipping Select - missing required props")
            return match.group(0)

        value_expr = value_match.group(1)
        onchange_expr = onchange_match.group(1)
        disabled_expr = disabled_match.group(1) if disabled_match else None

        # Extract SelectItems and convert to options
        items = re.findall(r'<SelectItem\s+value="([^"]*?)">([^<]*?)</SelectItem>', inner_content)

        if not items:
            print("⚠️  Skipping Select - no SelectItems found")
            return match.group(0)

        options_html = "\n".join(
            [f'                    <option value="{val}">{text}</option>' for val, text in items]
        )

        # Convert onChange handler
        # Replace (value) => ... with (e) => ... and value with e.target.value
        onchange_fixed = re.sub(r"\(value\)", "(e)", onchange_expr)
        onchange_fixed = re.sub(r"(?<![a-zA-Z])value(?![a-zA-Z])", "e.target.value", onchange_fixed)

        # Build native select
        select_html = "                <select\n"
        select_html += f"                  value={{{value_expr}}}\n"
        select_html += f"                  onChange={{{onchange_fixed}}}\n"
        if disabled_expr:
            select_html += f"                  disabled={{{disabled_expr}}}\n"
        select_html += '                  className="h-10 w-full rounded-md border border-slate-700 bg-slate-800 px-3 text-sm text-white"\n'
        select_html += "                >\n"
        select_html += options_html + "\n"
        select_html += "                </select>"

        print("✓ Converted Select component")
        return select_html

    # Apply replacement
    content = re.sub(pattern, replace_select, content, flags=re.DOTALL)

    # Remove Select-related imports
    content = re.sub(
        r'import\s*\{[^}]*\bSelect[^}]*\}\s*from\s*[\'"]@/components/ui/select[\'"]\s*;?\s*\n?',
        "",
        content,
    )

    return content


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert_selects.py <file-path>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content
        converted_content = convert_selects(content)

        if converted_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(converted_content)
            print(f"\n✅ File updated: {file_path}")
        else:
            print("\n⚠️  No changes made")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
