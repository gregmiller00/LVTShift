---
description: Re-run an existing LVTShift city model with changed parameters — a different split ratio, split-rate vs. building abatement, a different exemption treatment, or an expanded levy scope. Edits the notebook surgically, re-executes, re-validates, and reports a before/after diff.
argument-hint: [city] [what to change]
---

Invoke the `refine-model` skill for: $ARGUMENTS

Read `.claude/skills/refine-model/SKILL.md` before doing anything else, then follow its pipeline. It orchestrates the existing sub-skills — consult `.claude/skills/model-policy.md` for the mechanics of the requested change, `.claude/skills/build-notebook.md` for the notebook structure that must be preserved, and `.claude/skills/validate.md` for the gates. Make the smallest correct edit to `cities/<city>/model.ipynb`, re-execute, re-validate, re-run `analysis/cross_city.ipynb`, and report a before/after diff.

If `$ARGUMENTS` names a city with no existing `cities/<city>/model.ipynb`, tell the user there's nothing to refine and point them at `/lvt-city <city>` to build it first. If the refinement itself is unspecified, ask what they want to change.
