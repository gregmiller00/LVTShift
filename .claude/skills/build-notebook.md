# Skill: Build the Notebook

Sub-skill called from `add-city.md` Step 3.

This skill defines the canonical 7-section notebook template. Follow it exactly. Do not add sections, do not reorder sections, do not skip the closing pattern.

---

## Notebook Location and Name

```
cities/<city>/model.ipynb
```

Create the directory:
```bash
mkdir -p cities/<city>/data
```

---

## Required Header Constants

Every notebook must define these at the top of a dedicated constants cell:

```python
CITY_NAME = 'fort_collins'     # snake_case, matches analysis/data/<city>.csv
STATE_FIPS = '08'              # 2-digit zero-padded
COUNTY_FIPS = '069'            # 3-digit zero-padded
MODEL_TYPE = 'split_rate_4to1' # or 'abatement_75pct', 'split_rate_10to1', etc.
LAND_IMPROVEMENT_RATIO = 4.0   # for split-rate; omit if abatement
```

The `STATE_FIPS + COUNTY_FIPS` combined string is the FIPS code passed to Census.

---

## Kernelspec

The notebook must use the `cle-venv-new` kernel. Set this in the notebook metadata:

```json
"kernelspec": {
  "display_name": "cle-venv-new",
  "language": "python",
  "name": "cle-venv-new"
}
```

---

## Section 1 — Imports and Setup

```python
import sys
import json
import os
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, '../..')
REPO_ROOT = Path('../..').resolve()
load_dotenv(REPO_ROOT / '.env')

from lvt.cloud_utils import get_feature_data_with_geometry
from lvt.lvt_utils import (
    model_split_rate_tax,
    calculate_current_tax,
    calculate_category_tax_summary,
    print_category_tax_summary,
    save_standard_export,
)
from lvt.census_utils import get_census_data_with_boundaries, match_to_census_blockgroups

# Constants
CITY_NAME = 'fort_collins'
STATE_FIPS = '08'
COUNTY_FIPS = '069'
MODEL_TYPE = 'split_rate_4to1'
LAND_IMPROVEMENT_RATIO = 4.0

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
```

---

## Section 2 — Fetch / Load Parcel Data

```python
PARCEL_PATH = DATA_DIR / 'parcels.gpq'

if PARCEL_PATH.exists():
    gdf = gpd.read_parquet(PARCEL_PATH)
    print(f"Loaded {len(gdf):,} parcels from cache")
else:
    gdf = get_feature_data_with_geometry(
        dataset_name='larimer_parcels',
        base_url='https://gis.larimer.org/arcgis/rest/services/Parcels/FeatureServer',
        layer_id=0,
        paginate=True,
    )
    # Filter to city
    gdf = gdf[gdf['MUNICIPALITY'] == 'FORT COLLINS'].copy()
    gdf.to_parquet(PARCEL_PATH)
    print(f"Downloaded and cached {len(gdf):,} city parcels")
```

---

## Section 3 — Classify and Validate

Classify property types, identify exempt parcels, and validate against official figures.

```python
# 1. Exemption flag
gdf['full_exmp'] = (gdf['EXEMPT_CODE'].isin(['E', 'GOV', 'EXEMPT'])).astype(int)

# 2. Property category mapping
CATEGORY_MAP = {
    '100': 'Single Family Residential',
    '200': 'Small Multi-Family (2-4 units)',
    '300': 'Large Multi-Family (5+ units)',
    '400': 'Commercial',
    '500': 'Industrial',
    '600': 'Vacant Land',
    '700': 'Agricultural',
    '800': 'Transportation - Parking',
    '900': 'Exempt',
}
gdf['PROPERTY_CATEGORY'] = gdf['USE_CODE'].map(CATEGORY_MAP).fillna('Other')

# 3. Override: $0 improvement → Vacant Land
gdf.loc[gdf['IMPROVEMENT_VALUE'] <= 0, 'PROPERTY_CATEGORY'] = 'Vacant Land'

print(gdf['PROPERTY_CATEGORY'].value_counts())
```

---

## Section 4 — Current Tax Model

Model current tax and validate revenue. See `model-policy.md` for the right approach depending on the city's assessment system.

```python
OFFICIAL_REVENUE = 45_000_000  # from city budget document

gdf['taxable_land_value'] = gdf['LAND_VALUE'].clip(lower=0)
gdf['taxable_improvement_value'] = gdf['IMPROVEMENT_VALUE'].clip(lower=0)

gdf['millage_rate'] = 9.5  # mills (from city budget)

current_revenue, _, gdf = calculate_current_tax(
    df=gdf,
    tax_value_col='TOTAL_VALUE',
    millage_rate_col='millage_rate',
    exemption_flag_col='full_exmp',
)

gap_pct = (current_revenue / OFFICIAL_REVENUE - 1) * 100
print(f"Modeled: ${current_revenue:,.0f}   Official: ${OFFICIAL_REVENUE:,.0f}   Gap: {gap_pct:+.2f}%")
assert abs(gap_pct) < 5.0, f"Revenue gap {gap_pct:.1f}% exceeds threshold"
```

---

## Section 5 — Split-Rate Model

