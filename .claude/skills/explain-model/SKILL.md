---
name: explain-model
description: Produces a plain-language but rigorous methodology explainer for an existing LVTShift city model — what data was used, which levies were and were NOT modeled, how much revenue was modeled, how full and partial exemptions were applied (and how they interact), how property categories were built, the land/improvement split method, and the model's limitations. Use when the user says "explain the model for [city]", "explain-model [city]", "how was [city] modeled", "what choices were made for [city]", "document the methodology for [city]", or "what are the limitations of the [city] model". Independently verifies the notebook against the export and (when present) re-probes the cached parcel data to surface artifacts the notebook does not state.
---

# Skill: Explain a City Model

Invoked when the user says **"explain the model for [city]"**, **"explain-model [city]"**,
**"how was [city] modeled"**, or asks to document a model's methodology / limitations.

You are writing a **transparency and methodology audit** of a model that already exists.
The audience is a reviewer who needs to trust — or challenge — the model's results: a
CLE analyst, a partner, a journalist, a city staffer. The deliverable's value is *honesty
about choices and limits*, not a restatement of what the notebook says about itself.

The output is a Markdown explainer written to `analysis/explainers/<city>.md` (local-only,
gitignored — do not commit it).

---

## Operating principles

These govern every explainer. If you find yourself relaxing one, stop and reconsider.

1. **Audit, don't paraphrase.** The notebook's own markdown describes what the author
   *intended*. Your job is to verify it against the executed outputs, the standardized
   export, and (when available) the raw parcel data. Where the notebook's narrative and
   the data disagree, the data wins and you say so.

2. **Every number is traced to a source.** Revenue figures, millages, parcel counts, and
   match rates are quoted from the executed notebook outputs or recomputed from the export
   — never invented or rounded from memory. Cite the cell or the column you got each from.

3. **Name what was NOT modeled as clearly as what was.** The most important sentences in
   the explainer are usually about scope exclusions: secondary/bond levies, overlapping
   county/school/special-district levies, exempt classes, TIF, personal property. A reader
   who doesn't know what's excluded will over-read the results.

4. **Full and partial exemptions are different mechanisms — explain both, and their
   order.** Do not collapse them. State (a) what makes a parcel *fully* exempt and how it
   leaves the revenue-neutral base, (b) what *partial* relief (dollar exemptions,
   abatements) applies and in what order it hits improvement vs. land, (c) any percentage
   caps / circuit breakers, and (d) any post-tax credits — and the sequence in which these
   independent mechanisms stack.

5. **Hunt for collapsed signal.** A revenue-neutral split-rate redistributes the *same*
   total, so a parcel's % change is a pure function of its land share of value. If an
   assessor books a flat land ratio for a class of property, every such parcel moves by an
   identical %, and the result is an artifact of bookkeeping, not land economics. Always
   run the land-ratio uniformity probe (below) when data is present. This is the single
   highest-value check the skill performs.

6. **Plain language, precise mechanics.** Write for a smart non-modeler. Define jargon
   (millage, assessment ratio, LPV, tax capacity) on first use. But never sacrifice
   precision: "$1.2658 per $100 of assessed value = 12.658 mills" beats "about 1.3%".

7. **Limitations are a section, not an afterthought.** End with an explicit, ranked list
   of what the model cannot tell you and why. If a result is an artifact (principle 5),
   it belongs at the top of that list.

---

## Inputs to gather

For city slug `<city>`, locate and read (skip gracefully if absent):

| Artifact | Path | Use |
|---|---|---|
| Model notebook | `cities/<city>/model.ipynb` | Code + executed outputs — the authoritative record of what was run |
| Standardized export | `analysis/data/<city>.csv` | 16-column cross-city export — recompute revenue, category, exemption, demographic coverage |
| Cached parcel data | `cities/<city>/data/*.gpq`, `*.parquet`, `*.csv` | Deep-probe source (raw land/improvement values, classes, use codes) |
| Legality brief | `analysis/legal/<city>.md` | Which levy/vehicle the legal analysis assumed — cross-check against what was modeled |
| Core utilities | `lvt/lvt_utils.py`, `lvt/census_utils.py` | Ground-truth the mechanics of the functions the notebook calls |

Determine **probe depth** from what's present:
- **Deep probe** — cached parcel data exists → run all data diagnostics below.
- **Fallback** — only notebook + export exist → derive everything inferable from those,
  and explicitly flag each check you could not run for lack of data.

---

## How the modeling functions actually work (ground truth)

Read the relevant function in `lvt/lvt_utils.py` before describing it, but these are the
invariants to anchor on:

- **`calculate_current_tax`** — `tax = taxable_value × millage / 1000`. Millage is always
  per $1,000. A rate quoted "per $100 of assessed value" is `rate × 10` mills.
