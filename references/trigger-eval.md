# Trigger Eval

Trigger eval proves "would the right Skill be called?". Output eval proves "after calling, did the output actually improve?". The two are different problems; both matter.

## When trigger eval is required

- R1 and above: required.
- R0: optional but recommended.

## Three buckets, every case set

- `should_trigger` — realistic user phrasings that should select this Skill.
- `should_not_trigger` — adjacent phrasings that look similar but should select something else.
- `near_neighbor` — Skills in the catalog that could be confused; used to keep `description` narrow enough to avoid collision.

Minimum counts:
- `should_trigger` ≥ 3
- `should_not_trigger` ≥ 3
- `near_neighbor` ≥ 2

If you can't reach these minimums, the description is too narrow or the use case is too thin — pick a different job.

## Algorithm (deterministic)

The bundled `scripts/trigger_eval.py` is regex-based. It is fast, reproducible, and does not call the provider. It is not a semantic judge.

```
matched_concepts = intersection(prompt_terms, description_terms)
score = min(1.0, len(matched_concepts) / denominator)
predicted = score >= threshold AND no negative_pattern_hit
passed = predicted == expected
```

Default threshold: `0.34`. Adjust per Skill after seeing false positives/negatives, but document the rationale.

## Negative patterns

Anything that should immediately disqualify a prompt from triggering this Skill:

- "don't make it a skill"
- "just summarize", "just explain", "just translate"
- "brainstorm only"
- "ordinary Python package", "publish to PyPI" (when this is not the goal)

Place these in `evals/trigger_cases.json` under `negative_patterns`.

## When to do output eval

Only when correctness, safety, or repeatability cannot be shown by trigger tests alone. Concretely:

- Skill generates public content (README, blog post, tweet).
- Skill generates files others will read or execute.
- Skill has been called and produced a wrong result at least once.

Output eval structure (from `references/output-eval-method.md`, kept short here):

- `prompt` (real user phrasing)
- `baseline_output` (without the Skill)
- `with_skill_output` (with the Skill)
- `assertions` (machine-checkable)
- `human_notes` (judgment-based)

## What trigger eval cannot prove

- That the Skill's *content* is correct (use tests for that).
- That the Skill's *output* is high quality (use output eval for that).
- That the Skill is semantically right for an edge phrasing (regex doesn't think).

Don't pretend trigger eval is a quality oracle. It is a routing sanity check.