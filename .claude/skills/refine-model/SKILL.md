---
name: refine-model
description: Re-runs an existing LVTShift city model with changed parameters — a different split ratio (e.g. 2:1 instead of 4:1), a switch between split-rate and building abatement, a different exemption treatment (which classes are exempt, full vs. partial relief, adding/removing dollar relief or caps), or an expanded levy scope (e.g. add the secondary/bond levy or go full-stack). Use when the user says "refine the model for [city]", "refine-model [city]", "re-run [city] as 2:1", "change [city] to a building abatement", "model [city] with the county levy included", "exempt [X] in [city] instead", or otherwise asks to change one or more modeling choices for a city that is already modeled. Makes the minimal edit to cities/<city>/model.ipynb, re-executes, re-validates, re-runs cross_city, and reports a before/after diff.
---

# Skill: Refine a City Model

Invoked when the user says **"refine the model for [city]"**, **"refine-model [city]"**,
or asks to change a modeling choice for a city that **already has** a model
(`cities/<city>/model.ipynb`). If no model exists yet, stop and point them at
`/lvt-city <city>` (the `model-city` skill) instead.

This skill is an **orchestrator**, not a new modeling engine. The mechanics already live in
the sub-skills — your job is to translate the user's request into the smallest correct edit
and re-run the standard pipeline:

- **How** to implement each kind of change → `.claude/skills/model-policy.md`
- **What notebook structure must be preserved** → `.claude/skills/build-notebook.md`
- **How to validate the result** → `.claude/skills/validate.md`
- **Understanding / documenting the current and refined model** → `explain-model` skill

---

## Operating principles

1. **Surgical edits only.** Change the specific constants/cells the refinement requires and
   nothing else. Never rewrite the notebook, never reorder sections, and never touch the
   closing census-join → `save_standard_export` → `create_city_report` →
   `save_parcel_map_export` → `create_parcel_map` pattern (it must stay verbatim per
   `build-notebook.md`). Re-executing regenerates the interactive parcel map automatically.
2. **Snapshot before you change.** Capture the current millages, revenue, and category
   medians from the existing `analysis/data/<city>.csv` *before* editing, so you can report
   an honest before/after diff.
3. **State the diff, then act.** Restate the request as the concrete parameter change(s) you
   are about to make (old value → new value). If the request is ambiguous (e.g. "exempt
   nonprofits" when several use-codes could qualify, or "add the county levy" when the rate
   source is unclear), ask one clarifying question before editing. Otherwise proceed.
4. **Preserve revenue neutrality — but recompute the target when scope changes.** A split
   ratio or exemption change keeps the same revenue-neutral target. **Changing the levy
   scope changes the target revenue** (more levies = more dollars to re-raise) and usually
   the millage source too — handle this explicitly, don't reuse the old target.
5. **Always re-validate.** Run the four `validate.md` gates after re-executing. A refinement
   that breaks a gate is not done.
6. **Report what moved.** The deliverable is the before/after comparison, not just "it ran."

---

## Refinement taxonomy

Map the request to the change. Read the cited `model-policy.md` section before editing.

| Request | What to change in the notebook | Governing section |
|---|---|---|
| Different split ratio (4:1 → 2:1, 6:1, 10:1) | `LAND_IMPROVEMENT_RATIO` constant + `MODEL_TYPE` string (e.g. `split_rate_2to1`) | model-policy B1 |
| Split-rate → building abatement | Swap `model_split_rate_tax` for `model_full_building_abatement` / `model_stacking_improvement_exemption`; set `MODEL_TYPE` (e.g. `abatement_100pct`); drop ratio | model-policy B6 |
| Abatement → split-rate | Reverse of above | model-policy B1 |
| Change exemption treatment (which classes are fully exempt) | The exemption-flag construction cell (use-code / class membership) | model-policy A3, D |
| Full vs. partial relief (add/remove dollar relief) | Pass `exemption_col` (dollar relief, hits improvement first then land) and/or `exemption_flag_col`; relief is applied independently and *before* the full-exempt zeroing | model-policy A3, B2 |
| Add a percentage cap / circuit breaker | Pass `percentage_cap_col` to the model fn | model-policy A3 |
| Expand levy scope (add secondary/bond, county, school → full stack) | Add the new millage(s) and **recompute the target revenue**; for independent per-levy treatment, model each levy separately and recombine | model-policy A4, B6 |
| Change the tax base (assessed → market, LPV → FCV, etc.) | The `taxable_land_value` / `taxable_improvement_value` construction cell | model-policy A1, A2 |
| Dual rates (homestead vs non-homestead) | Split the frame, model each independently, recombine | model-policy B5 |

