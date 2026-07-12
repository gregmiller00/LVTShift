# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LVTShift is a toolkit for modeling Land Value Tax (LVT) policy shifts in U.S. cities/counties. It analyzes how shifting from traditional property taxes to land value taxes affects neighborhoods, property types, and demographic groups. Created by the Center for Land Economics.

The repo is designed to be driven by an agent. The user-facing entry points are four skills (see Skills below); most work happens inside per-city Jupyter notebooks that import the `lvt/` package.

## Environment Setup

```bash
# Any Python 3.11+ environment works; install the requirements into it
pip install -r requirements.txt

# Environment variables
cp env.template .env
# Add CENSUS_API_KEY (free at https://api.census.gov/data/key_signup.html)
```

Notebooks use the standard `python3` Jupyter kernel (provided by `ipykernel`, which is in the requirements). Execute headlessly with:

```bash
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=600 \
  --ExecutePreprocessor.kernel_name=python3 \
  model.ipynb
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

## Skills

The four user-facing skills live in `.claude/skills/` with slash-command wrappers in `.claude/commands/`:

- **model-city** (`/lvt-city`) — full pipeline for a new city. Orchestrates the sub-skills `discover-data.md` → `model-policy.md` → `build-notebook.md` → `validate.md`, then runs the canonical census join + standard export + 7-PNG report.
- **legality-analyzer** (`/legality-analyzer`) — legal pathway brief for a city/state, grounded in `docs/LVT_LEGAL_DECISIONING_GUIDE.md`.
- **explain-model** (`/explain-model`) — plain-language methodology audit of an existing city model.
- **refine-model** (`/refine-model`) — re-run an existing model with changed parameters (split ratio, abatement, exemptions, levy scope) via minimal notebook edits.

When modifying the pipeline, change the skill files — they are the canonical spec; this file is only a map.

## Architecture

Six core modules live in the `lvt/` package, used from Jupyter notebooks in `cities/`:

```
lvt/cloud_utils.py     → Fetch parcel data from county ArcGIS FeatureServers
lvt/census_utils.py    → Fetch Census demographics, spatial join to parcels
lvt/lvt_utils.py       → Tax modeling (split-rate, abatement, exemptions) — rate shifts
lvt/reassessment.py    → Revenue-neutral reassessment — base shifts (single + multi-district, decomposition) + IAAO ratio-study & equity metrics
lvt/policy_analysis.py → Identify vacant land, parking lots, development barriers
lvt/transit_utils.py   → GTFS feeds, routed walk-shed isochrones, OSM parking analysis
lvt/viz.py             → Scatter plots, quintile analysis, demographic charts, city report
```

Notebooks import via the package:
```python
import sys; sys.path.insert(0, '../..')  # from cities/<city>/
from lvt.lvt_utils import model_split_rate_tax
from lvt.cloud_utils import get_feature_data_with_geometry
```

**Data flow**: Fetch parcels (cloud_utils) → classify property types → rebuild current tax → model LVT scenarios (lvt_utils) → merge Census demographics (census_utils) → `save_standard_export()` → `create_city_report()` (viz)

### Key Design Patterns

- **Flexible column names**: Every function accepts column names as parameters (no hardcoded field names) to support different jurisdictions' data schemas
- **Revenue neutrality**: All tax models maintain identical total revenue. Uses `(target_revenue * 1000) / denominator` for rate calculation. Iterative solver (up to 40 iterations) when percentage caps exist
- **Millage rates are per $1000**: `model_split_rate_tax()` returns millage in per-$1000 units. Tax = `value * millage / 1000`
- **Exemption hierarchy**: Full exemption flags applied first → dollar exemptions to improvements → remaining to land
- **Centroid-based spatial joins**: Parcels joined to Census block groups via centroids in EPSG:3857 to avoid boundary edge cases
- **Census fetching**: TIGERweb block-group request (Layer 1), automatically chunked by tract for very large counties; calls run in a background thread with a 90-second timeout

### Jurisdiction-Specific Patterns

The tax base works differently by state; `model-policy.md` documents all real patterns with code. Examples: Ohio's 35% assessment ratio (Cincinnati), Minnesota Tax Capacity class rates (St. Paul), derived millage from observed bills (Baltimore), dual homestead/non-homestead rates (Rochester), per-levy abatement (Spokane), Texas entity-specific homestead/over-65 exemptions (Bryan, College Station).

One recurring pattern worth knowing: **condo collapse** (St. Paul / Ramsey County). Some assessors give condo units token land values ($1,000/unit). Before modeling, condos are collapsed by `PlatID` into buildings — summing values/taxes, imputing the land/building split from the neighborhood median improvement ratio of non-condo parcels, and unioning geometries via `collapse_geometries()`.

### Washington, DC — Derived-Bill Modeling and the Nominal-Rate-vs-Billed-Amount Trap

DC is a single unified city/county/state-equivalent government (FIPS 11001) — the real property tax is
one levy, no county/school layer to add. Parcel data comes from DC GIS's `Property_and_Land_WebMercator`
FeatureServer, Layer 40 (Owner Polygons / Common Ownership Layer), which merges geometry with CAMA
assessed values and a **live-computed per-parcel tax bill (`ANNUALTAX`)** — DC is unusual among modeled
cities in that `current_tax` is taken directly from this observed-bill field (the Baltimore B4 pattern
in `model-policy.md`) rather than reconstructed from class + value, since `ANNUALTAX` already reflects
DC's per-class rate brackets, the Homestead Deduction, Senior/Disabled 50% relief, and any mixed-use
blending exactly as billed.

**Exemption trap: key off `ANNUALTAX`, not `TAXRATE`.** A first pass flagged full exemption using
`TAXRATE == 0`. That missed 35 parcels assessed at $500M–$2.1B each (~$30B total, ~9% of the taxable
base) — large civic/institutional properties (several with `PAR ...`-prefixed SSLs, suggesting
federal-reservation-style records) carrying a nonzero nominal Class 2 `TAXRATE` (1.89%) but an actual
`ANNUALTAX` of $0. Including their assessed value in the split-rate solver's land base collapsed the
solved millage toward zero and pinned an unrelated category ("Other Commercial") at a false +647%
ceiling. Fix: flag full exemption off `ANNUALTAX <= 0` (the billed amount), not the nominal rate.

**Relief mechanics** (`HSTDCODE` column, verified empirically against the data): `1` = Homestead
Deduction only ($91,950 for TY2026); `5` = Homestead + Senior, and `3` = Homestead + Disabled — both
get an *additional* 50% cut on the computed bill (confirmed: `ANNUALTAX / (CAPCURR * TAXRATE / 100)`
≈ 0.50 for codes 3/5, ≈ 1.00 for codes 1/7); `7` = a rarer homestead variant, no 50% cut. The reform
preserves this structure via `model_split_rate_tax`'s `exemption_col` (dollar homestead deduction) and
`credit_rate_col` (0.5 for codes 3/5) parameters.

**Structural result — residential goes up, not down.** DC currently taxes commercial property (Class 2,
$1.65–1.89/$100) at roughly double the residential rate (Class 1, $0.85/$100). A single citywide
land/improvement millage pair solved across all classes together equalizes this differential: the
solved land millage lands between DC's current residential and commercial rates, so commercial
buildings get a large cut while residential land — previously taxed at less than half the commercial
rate — rises to meet the new blended rate. Confirmed by hand-checking the millage math against each
class's current rate; this is a real consequence of reforming an already-differentiated class-rate
system into a uniform land-value base, not a modeling artifact.

**Known revenue gap (~9%, documented, not closed).** Modeled current-tax revenue undershoots DC OCFO's
FY2026 Real Property Tax estimate ($2,748,983,000; September 2025 Revenue Estimates) by about 9%.
Ruled out: duplicate SSLs, condo double-counting, OLD- vs NEW-assessment-year confusion (aggregate
values agree within 0.3%). Leading unconfirmed hypothesis: OCFO's total likely includes Public Utility
Real Property (assessed by a separate OTR unit, not published on this parcel FeatureServer).

### lvt_utils.py (core modeling)

Key functions:
- `model_split_rate_tax(df, land_value_col, improvement_value_col, current_revenue, land_improvement_ratio)` → returns `(land_millage, imp_millage, revenue, df_with_new_tax)`
- `model_full_building_abatement` / `model_stacking_improvement_exemption` → building-exemption pathway
- `calculate_current_tax(...)` → rebuild the existing system, honoring exemptions
- `calculate_category_tax_summary(df, category_col, current_tax_col, new_tax_col)` → summary stats by property type
- `save_standard_export(...)` → standardized per-parcel CSV in `analysis/data/<city>.csv`
- `ensure_geodataframe(df)` → handles WKT, WKB hex, and binary geometry encodings

### cloud_utils.py (data fetching)

- `get_feature_data_with_geometry(dataset_name, base_url, layer_id, paginate=True)` — primary function
- Handles ArcGIS 2000-record pagination, CRS detection from layer metadata, ring→Polygon conversion

### census_utils.py (demographics)

- `get_census_data_with_boundaries(fips_code, year)` → returns `(census_data, census_boundaries)`
- `match_to_census_blockgroups(gdf, census_gdf)` → spatial join parcels to block groups
- Auto-detects large counties (Cook, LA, Harris, …) for chunked fetching

### Philadelphia — OPA / Carto Data Patterns

Philadelphia parcel data comes from the **OPA (Office of Property Assessment)** via Carto, not ArcGIS FeatureServer. Use `requests` + Carto SQL API directly — `get_feature_data_with_geometry` will not work here.

**Data sources:**
- OPA properties (current): `https://phl.carto.com/api/v2/sql?q=SELECT ... FROM opa_properties_public&format=csv` — geometry is WKB in `the_geom` column, parse with `gpd.GeoSeries.from_wkb()`
- Assessment history: `https://phl.carto.com/api/v2/sql?q=SELECT ... FROM assessments WHERE year=XXXX&format=csv` — use this for billing-year taxable values

