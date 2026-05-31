# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LVTShift is a toolkit for modeling Land Value Tax (LVT) policy shifts in U.S. cities/counties. It analyzes how shifting from traditional property taxes to land value taxes affects neighborhoods, property types, and demographic groups. Created by the Center for Land Economics.

## Environment Setup

```bash
# Python environment with pandas/geopandas
cd ~/packaging-test && source pkg-test/bin/activate

# Environment variables
cp env.template .env
# Add CENSUS_API_KEY (free at https://api.census.gov/data/key_signup.html)
```

### Loading `.env` in notebooks and scripts

Python does **not** auto-load `.env` files. `os.getenv("CENSUS_API_KEY")` only sees keys
that are already in the process environment, which on Windows (and a fresh shell on
Mac/Linux) usually means it returns an empty string even when `.env` is present.

Every notebook or script that needs `CENSUS_API_KEY` (or any other secret) must call
`load_dotenv` explicitly. The standard pattern, used by the canonical notebook
template (`.claude/skills/build-notebook.md`):

```python
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, '../..')
REPO_ROOT = Path('../..').resolve()
load_dotenv(REPO_ROOT / '.env')
```

Without this, `os.getenv("CENSUS_API_KEY")` returns `""` and the Census/equity sections
silently fall through.

When adding a new script under `scripts/` that needs a secret, replicate the same
pattern at the top of the file.

## Architecture

Five core modules live in the `lvt/` package, used from Jupyter notebooks in `cities/`:

```
lvt/cloud_utils.py     → Fetch parcel data from county ArcGIS FeatureServers
lvt/census_utils.py    → Fetch Census demographics, spatial join to parcels
lvt/lvt_utils.py       → Tax modeling (split-rate, abatement, exemptions)
lvt/policy_analysis.py → Identify vacant land, parking lots, development barriers
lvt/viz.py             → Scatter plots, quintile analysis, demographic charts
```

Notebooks import via the package:
```python
import sys; sys.path.insert(0, '../..')  # from cities/<city>/
from lvt.lvt_utils import model_split_rate_tax
from lvt.cloud_utils import get_feature_data_with_geometry
```

**Data flow**: Fetch parcels (cloud_utils) → calculate current tax → collapse condos by PlatID with imputed land values → model LVT scenarios (lvt_utils) → merge Census demographics (census_utils) → analyze equity impacts (viz/policy_analysis)

### Condo Collapse

Ramsey County assigns condo units token land values ($1,000/unit), not real assessments. Before modeling, condos are collapsed by `PlatID` into buildings:
- **Sum**: EMVTotal1, TaxCapacity, TotalTax1
- **Impute**: EMVLand1/EMVBuilding1 from neighborhood (District Council) median IR of non-condo parcels
- Geometries are unioned via `collapse_geometries()`
- Both collapse options (A: first-value, B: imputed IR) are in the code; Option B is used downstream

### Key Design Patterns

- **Flexible column names**: Every function accepts column names as parameters (no hardcoded field names) to support different jurisdictions' data schemas
- **Revenue neutrality**: All tax models maintain identical total revenue. Uses `(target_revenue * 1000) / denominator` for rate calculation. Iterative solver (up to 40 iterations) when percentage caps exist
- **Millage rates are per $1000**: `model_split_rate_tax()` returns millage in per-$1000 units. Tax = `value * millage / 1000`
- **Exemption hierarchy**: Full exemption flags applied first → dollar exemptions to improvements → remaining to land
- **Centroid-based spatial joins**: Parcels joined to Census block groups via centroids in EPSG:3857 to avoid boundary edge cases
- **Census fallback chain**: TIGERweb single request → chunked by tract → FTP shapefile download

### lvt_utils.py (core modeling)

Key functions:
- `model_split_rate_tax(df, land_value_col, improvement_value_col, current_revenue, land_improvement_ratio)` → returns `(land_millage, imp_millage, revenue, df_with_new_tax)`
- `calculate_category_tax_summary(df, category_col, current_tax_col, new_tax_col)` → summary stats by property type
- `ensure_geodataframe(df)` → handles WKT, WKB hex, and binary geometry encodings

Two modeling approaches used in St. Paul:
1. **EMV approach**: Split-rate applied to raw Estimated Market Values (EMVLand, EMVBuilding)
2. **Tax Capacity approach**: Split TaxCapacity by improvement ratio (IR = Building/Total EMV), then apply split-rate. Preserves Minnesota's class rate preferences.

### cloud_utils.py (data fetching)

