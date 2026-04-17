# Skill: Validate

Sub-skill called from `add-city.md` Step 5.

Run these checks after executing the notebook. A city passes when all four gates are green.

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

## Post-Validation Summary

Document in a notebook markdown cell:

```markdown
## Validation Summary

| Check | Result |
|---|---|
| Revenue match | +1.3% vs. official $45.2M (City of Fort Collins CAFR 2024) |
| Parcel count | 42,187 city parcels (expected ~42,000) |
| Census coverage | 94.1% matched to block groups |
| PNGs generated | 7 of 7 |
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
