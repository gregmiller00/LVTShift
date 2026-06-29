# LVT Modeling Guide

To add a new city, invoke the **model-city** skill — type `/lvt-city`, `model LVT for [city]`, or `add [city] to LVTShift`. It runs the full pipeline end-to-end and calls the sub-skills below in order.

---

## Skills

The pipeline has one master orchestrator and four sub-skills:

| Skill | File | What it does |
|---|---|---|
| **Model City** (master) | `.claude/skills/model-city/SKILL.md` | Policy questions → full 7-step pipeline |
| **Discover Data** | `.claude/skills/discover-data.md` | Find ArcGIS endpoint, download, filter, validate |
| **Model Policy** | `.claude/skills/model-policy.md` | Assessment ratios, millage sources, exemptions, split-rate or abatement |
| **Build Notebook** | `.claude/skills/build-notebook.md` | Canonical 7-section template with exact closing pattern |
| **Validate** | `.claude/skills/validate.md` | Revenue match, distribution sanity, census coverage, PNG output |

---

## Notebook Structure

Every city notebook follows the same 7-section structure:

| Section | Contents |
|---|---|
| 1. Imports & Setup | `sys.path`, imports, constants (`CITY_NAME`, `STATE_FIPS`, `COUNTY_FIPS`, `MODEL_TYPE`) |
| 2. Fetch / Load Data | `get_feature_data_with_geometry()`, city filter, cache to `data/` |
| 3. Classify & Validate | Exemption flags, `PROPERTY_CATEGORY` mapping, revenue validation |
| 4. Current Tax Model | `calculate_current_tax()`, revenue match assertion |
| 5. Split-Rate Model | `model_split_rate_tax()` or `model_stacking_improvement_exemption()` |
| 6. Exploration Charts | Optional city-specific charts (skipped in headless execution) |
| 7. Census Join + Export | Exact canonical pattern — see `build-notebook.md` |

---

## Modeling Approaches

### Split-Rate (most cities)

Land taxed at N× the improvement rate. Both stay revenue-neutral.

```python
land_millage, improvement_millage, revenue, df = model_split_rate_tax(
    df=parcels,
    land_value_col='taxable_land_value',
    improvement_value_col='taxable_improvement_value',
    current_revenue=current_revenue,
    land_improvement_ratio=4.0,
)
```

### Building Abatement (Spokane)

Exempt a percentage of improvement value per levy. See `model-policy.md` Part B6.

```python
df = model_stacking_improvement_exemption(
    df=parcels,
    land_col='land_value',
    improvement_col='improvement_value',
    current_revenue=target_revenue,
    improvement_exemption_pct=0.75,
    building_abatement_floor=100_000,
)
```

### Assessment Ratio (Cincinnati / Ohio)

Apply 35% ratio before modeling. See `model-policy.md` Part B2.

### Tax Capacity (St. Paul / Minnesota)

Split the pre-computed `TaxCapacity` column by improvement ratio. See `model-policy.md` Part B3.

### Derived Millage (Baltimore)

Back-calculate millage from observed tax bills. See `model-policy.md` Part B4.

### Dual Homestead/Non-Homestead (Rochester / New York)

Model homestead and non-homestead parcels with separate millage rates and separate revenue neutrality. See `model-policy.md` Part B5.

### Revenue-Neutral Reassessment (base shift, not rate shift)

Hold revenue constant while updating the *assessed values* — e.g. 1994 CAMA → current AVM — and roll the flat millage back, rather than changing the rate structure. This is the "who wins/loses from a reassessment" baseline that an LVT shift then layers on top. Use `lvt.reassessment`. Values come from the caller (an AVM, market sales, or a manual factor); value *generation* lives in the sibling `berks_open_avmkit` project, not here.

