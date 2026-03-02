#!/usr/bin/env python3
"""Add structured YAML frontmatter to all rules/*.md and agents/*.md files.

Adds (or updates) frontmatter with: id, version, category, tags, deprecated.
Skips files that already have complete frontmatter.
"""

from __future__ import annotations
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
TARGET_DIRS = ["rules", "agents"]
VERSION = "1.0.0"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def infer_category(path: Path) -> str:
    """Infer category from directory structure."""
    parts = path.relative_to(VAULT_ROOT).parts
    if len(parts) >= 2:
        return parts[1]  # subdirectory within rules/agents
    return parts[0] if parts else "general"


def infer_tags(path: Path, content: str) -> list[str]:
    """Infer tags from path and content."""
    tags = []
    name = path.stem
    parent = path.parent.name

    # From directory
    if parent not in ("rules", "agents", "."):
        tags.append(slugify(parent))

    # From filename hints
    for keyword in ("tdd", "spec", "security", "workflow", "typescript", "python", "go", "css", "testing"):
        if keyword in name.lower() or keyword in content[:500].lower():
            if keyword not in tags:
                tags.append(keyword)
            break

    return tags[:5]  # limit to 5


def parse_existing_frontmatter(content: str) -> tuple[dict, str]:
    """Extract existing YAML frontmatter if present."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end == -1:
        return {}, content
    yaml_block = content[3:end].strip()
    body = content[end + 4:].lstrip("\n")

    # Simple key: value parser (no nested, no lists)
    data = {}
    for line in yaml_block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                items = [i.strip().strip('"').strip("'") for i in v[1:-1].split(",")]
                data[k] = [i for i in items if i]
            elif v.lower() == "true":
                data[k] = True
            elif v.lower() == "false":
                data[k] = False
            else:
                data[k] = v
    return data, body


def build_frontmatter(path: Path, existing: dict, content: str) -> str:
    """Build complete frontmatter dict, preserving existing fields."""
    rel = path.relative_to(VAULT_ROOT)
    top_dir = rel.parts[0]  # rules or agents
    file_id = f"{top_dir}/{slugify(path.stem)}"

    fm = {
        "id": existing.get("id") or file_id,
        "version": existing.get("version") or VERSION,
        "category": existing.get("category") or infer_category(path),
        "tags": existing.get("tags") or infer_tags(path, content),
        "deprecated": existing.get("deprecated", False),
    }

    # Preserve any other existing fields (e.g. paths:)
    for k, v in existing.items():
        if k not in fm:
            fm[k] = v

    lines = ["---"]
    # Ordered important keys first
    for key in ("id", "version", "category", "tags", "deprecated"):
        val = fm.pop(key, None)
        if isinstance(val, list):
            if val:
                lines.append(f"{key}:")
                for item in val:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: []")
        elif isinstance(val, bool):
            lines.append(f"{key}: {str(val).lower()}")
        else:
            lines.append(f"{key}: {val}")
    # Remaining keys
    for key, val in fm.items():
        if isinstance(val, list):
            lines.append(f"{key}:")
            for item in val:
                lines.append(f"  - {item}")
        elif isinstance(val, bool):
            lines.append(f"{key}: {str(val).lower()}")
        else:
            lines.append(f"{key}: {val}")
    lines.append("---")
    return "\n".join(lines)


def process_file(path: Path) -> bool:
    """Add or update frontmatter. Returns True if file was modified."""
    content = path.read_text(encoding="utf-8")
    existing, body = parse_existing_frontmatter(content)

    # Check if all required fields present
    required = {"id", "version", "category", "tags", "deprecated"}
    if required.issubset(existing.keys()):
        return False  # Already complete

    fm = build_frontmatter(path, existing, content)
    new_content = fm + "\n\n" + body.lstrip("\n")
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main() -> int:
    modified = 0
    skipped = 0
    for dir_name in TARGET_DIRS:
        target_dir = VAULT_ROOT / dir_name
        if not target_dir.is_dir():
            continue
        for md_file in sorted(target_dir.rglob("*.md")):
            try:
                changed = process_file(md_file)
                if changed:
                    rel = md_file.relative_to(VAULT_ROOT)
                    print(f"  updated: {rel}")
                    modified += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  ERROR {md_file}: {e}", file=sys.stderr)

    print(f"\nDone: {modified} files updated, {skipped} already complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