If a request doesn't fit the table, fall back to `model-policy.md` and reason from the
mechanics — don't force it into the wrong row.

---

## Pipeline

### Step 1 — Locate and snapshot
- Confirm `cities/<city>/model.ipynb` exists (else redirect to `/lvt-city`).
- Read the constants cell and the current `analysis/data/<city>.csv`. Record: `MODEL_TYPE`,
  ratio/abatement %, land & improvement millages, modeled current revenue, and median
  `tax_change_pct` per category. This is the **"before"** snapshot.
- If you need to understand a non-obvious current choice, consult the city's
  `analysis/explainers/<city>.md` if present, or run a quick read of the relevant cell.

### Step 2 — Interpret and confirm the change
- Translate the request into concrete parameter edits using the taxonomy.
- Restate it to the user as `old → new` for each parameter. Ask one question only if
  genuinely ambiguous (rate source for a new levy; which use-codes a vague exemption means).

### Step 3 — Edit the notebook surgically
- Make the minimal edits. Update `MODEL_TYPE` to reflect the new model so the export and
  cross-city labels stay correct.
- If the change alters which variable holds the millages (split-rate → abatement), update
  the names passed to `save_standard_export` accordingly, but keep the closing pattern's
  structure intact.
- Do **not** alter the census-join / export / report / parcel-map cells beyond required variable names.

### Step 4 — Re-execute
```bash
cd /path/to/LVTShift/cities/<city> && \
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=600 \
  --ExecutePreprocessor.kernel_name=python3 \
  model.ipynb 2>&1
```

### Step 5 — Validate
Run the four `validate.md` gates: revenue match (and neutrality), distribution sanity for
the new parameters, census coverage, PNG output. Note that expected distribution signs
differ by reform (e.g. a 2:1 split moves everything less than 4:1; a 100% abatement zeroes
improvement tax entirely).

### Step 6 — Cross-city refresh
Re-run `analysis/cross_city.ipynb` so the comparison picks up the refined export.

### Step 7 — Report before/after
Present a compact diff:

```markdown
## <City> refinement: <one-line description>

| | Before | After |
|---|---|---|
| Model type | split_rate_4to1 | split_rate_2to1 |
| Land millage | 28.6765 | 18.1 |
| Improvement millage | 7.1691 | 9.05 |
| Modeled revenue | $229.97M | $229.97M (neutral) |
| SFR median change | -9.4% | -4.7% |
| Vacant median change | +126.5% | +63% |
| Validation | 4/4 gates | 4/4 gates |

<2–3 sentences on what the change means and any limitation it does or doesn't fix.>
```

Then **link the refreshed interactive map** as the visual payoff — it was regenerated by the
re-execute: `[Open the refined <City> parcel map](analysis/reports/<city>/parcel_map.html)`. If the
run printed `serve over http` (a tiled large city), tell the user to run
`python3 scripts/serve_maps.py` from the repo root and open
`http://localhost:8000/analysis/reports/<city>/parcel_map.html` instead.

If a known limitation persists (e.g. a flat assessor land ratio makes residential results
an artifact regardless of ratio), say so — a smaller split ratio shrinks the magnitude but
does not fix a collapsed signal. Offer to run `explain-model` to regenerate the full
methodology explainer for the refined model.

---

## Guardrails
- Never skip re-validation or the cross-city refresh.
- Never commit unless the user asks.
- If the refinement makes the model worse (breaks a gate, blows the revenue target),
  report it honestly and propose the fix rather than leaving a broken notebook.
- Scenario comparison: if the user wants to **keep** the old model and compare (e.g. "show
  2:1 next to 4:1"), don't overwrite — copy to `cities/<city>/model_<variant>.ipynb`, edit
  that, and export to `analysis/data/<city>_<variant>.csv`. Default is in-place refinement.
