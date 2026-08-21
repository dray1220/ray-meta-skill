# Gate Ladder

Gates match risk tier. Lower tier = fewer mandatory gates. Higher tier = all lower gates plus tier-specific ones.

## R0 (Draft)

- [ ] `SKILL.md` frontmatter (`name`, `description`)
- [ ] `description` includes `Use when...` and concrete trigger conditions
- [ ] Body fits in < 500 lines; complex detail moved to `references/`

## R1 (Local) — adds

- [ ] `README.md` hook (one-paragraph value statement, install, one example)
- [ ] `evals/trigger_cases.json` with `should_trigger` ≥ 3, `should_not_trigger` ≥ 3, `near_neighbor` ≥ 2
- [ ] `scripts/validate_skill.py` passes
- [ ] `scripts/trigger_eval.py` passes

## R2 (Shared) — adds

- [ ] `agents/interface.yaml` with `display_name`, `short_description`, `default_prompt`
- [ ] `reports/risk.md` populated
- [ ] `scripts/secret_scan.py` passes (zero findings)
- [ ] `manifest.json` present with `name`, `version`, `owner`, `updated_at`, `status`, `risk_tier`
- [ ] Trigger eval run record in `reports/trigger-eval.json`

## R3 (Public) — adds

- [ ] Versioning policy in `references/versioning.md` followed (semver; no overwrite of existing `vX.Y.Z` Release)
- [ ] `scripts/release_check.py` passes (`--phase local --run-tests`)
- [ ] `scripts/publish_skill.py --dry-run` produces no errors
- [ ] Every README "verified/production-grade/passed" claim has a pointer to `reports/<file>.json` or `tests/` log
- [ ] Remote version check: target GitHub Releases does not already have `vX.Y.Z`
- [ ] All publishing happens on a feature branch; direct push to `main`/`master` is refused

## Gate failure handling

A failed gate is a **stop**, not a warning. Either:

1. Fix the underlying issue.
2. Bump the tier down (only if no public artifact depends on it yet).

Do not ship past a failing gate. "It's a soft warning" is not in the vocabulary.

## Missing-evidence handling

If a gate requires evidence you cannot produce, mark the gate as `MISSING EVIDENCE` and surface it in the user-facing report. Do not silently downgrade the gate or hide the gap.