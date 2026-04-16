# LVT Modeling Guide

To add a new city, work through these skills in order. Each skill is self-contained — read it, do the work it describes, then move to the next.

---

## Skills

1. **[Fetch Data](skills/fetch-data.md)** — Find the county ArcGIS endpoint, inspect it, download parcel data, filter to the city, validate completeness.

2. **[Model Tax](skills/model-tax.md)** — Identify the correct millage, implement exemption logic, classify properties, run the split-rate or abatement model, validate revenue neutrality.

3. **[Validate Results](skills/validate-results.md)** — Check revenue match against official figures, confirm distribution sanity, verify Census join, check the export CSV.

4. **[Export & Visualize](skills/export-visualize.md)** — Call `save_standard_export()`, produce the standard 5-chart suite using consistent styles.

---

## Notebook structure

Every city notebook follows the same 7-section structure. See [notebook-template.md](skills/notebook-template.md) for the template with annotated code.

| Section | Contents | City-specific? |
|---|---|---|
| 1. Configuration | All parameters, imports, `apply_lvt_style()` | Yes |
| 2. Data | Fetch or load from cache | Yes |
| 3. Preprocessing | Filtering, validation, condo collapse | Yes |
| 4. Tax Modeling | Current tax + LVT model | Yes |
| 5. Export | `save_standard_export()` call | Minimal (args only) |
| 6. Analysis | Category summaries, policy analysis | No |
| 7. Equity & Visualization | Census join, quintile charts | No |

---

## Standard CSV output

Every city produces `analysis/data/<city>.csv` with these 16 columns:

| Column | Description |
|---|---|
| `city` | Lowercase slug |
| `property_category` | Standardized property type |
| `current_tax` | Current tax ($) |
| `new_tax` | Modeled LVT tax ($) |
| `tax_change` | new - current ($) |
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

**Model type format:** `<kind>:<param>[,<kind>:<param>]`
- `split_rate:4.0` — 4:1 land-to-improvement ratio
- `abatement:50pct` — 50% building abatement
- `abatement:100pct` — full building exemption
- `exemption:50000` — $50,000 dollar base exemption on improvements
- Stacked: `split_rate:4.0,exemption:50000`

---

## Cross-city analysis

Once CSVs exist for multiple cities, open `analysis/cross_city.ipynb` to compare results across cities — revenue figures, equity impacts, property category distributions.

## Regression validation

After any code change to `lvt_utils.py` or `viz.py`, run `analysis/validate_all.ipynb` to confirm all cities produce the same metrics as before.

---

*Previous guide content is archived in `LVT_MODELING_GUIDE_ARCHIVE.md`.*
