---
description: Run the full LVTShift pipeline end-to-end to model Land Value Tax for a new city or county.
argument-hint: [city, state]
---

Invoke the `model-city` skill for: $ARGUMENTS

Read `.claude/skills/model-city/SKILL.md` before doing anything else, then follow the master pipeline. Sub-skills live in `.claude/skills/discover-data.md`, `model-policy.md`, `build-notebook.md`, and `validate.md` — read each before running its step.

If `$ARGUMENTS` is empty, ask the user which city to model before proceeding. Also confirm the four upfront policy questions from the skill's "Before writing any code" section before touching any data.