**Assessment vintage matters.** The current `opa_properties_public` table always reflects the *latest* assessment year. Philadelphia reassesses annually, so current OPA values may be 1–2 assessment cycles ahead of the billing year you're modeling. For FY2024 modeling, `assessments WHERE year=2024` (not the current OPA table) reduces the city-levy cross-check gap from +21% to +5%. Always specify `year=` and join back to current OPA for geometry + category codes.

**Revenue structure:** Philadelphia is consolidated city-county. The published 1.3998% rate is **city (0.6317%) + school district (0.7681%)**. City budget documents report only the city's ~$796M share; school district is a separate budget (~$970M). When modeling the combined rate, validate the city-only portion (0.6317% × taxable base) against city actuals. A ~5% gap is normal delinquency.

**Exemptions are already in OPA taxable columns.** `taxable_land` and `taxable_building` already net out the Homestead Exemption, 10-year construction abatement, and institutional exemptions. Do not double-apply these.

**LOOP and Senior Freeze are NOT in OPA.** Philadelphia's Longtime Owner Occupant Program (LOOP) and Senior Citizen Tax Freeze are administered by Revenue, not OPA, and are not available as public parcel-level datasets. They contribute a small portion of the revenue gap (~1–3%), with assessment vintage mismatch being the dominant factor.

