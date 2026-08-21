#!/usr/bin/env python3
"""Regex-based trigger boundary smoke test.

Fast, deterministic, no provider calls. Proves whether the description
selects the right cases and rejects the wrong ones. Not a semantic judge.

Usage:
    python3 scripts/trigger_eval.py <path/to/skill> --cases <cases.json> --output <report.json>
    python3 scripts/trigger_eval.py <path/to/skill> --cases evals/trigger_cases.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

DEFAULT_CONCEPTS = {
    "skill": ["skill", "agent skill", "技能", "能力包"],
    "source_material": [
        "workflow", "prompt", "transcript", "docs", "runbook", "notes",
        "SOP", "流程", "工作流", "提示词", "对话记录",
    ],
    "authoring_action": [
        "create", "refactor", "evaluate", "package", "publish", "upgrade",
        "improve", "migrate", "install", "创建", "整理", "封装", "沉淀",
        "优化", "升级", "迁移", "安装", "打包", "审计", "评估", "诊断",
    ],
    "qiaomu_optional": ["qiaomu", "乔木", "ray", "ray-flavored"],
    "eval_release": [
        "eval", "trigger", "output", "release gate",
        "评估", "触发", "边界", "门禁", "发布",
    ],
}


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def phrase_present(text: str, phrase: str) -> bool:
    phrase = normalize(phrase)
    if not phrase:
        return False
    if re.search(r"[\u4e00-\u9fff]", phrase):
        return phrase in text
    return f" {phrase} " in f" {text} "


def parse_description(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return text
    lines = text.splitlines()
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return text
    block = "\n".join(lines[1:end])
    if yaml is not None:
        payload = yaml.safe_load(block) or {}
        if isinstance(payload, dict):
            return str(payload.get("description", ""))
    match = re.search(r"description:\s*\|?\s*(.*)", block)
    return match.group(1).strip() if match else text


def concept_hits(text: str, concepts: dict[str, list[str]]) -> list[str]:
    normalized = normalize(text)
    hits = []
    for name, phrases in concepts.items():
        if any(phrase_present(normalized, phrase) for phrase in phrases):
            hits.append(name)
    return hits


def negative_hit(text: str, patterns: list[str]) -> str | None:
    normalized = normalize(text)
    for pattern in patterns:
        if phrase_present(normalized, pattern):
            return pattern
    return None


def case_items(cases: dict[str, Any], bucket: str) -> list[dict[str, Any]]:
    output = []
    for raw in cases.get(bucket, []):
        if isinstance(raw, str):
            output.append({"text": raw, "family": "default"})
        elif isinstance(raw, dict):
            item = dict(raw)
            item.setdefault("family", "default")
            output.append(item)
    return output


def evaluate(root: Path, cases_path: Path, output_path: Path | None) -> dict[str, Any]:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    concepts = cases.get("positive_concepts") or DEFAULT_CONCEPTS
    threshold = float(cases.get("recommended_threshold", 0.34))
    negative_patterns = list(cases.get("negative_patterns", []))
    description = parse_description(root / "SKILL.md")
    description_hits = set(concept_hits(description, concepts))

    buckets: dict[str, list[dict[str, Any]]] = {
        "should_trigger": [],
        "should_not_trigger": [],
        "near_neighbor": [],
    }
    failures: list[dict[str, Any]] = []
    totals = {"total": 0, "passed": 0, "false_positive": 0, "false_negative": 0, "near_neighbor_collision": 0}

    denominator = max(3, min(5, len(description_hits) or len(concepts)))
    for bucket in buckets:
        # Only should_trigger expects a True prediction. The other two
        # buckets (should_not_trigger, near_neighbor) must NOT trigger.
        expected = bucket == "should_trigger"
        for item in case_items(cases, bucket):
            prompt = str(item.get("text", ""))
            hits = set(concept_hits(prompt, concepts))
            matched = sorted(hits & description_hits)
            neg = negative_hit(prompt, negative_patterns)
            score = min(1.0, len(matched) / denominator)
            predicted = score >= threshold and neg is None
            passed = predicted == expected
            record = {
                "prompt": prompt,
                "family": item.get("family", "default"),
                "bucket": bucket,
                "matched_concepts": matched,
                "score": round(score, 3),
                "negative_pattern": neg,
                "predicted": predicted,
                "expected": expected,
                "passed": passed,
            }
            buckets[bucket].append(record)
            totals["total"] += 1
            if passed:
                totals["passed"] += 1
            elif bucket == "should_trigger":
                totals["false_negative"] += 1
                failures.append(record)
            elif bucket == "should_not_trigger":
                totals["false_positive"] += 1
                failures.append(record)
            else:  # near_neighbor
                totals["near_neighbor_collision"] += 1
                failures.append(record)

    summary = {
        "total": totals["total"],
        "passed": totals["passed"],
        "false_positive": totals["false_positive"],
        "false_negative": totals["false_negative"],
        "near_neighbor_collision": totals["near_neighbor_collision"],
        "threshold": threshold,
        "description_concepts": sorted(description_hits),
    }
    report = {
        "ok": not failures,
        "summary": summary,
        "failures": failures,
        "buckets": buckets,
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Trigger-boundary smoke eval")
    parser.add_argument("path", help="Path to the Skill package root")
    parser.add_argument("--cases", required=True, help="Path to trigger_cases.json")
    parser.add_argument("--output", help="Optional report output path")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not (root / "SKILL.md").is_file():
        print(f"error: SKILL.md missing at {root}", file=sys.stderr)
        return 2

    cases_path = Path(args.cases).resolve()
    if not cases_path.is_file():
        print(f"error: cases file not found: {cases_path}", file=sys.stderr)
        return 2

    output_path = Path(args.output).resolve() if args.output else None
    report = evaluate(root, cases_path, output_path)

    summary = report["summary"]
    print(
        f"trigger eval: {summary['passed']}/{summary['total']} passed "
        f"(FP={summary['false_positive']}, FN={summary['false_negative']}, "
        f"NN={summary['near_neighbor_collision']}, threshold={summary['threshold']})"
    )
    if report["failures"]:
        print("Failures:")
        for f in report["failures"]:
            print(f"  - [{f['family']}] {f['prompt']!r}")
            print(f"    matched={f['matched_concepts']} score={f['score']} neg={f['negative_pattern']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())