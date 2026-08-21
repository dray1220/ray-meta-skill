#!/usr/bin/env python3
"""Release readiness check for a Skill package (R3).

Combines: structural validation, trigger eval, secret scan, version
consistency, manifest agreement. Stops on first hard failure.

Usage:
    python3 scripts/release_check.py <path/to/skill> --phase local
    python3 scripts/release_check.py <path/to/skill> --phase local --run-tests
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_module("ray_meta_validate", SCRIPT_DIR / "validate_skill.py")
TRIGGER = load_module("ray_meta_trigger", SCRIPT_DIR / "trigger_eval.py")
SECRET = load_module("ray_meta_secret", SCRIPT_DIR / "secret_scan.py")
RISK = load_module("ray_meta_risk", SCRIPT_DIR / "classify_risk.py")


def version_consistency(root: Path) -> dict:
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return {"ok": False, "error": "manifest.json missing"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = str(manifest.get("version", ""))
    name = str(manifest.get("name", ""))

    skill_md_text = (root / "SKILL.md").read_text(encoding="utf-8")
    fm_match = False
    if name:
        # crude frontmatter name check via YAML parse
        try:
            import yaml
            block = skill_md_text.split("---", 2)[1]
            fm = yaml.safe_load(block) or {}
            fm_match = str(fm.get("name", "")) == name
        except Exception:
            fm_match = False

    return {
        "ok": bool(name and version and fm_match),
        "manifest_name": name,
        "manifest_version": version,
        "skill_md_name_matches": fm_match,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Release readiness check")
    parser.add_argument("path", help="Path to the Skill package root")
    parser.add_argument("--phase", choices=["local", "pr", "published"], default="local")
    parser.add_argument("--run-tests", action="store_true", help="Run tests/ if present")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    failures: list[str] = []
    checks: dict = {}

    validation = VALIDATOR.validate(root, strict=True)
    checks["validate"] = validation
    if not validation["ok"]:
        failures.extend(validation["failures"])

    risk = RISK.classify(root)
    checks["risk"] = risk
    if not risk.get("ok"):
        failures.append(risk.get("error", "risk classification failed"))

    tier = risk.get("tier", "R0")
    if tier not in ("R2", "R3"):
        print(f"WARNING: tier is {tier}; release_check is most useful for R2/R3.")

    cases = root / "evals" / "trigger_cases.json"
    if cases.is_file():
        from pathlib import Path as _P
        report = TRIGGER.evaluate(root, cases, root / "reports" / "trigger-eval.json")
        checks["trigger_eval"] = report["summary"]
        if not report["ok"]:
            fp = report["summary"]["false_positive"]
            fn = report["summary"]["false_negative"]
            nn = report["summary"]["near_neighbor_collision"]
            failures.append(f"trigger_eval: {fp} FP + {fn} FN + {nn} near-neighbor collisions")
    else:
        failures.append("evals/trigger_cases.json missing (required for R1+)")

    secret = SECRET.scan(root)
    checks["secret_scan"] = {"finding_count": len(secret)}
    if secret:
        failures.append(f"secret_scan: {len(secret)} findings; refuse to release")

    vc = version_consistency(root)
    checks["version_consistency"] = vc
    if not vc["ok"]:
        failures.append(f"version_consistency: {vc}")

    if args.run_tests:
        tests_dir = root / "tests"
        if tests_dir.is_dir():
            import subprocess
            completed = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-p", "test_*.py"],
                capture_output=True,
                text=True,
                cwd=str(root),
            )
            checks["tests"] = {
                "returncode": completed.returncode,
                "stderr_tail": completed.stderr[-500:] if completed.stderr else "",
            }
            if completed.returncode != 0:
                failures.append(f"unit tests failed (exit {completed.returncode})")
        else:
            checks["tests"] = {"skipped": "tests/ directory missing"}

    print(json.dumps({"ok": not failures, "phase": args.phase, "tier": tier, "checks": checks, "failures": failures}, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())