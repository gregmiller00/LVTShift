# Skill: Add a New City

Invoked when the user says **"add [city] to LVTShift"** or **"model LVT for [city]"**.

This is the master skill. It runs the full pipeline end-to-end. Each numbered step maps to a sub-skill — read those for detail. Do not skip steps or reorder them.

---

## Before writing any code — ask these questions

Do not proceed until you have explicit answers. These decisions cannot be changed midway without restarting.

```
1. Which government body are we modeling?
   [ ] City levy only   [ ] Full stack (city + county + school + all levies)   [ ] Specific levies: ___

2. What reform are we modeling?
   [ ] Split-rate (land taxed at N× the improvement rate)  ratio: ___
   [ ] Building abatement (exempt ___% of improvement value)
   [ ] Both (compare scenarios)

3. Are we keeping all current exemptions, abatements, and credits in place?
   [ ] Yes — preserve existing structure, only change the rate split
   [ ] No — what changes? ___

4. What is the county and state?  ___  (need for Census FIPS code)

5. Do you know of an official revenue figure to validate against?
   Source: ___   Amount: $___
```

If any answer is unclear, default to: city levy only, 4:1 split-rate, preserve all existing exemptions.

---

## Pipeline

### Step 1 — Discover data
→ See `discover-data.md`

Find the county ArcGIS endpoint. Inspect it. Download the parcel data. Filter to the city. Validate column names, value ranges, and parcel count. Cache to `cities/<city>/data/`.

**Output:** GeoDataFrame loaded and understood. Column mapping table filled in.

---

### Step 2 — Model the policy
→ See `model-policy.md`

Work through the policy questionnaire. Understand the current tax system before modeling the reform. Establish the tax base, millage rate(s), and exemption handling. Implement `current_tax` and validate it against the official revenue figure.

**Output:** `df` has `current_tax`, `PROPERTY_CATEGORY`, and all policy parameters documented in notebook markdown.

---

### Step 3 — Build the notebook
→ See `build-notebook.md`

Write the city notebook following the canonical 7-section template. The census join must happen before the export call. The export call must capture the return value.

**Required closing cells (exact pattern):**
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
            df = match_to_census_blockgroups(df, census_gdf)
            # Merge demographic attributes onto df by std_geoid
            _demo_cols = ['std_geoid', 'median_income', 'minority_pct', 'black_pct', 'total_pop']
            df = df.merge(
                census_data[[c for c in _demo_cols if c in census_data.columns]],
                on='std_geoid', how='left'
            )
            print(f"Census join: {df['std_geoid'].notna().mean()*100:.1f}% matched")
        except concurrent.futures.TimeoutError:
            print("Census API timed out — skipping census join")
            for _col in ['std_geoid', 'median_income', 'minority_pct', 'black_pct']:
                df[_col] = float('nan')
except Exception as e:
    print(f"Census join failed: {e}")
    for _col in ['std_geoid', 'median_income', 'minority_pct', 'black_pct']:
        df[_col] = float('nan')

# Export — df must have census columns by this point
from lvt.lvt_utils import save_standard_export
out_df = save_standard_export(
    df=df,
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

### Step 4 — Execute the notebook
```bash
cd /path/to/LVTShift/cities/<city> && \
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=600 \
  --ExecutePreprocessor.kernel_name=cle-venv-new \
  model.ipynb 2>&1
```

---

### Step 5 — Validate
→ See `validate.md`

Check revenue match, distribution sanity, census coverage, and PNG output.

---

### Step 6 — Cross-city
Re-run `analysis/cross_city.ipynb` to include the new city:
```bash
cd /path/to/LVTShift/analysis && \
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=300 \
  --ExecutePreprocessor.kernel_name=cle-venv-new \
  cross_city.ipynb 2>&1
```

---

### Step 7 — Commit
```bash
git add cities/<city>/model.ipynb
git commit -m "Add <city> LVT model — <model_type>, <N> parcels"
git push
```
