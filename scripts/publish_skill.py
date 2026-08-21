#!/usr/bin/env python3
"""Dry-run-only publish entry point for a Skill package.

Refuses to push anything to a remote by default. Validates version
immutability against the configured remote (if `gh` is available),
runs the release check, and prints the action plan.

For real publishing, edit this file with explicit user-approved steps
and run outside the Agent's automatic loop. The script intentionally
does not call `git push` or `gh release create` without an
explicit `--apply` flag.

Usage:
    python3 scripts/publish_skill.py <path/to/skill> --dry-run
    python3 scripts/publish_skill.py <path/to/skill> --dry-run --repo owner/name
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
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


RELEASE = load_module("ray_meta_release", SCRIPT_DIR / "release_check.py")


def gh_release_exists(repo: str, tag: str) -> bool:
    if not repo:
        return False
    try:
        completed = subprocess.run(
            ["gh", "release", "view", tag, "--repo", repo],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return completed.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Skill package (dry-run by default)")
    parser.add_argument("path", help="Path to the Skill package root")
    parser.add_argument("--repo", help="GitHub owner/repo for remote version check")
    parser.add_argument("--phase", choices=["local", "pr", "published"], default="local",
                        help="Release phase to run; default 'local' is a full dry-run")
    args = parser.parse_args()

    root = Path(args.path).resolve()

    # Always dry-run from this Skill. Real publish requires explicit orchestration
    # outside the Agent loop.
    release = RELEASE.main()
    if release != 0:
        return release

    manifest_path = root / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        version = str(manifest.get("version", ""))
        tag = f"v{version}" if version and not version.startswith("v") else version
        if args.repo and tag:
            exists = gh_release_exists(args.repo, tag)
            print(f"remote_release_check: tag={tag} repo={args.repo} exists={exists}", file=sys.stderr)
            if exists:
                print("REFUSED: tag already exists on remote. Bump version and re-run.", file=sys.stderr)
                return 1

    print(
        f"dry-run (phase={args.phase}): no remote mutations. "
        "To publish for real, follow references/publishing.md step 1-9 with explicit user approval.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())