```python
# Exclude fully-exempt parcels from reform
taxable = gdf[gdf['full_exmp'] == 0].copy()

land_millage, improvement_millage, new_revenue, taxable = model_split_rate_tax(
    df=taxable,
    land_value_col='taxable_land_value',
    improvement_value_col='taxable_improvement_value',
    current_revenue=taxable['current_tax'].sum(),
    land_improvement_ratio=LAND_IMPROVEMENT_RATIO,
)

# Recombine exempt parcels (their new_tax = current_tax = 0)
exempt = gdf[gdf['full_exmp'] == 1].copy()
exempt['new_tax'] = 0.0
exempt['tax_change'] = 0.0
exempt['tax_change_pct'] = 0.0
gdf = pd.concat([taxable, exempt]).sort_index()

print(f"Land millage: {land_millage:.4f}   Improvement millage: {improvement_millage:.4f}")
print(f"Revenue check: ${new_revenue:,.0f} (should equal ${taxable['current_tax'].sum():,.0f})")

# Category summary
category_summary = calculate_category_tax_summary(
    df=gdf,
    category_col='PROPERTY_CATEGORY',
    current_tax_col='current_tax',
    new_tax_col='new_tax',
)
print_category_tax_summary(category_summary, title=f"{CITY_NAME} — 4:1 Split-Rate Tax Impact")
```

---

## Section 6 — Exploration Charts (optional)

Add any city-specific exploratory charts here. These are not part of the standard report. Examples:
- Bar chart of tax change by property category (quick visual)
- Scatter of land value vs. tax change
- Map of parcels colored by tax change direction

Keep these cells optional — they may be skipped when executing headlessly.

```python
import matplotlib
matplotlib.use('Agg')  # headless

fig, ax = plt.subplots(figsize=(10, 6))
summary = gdf.groupby('PROPERTY_CATEGORY')['tax_change_pct'].median()
summary.sort_values().plot.barh(ax=ax)
ax.set_title(f'{CITY_NAME} — Median Tax Change % by Category (4:1 Split-Rate)')
ax.set_xlabel('Median % Change')
plt.tight_layout()
plt.savefig(DATA_DIR / 'category_preview.png', dpi=150)
plt.close()
```

---

## Section 7 — Census Join + Export (EXACT PATTERN — DO NOT MODIFY)

This section must appear verbatim as the final executable cells. Copy-paste exactly. Only change `CITY_NAME`, `STATE_FIPS + COUNTY_FIPS`, `output_path`, `model_type`, millage variable names, and column names.

```python
# Census join — must happen before export
import concurrent.futures
from lvt.census_utils import get_census_data_with_boundaries, match_to_census_blockgroups

_fips = STATE_FIPS + COUNTY_FIPS
try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as _ex:
        _future = _ex.submit(get_census_data_with_boundaries, _fips, 2022)
        try:
            census_data, census_gdf = _future.result(timeout=90)
            gdf = match_to_census_blockgroups(gdf, census_gdf)
            # census_gdf already carries demographics — spatial join adds them above.
            # Do NOT do a second gdf.merge(census_data) here: census_gdf has the columns
            # baked in, so a second merge creates median_income_x/y duplicates and silently
            # zeros out all demographic output.
            if 'minority_pct' not in gdf.columns and 'total_pop' in gdf.columns and 'white_pop' in gdf.columns:
                gdf['minority_pct'] = ((gdf['total_pop'] - gdf['white_pop']) / gdf['total_pop'] * 100).round(2)
            if 'black_pct' not in gdf.columns and 'total_pop' in gdf.columns and 'black_pop' in gdf.columns:
                gdf['black_pct'] = (gdf['black_pop'] / gdf['total_pop'] * 100).round(2)
            print(f"Census join: {gdf['std_geoid'].notna().mean()*100:.1f}% matched")
        except concurrent.futures.TimeoutError:
            print("Census API timed out — skipping census join")
            for _col in ['std_geoid', 'median_income', 'minority_pct', 'black_pct']:
                gdf[_col] = float('nan')
except Exception as e:
    print(f"Census join failed: {e}")
    for _col in ['std_geoid', 'median_income', 'minority_pct', 'black_pct']:
        gdf[_col] = float('nan')
```

```python
# Export — gdf must have census columns by this point
from lvt.lvt_utils import save_standard_export
out_df = save_standard_export(
    df=gdf,
    city=CITY_NAME,
    output_path=f'../../analysis/data/{CITY_NAME}.csv',
    model_type=MODEL_TYPE,
    land_millage=land_millage,
    improvement_millage=improvement_millage,
    property_category_col='PROPERTY_CATEGORY',
    current_tax_col='current_tax',
    new_tax_col='new_tax',
    tax_change_col='tax_change',
    tax_change_pct_col='tax_change_pct',
    taxable_land_col='taxable_land_value',
    taxable_improvement_col='taxable_improvement_value',
)

# Standard report — 7 PNGs in analysis/reports/<city>/
from lvt.viz import create_city_report
create_city_report(out_df, CITY_NAME, show=False)
print("Done.")
```

---

## Common Pitfalls

**Census data not showing in charts**: The census join result must be stored back into the same variable that is passed to `save_standard_export`. If you join census onto an intermediate GeoDataFrame, propagate those columns forward before calling export.

```python
# If census join used a different variable name:
_census_cols = ['std_geoid', 'median_income', 'minority_pct', 'black_pct', 'total_pop']
for _col in _census_cols:
    if _col in census_joined_gdf.columns:
        final_df[_col] = census_joined_gdf[_col]
```

**`show=False` is required** when executing headlessly — otherwise matplotlib blocks waiting for display.

**Import path**: Always `sys.path.insert(0, '../..')` from `cities/<city>/model.ipynb`.

**Kernel**: Always `cle-venv-new`. Execute with:
```bash
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=600 \
  --ExecutePreprocessor.kernel_name=cle-venv-new \
  model.ipynb
```
