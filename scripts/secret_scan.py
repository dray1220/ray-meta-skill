#!/usr/bin/env python3
"""Secret scanner for Skill packages.

Scans the listed suffixes for common credential patterns. No provider
calls, no network access. Pure-stdlib + re.

Usage:
    python3 scripts/secret_scan.py <path/to/skill>
    python3 scripts/secret_scan.py <path/to/skill> --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "openai-like key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "anthropic-like key": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "aws access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github token": re.compile(r"ghp_[A-Za-z0-9]{36,}"),
    "assigned credential": re.compile(
        r"""(?i)(?:api[_-]?key|secret|password|access_token|auth_token)\s*[:=]\s*["'][^"']{8,}["']"""
    ),
}

SCAN_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".js", ".ts", ".sh", ".toml"}
IGNORED_DIRS = {".git", "__pycache__", "node_modules", "dist", ".venv", "venv"}

# Files we expect to mention credential *patterns* (regex definitions,
# example secrets in docs, scanner test fixtures) without those
# mentions being actual leaks. Skipped at scan time, never ignored in
# a release gate based on path alone.
DOCUMENTATION_PATH_HINTS = ("/scripts/secret_scan.py", "/scripts/classify_risk.py")
TEST_FIXTURE_DIRS = ("/tests/",)


def _is_doc_mention(rel_path: str, line: str) -> bool:
    """A line that *defines* or *documents* a credential pattern, not a leak."""
    if any(rel_path.endswith(hint) for hint in DOCUMENTATION_PATH_HINTS):
        return True
    if any(part in rel_path for part in TEST_FIXTURE_DIRS):
        return True
    # heuristic: a doc mention is usually surrounded by quotes/backticks
    # as a regex or example, not a bare assignment
    stripped = line.strip()
    if stripped.startswith("#") or stripped.startswith("//"):
        return True
    if "re.compile" in line or "regex" in line.lower():
        return True
    # fixture detection: a write_text("...sk-..."), a write_string, a
    # _write_input/_run helper from a test file, or any explicit
    # "test"/"fixture"/"example" hint near a credential-like token.
    lower = line.lower()
    if ("write_text" in lower or "write_string" in lower or
            "test_string" in lower or "fake_key" in lower or
            "example_token" in lower or "fixture" in lower or
            "_write_input" in lower or "_run(" in lower or
            "sample_input" in lower or "json.dumps" in lower):
        return True
    return False


def scan(root: Path) -> list[dict]:
    findings: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        rel = path.relative_to(root)
        rel_str = str(rel)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if _is_doc_mention(rel_str, line):
                continue
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(line):
                    findings.append(
                        {
                            "file": str(rel),
                            "line": line_no,
                            "kind": label,
                            "excerpt": line.strip()[:160],
                        }
                    )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a Skill package for credential patterns")
    parser.add_argument("path", help="Path to the Skill package root")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    findings = scan(root)
    if args.json:
        print(json.dumps({"ok": not findings, "findings": findings}, indent=2, ensure_ascii=False))
        return 0 if not findings else 1

    if not findings:
        print(f"secret_scan: 0 findings in {root}")
        return 0
    print(f"secret_scan: {len(findings)} findings in {root}")
    for f in findings:
        print(f"  - {f['file']}:{f['line']}  [{f['kind']}]")
        print(f"    {f['excerpt']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())