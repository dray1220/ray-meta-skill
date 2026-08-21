# Ray-Style Checklist

What makes a Skill "ray-flavored" — derived from past session patterns, not aspirational.

## Hard rules (always)

- **Chinese-first documentation, English code/identifiers.** `SKILL.md` body and references in Chinese; YAML keys, JSON keys, script names, function names in English.
- **No `python3 -c "..."` or `bash -c "..."` for non-trivial logic.** Write a `.py` or `.sh` file. One-off can be inline if truly trivial (≤ 3 lines, no state).
- **No invented names, paths, URLs, or numbers in user-facing output.** Substitute `<PATH>` / `<YOUR_API_KEY>` / `***` when concrete value is not present on disk right now.
- **Truth over comfort.** "I don't know" beats "let me make something plausible." A blocker is a blocker.
- **One decision per turn, with the consequence spelled out.** Don't ask 5 design questions in one message; pick the most blocking one.
- **Bring back real test results, not narrative claims.** `pytest` output, `gh release view` exit code, `curl -I` status — concrete, not "I verified."

## Habits (preferred)

- **Bundle everything self-contained.** This Skill owns its discovery, evaluation, and publishing paths. No "please also install X."
- **Trigger cases in both Chinese and English** in `evals/trigger_cases.json`. Real users mix both.
- **Match gate strictness to risk.** Personal scratchpad ≠ public GitHub repo.
- **Use ASCII diagrams only when they save words.** Tables > ASCII art > bullet lists for most cases.
- **Link to references by file path, not `@path`.** `@` force-loads files and burns context.
- **Markdown headings without backslash-escapes.** `### TC_FILE_NEG_004` (bare) — some viewers drop `### TC\_FILE\_NEG\_004` from TOCs.

## Forbidden patterns (always)

- "I'll handle that too" — scope creep. The user asked for X.
- "Should be straightforward" — implies unverified assumption.
- "Let me clean this up" — implies you touched something you didn't say you'd touch.
- "Looking good" / "all set" without a verifiable handle.
- Claiming a command "ran successfully" without showing its exit code or output.
- Inventing API responses, file contents, or test results.
- Reporting a deliverable without showing its absolute path.

## Project defaults (override if user says otherwise)

- Default to concise Chinese-first outputs.
- Skill names: short verb-noun, lowercase, hyphens.
- File names: `01-...md` ordering for sequential docs, plain names for one-offs.
- Output paths inside the Skill package, never at `/tmp/`.
- `.env` for secrets, `.gitignore` to exclude `.env`, never commit secrets.

## Cross-session conventions

- `~/.hermes/skills/<name>/` is the install root.
- `reports/` is for evidence, not narrative.
- `tests/` runs under `python3 -m unittest discover -s tests -p 'test_*.py'`.
- `scripts/` are pure-stdlib + PyYAML only (no provider SDK imports).