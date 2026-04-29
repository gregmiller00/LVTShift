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

## Per-notebook skills

In "examples/" you will find a folder, "skills/". This contains .md files that correspond to a notebook and contain specific instructions for it. When you are working on a particular notebook, first read the relevant skills file to inform you.

## Code Style

- No decorative comment headers (avoid `# =============================================================================`)
- Use simple comments (e.g., `# Step 2: Load data`)
- No decorative print statements (avoid `print("=" * 60)`)
- Extensive type hints (Optional, Union, List, Tuple)
- Detailed docstrings with Parameters/Returns sections

## Data Files

All data files (.csv, .xlsx, .parquet, .gpq, .geojson, .shp) are gitignored. Each example city stores scraped data locally in `examples/data/<city>/`. The `data_scrape` flag in notebooks controls whether to fetch fresh data or load from cached files.
