#!/usr/bin/env python3
"""Classify a Skill package into a risk tier.

Reads SKILL.md, manifest.json, agents/interface.yaml (when present),
and reports a recommended tier (R0/R1/R2/R3) along with the triggers
that fired and the gates the package must pass.

Usage:
    python3 scripts/classify_risk.py <path/to/skill>
    python3 scripts/classify_risk.py <path/to/skill> --json
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
IGNORED_DIRS = {".git", "dist", "node_modules", "__pycache__", ".venv", "venv"}

SECRET_HINT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("openai-like key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("anthropic-like key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("aws access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github token", re.compile(r"\bghp_[A-Za-z0-9]{36,}\b")),
)


def _is_doc_mention_line(rel_path: str, line: str) -> bool:
    """Mirror of secret_scan's doc-mention heuristic, used by risk classification."""
    if rel_path.endswith("/scripts/secret_scan.py") or rel_path.endswith("/scripts/classify_risk.py"):
        return True
    if "/tests/" in rel_path:
        return True
    stripped = line.strip()
    if stripped.startswith("#") or stripped.startswith("//"):
        return True
    if "re.compile" in line or "regex" in line.lower():
        return True
    lower = line.lower()
    if ("write_text" in lower or "write_string" in lower or
            "fixture" in lower or "fake_key" in lower or
            "_write_input" in lower or "_run(" in lower or
            "sample_input" in lower or "json.dumps" in lower):
        return True
    return False


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
    for line in block.splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        k, v = line.split(":", 1)
        out[k.strip()] = v.strip().strip("'|\"")
    return out


def has_secret_hints(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in (
            ".md", ".json", ".yaml", ".yml", ".py", ".js", ".ts", ".sh", ".toml"
        ):
            continue
        rel = path.relative_to(root)
        rel_str = str(rel)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line in text.splitlines():
            if _is_doc_mention_line(rel_str, line):
                continue
            for label, pattern in SECRET_HINT_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{rel} contains '{label}'")
                    break
    return findings


def find_skill_md_paths(root: Path) -> list[Path]:
    out = []
    for p in root.rglob("SKILL.md"):
        rel = p.relative_to(root)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        out.append(rel)
    return sorted(out)


def classify(root: Path) -> dict:
    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        return {
            "ok": False,
            "error": "SKILL.md missing at package root",
            "tier": None,
            "triggers": [],
            "required_gates": [],
            "missing_files": ["SKILL.md"],
        }

    fm = parse_frontmatter(read_text(skill_md))
    missing_fm = [k for k in REQUIRED_FRONTMATTER if k not in fm or not fm[k]]
    if missing_fm:
        return {
            "ok": False,
            "error": f"SKILL.md frontmatter missing fields: {missing_fm}",
            "tier": None,
            "triggers": [],
            "required_gates": [],
            "missing_files": [],
        }

    description = str(fm.get("description", ""))
    triggers_fired: list[str] = []
    triggers_fired.append("name_present")
    triggers_fired.append("description_present")

    # Detect "publish" intent from description wording
    desc_lower = description.lower()
    if any(k in desc_lower for k in ("publish", "release", "github", "npm", "npx", "registry")):
        triggers_fired.append("publish_intent")

    # Manifest signals
    manifest_path = root / "manifest.json"
    manifest: dict = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(read_text(manifest_path))
        except json.JSONDecodeError as exc:
            return {"ok": False, "error": f"manifest.json invalid: {exc}", "tier": None}

    declared_tier = str(manifest.get("risk_tier", "")).upper()

    # File-presence signals
    entries = find_skill_md_paths(root)
    if len(entries) > 1:
        triggers_fired.append("multiple_skill_entrypoints")

    secret_findings = has_secret_hints(root)
    if secret_findings:
        triggers_fired.append("secret_hints_in_files")

    # Tier decision
    if declared_tier in ("R0", "R1", "R2", "R3"):
        tier = declared_tier
        reason = f"declared in manifest.json"
    elif "publish_intent" in triggers_fired or "secret_hints_in_files" in triggers_fired:
        tier = "R3"
        reason = "publish intent or secret hints present"
    elif (root / "agents" / "interface.yaml").is_file():
        tier = "R2"
        reason = "agents/interface.yaml present"
    elif (root / "README.md").is_file() and (root / "evals" / "trigger_cases.json").is_file():
        tier = "R1"
        reason = "README + evals/trigger_cases.json present"
    else:
        tier = "R0"
        reason = "minimum frontmatter only"

    # Gates required for this tier
    gate_map = {
        "R0": ["validate_frontmatter"],
        "R1": ["validate_frontmatter", "trigger_eval", "readme_hook"],
        "R2": [
            "validate_frontmatter",
            "trigger_eval",
            "readme_hook",
            "interface_yaml",
            "risk_report",
            "secret_scan",
            "manifest_consistent",
        ],
        "R3": [
            "validate_frontmatter",
            "trigger_eval",
            "readme_hook",
            "interface_yaml",
            "risk_report",
            "secret_scan",
            "manifest_consistent",
            "version_immutability",
            "release_gate",
            "remote_version_check",
            "public_claim_guard",
        ],
    }
    required_gates = gate_map[tier]

    return {
        "ok": True,
        "tier": tier,
        "reason": reason,
        "triggers": triggers_fired,
        "required_gates": required_gates,
        "secret_findings": secret_findings,
        "skill_entrypoints": [str(p) for p in entries],
        "manifest_version": manifest.get("version"),
        "missing_files": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify a Skill package's risk tier")
    parser.add_argument("path", help="Path to the Skill package root")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    result = classify(root)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1

    if not result.get("ok"):
        print(f"FAIL: {result.get('error')}")
        return 1

    print(f"Risk tier: {result['tier']}")
    print(f"Reason: {result['reason']}")
    print(f"Triggers fired: {', '.join(result['triggers']) or '(none)'}")
    print(f"Required gates: {', '.join(result['required_gates'])}")
    if result.get("secret_findings"):
        print("Secret findings:")
        for s in result["secret_findings"]:
            print(f"  - {s}")
    if len(result.get("skill_entrypoints", [])) > 1:
        print("Multiple SKILL.md entrypoints (recursive discovery risk):")
        for e in result["skill_entrypoints"]:
            print(f"  - {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())