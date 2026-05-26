---
description: Analyze the legal pathway for LVT reform in a U.S. city or state. Produces a citation-heavy brief grounded in primary sources.
argument-hint: [city, state] | [state]
---

Invoke the `legality-analyzer` skill for: $ARGUMENTS

Read `.claude/skills/legality-analyzer/SKILL.md` and `docs/LVT_LEGAL_DECISIONING_GUIDE.md` before doing anything else, then follow the skill's pipeline exactly.

If `$ARGUMENTS` is empty, ask the user which jurisdiction to analyze before proceeding.
