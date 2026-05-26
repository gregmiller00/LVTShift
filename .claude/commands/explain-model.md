---
description: Explain how an existing LVTShift city model was built — data sources, levies modeled vs. not, revenue, full and partial exemptions and how they stack, property categories, the land/improvement split, and the model's limitations.
argument-hint: [city]
---

Invoke the `explain-model` skill for: $ARGUMENTS

Read `.claude/skills/explain-model/SKILL.md` before doing anything else, then follow its pipeline exactly. Audit the model against its executed notebook and standardized export, and — when the cached parcel data is present — re-probe the data to surface limitations the notebook does not state (especially collapsed-signal / flat land-ratio artifacts).

If `$ARGUMENTS` is empty, list the cities under `cities/` that have a `model.ipynb` and ask which one to explain.
