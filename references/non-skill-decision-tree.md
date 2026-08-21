# Non-Skill Decision Tree

## Refuse to package when

- The task is one-off and won't repeat (`翻译一下`, `总结一下`, `解释一下 X`).
- The "rule" is implicit and unstable (`how should I...`, `帮我看看`, open-ended brainstorm).
- The output is a single artifact with no recurring structure (one email, one diagram, one bug fix).
- It is a project-specific convention (put it in `AGENTS.md` / `SOUL.md`, not a Skill).
- It is enforceable by regex/validator (automate it; documentation is for judgment calls).

## Package when

- The same workflow appears across ≥ 2 unrelated projects or ≥ 3 sessions.
- Rules are stable enough that re-reading them next month is still correct.
- The Agent's role matters: must invoke a specific behavior consistently.

## The Stop Rule

If the user gave enough info to write a defensible capability description:

```
This skill receives <real input>, used for <recurring task>, outputs <deliverable>, 
excludes <adjacent requests that should NOT trigger this>.
```

Stop asking questions. Proceed with that contract and surface assumptions at the top of the output.

## Anti-patterns that look like Skills

- **"How to use the terminal"** — that's a man page, not a Skill.
- **"My preferences"** — preferences belong in memory or config, not a Skill.
- **"How I think about X"** — that's an essay, not a Skill.

Skills are **executable behavior contracts for Agents**, not knowledge bases for humans.