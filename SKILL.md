---
name: ray-meta-skill
description: |
  Use when turning a repeated workflow, prompt, SOP, transcript, script, or existing skill into a Hermes Skill package. Routes by risk class, enforces evidence-bound claims, blocks unsafe publish paths, and matches gate strictness to risk tier. Do NOT use for one-off summaries, translations, brainstorms, prompt-phrasing tweaks, or tasks that should stay as plain conversation.
metadata:
  author: Ray
  version: "0.1.0"
  upstream_inspiration: joeseesun/qiaomu-meta-skill; yaojingang/yao-meta-skill
---

# ray-meta-skill

Turn a repeated workflow into a real Hermes Skill, not a long prompt.

## Router rules (HARD)

These override any later guidance. If a conflict appears, the earlier rule wins.

1. **One-shot → refuse to package.** Brainstorms, summaries, translations, explanations, one-off scripts, ordinary documentation → answer directly and create no package. See `references/non-skill-decision-tree.md`.
2. **Audit/evaluate/diagnose-only requests → read-only mode.** No file mutation, no install, no publish unless explicitly requested.
3. **Publish only when explicitly requested.** Bundled publisher is self-contained; do not require or invoke a separate publisher skill after this package is selected.
4. **No silent fallback to creator/discovery/publisher skills.** This skill owns the full path.
5. **Match strictness to risk, not to ceremony.** Personal experiments do not need Governance gates; public/high-trust Skills earn them.
7. **Never fabricate evidence.** Missing provider runs, install proofs, or human reviews stay marked `missing evidence`. Planned work is not proof.
8. **Honor scope.** If the request is bounded (audit, evaluate, fix one file), do not cross directory boundaries or invent context.

## Risk classification (DETERMINISTIC)

Run this BEFORE creating files. The risk tier drives which gates apply.

| Tier | Trigger | Gate set |
|---|---|---|
| **R0 Draft** | Personal note, scratchpad, will not run on real systems | `validate` only |
| **R1 Local** | Runs on your machine only, no network, no public exposure | + `trigger_eval` + `README hook` |
| **R2 Shared** | Reused by team or by multiple profiles; touches real systems | + `interface.yaml` + `risk report` + `secret scan` + `trigger eval` |
| **R3 Public** | GitHub public repo, npm/npx install path, or any external API key involvement | + all above + `version immutability` + `release gate` + `remote version check` + `public-claim guard` |

Public-claim guard means: every claim in README/description that says "verified", "passed", "production-grade" or similar MUST point to a concrete evidence path (`reports/<x>.json`, `tests/test_*.py PASS log`, etc.).

Default to the lowest tier; bump up only when the trigger actually applies. **Do not skip tiers to save work.**

## Workflow

```
1. Decision      → Is this really a reusable Skill? (non-skill decision tree)
2. Risk class    → R0/R1/R2/R3 (this file's table)
3. Intent        → Inputs, output, exclusions, success standard
4. Prior art     → Quick check, NOT exhaustive; record only what you learned
5. Package       → SKILL.md + earned files per tier
6. Evaluate      → trigger eval first; output eval only if R3 or quality-dependent
7. Review        → validate + secret scan + version check
8. Publish       → only on explicit request; never push default branch directly
```

Skip a step means the corresponding output is not produced, **not** that the step is silently done. Mark `not applicable` with one-line reason.

## Hard prohibitions (zero-tolerance)

These override all other guidance. Violation = stop and report, do not fix forward.

- **No API keys, tokens, passwords, cookies, private paths, or real names in any `.md` / `.json` / `.yaml` / `.py` / `.js` / `.sh` / `.ts` / `.toml` file** in a Skill package. Use `.env` (gitignored) and `os.environ`. Substitute `<YOUR_API_KEY>` or `***` in docs.
- **No direct push to `main` / `master`.** All publishing goes through a feature branch + PR.
- **No overwriting an existing `vX.Y.Z` Release tag.** Bump the version.
- **No fake test results, fake API responses, or made-up file contents.** Return the blocker, not a plausible lie.
- **No `python3 -c "..."` or `bash -c "..."` for non-trivial logic.** Write a `.py` / `.sh` file under `scripts/`.
- **No cross-directory scope creep.** Defect registration on project X must not read project Y. ONES/registration boundary is the user's, not the Agent's.
- **No "I already verified that" without a verifiable handle.** `read back the file`, `curl -I the URL`, `pytest --tb=short` output, `gh release view` exit code — concrete, not narrative.
- **No command in a Skill that the user has not approved.** If a command could mutate state outside the package boundary, surface it and wait.

## Trigger evaluator

`scripts/trigger_eval.py` is a regex-based smoke test, not a semantic judge. Three buckets:

- `should_trigger` — realistic user phrasings that should select this Skill.
- `should_not_trigger` — adjacent phrasings that look similar but should select something else.
- `near_neighbor` — similar Skills in the catalog; used to keep `description` narrow enough not to collide.

Threshold default `0.34`. See `evals/trigger_cases.json` for the canonical case set.

## Output contract

Produce only what the risk tier earns:

- R0: `SKILL.md` (frontmatter + intent + the most minimal body)
- R1: + `README.md` hook + `evals/trigger_cases.json`
- R2: + `agents/interface.yaml` + `reports/risk.md` + secret scan output
- R3: + `manifest.json` + versioned Release + install proof + remote version check evidence

Do not produce ceremonial empty directories. If `scripts/` is empty, do not create `scripts/`.

## Reference map

- Decision: `references/non-skill-decision-tree.md`, `references/intent-dialogue.md`
- Risk + gates: `references/risk-classification.md`, `references/gate-ladder.md`
- Quality: `references/trigger-eval.md`, `references/evidence-and-claims.md`
- Publishing: `references/publishing.md`, `references/versioning.md`
- Style: `references/ray-style-checklist.md` (what makes a Skill "ray-flavored")

Scripts under `scripts/` are deterministic and have no LLM calls. They can be re-run by any user on any clone.