**OPA land/building split:** ~45% of improved parcels have a land ratio of exactly 0.200 (OPA's default formula). Multi-family and commercial are especially affected. This attenuates split-rate impact. Document this limitation in the notebook.

**Philadelphia category classification uses four stacked overrides** (in order):
1. `taxable_building <= 0` → "Vacant Land" (catch-all for zero-improvement parcels)
2. Non-vacant OPA code AND `taxable_building <= 0` AND `taxable_land > 0` → "Abated / Construction Exemption" (active 10-year construction abatement)
3. Vacant OPA code (6/12/13) AND `taxable_building > 0` → "Improved Vacant Land" (OPA calls it vacant but carries a building record; ~1,500 parcels with small structures)
4. `full_exmp = 1` (both taxable values = 0) → "[OPA category] — Exempt" (reclassifies exempt parcels out of "Vacant Land" into typed buckets)

Always apply these in this order. Override 3 before Override 4 matters: the full-exempt check must come after the improved-vacant reclassification or some parcels can end up in the wrong bucket.

**Abated parcels: impute building value for the reform scenario.** Parcels with `taxable_building = 0` and active abatements have LR=1.0 in the split-rate base, producing an artificially large result. Fix: set `model_building = 4 × taxable_land` (restoring OPA's implicit 20% land ratio) for the reform calculation only. Keep `current_tax` as actual (land-only). Add $12.5B to the reform improvement base; both millages decrease ~5%. The "Abated / Construction Exemption" category shows +315.5%, representing the shift from an almost-free land-only bill to a full LVT bill on the estimated complete value.

**Fully exempt SFR parcels are low-value homesteaders, not vacant lots.** ~27K SFR parcels with `market_value <= $80K` have their entire assessed value wiped out by the Homestead Exemption. They show up as `full_exmp=1` and end up in "Vacant Land" if not reclassified. Override 4 moves them to "Single Family Residential — Exempt."

**Kernel name:** On Windows, the `cle-venv-new` kernel may not be registered. Check `jupyter kernelspec list` and use the available kernel (e.g., `python3`) for `nbconvert --execute`.

**Philadelphia has four notebooks.** `cities/philadelphia/` contains `model.ipynb` (OPA), `model_lycd.ipynb` (LYCD), `model_post_abatement.ipynb` (OPA post-abatement), and `model_lycd_post_abatement.ipynb` (LYCD post-abatement). All four export to `analysis/data/philadelphia*.csv` with a `parcel_id` column (added via `parcel_id_col='parcel_number'` in `save_standard_export`).

**All four notebooks share one cache: `cities/philadelphia/data/parcels.gpq`.** Any rebuild of the cache (the fetch fallbacks in `model.ipynb` and `model_post_abatement.ipynb`) must emit the full column superset: the assessment value columns plus `pin` + `total_area` (LYCD lot-area chain) and `owner_1` + `owner_2` (owner-concentration analysis in `model.ipynb`). The LYCD notebooks read the cache unconditionally and raise a clear error if columns are missing. Keep `pin` integer-typed — the LYCD notebooks stringify it as a join key, and a float dtype would add a `.0` suffix and break the PIN match. Also note Carto's `assessments.year` column is varchar: the filter must be `WHERE year = '2024'` (quoted); an unquoted integer comparison returns HTTP 400.

**`parcels.gpq` row order does NOT match the CSV row order.** Do not join by index. Verified: 480K out of 579K rows differ between `taxable_land` in `parcels.gpq` and `taxable_land_value` in `philadelphia.csv`. Always join on `parcel_id` ↔ `parcel_number` (stripping leading zeros: `parcels['parcel_id'] = parcels['parcel_number'].astype(str).str.lstrip('0').astype('Int64')`).

## Notebooks

Located in `cities/<city>/model.ipynb`. Each follows the 7-section template in `.claude/skills/build-notebook.md`:
1. Imports, constants, `.env` load
2. Fetch/load parcel data from county GIS (cached in `cities/<city>/data/`)
3. Classify parcels (exempt flags, property categories) and validate against official tax base data
4. Rebuild the current tax and check against the official revenue figure
5. Run the split-rate or abatement model
6. Optional exploration charts
7. Census join → `save_standard_export()` → `create_city_report()` (exact closing pattern — do not modify)

`save_standard_export` accepts an optional `parcel_id_col` parameter. When provided (e.g., `parcel_id_col='parcel_number'`), a `parcel_id` column is prepended to the output CSV, enabling downstream spatial joins without re-running the notebook.

## Documentation

- `docs/LVT_MODELING_GUIDE.md` — step-by-step guide for adding a new city
- `docs/LVT_LEGAL_DECISIONING_GUIDE.md` — legal framework behind the legality-analyzer skill
- `docs/LVT_MODELING_GUIDE_ARCHIVE.md` — legacy modeling guide (pre-refactor, kept for reference)

## Code Style

- No decorative comment headers (avoid `# =============================================================================`)
- Use simple comments (e.g., `# Step 2: Load data`)
- No decorative print statements (avoid `print("=" * 60)`)
- Extensive type hints (Optional, Union, List, Tuple)
- Detailed docstrings with Parameters/Returns sections

## Data Files

All data files (.csv, .xlsx, .parquet, .gpq, .geojson, .shp) are gitignored. Each city's scraped data is cached locally in `cities/<city>/data/`; notebooks auto-detect cached files and skip re-scraping when a recent file exists. Standard exports land in `analysis/data/` and reports in `analysis/reports/` (both gitignored). The `data_scrape` flag in notebooks controls whether to fetch fresh data or load from cached files.

## Batch Execution

`scripts/run_all_cities.py` runs all city notebooks via `nbconvert`. It:
- Auto-detects missing data caches and patches `data_scrape = 0 → 1` (handles both `data_scrape` and `scrape_data` variable names)
- Executes to a throw-away `_executed.ipynb`, leaving the source notebook untouched
- Reports pass/fail and CSV row counts

`scripts/patch_notebooks.py` applies idempotent fixes to notebook cells — safe to re-run. Add new patches as functions there rather than editing notebooks manually.

## Ratio Harmonization

All runnable city notebooks are set to 4:1 split-rate. The canonical variable names are:
- `LAND_IMPROVEMENT_RATIO = 4.0` (most cities)
- `MODEL_TYPE = 'split_rate:4.0'` (canonical string — use colon format, not underscore)

## Known Blocked Cities

**Cincinnati** — The original `CAGIS_Open_Data` ArcGIS service (layer 12) returns 400 errors. The nearest replacement (`Cincinnati_Parcels_Indicators_2025/127`) is missing `MKTLND` (land value), which is required for LVT modeling. Notebook has auto-scrape fallback code but will fail until a new source with parcel-level land values is found.

**Spokane** — After scraping parcel geometry, the notebook requires `charge_info_1.xlsx` and `charge_info_2.xlsx` — per-parcel levy charge tables manually downloaded from Spokane County. No download URL exists in the codebase. Obtain from: https://gisdatacatalog-spokanecounty.opendata.arcgis.com/pages/parcel-data-file-downloads

**Denver** — Depends on manually-assembled `data/1-assemble-universe.parquet` and `data/_just_city_county_millage_2024.csv` (never committed, created by Lars Doucet locally). Notebook also has syntax errors (mismatched quotes) and non-standard property categories. Needs a full rebuild from public data sources.

## Fort Collins Notes

The `build_fort_collins_propinfo_cache.py` script (fetches per-parcel state tax relief from the Larimer County Treasurer API) was never committed. The notebook now defaults to `owner_tax_share = 1.0` when the script/cache is absent, which slightly overstates current tax for parcels receiving state relief but does not affect LVT % change calculations.

The Larimer County GIS parcel shapefile (`GIS_ParcelOwnerSHP.zip`) contains date fields (`DEEDDATE`, `SALEDATE`, `UPDATEDATE`) with year=0 values that Fiona cannot parse. Fix: `gpd.read_file(url, ignore_fields=['DEEDDATE', 'SALEDATE', 'UPDATEDATE'])`.

## Notebook Data-Scrape Variable Names

Some notebooks use `scrape_data = 0` (Bellingham, Spokane) instead of `data_scrape = 0`. The batch runner patches both. When writing new notebooks, prefer `data_scrape` for consistency.

## Cook County / PTAXSIM Pattern (Oak Forest)

Oak Forest uses a different data stack than all other cities — CCAO open data + PTAXSIM SQLite database, loaded from the sibling project `C:/projects/oak-forest-profit-loss-map/`.

**Critical: always filter PTAXSIM queries to Oak Forest tax codes first.** The `pin` table has 1.86 million Cook County rows. A naïve `WHERE year = 2023` query takes forever. Always add `AND p.tax_code_num IN (SELECT tax_code_num FROM city_tcs)` where `city_tcs` filters by `agency_num = '030900000'`. Oak Forest has 53 tax codes; the filtered query runs in 0.1s.

**Taxable EAV approach.** Don't compute `(av_clerk - exemptions) × eq_factor` directly for the split-rate base. Instead, back-calculate from city_tax: `effective_taxable_eav = city_tax / (city_rate / 1000)`. This automatically handles TIF base-EAV constraints for the 453 TIF-district parcels — no manual TIF correction needed. PTAXSIM already computes city_tax as the city's proportional share of the total bill, which for TIF parcels reflects only the frozen base EAV.

**Scale PTAXSIM to match official levy.** The proportional method (`tax_bill_total × city_rate / total_code_rate`) produces ~2% above the official levy. Apply `scale = CITY_LEVY / raw_total` before using city_tax values.

**Census join: skip `get_census_data_with_boundaries`.** It downloads all of Cook County's ~1,300 block groups including TIGERweb boundaries — takes 600+ seconds and times out. Use `get_census_data('17031', 2022)` (ACS-only, fast) then filter to the 24 Oak Forest block groups already in `parcel_universe['census_block_group_geoid']`. The CCAO parcel universe pre-computes block group GEOIDs; set `df['std_geoid'] = df['census_block_group_geoid']` and skip `match_to_census_blockgroups` entirely.

**Improvement ratio quality.** CCAO board-certified AV has genuine parcel-level land/building splits (unlike Philadelphia's OPA which defaults 80% of parcels to 20% LR). Oak Forest median improvement ratio = 0.852, with <0.2% of parcels at any single default value. The split is trustworthy.

**Constitutional cap note (Illinois).** Illinois Art. IX §4(b) limits the class differential in Cook County to 2.5×. A 4:1 modeled ratio is illustrative but would require a constitutional amendment to implement. The legally achievable ratio under state enabling legislation is 2.5:1.
