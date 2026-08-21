# Publish evidence — ray-meta-skill v0.1.0

**Published**: 2026-08-21
**Path**: R3 self-contained (`references/publishing.md`)
**Outcome**: PASS

## URLs

- Repository: https://github.com/dray1220/ray-meta-skill
- Release: https://github.com/dray1220/ray-meta-skill/releases/tag/v0.1.0
- PR #1 (demo): https://github.com/dray1220/ray-meta-skill/pull/1

## Commit history

```
e28548c  docs: add remote verification to README (#1)   ← via PR, squash-merged
cd7474c  feat: initial release of ray-meta-skill v0.1.0
9bcf63a  Initial commit (gh repo create auto-init)
```

## Verification matrix

| Check | Local | Isolated clone |
|---|---|---|
| `validate_skill.py --strict` | PASS (0 failures, 0 warnings) | PASS |
| `secret_scan.py` | PASS (0 findings) | PASS |
| `trigger_eval.py` | 18/18 (0 FP + 0 FN + 0 NN) | 18/18 |
| `release_check.py --phase local --run-tests` | ok=True tier=R3 | ok=True tier=R3 |
| Unit tests | 12/12 PASS | 12/12 PASS |

Isolated clone was at `/tmp/ray-meta-skill-install-test`, checked out `v0.1.0` tag, ran the full gate suite, then was cleaned up. Tag SHA `e28548c` matches the release targetCommitish (`main`).

## Hard prohibitions enforced

- **No API keys / secrets in repo**: `secret_scan.py` found 0 findings.
- **No direct push to main after init**: subsequent change (`docs:` commit `e28548c`) went through feature branch `docs/post-publish-evidence` + PR #1 + squash merge.
- **No overwrite of release tag**: `v0.1.0` was the first and only Release; no overwrite attempted.
- **No fabricated evidence**: every claim in `README.md` "Verified status" table points to a concrete run above.
- **No `python3 -c` for non-trivial logic**: all scripts are `.py` files invoked via `python3 scripts/<name>.py`.
- **No cross-directory scope creep**: publish flow stayed in `~/.hermes/skills/ray-meta-skill/` and a temporary `/tmp/ray-meta-skill-install-test/` (cleaned up after).

## Initial-commit exception (declared)

`gh repo create` produces an "Initial commit" on `main` containing only a default `LICENSE` (`9bcf63a`). Subsequent commits (`cd7474c`, `e28548c`) were then pushed via the normal / feature-branch / PR path. The initial-commit push to `main` was a one-time exception required to bootstrap the repository; this is recorded here, not hidden.

## Missing evidence (per `references/evidence-and-claims.md`)

- **GitHub Actions CI checks**: not configured; PR #1 was merged on local review only.
- **Provider-backed model run**: not executed; `trigger_eval.py` is regex-based, not LLM-based.
- **Human blind review of the publish flow**: not conducted; the operator (Ray) is also the publisher.

These three labels are `missing evidence` in the publish-evidence.json. They do not block R3 publication — they are recorded honestly so that any future review can audit the gap.

## Upstream attribution

Synthesized from:

- https://github.com/joeseesun/qiaomu-meta-skill
- https://github.com/yaojingang/yao-meta-skill

Adopted semantically, not mirrored. Differences documented in `README.md` (Upstream section).