- **Order of operations inside the tax computation** (independent, stacked mechanisms):
  1. **Partial relief** (`exemption_col`, a dollar amount): subtracted from **improvement
     value first**, and only the remainder spills onto **land** (`_compute_adjusted_tax_components`).
  2. **Full exemption** (`exemption_flag_col`): forces both land and improvement taxable
     values to **zero** — applied *after* partial relief, so a fully-exempt flag overrides
     any partial relief math.
  3. **Millage** multiply.
  4. **Percentage cap** (`percentage_cap_col`): caps tax at a share of property value
     (circuit breakers, e.g. the AZ 1%-of-FCV residential cap, Indiana caps).
  5. **Post-tax credits** (`credit_col` fixed $, `credit_rate_col` share of tax),
     clipped at zero.
- **`model_split_rate_tax`** — solves revenue-neutral land & improvement millages with
  `land_millage = ratio × improvement_millage`, iterating when caps/credits are present.
  The fully-exempt parcels must be **excluded from the solver** and recombined with
  `new_tax = 0` afterward, or revenue neutrality is wrong.
- **`model_full_building_abatement` / `model_stacking_improvement_exemption`** — abatement
  reforms (exempt some % of improvement value). Spokane applies these **per levy**, with
  revenue neutrality maintained independently for each levy district.
- **`save_standard_export`** — if no `exempt_flag_col` is passed, `is_fully_exempt` is
  *derived* as (taxable_land == 0 AND taxable_improvement == 0 AND current_tax == 0). Note
  whether the city passed an explicit flag or relied on the derivation.

---

## Pipeline

### Step 1 — Confirm target and inventory artifacts
Resolve the city slug. List which of the five artifacts exist. State the probe depth you
will use. If the notebook is missing, stop and tell the user there is no model to explain.

### Step 2 — Extract the modeling spec from the notebook
From the constants cell and the executed outputs, capture verbatim:
- `CITY_NAME`, FIPS, `MODEL_TYPE`, `LAND_IMPROVEMENT_RATIO` (or abatement %).
- The tax base column and what it represents (market FCV / fractional assessed / LPV /
  Minnesota Tax Capacity / derived-from-bills).
- The current millage(s) and their **source** (budget doc / county levy table / derived
  from observed bills / CAFR). Note derived vs. published.
- Every `lvt.*` function the notebook calls, with the exact column arguments.
- The land/improvement split method (direct values, FCV-ratio allocation of a combined
  base, tax-capacity split, condo collapse, etc.).

### Step 3 — Reconcile revenue and levy scope
- **Modeled revenue:** quote the modeled current revenue and the revenue-neutral new
  revenue from the outputs; confirm they match (revenue neutrality). Recompute the sums
  from the export CSV as an independent check.
- **Official figure & gap:** quote the validation gap and the official source. State the
  tax year of the data vs. the tax year of the official figure if they differ.
