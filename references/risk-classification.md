# Risk Classification

The risk tier drives which gates apply. Default to lowest, bump up only when the trigger actually applies.

## Tier table

| Tier | Trigger conditions | Gate set |
|---|---|---|
| **R0 Draft** | Personal scratchpad, will not run on real systems | `validate` |
| **R1 Local** | Runs only on your machine; no network, no public exposure | + `trigger_eval`, `README hook` |
| **R2 Shared** | Team reuse, multi-profile reuse, or any real-system touch | + `interface.yaml`, `risk report`, `secret scan` |
| **R3 Public** | GitHub public repo, `npx`/`npm` install path, or external API key involvement | + all above + `version immutability`, `release gate`, `remote version check`, `public-claim guard` |

## Decision aid

Ask these three; any "yes" bumps you up:

1. Will this touch anything outside your local machine (network, API, shared file)? → +1 tier
2. Will anyone else install or invoke it? → +1 tier
3. Will it publish to a registry or repo (npm, PyPI, GitHub Releases)? → +1 tier

## Bump-up rules

- Goes from R0 to R1 when you'll actually run it on real data, even once.
- Goes from R1 to R2 the moment any team member or another profile will use it.
- Goes from R2 to R3 the moment it appears on a public registry or external API key is needed.

## Bump-down is allowed ONLY when

- The original tier assumption was wrong AND no public artifact exists yet.
- Document why it was bumped down in `reports/risk.md`.

## Risk report template (R2+)

```markdown
# Risk Report — <skill-name> v<version>

## Tier: R<0|1|2|3>

## Triggers (which ones fired)
- [ ] Touches outside local machine
- [ ] Other users / profiles
- [ ] Public registry / external API key

## Mutations this Skill can cause
- Writes files under: <paths>
- Reads network: <hosts>
- Subprocess: <binaries>

## Hard permissions needed
- Network: <which>
- Subprocess: <which>
- File write: <which>

## What this Skill refuses to do (even if asked)
- ...

## Missing evidence
- Provider-backed run: <present | missing>
- Install proof: <present | missing>
- Human review: <present | missing>
```

## Anti-patterns

- Treating R3 as the default for "I want it to look serious." Wrong.
- Treating R0 as the default for "this is for me, who cares." Wrong if you ever share it.
- Using tier as a status symbol instead of a measured consequence.