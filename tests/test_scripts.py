#!/usr/bin/env python3
"""Unit tests for ray-meta-skill bundled scripts.

Run with:  python3 -m unittest discover -s tests -p 'test_*.py'
"""

import json
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"


def _load(name):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATE = _load("validate_skill")
TRIGGER = _load("trigger_eval")
SECRET = _load("secret_scan")
RISK = _load("classify_risk")


def _make_skill(tmpdir: Path, *, with_readme: bool = True, with_evals: bool = True, with_interface: bool = False, with_manifest: bool = True, manifest_name: str = "test-skill") -> Path:
    (tmpdir / "SKILL.md").write_text(
        "---\n"
        f"name: {manifest_name}\n"
        "description: Use when turning a workflow into a hermes skill\n"
        "---\n\n"
        "# test skill\n",
        encoding="utf-8",
    )
    if with_readme:
        (tmpdir / "README.md").write_text("# test\n", encoding="utf-8")
    if with_evals:
        (tmpdir / "evals").mkdir()
        (tmpdir / "evals" / "trigger_cases.json").write_text(
            json.dumps(
                {
                    "positive_concepts": TRIGGER.DEFAULT_CONCEPTS,
                    "should_trigger": ["package this workflow as a skill"],
                    "should_not_trigger": ["translate this"],
                }
            ),
            encoding="utf-8",
        )
    if with_interface:
        (tmpdir / "agents").mkdir()
        (tmpdir / "agents" / "interface.yaml").write_text(
            "interface:\n"
            "  display_name: Test\n"
            "  short_description: Test\n"
            "  default_prompt: Test prompt\n",
            encoding="utf-8",
        )
    if with_manifest:
        (tmpdir / "manifest.json").write_text(
            json.dumps(
                {
                    "name": manifest_name,
                    "version": "0.1.0",
                    "owner": "Ray",
                    "updated_at": "2026-08-21",
                    "status": "active",
                }
            ),
            encoding="utf-8",
        )
    return tmpdir


class TestValidate(unittest.TestCase):
    def test_minimal_skill_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_skill(Path(td), with_evals=False, with_interface=False, with_readme=False, with_manifest=False)
            result = VALIDATE.validate(root)
            self.assertTrue(result["ok"], msg=result["failures"])
            self.assertNotIn("SKILL.md frontmatter missing or empty: description", result["failures"])

    def test_missing_frontmatter_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "SKILL.md").write_text("---\nname: test-skill\n---\n", encoding="utf-8")
            result = VALIDATE.validate(root)
            self.assertFalse(result["ok"])
            self.assertTrue(any("description" in f for f in result["failures"]))

    def test_invalid_name_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "SKILL.md").write_text(
                "---\nname: Test Skill!\ndescription: Use when doing things\n---\n",
                encoding="utf-8",
            )
            result = VALIDATE.validate(root)
            self.assertFalse(result["ok"])
            self.assertTrue(any("does not match" in f for f in result["failures"]))

    def test_manifest_name_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_skill(Path(td), manifest_name="alpha")
            (root / "manifest.json").write_text(
                json.dumps(
                    {"name": "beta", "version": "0.1.0", "owner": "Ray", "updated_at": "2026-08-21", "status": "active"}
                ),
                encoding="utf-8",
            )
            result = VALIDATE.validate(root)
            self.assertFalse(result["ok"])
            self.assertTrue(any("!= SKILL.md name" in f for f in result["failures"]))


class TestTrigger(unittest.TestCase):
    def test_should_trigger_passes_when_concepts_match(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_skill(Path(td))
            cases = root / "evals" / "trigger_cases.json"
            report = TRIGGER.evaluate(root, cases, None)
            self.assertTrue(report["ok"], msg=report["failures"])
            self.assertEqual(report["summary"]["false_positive"], 0)
            self.assertEqual(report["summary"]["false_negative"], 0)

    def test_should_not_trigger_rejected_by_negative_pattern(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_skill(Path(td))
            cases = root / "evals" / "trigger_cases.json"
            # add an extra should_trigger that contains a negative pattern
            data = json.loads(cases.read_text(encoding="utf-8"))
            data["should_trigger"].append({"text": "just translate this workflow", "family": "x"})
            cases.write_text(json.dumps(data), encoding="utf-8")
            report = TRIGGER.evaluate(root, cases, None)
            self.assertFalse(report["ok"])


class TestSecretScan(unittest.TestCase):
    def test_clean_skill_has_no_findings(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_skill(Path(td))
            findings = SECRET.scan(root)
            self.assertEqual(findings, [])

    def test_fake_openai_key_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_skill(Path(td))
            (root / "leak.md").write_text("My token is sk-aBcDeFgHiJkLmNoPqRsTuVwXyZ123456\n", encoding="utf-8")
            findings = SECRET.scan(root)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["kind"], "openai-like key")


class TestClassifyRisk(unittest.TestCase):
    def test_minimal_skill_is_R0(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_skill(Path(td), with_evals=False, with_interface=False, with_readme=False, with_manifest=False)
            result = RISK.classify(root)
            self.assertTrue(result["ok"])
            self.assertEqual(result["tier"], "R0")

    def test_with_readme_and_evals_is_R1(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_skill(Path(td))
            result = RISK.classify(root)
            self.assertTrue(result["ok"])
            self.assertEqual(result["tier"], "R1")

    def test_with_interface_yaml_is_R2(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_skill(Path(td), with_interface=True)
            result = RISK.classify(root)
            self.assertTrue(result["ok"])
            self.assertEqual(result["tier"], "R2")

    def test_manifest_declared_R3_overrides(self):
        with tempfile.TemporaryDirectory() as td:
            root = _make_skill(Path(td))
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            manifest["risk_tier"] = "R3"
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = RISK.classify(root)
            self.assertEqual(result["tier"], "R3")
            self.assertIn("public_claim_guard", result["required_gates"])


if __name__ == "__main__":
    unittest.main()