- **Levies modeled vs NOT modeled:** name the specific levy modeled (e.g. "City primary
  only"). Then enumerate the levies that exist on a parcel in this jurisdiction but were
  **excluded** (secondary/bond, county, school district, community college, special /
  improvement districts, statewide centrally-valued levies). If the legality brief exists,
  confirm the modeled levy matches the vehicle the legal analysis assumed.

### Step 4 — Exemption analysis (full, partial, caps, credits — and their independence)
- **Full exemptions:** what flags a parcel fully exempt (use code range, class, explicit
  flag, or derived). Count them and their share of parcels (from the export's
  `is_fully_exempt` or the data). Confirm they were excluded from the revenue-neutral base.
- **Partial / dollar relief:** is any applied? If so, to which column first (improvement,
  then land) and from what source (abatement file, homestead exemption, etc.). If none,
  say so explicitly — "no partial exemptions were modeled" is a finding.
- **Percentage caps / circuit breakers:** present? (e.g. AZ 1% residential cap, Indiana
  circuit breaker, South Bend.) Were they modeled, or noted-but-not-modeled? A cap that is
  legally real but omitted from the model is a limitation.
- **Credits:** any post-tax credits modeled?
- **Independence & order:** state plainly how these mechanisms stack (partial relief →
  full-exempt zeroing → millage → cap → credits) and that they are applied per-parcel
  independently. For per-levy models (Spokane), explain that exemptions/abatements are
  applied and revenue-balanced **separately per levy**.

### Step 5 — Property category construction
- Describe the source field(s) used (use code, class code, tax district) and the mapping
  logic (flat map vs. function with subcode splits).
- State the **$0-improvement → Vacant Land** override and whether it was applied.
- Report the category distribution (counts) from the export.
- Flag oversized residual buckets: if `Other`, `Other Residential`, or `Other Commercial`
  exceeds ~10% of parcels, say so and note what's hiding in them.

### Step 6 — Land/improvement split + DEEP PROBE for artifacts
Describe how each parcel's tax base was split into land vs. improvement. Then, **when data
is present**, run these diagnostics and report the results:

1. **Land-ratio uniformity (the key probe).** For each major category, compute
   `land_ratio = land_value / (land_value + improvement_value)` and report the median,
   std, and the **share of parcels at the single most common rounded value**. A category
   where >50% of parcels share an identical land ratio is a flat-allocation artifact —
   the split-rate cannot differentiate those parcels, and their tax change will be
   uniform. (This is exactly the Maricopa/Phoenix residential flat-20% case.)
2. **Collapsed % change.** From the export, for each category report the share of taxable
   parcels whose `tax_change_pct` rounds to the category median. A near-100% share
   confirms a collapsed signal.
3. **Coverage checks.** Census match rate (`std_geoid` / `median_income` non-null share)
   and what it implies for the equity charts; exempt share; parcels with $0 or negative
   values.

In **fallback** mode, attempt diagnostics 2 and 3 from the export alone, and state that
the land-ratio probe (1) could not be run because the raw data was absent.

### Step 7 — Synthesize limitations
Rank the limitations by how much they constrain the conclusions a reader can draw. Lead
with any collapsed-signal artifact. Include: excluded levies, omitted caps, census
coverage gaps, tax-year drift, residual-bucket coarseness, and any assessor data-quality
issue. For each, state in one line *what conclusion it undermines*.

### Step 8 — Write the explainer
Write to `analysis/explainers/<city>.md` using the template below. Confirm
`analysis/explainers/` is gitignored before writing (it is, by repo `.gitignore`). Report
the path to the user and give a 4–6 sentence summary of the most important findings —
especially any limitation that changes how the results should be read.

---

## Output template

```markdown
# <City>, <State> — LVT Model Methodology & Limitations

**Model:** <model_type, e.g. 4:1 split-rate, revenue-neutral>
**Explainer generated:** <YYYY-MM-DD>  ·  **Probe depth:** <deep / fallback>
**One-line read:** <the single most important thing a reader should know — often a limitation>

## 1. What was modeled
- Jurisdiction & government body, levy modeled, reform modeled, revenue-neutrality basis.

## 2. Data provenance
- Source endpoint(s) / file(s), tax year, parcel count, join method + match rate, caching.
- Independent vs. derived figures.

## 3. Tax base & millage
- What value the rate is applied to (market / assessed / LPV / tax capacity) and why.
- Assessment ratios / class structure preserved.
- Current millage(s) and source; modeled land & improvement millages and their ratio.

## 4. Revenue
| | Amount | Source |
|---|---|---|
| Modeled current revenue | $ | notebook cell N / export |
| Revenue-neutral new revenue | $ | notebook cell N |
| Official figure | $ | <source, tax year> |
| Gap | % | <explanation if non-trivial> |

## 5. Levies modeled vs NOT modeled
- Modeled: <…>
- Excluded (and why): secondary/bond, county, school, special districts, centrally-valued, …

## 6. Exemptions
- **Full:** trigger, count/share, exclusion from base.
- **Partial / dollar relief:** mechanism + order (improvement first, then land), or "none modeled".
- **Caps / circuit breakers:** modeled / noted-not-modeled / n/a.
- **Credits:** …
- **How they stack:** partial relief → full-exempt zeroing → millage → cap → credits, per parcel; per-levy independence if applicable.

## 7. Property categories
- Source field(s), mapping logic, $0-improvement override, distribution table, residual-bucket notes.

## 8. Land/improvement split
- Method, and the deep-probe diagnostics (land-ratio uniformity table, collapsed-% table).

## 9. Limitations (ranked)
1. <most consequential — e.g. collapsed residential signal> — undermines: <which conclusion>.
2. …

## 10. What the model CAN and CANNOT support
- Can: <claims the data genuinely supports>.
- Cannot: <claims it does not>.
```

---

## Output checklist
- [ ] Every figure traced to a notebook cell or recomputed from the export.
- [ ] Levies NOT modeled are enumerated, not just the one that was.
- [ ] Full vs. partial exemptions distinguished, with stacking order stated.
- [ ] Land-ratio uniformity probe run (deep) or explicitly skipped (fallback).
- [ ] Limitations ranked, collapsed-signal artifacts first.
- [ ] Written to `analysis/explainers/<city>.md`; path reported; not committed.
- [ ] If `analysis/reports/<city>/parcel_map.html` exists, linked it in the chat wrap-up as the visual companion (`[Open the <City> parcel map](analysis/reports/<city>/parcel_map.html)`; for a tiled city, note `python3 scripts/serve_maps.py`).
