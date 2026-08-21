# Intent Dialogue

Before writing files, confirm intent. Goal: avoid wrapping a fuzzy idea in the wrong structure.

## When to ask

- The user gave only a rough idea, no inputs or outputs stated.
- The Skill will be reused by others or published.
- Trigger boundaries and adjacent requests could easily collide.
- The user gave upstream projects, competitors, prompts, or long transcripts — borrowing scope is unclear.

If the user gave enough info already, write down your own assumptions and proceed.

## Must capture (7 fields)

1. **Recurring task** — what job will this Skill reliably catch in the future?
2. **Inputs** — what will users actually hand it (paste, file, command output, prior Skill output)?
3. **Outputs** — files, reports, commands, releases, or conclusions.
4. **Exclusions** — adjacent requests that must NOT trigger this Skill.
5. **Top standard** — speed, consistency, auditability, publishability, cross-platform, or "ray style".
6. **Prior art to consult** — only borrow structure and method, not prose.
7. **Existing assets** — scripts, templates, READMEs, old Skills, logs, samples already on disk.

## Stop rule (defensible capability description)

When you can write the following, stop asking:

```
This Skill receives <real input>, used for <recurring task>, outputs <deliverable>,
excludes <adjacent requests that should NOT trigger this>.
```

Do not keep asking to "complete the structure." Questions that don't affect design are noise.

## Two opening scripts

For a fuzzy request:

> 我先不急着定结构。你像聊天一样告诉我:这个 Skill 以后最想稳定接住哪类重复工作?别人通常丢什么给它?它最后交回什么结果才算好用?

For a clear request:

> 我按可复用 Skill 做。我的假设是:它处理 X,输入 Y,输出 Z,不做 A/B。如果不对我在动手前改。