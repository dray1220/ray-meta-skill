# ray-meta-skill

> Turn a repeated workflow into a real Hermes Skill, with gates matched to risk.

A personal meta-skill for authoring, evaluating, and publishing Hermes Skill packages. Risk-driven gating, evidence-bound claims, and self-contained publishing.

## What it does

- Classifies a Skill package's risk tier deterministically (`R0`/`R1`/`R2`/`R3`).
- Applies gates proportional to risk — no ceremonial directories.
- Bundles the full path: intent → prior-art quick check → package → trigger eval → release check → publish. No separate creator, discovery, or publisher skill required.
- Refuses to fabricate evidence. Missing provider runs, install proofs, or human reviews stay marked `missing evidence`.
- For public release: feature branch + PR + versioned GitHub Release + isolated clean install verification. Never pushes to `main`/`master`, never overwrites an existing `vX.Y.Z` Release.

## Hard rules

- **No API keys, tokens, passwords, cookies, private paths, or real names** in any committed file. Use `.env` (gitignored) and substitute `<YOUR_API_KEY>` or `***` in docs.
- **No direct push to default branch.** All publishing goes through a feature branch + PR.
- **No overwriting an existing Release tag.** Bump the version.
- **No fake test results, fake API responses, or made-up file contents.** Return the blocker, not a plausible lie.
- **No `python3 -c "..."` or `bash -c "..."` for non-trivial logic.** Write a `.py` / `.sh` file under `scripts/`.
- **No cross-directory scope creep.** If the request is bounded, stay bounded.
- **No claim without a verifiable handle.** `pytest` output, `gh release view` exit code, `curl -I` status — concrete, not narrative.

## Risk tiers

| Tier | Trigger | Gates |
|---|---|---|
| R0 Draft | Personal scratchpad | validate only |
| R1 Local | Runs on your machine only | + trigger eval, README hook |
| R2 Shared | Team / multi-profile reuse | + interface.yaml, risk report, secret scan |
| R3 Public | GitHub public, npm/npx, external API key | + version immutability, release gate, remote version check, public-claim guard |

## Install

```bash
# from your local Hermes skills directory
ln -s ~/.hermes/skills/ray-meta-skill /your/install/root/ray-meta-skill
```

(or copy the directory; this Skill is not yet published to a registry.)

## Verify

```bash
python3 scripts/classify_risk.py .
python3 scripts/validate_skill.py . --strict
python3 scripts/secret_scan.py .
python3 scripts/trigger_eval.py . --cases evals/trigger_cases.json --output reports/trigger-eval.json
python3 scripts/release_check.py . --phase local --run-tests
```

## Directory

```
ray-meta-skill/
├── SKILL.md                     # router + risk + workflow
├── README.md                    # this file
├── manifest.json                # name/version/owner/risk_tier/gates
├── agents/interface.yaml        # cross-agent default_prompt
├── references/
│   ├── non-skill-decision-tree.md
│   ├── intent-dialogue.md
│   ├── risk-classification.md
│   ├── gate-ladder.md
│   ├── evidence-and-claims.md
│   ├── trigger-eval.md
│   ├── publishing.md
│   ├── versioning.md
│   └── ray-style-checklist.md
├── scripts/
│   ├── classify_risk.py         # R0-R3 deterministic
│   ├── validate_skill.py        # structural contract
│   ├── trigger_eval.py          # regex-based, no LLM
│   ├── secret_scan.py           # credential patterns
│   ├── release_check.py         # local / PR / published phases
│   └── publish_skill.py         # dry-run only by default
├── evals/
│   └── trigger_cases.json       # should/should_not/near_neighbor
├── reports/                     # machine-readable evidence
└── tests/                       # unit tests for scripts
```

## Style

Chinese-first docs, English code/identifiers. Bundled self-contained. No `python3 -c` for non-trivial logic. Always bring back real test outputs.

See `references/ray-style-checklist.md`.

## Verified status

| Check | Result |
|---|---|
| `validate_skill.py --strict` | 0 failures, 0 warnings |
| `secret_scan.py` | 0 findings |
| `trigger_eval.py` | 18/18 (0 FP + 0 FN + 0 NN collision) |
| `release_check.py --phase local --run-tests` | ok=True, tier=R3 |
| `publish_skill.py --phase local` | clean dry-run, stdout=JSON, stderr=log |
| Unit tests (`unittest discover`) | 12/12 PASS |
| Remote default branch | `cd7474c feat: initial release of ray-meta-skill v0.1.0` |
| GitHub URL | `https://github.com/dray1220/ray-meta-skill` |

The `prompt-phrasing tweaks` boundary is covered via both the description and the negative-pattern list. Real users who say "打磨 prompt 措辞" (different phrasing) would still hit this Skill; if that becomes a real false-positive in production, add more negative variants.

## Upstream

Synthesized from `joeseesun/qiaomu-meta-skill` and `yaojingang/yao-meta-skill`. Adopted semantically, not mirrored wholesale. Differences:

- Risk tiers are **dynamic** (matched to trigger, not ceremony) instead of fixed 4 levels.
- `classify_risk.py` is the deterministic entry point; qiaomu uses 4 fixed tiers.
- `publish_skill.py` is **dry-run-only** by default; real publish requires explicit user-approved orchestration outside the automatic Agent loop.
- Tighter hard-prohibition list, derived from real session failures (not aspirational).

## License

MIT.

---

Status: v0.1.0, R3, lifecycle=local. Scripts are pure-stdlib + PyYAML only.