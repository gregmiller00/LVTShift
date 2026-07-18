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

**Fairness lens.** Beyond who-wins/loses, score the analysis the way an IAAO ratio study would. `assessment_ratio_stats(df, assessed_col, market_col)` measures how (un)fair the *current* base is — median ratio (level), COD (uniformity / horizontal equity), and PRD / PRB (regressivity / vertical equity), each with IAAO-standard flags. `reassessment_equity(df, ...)` stratifies the winners/losers by income quintile, racial-composition band (IAAO §7.3), and value decile (pass `value_col` — the vertical equity of the shift), with optional per-stratum current-base COD (`ratio_cols`) and bootstrap confidence intervals (`n_boot`, so thin strata aren't read as precise). `lvt.viz.reassessment_equity_chart` renders any breakdown (median change + % winners, with the COD gradient overlaid). See Part D of `cities/reading/model_reassessment.ipynb`.

### Wage-Tax-for-Land-Tax Swap (different tax instrument, not a property-tax reform)

Model eliminating a non-property tax (e.g. Philadelphia's Wage & Earnings Tax) and replacing its revenue with a new, separate, pure land value tax — the existing property tax is left untouched. This is a different modeling paradigm than the reforms above: there's no parcel-level wage data, so the analysis runs at census tract granularity for the eliminated tax and rolls the parcel-level modeled land tax up to the same tracts for comparison. Use `lvt.wage_tax_utils` together with the tract-level fetch functions in `lvt.census_utils` (`get_census_tract_data`, `get_census_tracts_shapefile`, `match_to_census_tracts`, `aggregate_parcels_to_geography`). See **`docs/WAGE_TAX_SWAP_GUIDE.md`** for the full methodology, data sources, and limitations, and `cities/philadelphia/model_wage_tax_swap.ipynb` for the worked example.

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
  --ExecutePreprocessor.kernel_name=python3 \
  model.ipynb 2>&1

# Re-run cross-city comparison
cd analysis && \
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=300 \
  --ExecutePreprocessor.kernel_name=python3 \
  cross_city.ipynb 2>&1
```

---

## Optional: Transit Walk-Shed Parking Analysis

Quantifies how much land within a 10-minute walk of high-frequency transit is
consumed by parking lots, and what a split-rate shift does to those parcels.
First built as Step 9 of `cities/st_paul/model.ipynb` — copy that section and
swap the city-specific pieces. All machinery lives in `lvt/transit_utils.py`.

Requires `osmnx`, `folium`, and `mapclassify` (`pip install osmnx folium mapclassify`).

```python
from lvt.transit_utils import (
    download_gtfs_from_mobility_database, gtfs_route_stops,
    get_walk_network, route_walk_sheds, fetch_osm_parking,
    flag_parking_parcels, walk_shed_stats,
)

# 1. GTFS: find the transit agency in the Mobility Database catalog
gtfs_path = download_gtfs_from_mobility_database(
    'data/gtfs.zip', provider='Valley Metro', subdivision='Arizona')
gtfs = gtfs_route_stops(gtfs_path, route_selector='Light Rail')  # prefix or callable mask

# 2. Filter stops to the city boundary, then route 800 m walk sheds
#    (use the city's UTM zone, e.g. EPSG:26912 for Phoenix)
G = get_walk_network(city_boundary_utm, 'EPSG:26912', 'data/walk.graphml')
walk_sheds = route_walk_sheds(G, stops_utm, cutoff_m=800)

# 3. OSM parking (assessor codes usually miss surface lots) + parcel flags
osm_parking = fetch_osm_parking(city_boundary_gdf, 'data/osm_parking.gpkg', to_crs='EPSG:26912')
parcels_flagged = flag_parking_parcels(modeled_parcels_utm, osm_parking.union_all(),
                                       category_col='PROPERTY_CATEGORY')

# 4. Stats per line (column names are parameters — match the city's schema)
row = walk_shed_stats(walk_sheds.union_all(), all_parcels_utm, parcels_flagged,
                      osm_parking.union_all(), label='All lines', n_stops=len(stops_utm),
                      taxable_flag_col='pays_city_tax', new_tax_col='new_tax_tc')
```

City-specific decisions to revisit:
- **Route selection**: `route_selector` — Twin Cities uses the `'METRO'` long-name
  prefix; other agencies need a different prefix or a callable on the routes table.
- **Walk-shed parameters**: 800 m cutoff (10 min at 80 m/min) and 60 m street
  buffer (one parcel depth) are defaults, not constants of nature.
- **Parking definition**: a parcel is a parking lot if its assessor category says
  so or OSM parking covers ≥ 50% of it. Underground garages and on-street lanes
  are excluded.
- **Caching**: the walk graph (~60 MB GraphML) and routed sheds are cached in
  `data/` — routing ~100 stops takes ~10 minutes fresh, seconds cached. GTFS and
  OSM are living datasets; note the snapshot date.

The St. Paul notebook also builds an interactive folium map (CartoDB positron,
parking choropleth by underlying land value/acre, GTFS brand-colored route lines,
a pinned per-line outcomes panel) and saves a standalone copy to
`data/transit_parking_map.html`. The notebook must be `jupyter trust`-ed for the
map to render inline.
