# Notebook Template

Every city notebook follows this 7-section structure. Sections 1–4 contain city-specific code. Sections 5–7 are as close to identical as possible across cities.

Copy this structure when starting a new city. The section headers must be exactly as written here — the validation notebook uses them as markers.

---

## Section layout

```
examples/<city>/model.ipynb
```

---

### Section 1 — Configuration

ALL city-specific parameters go here. Nothing below section 1 should contain hardcoded city names, URLs, column names, millage rates, or FIPS codes.

What belongs here:
- Imports (standard: sys, Path, pandas, geopandas, matplotlib, from lvt import ...)
- `apply_lvt_style()` call
- `data_scrape` flag
- ArcGIS service URL and layer ID
- Column name mappings (land_col, improvement_col, exempt_col, etc.)
- Millage rate(s)
- FIPS code for Census
- Land-to-improvement ratio for modeling
- `data_dir = Path('data')`

Template first cell:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('../../').resolve()))

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from lvt import cloud_utils, lvt_utils, census_utils, policy_analysis, viz
from lvt.style import apply_lvt_style, CATEGORY_COLORS
from lvt.lvt_utils import (
    calculate_current_tax, model_split_rate_tax,
    calculate_category_tax_summary, print_category_tax_summary,
    save_standard_export,
)

apply_lvt_style()

# ── City configuration ────────────────────────────────────────────────
data_scrape = 0           # 1 = fetch fresh, 0 = load from cache
data_dir    = Path('data')

CITY_NAME   = 'baltimore'
STATE_FIPS  = '24'
COUNTY_FIPS = '510'       # Independent City of Baltimore

BASE_URL    = 'https://...'
LAYER_ID    = 0

LAND_COL        = 'BFCVLAND'
IMPROVEMENT_COL = 'BFCVIMPR'
TOTAL_COL       = 'ARTAXBAS'
EXEMPT_FLAG_COL = 'full_exmp'
MILLAGE         = 22.48

LIR             = 4.0     # land-to-improvement ratio for modeling
```

---

### Section 2 — Data

Fetch or load from cache. One pattern:

```python
if data_scrape:
    gdf = cloud_utils.get_feature_data_with_geometry(
        dataset_name=CITY_NAME, base_url=BASE_URL, layer_id=LAYER_ID,
    )
    gdf.to_parquet(data_dir / f'{CITY_NAME}_{pd.Timestamp.now():%Y_%m_%d}.parquet')
else:
    latest = sorted(data_dir.glob(f'{CITY_NAME}_*.parquet'))[-1]
    gdf = gpd.read_parquet(latest)

print(f'{len(gdf):,} parcels loaded')
```

---

### Section 3 — Preprocessing

City-specific operations: geographic filtering, column selection, condo collapse, data validation.

```python
# Filter to city boundary (if county-wide dataset)
df = gdf[gdf['CITY'] == 'BALTIMORE'].copy()

# Drop rows missing required value fields
df = df.dropna(subset=[LAND_COL, IMPROVEMENT_COL])

# Classify property types
df['PROPERTY_CATEGORY'] = df.apply(lambda r: ..., axis=1)
df.loc[df[IMPROVEMENT_COL] == 0, 'PROPERTY_CATEGORY'] = 'Vacant Land'
```

---

### Section 4 — Tax Modeling

Current tax → property classification → LVT model. City-specific.

```python
# Current tax
current_revenue, _, df = calculate_current_tax(
    df=df,
    tax_value_col=LAND_COL,        # or TOTAL_COL depending on city
    millage_rate=MILLAGE,
    exemption_flag_col=EXEMPT_FLAG_COL,
)
print(f'Current revenue: ${current_revenue:,.0f}')

# Validate against official figure
OFFICIAL_REVENUE = 1_157_401_814
assert abs(current_revenue - OFFICIAL_REVENUE) / OFFICIAL_REVENUE < 0.02, \
    f'Revenue mismatch: {current_revenue:,.0f} vs {OFFICIAL_REVENUE:,.0f}'

# LVT model
land_millage, improvement_millage, new_revenue, df = model_split_rate_tax(
    df=df,
    land_value_col=LAND_COL,
    improvement_value_col=IMPROVEMENT_COL,
    current_revenue=current_revenue,
    land_improvement_ratio=LIR,
    exemption_flag_col=EXEMPT_FLAG_COL,
)
```

---

### Section 5 — Export

Identical across all cities (only arguments change).

```python
# Export standardized CSV — do not remove or move above Census join
save_standard_export(
    df=df,
    city=CITY_NAME,
    output_path=f'../../analysis/data/{CITY_NAME}.csv',
    model_type=f'split_rate:{LIR}',
    land_millage=land_millage,
    improvement_millage=improvement_millage,
    exempt_flag_col=EXEMPT_FLAG_COL,
)
```

---

### Section 6 — Analysis

Category summaries, policy analysis. Mostly identical across cities.

```python
summary = calculate_category_tax_summary(
    df=df, category_col='PROPERTY_CATEGORY',
    current_tax_col='current_tax', new_tax_col='new_tax',
)
print_category_tax_summary(summary)
```

---

### Section 7 — Equity & Visualization

Census join + quintile analysis + standard charts. Mostly identical across cities.

```python
# Census join
fips = STATE_FIPS + COUNTY_FIPS
census_data, census_boundaries = census_utils.get_census_data_with_boundaries(fips)
df = census_utils.match_to_census_blockgroups(df, census_boundaries)
df = census_utils.match_parcels_to_demographics(df, census_data)

# Quintile analysis
income_q = viz.create_quintile_summary(df, 'median_income')
viz.plot_quintile_analysis(income_q, title='Tax Change by Income Quintile')
```
