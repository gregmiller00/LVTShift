# Skill: Validate Results

## Goal
Confirm that the model produces correct and internally consistent results before publishing analysis. Validation catches wrong millage rates, incorrect exemption logic, bad property classification, and Census join failures.

---

## Validation 1 — Revenue match

**Current tax vs. official budget:**
- Source of truth: city's adopted budget document, or assessor's abstract of assessment.
- Acceptable variance: ±2%.
- Common causes of mismatch:
  - Modeling only the city portion but the assessor data includes school/county.
  - Missing a cap or abatement in the current tax calculation.
  - Filtering out parcels that should be included (or including ones that shouldn't be).
  - Cook County: forgetting to multiply by 3.0 for fractional assessment values.

**New tax vs. current tax (revenue neutrality):**
- `new_tax.sum()` should be within 0.5% of `current_tax.sum()`.
- If it's off by more, `model_split_rate_tax()` likely received the wrong `current_revenue` argument or hit an edge case in its iterative solver.

---

## Validation 2 — Parcel count sanity

Check against published assessor counts (usually in the assessor's annual report or abstract):
- Total parcels in the dataset
- Taxable parcels (non-exempt)
- Fully exempt parcels

---

## Validation 3 — Distribution checks

Run these after modeling and record the results in the notebook:

| Check | Expected range | What mismatch means |
|---|---|---|
| % parcels with tax increase at 4:1 | 55–70% | Wrong ratio, wrong value columns, or very unusual land/improvement ratio for the city |
| Median SFR tax change % at 4:1 | -10% to +10% | SFR in most cities has moderate land share; big swings suggest wrong exemption handling |
| Vacant Land median tax change % | +50% to +500% | Vacant land should always increase substantially under LVT |
| `tax_change.sum()` | < $1,000 | Revenue-neutrality check (should be near zero) |

---

## Validation 4 — Property category sanity

```
df['PROPERTY_CATEGORY'].value_counts()
```

Check:
- Are there any nulls? (Should be zero)
- Does the count by category match what you'd expect for the city? (E.g., Baltimore should have mostly Single Family Residential)
- Are any categories suspiciously small or large?

---

## Validation 5 — Census join

After `match_to_census_blockgroups()`:
- `df['std_geoid'].notna().mean()` — should be >90% for dense urban cities. Values below 80% suggest a CRS mismatch or wrong FIPS code.
- `df['median_income'].notna().mean()` — should roughly equal the GEOID match rate.
- `df['median_income'].describe()` — income values should be in the $20,000–$200,000 range for most U.S. cities.
- Spot-check: do parcels in wealthy neighborhoods have high `median_income` and parcels in low-income neighborhoods have low `median_income`?

**Common Census join failures:**
- Wrong `fips_code` — double-check state FIPS + county FIPS (e.g., Allegheny County PA is 42003).
- Wrong CRS for spatial join — the join uses centroids projected to EPSG:3857; if parcel geometries have a non-standard CRS, the join fails silently.
- Large county — Cook County and LA County require chunked fetching; pass `auto_chunked=True`.

---

## Validation 6 — Export check

After `save_standard_export()`:
- Open the CSV and confirm it has exactly 16 columns.
- Row count should match the full DataFrame (including exempt parcels).
- `property_category` column has no nulls.
- `current_tax`, `new_tax`, `tax_change` columns are numeric with no unexpected NaN values.
- `std_geoid` nulls are explained (rural edges, water parcels, etc.).

---

## Validation 7 — Cross-city sanity (after export)

Once the CSV is in `analysis/data/`, open `analysis/cross_city.ipynb` and add the city. Run the cross-city notebook and check:
- Does the city's distribution look reasonable compared to others?
- Is the revenue figure plausible?
- Does the equity curve (income quintile vs. tax change) follow the expected pattern?

**Verification criteria for this skill:**
- [ ] `current_tax.sum()` within 2% of official figure (documented in notebook)
- [ ] `new_tax.sum()` within 0.5% of `current_tax.sum()`
- [ ] All PROPERTY_CATEGORY values non-null
- [ ] Census GEOID match rate >85% (or documented exception)
- [ ] Export CSV has 16 columns and expected row count
- [ ] No unexplained large outliers in tax_change_pct (>1000% or <-100%)