- `get_feature_data_with_geometry(dataset_name, base_url, layer_id, paginate=True)` — primary function
- Handles ArcGIS 2000-record pagination, CRS detection from layer metadata, ring→Polygon conversion

### census_utils.py (demographics)

- `get_census_data_with_boundaries(fips_code, year)` → returns `(census_data, census_boundaries)`
- `match_to_census_blockgroups(gdf, census_gdf)` → spatial join parcels to block groups
- Auto-detects large counties (Cook, LA, Harris) for chunked fetching

### Philadelphia — OPA / Carto Data Patterns

Philadelphia parcel data comes from the **OPA (Office of Property Assessment)** via Carto, not ArcGIS FeatureServer. Use `requests` + Carto SQL API directly — `get_feature_data_with_geometry` will not work here.

**OPA has two parcel identifier fields** — do not confuse them:
- `parcel_number` — 9-digit OPA account number (zero-padded), e.g. `011000017`. Join assessments on this.
- `pin` — 10-digit DOR format, e.g. `1001197382`. Matches the `PIN` column in the Philadelphia DOR Parcels GeoJSON (`Philadelphia_DOR_Parcels_2023.geojson`). Use for lot area joins. The DOR `.shp` shapefile has `TENCODE` which does NOT match either OPA field.

Always pull both in the OPA query: `SELECT parcel_number, pin, category_code, total_area, the_geom FROM opa_properties_public`

**Data sources:**
- OPA properties (current): `https://phl.carto.com/api/v2/sql?q=SELECT ... FROM opa_properties_public&format=csv` — geometry is WKB in `the_geom` column, parse with `gpd.GeoSeries.from_wkb()`
- Assessment history: `https://phl.carto.com/api/v2/sql?q=SELECT ... FROM assessments WHERE year=XXXX&format=csv` — use this for billing-year taxable values

**Assessment vintage matters.** The current `opa_properties_public` table always reflects the *latest* assessment year. Philadelphia reassesses annually, so current OPA values may be 1–2 assessment cycles ahead of the billing year you're modeling. For FY2024 modeling, `assessments WHERE year=2024` (not the current OPA table) reduces the city-levy cross-check gap from +21% to +5%. Always specify `year=` and join back to current OPA for geometry + category codes.

**Revenue structure:** Philadelphia is consolidated city-county. The published 1.3998% rate is **city (0.6317%) + school district (0.7681%)**. City budget documents report only the city's ~$796M share; school district is a separate budget (~$970M). When modeling the combined rate, validate the city-only portion (0.6317% × taxable base) against city actuals. A ~5% gap is normal delinquency.

**Exemptions are already in OPA taxable columns.** `taxable_land` and `taxable_building` already net out the Homestead Exemption, 10-year construction abatement, and institutional exemptions. Do not double-apply these.

**LOOP and Senior Freeze are NOT in OPA.** Philadelphia's Longtime Owner Occupant Program (LOOP) and Senior Citizen Tax Freeze are administered by Revenue, not OPA, and are not available as public parcel-level datasets. They contribute a small portion of the revenue gap (~1–3%), with assessment vintage mismatch being the dominant factor.

