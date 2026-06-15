# Skill: Validate

Sub-skill called from `model-city/SKILL.md` Step 5.

Run these checks after executing the notebook. A city passes when all five gates are green.

Gates 1–4 confirm the model *ran correctly*. **Gate 5 confirms the results are *believable*** — it is
the one that catches data artifacts the mechanics can't. Never report a model as done until Gate 5
has been worked through and every surprising category can be explained.

---

## Gate 1 — Revenue Match

Open the executed notebook and find the revenue validation output in Section 4.

```
Modeled: $XX,XXX,XXX   Official: $XX,XXX,XXX   Gap: +X.XX%
```

**Pass**: gap < 2%  
**Acceptable**: gap 2–5% with a documented explanation  
**Fail**: gap > 5% → stop, return to `model-policy.md`

Common causes of large gaps:
- TIF parcels included in city revenue (should be excluded)
- Exempt parcels not flagged correctly
- Assessment ratio applied to only one value column
- Wrong millage (e.g., using county rate for city-only model)
- Dollar exemptions not applied before multiplying by millage

---

## Gate 2 — Distribution Sanity

Check the category summary table output from `print_category_tax_summary()`.

Expected directional signs for a standard 4:1 split-rate:

| Category | Expected direction |
|---|---|
| Vacant Land | Large increase (+50% to +200%) |
| Transportation - Parking | Large increase |
| Commercial | Moderate increase or mixed |
| Agricultural | Mixed (depends on improvement ratio) |
| Single Family Residential | Modest decrease (-5% to -20%) |
| Small Multi-Family (2-4 units) | Decrease |
| Large Multi-Family (5+ units) | Decrease |

**Red flags that indicate a modeling error:**
- Single Family Residential shows a large increase (>20%) on average → check land/improvement value split
- Vacant Land shows a decrease → land and improvement columns may be swapped
- All parcels show 0% change → split-rate model may not have run (check `new_tax` column)
- Standard deviation of `tax_change_pct` < 1% → likely no variation, something collapsed

Quick check:
```python
print(gdf.groupby('PROPERTY_CATEGORY')[['current_tax', 'new_tax', 'tax_change_pct']].agg({
    'current_tax': 'sum',
    'new_tax': 'sum',
    'tax_change_pct': 'median'
}).round(2))
```

---

## Gate 3 — Census Coverage

Check the census join line in the notebook output:
```
Census join: XX.X% matched
```