```python
from lvt.reassessment import model_revenue_neutral_reassessment
flat_millage, new_revenue, df = model_revenue_neutral_reassessment(
    df, new_value_col='avm_value', old_value_col='assr_market_value',
    current_millage=CITY_MILLAGE, exemption_flag_col='full_exmp',
)
```

For overlapping taxing districts (county / municipality / school), use `model_multi_district_reassessment` — each district is rolled back to revenue neutrality *within itself* (the Pennsylvania anti-windfall method, 53 Pa.C.S. § 8823), and a parcel's bill is summed across the districts it belongs to. To separate the reassessment effect from an LVT shift, stack `model_split_rate_tax` on the new base and call `decompose_reassessment_and_lvt`. Worked example: `cities/reading/model_reassessment.ipynb`; the real Reading decomposition runs in `cities/reading/model_lycd.ipynb` Section 7b.

---

## Property Categories

Use `PROPERTY_CATEGORY` for category summaries and the standard export. Start with the broad cross-city categories, but keep more detail when the assessor data supports it and the class is large or policy-relevant. In particular, split these classes instead of burying them in broad `Residential` or `Commercial` buckets:

| Category | Use when source data identifies |
|---|---|
| `Condominium` | Residential condo/unit records |
| `Townhome / Rowhouse` | Townhomes, rowhomes, rowhouse developments |
| `Mixed Use` | Mixed commercial/residential parcels or buildings |
| `Hotel` | Hotels, motels, rooming houses, apartment hotels |
| `Office / Commercial Condo` | Office buildings and commercial condo/garage units |
| `Retail / General Commercial` | Retail, shopping centers, supermarkets, one-story/general commercial, minor commercial |
| `Other Commercial` | Meaningful commercial classes not covered above |

Keep `Other Residential`, `Other Commercial`, and `Other` as true residual buckets. If a residual bucket is large, inspect the source class codes and add a better mapping before exporting.

---

## Standard CSV Output

Every city produces `analysis/data/<city>.csv` with these 16 columns:

| Column | Description |
|---|---|
| `city` | Lowercase slug |
| `property_category` | Standardized property type |
| `current_tax` | Current tax ($) |
| `new_tax` | Modeled LVT tax ($) |
| `tax_change` | new − current ($) |
| `tax_change_pct` | Percentage change (null if current = 0) |
| `taxable_land_value` | Post-exemption land value used in model |
| `taxable_improvement_value` | Post-exemption improvement value |
| `is_fully_exempt` | Parcel was zeroed from tax base |
| `std_geoid` | 12-digit Census block group GEOID (nullable) |
| `median_income` | Block group median income (nullable) |
| `minority_pct` | % non-white population (nullable) |
| `black_pct` | % Black/African American (nullable) |
| `model_type` | Encoded model string, e.g. `split_rate:4.0` |
| `land_millage` | Effective land millage per $1,000 |
| `improvement_millage` | Effective improvement millage per $1,000 |

---

## Standard Report Output

`create_city_report()` produces up to 7 PNGs in `analysis/reports/<city>/`:

| File | Description |
|---|---|
| `category_impact.png` | Median % tax change by property category |
| `ten_pct_share.png` | % of parcels with >10% decrease vs. increase |
| `distribution.png` | Histogram of parcel-level tax change % |
| `income_quintile_non_vacant.png` | Median % change by income quintile (all non-vacant) |
| `income_quintile_residential.png` | Same, residential only |
| `minority_quintile_non_vacant.png` | Median % change by minority share quintile |
| `minority_quintile_residential.png` | Same, residential only |

Census charts are generated only when block-group income and minority data are available (≥ 70% Census join rate).

---

## Execution

```bash
# Run one city
cd cities/<city> && \
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=600 \
  --ExecutePreprocessor.kernel_name=cle-venv-new \
  model.ipynb 2>&1

# Re-run cross-city comparison
cd analysis && \
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=300 \
  --ExecutePreprocessor.kernel_name=cle-venv-new \
  cross_city.ipynb 2>&1
```
