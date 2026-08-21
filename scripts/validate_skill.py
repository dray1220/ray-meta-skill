#!/usr/bin/env python3
"""Validate a Skill package's structural contract.

Pure-stdlib + PyYAML. No provider calls. Re-runnable on any clone.

Usage:
    python3 scripts/validate_skill.py <path/to/skill>
    python3 scripts/validate_skill.py <path/to/skill> --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

REQUIRED_FRONTMATTER = ["name", "description"]
REQUIRED_MANIFEST_FIELDS = ["name", "version", "owner", "updated_at", "status"]
IGNORED_DIRS = {".git", "dist", "node_modules", "__pycache__", ".venv", "venv"}
MAX_PRODUCTION_SKILL_BYTES = 14_000

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    lines = text.splitlines()
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return {}
    block = "\n".join(lines[1:end])
    if yaml is not None:
        payload = yaml.safe_load(block) or {}
        return payload if isinstance(payload, dict) else {}
    out: dict = {}
    current = ""
    for line in block.splitlines():
        if not line.strip():
            continue
        if line.startswith(" ") and current:
            out[current] = f"{out.get(current, '')}\n{line.strip()}".strip()
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        current = k.strip()
        out[current] = v.strip().strip("'\"|")
    return out


def find_skill_md_paths(root: Path) -> list[Path]:
    out = []
    for p in root.rglob("SKILL.md"):
        rel = p.relative_to(root)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        out.append(rel)
    return sorted(out)


def validate(root: Path, strict: bool = False) -> dict:
    failures: list[str] = []
    warnings: list[str] = []

    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        return {"ok": False, "failures": ["SKILL.md missing"], "warnings": []}

    fm = parse_frontmatter(read_text(skill_md))
    for key in REQUIRED_FRONTMATTER:
        if key not in fm or not fm[key]:
            failures.append(f"SKILL.md frontmatter missing or empty: {key}")

    name = str(fm.get("name", ""))
    if name and not NAME_RE.match(name):
        failures.append(
            f"SKILL.md name '{name}' does not match ^[a-z0-9]+(-[a-z0-9]+)*$ "
            "(lowercase letters, digits, hyphens)"
        )

    desc = str(fm.get("description", ""))
    if desc and "Use when" not in desc and "use when" not in desc:
        warnings.append("description does not start with 'Use when'")

    body_bytes = len(read_text(skill_md).encode("utf-8"))
    if body_bytes > MAX_PRODUCTION_SKILL_BYTES:
        warnings.append(
            f"SKILL.md is {body_bytes} bytes (>{MAX_PRODUCTION_SKILL_BYTES}); "
            "move detail to references/"
        )

    entries = find_skill_md_paths(root)
    if len(entries) > 1:
        warnings.append(
            f"multiple SKILL.md entrypoints found: {[str(p) for p in entries]}; "
            "recursive discovery may collide"
        )

    manifest_path = root / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(read_text(manifest_path))
        except json.JSONDecodeError as exc:
            failures.append(f"manifest.json invalid JSON: {exc}")
            manifest = {}
        for key in REQUIRED_MANIFEST_FIELDS:
            if key not in manifest or not manifest[key]:
                failures.append(f"manifest.json missing field: {key}")
        if name and str(manifest.get("name", "")) != name:
            failures.append(f"manifest.json name '{manifest.get('name')}' != SKILL.md name '{name}'")
    else:
        warnings.append("manifest.json missing (required for R2+)")

    interface_path = root / "agents" / "interface.yaml"
    if interface_path.is_file():
        if yaml is None:
            warnings.append("agents/interface.yaml present but PyYAML unavailable; cannot validate")
        else:
            try:
                iface = yaml.safe_load(read_text(interface_path)) or {}
            except yaml.YAMLError as exc:
                failures.append(f"agents/interface.yaml invalid YAML: {exc}")
                iface = {}
            if isinstance(iface, dict):
                interface = iface.get("interface", iface)
                for k in ("display_name", "short_description", "default_prompt"):
                    if not interface.get(k):
                        warnings.append(f"agents/interface.yaml missing field: {k}")

    # In strict mode, warnings become failures
    if strict:
        failures.extend(warnings)

    return {
        "ok": not failures,
        "failures": failures,
        "warnings": warnings,
        "skill_md_bytes": body_bytes,
        "skill_md_entries": [str(p) for p in entries],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Skill package structure")
    parser.add_argument("path", help="Path to the Skill package root")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    result = validate(root, strict=args.strict)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())