**Pass**: ≥ 85% matched  
**Acceptable**: 70–85% (note in a markdown cell why some parcels don't match — e.g., parcels on city border, water parcels, county slivers)  
**Fail**: < 70% → investigate

If coverage is low:
1. Check that parcel geometries are valid: `gdf.geometry.is_valid.mean()`
2. Check CRS: `gdf.crs` should be a projected CRS or geographic — `match_to_census_blockgroups` handles reprojection internally
3. Check that parcel centroids fall within the county boundaries (parcels on the city edge may fall outside the county FIPS boundary used for Census block group download)

Also verify that census columns are present in the exported CSV:
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('analysis/data/<city>.csv')
print(df[['std_geoid', 'median_income', 'minority_pct', 'black_pct']].describe())
print('Non-null pct:', df['median_income'].notna().mean())
"
```

---

## Gate 4 — PNG Output

Check that the standard report was generated:
```bash
ls -la analysis/reports/<city>/
```

Expected files (up to 7, depending on census coverage):
```
category_impact.png
ten_pct_share.png
distribution.png
income_quintile_non_vacant.png        # only if census coverage ≥ 70%
income_quintile_residential.png       # only if census coverage ≥ 70%
minority_quintile_non_vacant.png      # only if census coverage ≥ 70%
minority_quintile_residential.png     # only if census coverage ≥ 70%
```

If fewer than 3 PNGs exist, the report cell failed. Check the notebook output for errors.

If census PNGs are missing despite good coverage, the census columns may not have been passed into `save_standard_export`. Run:
```python
import pandas as pd
df = pd.read_csv('analysis/data/<city>.csv')
print(df['median_income'].notna().sum(), 'parcels have income data')
```
If 0 or very few → the census propagation bug struck. See `build-notebook.md` for the fix pattern.

---

## Gate 5 — Read the Results (Artifact Scan)

**This is the gate that catches "garbage that ran cleanly."** A model can pass Gates 1–4 — revenue
matches, signs look right, charts render — and still be wrong because the *input data* lied. Your job
here is to read the category results like a skeptic and explain every surprising row before publishing.
The canary is almost always **a category (or a few) that looks off**: too uniform, too extreme, or
economically implausible.

Run this diagnostic and actually look at it:

```python
import numpy as np
d = gdf[gdf['full_exmp'] == 0].copy()      # modeled parcels only
d['bldg_share'] = d['taxable_improvement_value'] / (
    d['taxable_land_value'] + d['taxable_improvement_value']).replace(0, np.nan)
# For a building exemption the max possible increase is the land-only outcome:
#   ceiling = land_millage / current_combined_rate - 1   (everything that is "all land" lands here)
summary = d.groupby('PROPERTY_CATEGORY').agg(
    n=('tax_change_pct', 'size'),
    median_pct=('tax_change_pct', 'median'),
    median_bldg_share=('bldg_share', 'median'),
    pct_zero_bldg=('taxable_improvement_value', lambda s: (s <= 1000).mean()),
).sort_values('median_pct', ascending=False)
print(summary.round(3))
```

Then walk the **canary checklist**. If any fires, the result is suspect until proven otherwise:

1. **Ceiling clustering.** Several *distinct* categories share a near-identical, extreme median — e.g.
   Retail, Parking, Other Commercial all at the same +54% as Vacant Land. Under a building exemption no
   parcel can rise more than `land_millage / current_rate − 1`; categories piling up there are being
   seen as **bare land**. Real, varied property types should *not* converge on one number.
2. **Implausible land/building split.** Median building share by category against priors: built-up
   commercial/office/retail/industrial should be ~20–60% building; if a built category shows ~0–1%
   building share, the **improvement value is missing or a placeholder**. Residential that is nearly
   constant land-share across very different homes signals a **flat assessor land ratio**.
3. **Placeholder / off-parcel value.** A high `pct_zero_bldg` for a category that obviously has
   buildings (retail, apartments) ⇒ values booked off-parcel (leasehold / personal property), assessed
   land-only, or condo/parent-parcel collapse. Cross-check a building-characteristics source (square
   footage) to confirm the building physically exists.
4. **Direction sanity.** A building exemption should *lower* tax on building-heavy parcels (apartments,
   mixed-use, hotels) and *raise* it on land-heavy ones; a split-rate likewise. A building-heavy
   category rising sharply (or a land-only one falling) means the land/improvement columns are swapped
   or mis-valued.
5. **Base reconciliation.** Compare the modeled taxable base to an independent control (certified levy ÷
   rate, or county AV × the city's share). A shortfall >~10% points to missing value — personal
   property, state-assessed utilities, or (as in Seattle) missing commercial improvements.
6. **Tiny-N caution.** Categories under ~50 parcels swing wildly — don't over-read them, but a tiny
   category sitting exactly at the ceiling can still flag a data problem worth tracing.

**If a canary fires — do not publish the result. Instead:**
1. Trace it to the parcel level (dump the suspect category's land / improvement / sqft).
2. Decide: **data artifact** vs. **real economic result**. (Real: a city genuinely dominated by surface
   parking will show parking at the ceiling — that's fine. Artifact: retail buildings valued at $1,000.)
3. If an artifact, **fix the data** — re-pull, augment, collapse condos, or impute from a defensible
   source (e.g. building sqft × observed $/sqft), and **document the fix** in the notebook limitations.
4. Re-run and re-scan. Only then is the city done.

**Worked precedents (known artifacts this gate is meant to catch):**
- **Seattle / King County** — income-producing commercial parcels carry a **$1,000 placeholder**
  improvement value (building value held off-parcel); retail/parking/commercial pinned at the increase
  ceiling. Fixed by cost-approach imputation from the Commercial Building file (see the Seattle model's
  Section 1b and `data/assessor/build_value_corrections.py`).
- **Maricopa / Phoenix** — the assessor books residential **land at a flat ~20% of value**, so the
  per-home land signal is an artifact; a split ratio cannot fix a collapsed signal.
- **St. Paul / Ramsey** — condos given token **$1,000/unit land**; collapse units by `PlatID` into
  buildings before modeling.

---

## Post-Validation Summary

Document in a notebook markdown cell:

```markdown
## Validation Summary

| Check | Result |
|---|---|
| Revenue match | +1.3% vs. official $45.2M (City of Fort Collins CAFR 2024) |
| Parcel count | 42,187 modeled city parcels (+1,803 fully-exempt held out & excluded from charts) |
| Census coverage | 94.1% matched to block groups |
| PNGs generated | 7 of 7 |
| Artifact scan (Gate 5) | Clean — building shares plausible by category; no ceiling clustering; base reconciles within 4% |
| SFR median change | -8.4% |
| Vacant land median change | +134.2% |
```

---

## If a Gate Fails

| Gate | Failure | Where to look |
|---|---|---|
| Revenue | > 5% gap | `model-policy.md` Part C — check TIF filter, exemptions, millage source |
| Distribution | SFR increases | Check land/improvement column mapping in Section 4 |
| Census | < 70% matched | Check parcel CRS, geometry validity, county FIPS code |
| PNGs | Missing census charts | Check census propagation before `save_standard_export()` call |
| Artifact scan | Categories pinned at the ceiling / implausible building share / base shortfall | Trace to parcel level; fix the source data (re-pull, collapse condos, or impute from building sqft) and document — see Gate 5 precedents |
