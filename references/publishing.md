# Publishing (Self-Contained)

This Skill owns the full public release path. Do not require or invoke a separate publisher Skill.

## What publish means here

For R3, "publish" means:

1. `scripts/release_check.py --phase local --run-tests` passes
2. `scripts/publish_skill.py --dry-run` produces no errors
3. **The user has explicitly asked to publish.** "I made a Skill" is not "publish it."
4. Feature branch is created and pushed
5. PR is opened and checks pass
6. Merge happens (user approval if required)
7. Remote `vX.Y.Z` Release is created
8. Install on a clean machine is verified (`npx skills add` or equivalent)
9. README claims are still evidence-bound

Steps 5–9 are external operations. The Agent must surface each one before executing it and wait for confirmation.

## What publish does NOT mean

- Does not mean "push to main" — feature branch only.
- Does not mean "overwrite existing Release tag" — version bump required.
- Does not mean "the local clone looks right" — install proof required.
- Does not mean "I trust the upstream" — every claim must be locally verifiable.

## Dry run is mandatory

Before any real publish:

```bash
python3 scripts/publish_skill.py /path/to/skill --dry-run
```

Dry-run output must be reviewed by the user (or by you, in a non-interactive context, with the review recorded in `reports/release-audit.md`).

## Failure handling

| Failure mode | Behavior |
|---|---|
| Pre-flight gate fails | Stop. Report which gate. Do not attempt publish. |
| Secret scan finds anything | Stop. Report file and pattern. Do not commit. |
| `vX.Y.Z` already exists | Stop. Bump version. Re-run. |
| Push to default branch attempted | Refused. Require a feature branch. |
| PR checks fail or pending | Stop. Report check status. Do not merge. |
| Install on clean machine fails | Stop. Do not declare publish complete. |
| Publish script itself errors | Stop. Report error verbatim. Do not retry silently. |

## Anti-patterns

- "Pushed, so it's published." Wrong — push is one of 9 steps.
- "The dry run passed, so it will work in prod." Wrong — dry run is read-only.
- "I'll fix it after publish." Wrong — fix before publish.
- "v1.0.0 is close enough to v1.0.1, let me overwrite." Wrong — Releases are immutable.