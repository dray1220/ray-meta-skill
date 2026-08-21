# Versioning

Semver (`vMAJOR.MINOR.PATCH`). Releases are immutable.

## When to bump

- `MAJOR`: incompatible schema/contract change to the Skill's frontmatter, interface, or trigger contract.
- `MINOR`: new gates added, new references, new scripts, but existing triggers and contract unchanged.
- `PATCH`: wording fixes, typo fixes, doc clarifications, eval case additions without contract changes.

## Immutability

Once a `vX.Y.Z` GitHub Release is created:

- It cannot be deleted and re-created at the same version.
- It cannot be force-pushed to overwrite.
- If you must change the published artifacts, bump the version and publish again.

## Manifest version

The `version` field in `manifest.json` is the source of truth for the next release. If you change Skill behavior in a way users would notice, bump there first, then everywhere else.

## Cross-checking

For R3:

1. Local `manifest.json` version
2. Git tag (local)
3. Remote Release tag (via `gh release view`)
4. `reports/release-audit.md` entry

All four must agree. If any disagree, fix the source of disagreement before publishing.

## Pre-release tags

Use `vX.Y.Z-rc.N` for release candidates. They:

- Are not considered "released" for install purposes.
- Can be overwritten within the `-rc.N` namespace.
- Do not block later `vX.Y.Z` releases.

## Anti-patterns

- "v1.0 is fine, I'll just edit the README in the Release." Wrong — Releases are immutable. Bump.
- "I'll bump MAJOR for a doc fix." Wrong — that's a PATCH.
- "Let me skip version bumps for minor things." Wrong — drift kills trust.