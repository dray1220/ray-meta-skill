# Evidence and Claims

Every public claim must be evidence-bound. This is non-negotiable for R3, strongly recommended for R2.

## Claim categories

| Label | Meaning | Allowed wording |
|---|---|---|
| `design advantage` | Source-visible difference, fits the stated target job | "This design adds…", "Compared with X, this package explicitly…" |
| `validated advantage` | Supported by named trigger, output, runtime, install, or human evaluation | "Passed 16/16 trigger cases…", "Install verified at <url>" |
| `hypothesis` | Plausible but unproven | "Expected to help…, but provider-backed comparison is missing evidence." |

## Forbidden claims

Do not write any of these unless a fair comparison supports it:

- "best", "world-class", "leading"
- "more accurate than X"
- "better than X"
- "production-grade" without trigger eval + install proof
- "verified" without a concrete verifiable handle (file path, exit code, URL)

## Missing evidence

If a tier requires evidence you can't produce, mark `missing evidence`:

- `provider-backed run` — only after running a real provider API
- `human blind review` — only with reviewer ID, `reviewed_at`, decision, rubric-based reason
- `install simulation / install proof` — only after `npx skills add` or equivalent on a clean machine
- `secret scan` — only after `scripts/secret_scan.py` returns zero findings on committed files
- `public release / PR merge` — only after the remote Release tag is created

Planned work is not proof. Scheduled is not done. Drafted is not verified.

## Public-claim guard

Each claim in README, description, or release notes must point to one of:

- `reports/<file>.json` — machine-readable evidence
- `tests/test_*.py` PASS log — test output
- `npx skills add` output — install proof
- A specific commit SHA — code state

If you cannot point to a concrete handle, **the claim is downgraded** to `hypothesis` or removed.

## Anti-patterns

- "Comprehensive test coverage" without a test file.
- "Battle-tested" without a user count or duration.
- "Production-ready" without a trigger eval.
- "Trusted by X" without permission from X.

These are exactly the claims that get retracted in post-mortems.