**OPA land/building split:** ~45% of improved parcels have a land ratio of exactly 0.200 (OPA's default formula). Multi-family and commercial are especially affected. This attenuates split-rate impact. Document this limitation in the notebook.

**Lot area — use a three-source priority chain:**
1. OPA `total_area` (from `opa_properties_public`) — direct, one-to-one, no spatial artifact. Zero for ~32K parcels (condos, accessory structures).
2. PIN-keyed DOR polygon area — `parcel_areas_by_pin.parquet` (join via OPA's `pin` field to DOR GeoJSON's `PIN`). Only useful if the parquet has been built from `Philadelphia_DOR_Parcels_2023.geojson`.
3. DOR spatial join — `parcel_areas_dor.parquet` — prone to shared-campus-polygon artifact for parcels that lack individual DOR boundaries (esp. OPA code 8). Use `.drop_duplicates()` before `.set_index()` when building a lookup map from this file.

Use `.map()` not `.merge()` when applying these lookups to avoid fan-out from duplicate identifiers.

**Philadelphia category classification uses four stacked overrides** (in order):
1. `taxable_building <= 0` → "Vacant Land" (catch-all for zero-improvement parcels)
2. Non-vacant OPA code AND `taxable_building <= 0` AND `taxable_land > 0` → "Abated / Construction Exemption" (active 10-year construction abatement)
3. Vacant OPA code (6/12/13) AND `taxable_building > 0` → "Improved Vacant Land" (OPA calls it vacant but carries a building record; ~1,500 parcels with small structures)
4. `full_exmp = 1` (both taxable values = 0) → "[OPA category] — Exempt" (reclassifies exempt parcels out of "Vacant Land" into typed buckets)

Always apply these in this order. Override 3 before Override 4 matters: the full-exempt check must come after the improved-vacant reclassification or some parcels can end up in the wrong bucket.

**Abated parcels: use `exempt_building` for the reform scenario.** Parcels with `taxable_building = 0` have their building value in `exempt_building` — OPA still assesses the building, it just moves to the exempt column. Use `model_building = exempt_building` (available for ~93% of abated parcels); fall back to `market_value - taxable_land` for the ~7% where `exempt_building` is also zero (mid-construction). **Do not use `4 × taxable_land`** — that overstates by ~58% at the median.

**Fully exempt SFR parcels are low-value homesteaders, not vacant lots.** ~27K SFR parcels with `market_value <= $80K` have their entire assessed value wiped out by the Homestead Exemption. They show up as `full_exmp=1` and end up in "Vacant Land" if not reclassified. Override 4 moves them to "Single Family Residential — Exempt."

**Kernel name:** On Windows, the `cle-venv-new` kernel may not be registered. Check `jupyter kernelspec list` and use the available kernel (e.g., `python3`) for `nbconvert --execute`.

**Philadelphia LYCD model** (`cities/philadelphia/model_lycd.ipynb`) uses GMA hierarchical LYCD land values instead of OPA's taxable_land. Algorithm: OPA 2024 `market_value / lot_area_sqft` zone median × 20% × parcel lot area; 100% for vacant (OPA codes 6/12/13). Uses OPA's 613-zone L3 GMA hierarchy (fallback to L2/L1 for sparse zones). Applies improved-only `market_value` cap: `lycd_land = min(lycd_land, market_value)` for non-vacant parcels — prevents spatial-join lot-area artifacts from inflating results; vacant parcels are exempt from the cap so their development-potential signal survives.

**Philadelphia post-abatement models** (`model_post_abatement.ipynb`, `model_lycd_post_abatement.ipynb`) model the LVT shift from a counterfactual pre-shift baseline where all active 10-year construction abatements have expired. Key difference from standard models: `exempt_building` is added back to the taxable base for abated parcels *before* computing `current_tax`, so the revenue target is higher (~$2.06B vs $1.85B actual FY2024). Pattern: build `model_building` (restoring `exempt_building`) → compute `post_abatement_total = taxable_land + model_building` → pass `tax_value_col='post_abatement_total'` to `calculate_current_tax()` → run split-rate reform revenue-neutral to that higher baseline. The LYCD variant additionally uses `lycd_land_value` as `model_land` for the reform. **Do not validate `current_revenue` against FY2024 actuals in these notebooks** — the baseline is intentionally counterfactual and will be ~$210M higher.

### viz.py — create_city_report path issue

`create_city_report(df, city, output_dir='../../analysis/reports')` uses a **relative path**. It must be called from `cities/<city>/` or the figures write to the wrong location. When running standalone regen scripts, either `os.chdir` to `cities/<city>/` first, or pass an absolute `output_dir`. Symptom: figures appear fresh but show stale data.

Also: delete `lvt/__pycache__/` before regenerating if you've just edited `lvt/viz.py` — Python may use the old bytecode.

## Notebooks

Located in `cities/<city>/model.ipynb`. Each follows a pattern:
1. Fetch/load parcel data from county GIS
2. Validate against official tax base data
3. Classify parcels (TIF, exempt, city-taxable)
4. Categorize property types
5. Run split-rate model(s)
6. Visualize by category (bar charts, butterfly charts, scatter plots)
7. Merge Census data for equity analysis (income/minority quintiles)
8. `save_standard_export()` → `create_city_report()`

Data stored locally in `cities/<city>/data/` as geoparquet files (gitignored).

## Documentation

- `docs/LVT_MODELING_GUIDE.md` — step-by-step guide for adding a new city
- `docs/LVT_MODELING_GUIDE_ARCHIVE.md` — legacy modeling guide (pre-refactor)

## Code Style

- No decorative comment headers (avoid `# =============================================================================`)
- Use simple comments (e.g., `# Step 2: Load data`)
- No decorative print statements (avoid `print("=" * 60)`)
- Extensive type hints (Optional, Union, List, Tuple)
- Detailed docstrings with Parameters/Returns sections

## Data Files

All data files (.csv, .xlsx, .parquet, .gpq, .geojson, .shp) are gitignored. Each example city stores scraped data locally in `examples/data/<city>/`. The `data_scrape` flag in notebooks controls whether to fetch fresh data or load from cached files.
