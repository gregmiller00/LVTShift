# LVT Shift Modeling Guide

A step-by-step questionnaire and reference for modeling Land Value Tax (LVT) shift or Universal Building Exemption (UBE) scenarios for a new city using this codebase.

## Core Goal

The goal of every new city notebook is twofold:

1. **Properly simulate the current property tax system as it exists today.**
2. **Properly simulate the proposed reform while changing as little else as possible.**

This guide assumes a conservative policy-design principle:

- **Do not change the current property tax structure unless the user explicitly wants that change.**
- Existing assessment ratios, taxable-value definitions, exemptions, abatements, credits, circuit breakers, and caps should generally remain in place.
- The more pieces of the current system you remove or redesign, the less realistic the model becomes and the less likely the policy is to reflect what could actually pass.

In other words: the default LVT exercise is **not** "replace the whole property tax code." The default is **"hold the current structure constant, then shift the rate structure toward land."**

## Required Workflow

Before building a new notebook, explicitly work through these two stages:

### Stage A — Reconstruct the current system

- Identify the actual tax base used by the jurisdiction.
- Determine whether values are market value, assessed value, taxable value, tax capacity, or some other state-specific construct.
- Confirm the order of operations:
  1. Assessment ratio or state equalization, if any
  2. Exemptions / abatements / exclusions
  3. Tax rate application
  4. Credits / rollbacks / circuit breakers
  5. Floors and caps, including "tax cannot go below zero"
- Validate the modeled current revenue against a known city or levy benchmark whenever possible.

### Stage B — Design the reform with the user

There are many legitimate policy choices, and the notebook should not silently choose among them. The analyst or AI system should ask the user what policy they want to simulate and explain the main options.

At minimum, ask:

- Is the policy city levy only, or the full levy stack?
- Is the reform a split-rate tax, a building exemption, or another land-focused design?
- Should existing exemptions and abatements remain in place? Default: **yes**
- Should existing credits / rollbacks remain in place after tax is computed? Default: **yes**
- Are any current features intentionally being changed by the proposal, or should everything besides the land/building rate structure stay the same? Default: **keep everything else the same**

If the answer is not explicit, default to preserving the current system and note that assumption in the notebook markdown.

Answer the questions in each section in order. Your answers will map directly to the code decisions you need to make in your notebook.

---

## Table of Contents

1. [Section 1 — Data Source](#section-1--data-source)
2. [Section 2 — Key Column Identification](#section-2--key-column-identification)
3. [Section 3 — Geographic Filtering](#section-3--geographic-filtering)
4. [Section 4 — Condo & Stacked-Unit Handling](#section-4--condo--stacked-unit-handling)
5. [Section 5 — Exempt Property Handling](#section-5--exempt-property-handling)
6. [Section 6 — Property Category Mapping](#section-6--property-category-mapping)
7. [Section 7 — Millage Rate & Levy Scope](#section-7--millage-rate--levy-scope)
8. [Section 8 — Current Tax Calculation](#section-8--current-tax-calculation)
9. [Section 9 — Policy Modeling](#section-9--policy-modeling)
10. [Section 10 — Demographic & Equity Analysis](#section-10--demographic--equity-analysis)
11. [Section 11 — Output & Visualization Checklist](#section-11--output--visualization-checklist)
12. [Appendix: City-by-City Reference](#appendix-city-by-city-reference)

---

## Section 1 — Data Source

**Goal:** Locate the parcel-level property assessment data for the city.

### Q1.0 — What policy design assumptions must be confirmed with the user before modeling?

Before touching code, write down the policy choices the user has made and the ones still unresolved.

```
Policy scope confirmed with user: ___________________________________
Current structure preserved unless otherwise specified?  [ ] Yes  [ ] No
Keep existing exemptions / abatements?                   [ ] Yes  [ ] No
Keep existing credits / rollbacks?                       [ ] Yes  [ ] No
Any intentional departures from current law?             ___________________________________
```

> **Instruction for analysts / AI systems:** Do not guess silently here. Summarize the available policy options, ask the user which version they want, and record the answer in the notebook markdown before modeling.

### Q1.1 — What is the primary data portal for this city's parcel data?

Most cities use one of these:
- **ArcGIS REST FeatureServer** (most common): found via city/county GIS portals, e.g., `https://<host>/arcgis/rest/services/<dataset>/FeatureServer/<layer_id>/query`
- **ArcGIS MapServer**: same structure but `/MapServer/` instead
- **Direct CSV or Excel download**: from an open data portal
- **State-level database**: e.g., Minnesota Department of Revenue for St. Paul

> **Action:** Browse the city or county GIS open data portal. Search for "parcels," "property assessment," or "real property." Open the service in a browser and confirm it has the fields you need (land value, improvement value, use code, exemptions).

### Q1.2 — What is the exact ArcGIS service URL and layer ID?

```
Base URL:   ___________________________________________________
Dataset:    ___________________________________________________
Layer ID:   ___ (default is 0; check the service metadata page)
```

**Examples:**
| City | Service URL pattern | Layer |
|------|---------------------|-------|
| Baltimore | `geodata.baltimorecity.gov/.../Realproperty_OB/FeatureServer` | 0 |
| Rochester | `maps.cityofrochester.gov/.../FeatureServer` | 0, 8 |
| Spokane | `services1.arcgis.com/ozNll27nt9ZtPWOn/ArcGIS/rest/services/Parcels` | 0 |
| Chicago | `gis.cookcountyil.gov/.../CookViewer3Parcels/MapServer` | 0 |
| Bellingham | `gis.whatcomcounty.us/.../ParcelViewerAddOnData/MapServer` | 8 |

### Q1.3 — Does the dataset require pagination?

ArcGIS services typically cap at 1,000–2,000 records per query. For a full city:
- Use `get_feature_data()` or `get_feature_data_with_geometry()` from `cloud_utils.py`, both of which paginate automatically.
- Set `paginate=True`.

### Q1.4 — Does the dataset need geographic filtering (city within a county dataset)?

Some cities share a county-wide ArcGIS dataset. You must filter to the city:

```python
# Filter by city name field at query time using a WHERE clause:
where_clause = "UPPER(CITYNAME) = 'CHICAGO'"

# Or filter after loading:
df = df[df['situs_city'].str.upper() == 'BELLINGHAM']
```

> **Key question:** Is this a city-only dataset or county-wide? If county-wide, what column and value identify the target city?

### Q1.5 — What supplemental data sources are needed?

Beyond the main parcel file, two types of supplemental data are commonly needed. Identify which apply to this city:

---

#### Supplemental Type 1: Exemption Amounts

Some parcel datasets do not include exemption dollar amounts in the main table. They may live in a separate layer or file that must be merged onto the parcel data by parcel ID.

```
Are exemption amounts in the main parcel table?  [ ] Yes  [ ] No, separate source
Exemption source (if separate): ___________________________________
Join key: ___  (parcel ID column shared between tables)
```

**Example:** Rochester loads exemptions from a separate ArcGIS layer (layer 8) and merges on `PARCELID`.

---

#### Supplemental Type 2: Millage / Levy Rates

The tax rate applied to each parcel may not be in the main parcel dataset. It may need to come from one of these sources:

| Source type | Example cities | Notes |
|-------------|---------------|-------|
| Already a column in the parcel data | Bellingham (`total_millage`) | Simplest case |
| Scraped from county assessor website | Spokane | Levy table by tax code area |
| Looked up from a separate levy table | Seattle | Match parcel's levy code to rate table |
| Derived from actual tax revenue data | Baltimore, Cincinnati | Divide known total tax revenue by total taxable base |
| Single rate set manually | Chicago, South Bend, Syracuse | Use official city levy rate from budget |

```
Millage rate source: ___________________________________
```

See **Section 7** for the full decision on how to model millage rates, including the critical choice of whether to model the city levy only or the full stack of all levies.

---

## Section 2 — Key Column Identification

**Goal:** Map the source dataset's column names to the standard modeling columns.

After loading the data, run:
```python
print(df.columns.tolist())
print(df.head(2))
df.dtypes
```

Fill in this mapping table:

### Q2.1 — Value Columns

| Modeling concept | Your column name | Notes |
|------------------|-----------------|-------|
| **Land (market) value** | `___` | The assessed land-only value |
| **Improvement (building) value** | `___` | Buildings/structures only |
| **Total assessed value** | `___` | Often land + improvement |
| **Taxable value** | `___` | After exemptions; may differ from total |

**Common naming patterns across cities:**

| City | Land value col | Improvement col | Total col |
|------|---------------|-----------------|-----------|
| Baltimore, Cincinnati | `CURRLAND` | `CURRIMPR` | `CURRFMV` |
| Rochester | `land_value` | `improvement_value` | `CURRENT_TOTAL_VALUE` |
| Spokane, Seattle | `land_value` | `improvement_value` | — |
| Chicago (Cook Co.) | `CURRENTVALUE_LAND` | `CURRENTVALUE_BLDG` | `CURRENTVALUE_TOTAL` |
| Bellingham | `market_land_val` | `market_improvement_val` | `appraised_val_total` |
| South Bend | `REALLANDVA` | `REALIMPROV` | — |
| St. Paul | `EMVLand1` | `EMVBuilding1` | `EMVTotal1` |
| Syracuse | `Lvalue` | computed: `Fvalue - Lvalue` | `Fvalue` |
| Morgantown | `aprland` | `aprbldg` | — |

> **Watch out:** Some jurisdictions (e.g., Chicago Cook County) report values at a fraction of market value (e.g., 1/3). You may need a multiplier:
> ```python
> df['CURRENTVALUE_TOTAL'] = df['CURRENTVALUE_TOTAL'] * 3.0
> df['CURRENTVALUE_LAND'] = df['CURRENTVALUE_LAND'] * 3.0
> df['CURRENTVALUE_BLDG'] = df['CURRENTVALUE_BLDG'] * 3.0
> ```

### Q2.2 — Parcel Identifier Column

```
Parcel ID column: ___  (e.g., PARCELID, prop_id, PIN, APN)
```

Needed for merging supplemental tables (exemptions, levy rates) and for spatial joins.

### Q2.3 — Property Use / Land Use Code Column

```
Property use column: ___  (e.g., LandUse, property_use_description, PROPTYPE, major_class_description)
```

This is used in Section 6 to create the `PROPERTY_CATEGORY` column. It may be a numeric code, a text description, or both.

### Q2.4 — Owner Column (optional, for vacancy analysis)

```
Owner column: ___  (e.g., owner_name, OWNER1)
```

Used in `analyze_vacant_land()` to identify concentrated ownership.

### Q2.5 — Neighborhood / Geography Column (optional)

```
Neighborhood column: ___  (e.g., neighborhood, NBHD, planning_district)
```

Used for spatial breakdowns in analysis.

---

## Section 3 — Geographic Filtering

**Goal:** Ensure the dataframe contains only parcels in the target city.

### Q3.1 — Does the raw dataset cover only the city, or a larger region?

- **City-only dataset** → No filtering needed.
- **County or regional dataset** → Must filter to city parcels.

### Q3.2 — What column and value identifies the city?

```python
# Common patterns:
df = df[df['PROP_CITY'].str.upper().str.contains('SOUTH BEND', na=False)]
df = df[df['situs_city'].str.upper() == 'BELLINGHAM']
df = df[df['CITYNAME'] == 'CHICAGO']
```

### Q3.3 — Are there TIF (Tax Increment Financing) districts?

TIF districts divert property tax revenue from the general fund to a special district account. **For most analyses, TIF districts can simply be ignored** — include all parcels in the model and the analysis remains valid for policy purposes.

Only exclude TIF parcels if you need to precisely match the city's actual general-fund property tax revenue (e.g., for a detailed revenue validation). In that case:

```python
# St. Paul approach (only needed for precise revenue validation):
in_tif = (gdf['TIFDistrict'].notna() & (gdf['TIFDistrict'].str.strip() != ''))
pays_city_tax = (~in_tif & ~fully_exempt & ...)
df_model = gdf[pays_city_tax].copy()
```

```
Does this city have TIF districts?  [ ] Yes  [ ] No  [ ] Unknown
Excluding TIF from model?           [ ] Yes (precise revenue match needed)  [ ] No (typical)
```

---

## Section 4 — Condo & Stacked-Unit Handling

**Goal:** Determine whether individual condo units (or similar sub-parcel records) need to be aggregated to the land parcel level before modeling.

### Q4.1 — Does the dataset have separate rows for individual condo/unit records?

In many assessor databases, each condo unit is its own parcel row with its own assessed value, but they all share a single land parcel. Unit records often have zero or nominal land value, with land value attributed to the "master" parcel only.

**Diagnostic check:**
```python
# Look for duplicate addresses or parcel IDs that might be unit records
df['parcel_id'].duplicated().sum()
df[df['land_value'] == 0].shape[0]      # Units often have $0 land
df['property_use'].value_counts()       # Look for "Condo", "CONDO", "Condominium"
```

### Q4.2 — If condos exist, how do you merge them to the land parcel?

The goal is one row per physical land parcel, with improvements representing the total building value on that land.

**Option A — Master parcel has land, units have zero land:**
Sum improvement values of all units onto their master parcel.
```python
condo_master = df[df['is_condo_master']].copy()
condo_units = df[df['is_condo_unit']].copy()
unit_improvements = condo_units.groupby('master_parcel_id')['improvement_value'].sum()
condo_master = condo_master.join(unit_improvements, on='parcel_id', rsuffix='_from_units')
condo_master['improvement_value'] = condo_master['improvement_value_from_units'].fillna(
    condo_master['improvement_value']
)
# Then combine condo_master with the non-condo parcels
```

**Option B — Each unit record has its own land value:**
Sum both land and improvement values by master parcel or by address.

```
Do condos/stacked units appear as separate rows?  [ ] Yes  [ ] No  [ ] Unknown
Column that links units to master parcel: ___
Aggregation approach (A or B): ___
```

> **Note:** Most existing city notebooks in this repo do not explicitly show condo merging — the assessor dataset may already consolidate them, or the city may not use separate unit records. Verify by checking whether `land_value == 0` rows are numerous and clearly correspond to condo units.

---

## Section 5 — Exempt Property Handling

**Goal:** Identify and properly handle tax-exempt properties (government, religious, nonprofit, etc.) so they don't distort the revenue model.

### Q5.1 — What column(s) identify exempt properties?

There are two common patterns:

**Pattern A — Exemption amount column:**
A column with the dollar value of the exemption. If `exemption_amount >= total_value`, the parcel is fully exempt.

```python
# Baltimore / Cincinnati style:
df['full_exmp'] = (df['EXMPFMV'] >= df['BFCVFMV']).astype(int)

# Spokane / Seattle style:
df['full_exmp'] = (df['taxable_amt'] <= 0).astype(int)

# Bellingham style:
df['exp_flag'] = (df['taxable_val_total'] == 0).astype(int)

# Syracuse style:
df['exemptions'] = df['Fvalue'] - df['CityTaxabl']
```

**Pattern B — Exemption type/code column:**
A categorical column with codes like `'Y'`, `'Exempt'`, `'FULL'`, etc.

```python
# St. Paul style:
fully_exempt = (gdf['TaxExemptYN'] == 'Y')

# Chicago style:
df = df[df['major_class_description'] != 'Exempt Property']

# South Bend style:
df['exemption_flag'] = df['PROPTYPE'].apply(lambda x: 1 if 'Exempt' in str(x) else 0)
```

### Q5.2 — Fill in this table for your city:

```
Exemption amount column (dollar value):     ___  (or None)
Exemption flag/code column:                  ___  (or None)
Value that means "fully exempt":             ___
Partial exemption handling:                  [ ] Apply to improvements first, then land
                                             [ ] Apply to total value only
                                             [ ] No partial exemptions in this dataset
```

### Q5.3 — Filter out fully exempt properties before modeling

```python
# Create the flag
df['full_exmp'] = (df[exemption_col] >= df[total_value_col]).astype(int)

# Remove fully exempt
df_model = df[df['full_exmp'] != 1].copy()
print(f"Removed {len(df) - len(df_model):,} fully exempt parcels")
print(f"Remaining: {len(df_model):,} parcels")
```

> **Important:** The `model_split_rate_tax()` and `calculate_current_tax()` functions also accept `exemption_col` and `exemption_flag_col` parameters to handle partial exemptions within the calculation. You can retain partially-exempt parcels in the model and let the functions zero out their exempt portion.

### Q5.4 — Are there partial exemptions (e.g., homestead, senior, veteran)?

```
Does this city have partial exemptions?     [ ] Yes  [ ] No
Exemption types present:                     ___________________________________
Partial exemption column:                    ___
```

The standard approach in this codebase: partial exemptions reduce improvement value first, then land value (see `_compute_adjusted_values()` in `policy_analysis.py`).

### Q5.5 — Are there post-tax credits, rollbacks, or circuit breakers?

This question is separate from exemptions. Many jurisdictions compute tax on taxable value first and then reduce the bill through credits or rollbacks.

```
Are there post-tax credits / rollbacks?   [ ] Yes  [ ] No  [ ] Unknown
Credit type(s):                            ___________________________________
Credit amount column:                      ___  (or None)
Credit rate/share column:                  ___  (or None)
Applied before or after tax calculation?   [ ] Before  [ ] After  [ ] Need to verify
```

> **Default modeling rule:** If the current system applies credits after tax is computed, the reform model should also apply them after the new tax is computed, unless the user explicitly wants to model a change to those credits.

### Q5.6 — Are there special tax regimes to exclude?

```
Special tax regimes or geographic exclusions: ___________________________________
```

Examples:
- **Rochester:** Homestead vs. non-homestead parcels have different millage rates — must be modeled separately or with per-parcel rate columns
- **Spokane:** Only one tax code area ("Spokane General") is included, not the full county

---

## Section 6 — Property Category Mapping

**Goal:** Create a standardized `PROPERTY_CATEGORY` column that classifies every parcel into a consistent set of types used for all summary tables, charts, and maps.

Assessor databases often have dozens or hundreds of distinct land use codes. This section collapses them into a small set of analytically meaningful categories.

### Q6.1 — What source column contains the property use/type?

```
Source column for categories: ___  (e.g., LandUse, major_class_description, PROPTYPE)
```

### Q6.2 — Enumerate all unique values in that column

```python
print(df['your_use_column'].value_counts(dropna=False).head(60))
```

Review the full list. Note which values correspond to which standard category below. Values that don't fit neatly should be mapped to `'Other'`.

### Q6.3 — Map to standard categories

The seven core property categories used throughout the analysis are:

| Standard Category | Description |
|-------------------|-------------|
| `Single Family Residential` | 1-family homes, townhomes |
| `Small Multi-Family (2-4 units)` | Duplexes, triplexes, quadplexes |
| `Large Multi-Family (5+ units)` | Apartment buildings, garden apartments |
| `Commercial` | Retail, office, hotels, service businesses |
| `Industrial` | Manufacturing, warehousing, utilities |
| `Vacant Land` | Unimproved parcels with no meaningful structure |
| `Transportation - Parking` | Surface parking lots, parking garages |

Additional categories used in some cities:
| Standard Category | Description |
|-------------------|-------------|
| `Other Residential` | Mobile homes, senior housing, mixed residential |
| `Agricultural` | Farm, forestry, agricultural land |
| `Other` | Catch-all for miscellaneous / uncategorized |

**Create your mapping dictionary:**

```python
MY_CITY_LANDUSE_TO_CATEGORY = {
    # Source value             : Standard category
    'RESIDENTIAL 1 FAMILY'    : 'Single Family Residential',
    'RESIDENTIAL 2 FAMILY'    : 'Small Multi-Family (2-4 units)',
    'RESIDENTIAL 3-4 FAMILY'  : 'Small Multi-Family (2-4 units)',
    'APARTMENTS GARDEN'       : 'Large Multi-Family (5+ units)',
    'APARTMENTS HIGH RISE'    : 'Large Multi-Family (5+ units)',
    'COMMERCIAL RETAIL'       : 'Commercial',
    'OFFICE'                  : 'Commercial',
    'INDUSTRIAL'              : 'Industrial',
    'WAREHOUSE'               : 'Industrial',
    'VACANT LAND'             : 'Vacant Land',
    'PARKING LOT'             : 'Transportation - Parking',
    # ... map ALL values from Q6.2
}

df['PROPERTY_CATEGORY'] = df['your_use_column'].map(MY_CITY_LANDUSE_TO_CATEGORY)
df['PROPERTY_CATEGORY'] = df['PROPERTY_CATEGORY'].fillna('Other')
```

### Q6.4 — Override vacant land based on improvement value

Regardless of use code, parcels with zero (or near-zero) improvement value should be reclassified as Vacant Land. This catches parcels that are coded as residential or commercial but have no building on them:

```python
# Override: zero improvement value → Vacant Land
df.loc[df['improvement_value'] == 0, 'PROPERTY_CATEGORY'] = 'Vacant Land'

# Optional: small threshold to catch nominal values (e.g., Morgantown used <= 100):
# df.loc[df['improvement_value'] <= 100, 'PROPERTY_CATEGORY'] = 'Vacant Land'
```

```
Override threshold for Vacant Land: ___  (0 = only truly $0 improvement value)
```

### Q6.5 — Verify the mapping

```python
# Check for unmapped categories
unmapped = df[df['PROPERTY_CATEGORY'] == 'Other']['your_use_column'].value_counts()
print("Codes mapped to 'Other':\n", unmapped)

# Check final distribution
print(df['PROPERTY_CATEGORY'].value_counts())
assert df['PROPERTY_CATEGORY'].isna().sum() == 0, "Nulls remain — fix the mapping"
```

All rows must be mapped before proceeding.

---

## Section 7 — Millage Rate & Levy Scope

**Goal:** Determine what tax rate to apply to each parcel and — critically — which levies are included in the scenario being modeled.

This is one of the most important analytical decisions in the notebook. The answer shapes what revenue you are targeting, what rate you use, and how to interpret the results.

### Q7.1 — What policy scope are you modeling?

Property tax bills are typically the sum of many separate levies: city, county, school district, library, transit, fire, special districts, etc. You must decide:

**Option A — Model the city levy only**

You are analyzing what happens if the *city* shifts its own levy to land value. This is the most common approach for a city-focused analysis.

- Use only the city's millage rate
- Revenue target = city's portion of total property tax revenue
- Results show "what would happen to your city tax bill"

```python
# Example: use the city-specific rate derived from city budget data
city_millage = 22.48  # city levy only, not county or school
```

**Option B — Model the full levy stack**

You are analyzing the cumulative impact of all levies shifting to land value simultaneously. This applies when the parcel data already contains the total millage (all levies combined) or when modeling a statewide policy.

- Use the total millage rate applied to each parcel
- Revenue target = total property tax revenue from all levies
- Results show "what would happen to your total property tax bill"

```python
# Example: Bellingham has total_millage per parcel (all levies combined)
# This models the full stack shift
df['millage_rate'] = df['total_millage']
```

```
Scope of analysis:  [ ] City levy only   [ ] Full levy stack   [ ] Specific levy: ___
```

> **Why this matters:** A city-only analysis will show smaller dollar changes (since the city levy is typically only 20–40% of the total bill) but is more policy-relevant if city council is the decision-maker. A full-stack analysis shows the maximum potential impact but requires legislative action at multiple levels.

### Q7.2 — What is the millage rate for the chosen scope?

The millage rate is expressed as dollars per $1,000 of taxable value (e.g., `22.48` means $22.48 per $1,000, or 2.248%).

**Four ways to obtain it:**

**Method 1 — Derive from actual tax revenue data (most accurate)**
If the dataset includes actual tax bills paid, back-calculate the effective rate:

```python
# Only use non-exempt parcels; filter out outliers if needed
implied_millage = (df['CITY_TAX'].sum() / df['taxable_value'].sum()) * 1000
print(f"Implied millage rate: {implied_millage:.4f}")
```

This is the most accurate method because it accounts for caps, deferrals, and other adjustments that cause actual bills to differ from the posted rate.

**Method 2 — Use a levy table per parcel**
Some datasets include a levy code per parcel; you join a separate levy rate table:

```python
levy_rates = pd.read_csv('levy_rates.csv')  # or scraped from county site
df = df.merge(levy_rates, on='levy_code', how='left')
df['millage_rate'] = df['levy_rate']
```

**Method 3 — Single rate from city budget**
For simplicity, or when parcel-level rates aren't available:

```python
df['millage_rate'] = 22.48  # from city budget document
```

**Method 4 — Already a column in the parcel data**
```python
# Bellingham: total_millage column already present
# No additional work needed
df['millage_rate'] = df['total_millage']
```

```
Method used: ___
Rate value or column: ___
Are there multiple rates (e.g., homestead vs. non-homestead)?  [ ] No  [ ] Yes: ___
```

**Examples from existing cities:**

| City | Rate | Method |
|------|------|--------|
| Baltimore | 22.48 | Derived from `CITY_TAX` / taxable base |
| Rochester | 7.05 (homestead) / 15.7 (non-homestead) | Derived from actual bills; dual rate |
| Spokane | Web-scraped levy table | Per-parcel levy code → rate lookup |
| Chicago | 1.612 | City budget; applied to 3× adjusted values |
| South Bend | 3.3 | City budget |
| Syracuse | 9.2645 | City budget |
| Bellingham | `total_millage` col | Per-parcel (full stack) |
| St. Paul | Derived from Tax Capacity data | State assessment framework |

---

## Section 8 — Current Tax Calculation

**Goal:** Accurately compute the current property tax bill for each parcel. This becomes the baseline for the policy model.

### Q8.0 — What is the current tax formula, in order?

Write the jurisdiction's current tax formula in plain language before coding it.

```
Step 1: _____________________________________________________________
Step 2: _____________________________________________________________
Step 3: _____________________________________________________________
Step 4: _____________________________________________________________
Step 5: _____________________________________________________________
```

Example:

1. Start from market value
2. Apply statewide assessment ratio
3. Subtract exemptions / abatements
4. Apply the relevant levy millage
5. Apply rollbacks / credits

If the jurisdiction provides already-computed taxable land / building values, use those directly rather than reconstructing earlier steps unnecessarily.

### Q8.1 — What is the tax base?

| Approach | Formula | When to use |
|----------|---------|-------------|
| **Total assessed value minus exemptions** | `(land + improvement - exemptions) × rate` | Most cities |
| **Pre-computed taxable value column** | `taxable_value × rate` | When the dataset provides a ready-to-use taxable value (Rochester, St. Paul) |
| **Tax capacity (state-computed)** | `TaxCapacity × rate` | Minnesota cities (St. Paul) |

```
Tax base approach for this city: ___
Tax base column(s): ___
```

### Q8.2 — Calculate current tax using `calculate_current_tax()`

```python
from lvt_utils import calculate_current_tax

# Millage rate must be a column, not a scalar
df['millage_rate'] = 22.48   # or df['total_millage'] or the column you identified in Q7.2

current_revenue, second_revenue, df = calculate_current_tax(
    df=df,
    tax_value_col='your_total_value_col',   # e.g., 'CURRFMV', 'appraised_val_total'
    millage_rate_col='millage_rate',
    exemption_col='your_exemption_col',     # relief applied before tax, or None
    exemption_flag_col='full_exmp',         # or None
    land_value_col='your_taxable_land_col',         # preferred when available
    improvement_value_col='your_taxable_impr_col',  # preferred when available
    credit_col='your_credit_amount_col',            # post-tax credit, or None
    credit_rate_col='your_credit_rate_col',         # post-tax credit share, or None
)

print(f"Modeled current revenue: ${current_revenue:,.0f}")
```

The function returns `(total_revenue, second_revenue, updated_df)` where `updated_df` has a `current_tax` column added.

**Preferred approach:**

- If the dataset has already-computed taxable land and taxable improvement values, use those for the current-tax reconstruction.
- If the dataset only has gross land/building values plus relief amounts, reconstruct taxable values by applying relief in the documented legal order.
- If the system has post-tax credits, apply them after tax is computed.
- In all cases, clip at zero so no parcel has negative taxable value or negative tax.

### Q8.3 — Validate against known revenue figures

```python
actual_revenue = 123_456_789  # from city budget or annual report
print(f"Actual:  ${actual_revenue:,.0f}")
print(f"Modeled: ${current_revenue:,.0f}")
print(f"Difference: {(current_revenue/actual_revenue - 1)*100:.1f}%")
```

A match within ~5% is acceptable. Large discrepancies typically mean:
- Wrong millage rate or wrong scope (city-only vs. full stack)
- Exempt properties not correctly excluded
- Missing parcels (check total parcel count)
- TIF or other excluded revenue class
- Assessment ratio adjustment needed (e.g., Cook County ×3)

---

## Section 9 — Policy Modeling

**Goal:** Model the impact of a policy shift on every parcel's tax bill, maintaining revenue neutrality.

### Q9.0 — Which parts of the current system remain unchanged in the reform?

This should be answered explicitly before running any scenario.

```
Assessment ratio remains unchanged?         [ ] Yes  [ ] No
Existing exemptions remain unchanged?       [ ] Yes  [ ] No
Existing abatements remain unchanged?       [ ] Yes  [ ] No
Existing credits / rollbacks unchanged?     [ ] Yes  [ ] No
Any other current-law feature preserved?    ___________________________________
```

> **Default rule for new notebooks:** Preserve all current-law features except for the land/building rate structure being tested.

### Q9.1 — Which policy are you modeling?

Two distinct policy types are supported:

| Policy | Description | Function |
|--------|-------------|----------|
| **Split-rate LVT** | Tax land at a higher rate than improvements (e.g., 2:1 or 4:1 ratio) | `model_split_rate_tax()` |
| **Building Exemption** | Exempt a percentage (or dollar amount) of improvement value from taxation; remaining base taxed at a single higher rate | Manual calculation (see Q9.3) |

These are related — a building exemption is economically similar to a split-rate tax — but they are modeled differently in the code.

```
Policy type:  [ ] Split-rate LVT   [ ] Building exemption (UBE)   [ ] Both
```

---

### Q9.2 — Split-Rate LVT: `model_split_rate_tax()`

Land is taxed at a rate that is `land_improvement_ratio` times the improvement rate. Both rates are solved simultaneously to hit the revenue target.

**Default implementation rule:** Apply all existing exemptions / abatements first, using the current-law allocation order, then compute the split-rate tax, then apply any credits / rollbacks that currently occur post-tax. Do not remove those features unless the user explicitly asks for that policy change.

**Example scenarios:**

| Ratio | Meaning |
|-------|---------|
| 2:1 | Land taxed at 2× the building rate |
| 4:1 | Land taxed at 4× the building rate |
| Very high (e.g., 100:1) | Approximates a pure land-value tax |

```python
from lvt_utils import model_split_rate_tax

land_millage, improvement_millage, new_revenue, df = model_split_rate_tax(
    df=df,
    land_value_col='your_land_col',
    improvement_value_col='your_impr_col',
    current_revenue=current_revenue,       # from calculate_current_tax()
    land_improvement_ratio=2,              # choose your ratio
    exemption_col='your_exemption_col',    # existing relief applied before tax
    exemption_flag_col='full_exmp',        # or None
    credit_col='your_credit_amount_col',   # existing post-tax credit, or None
    credit_rate_col='your_credit_rate_col',# existing post-tax credit share, or None
)

print(f"Land millage:        {land_millage:.4f}")
print(f"Improvement millage: {improvement_millage:.4f}")
print(f"Revenue:             ${new_revenue:,.0f}")
```

The function adds to `df`:
- `land_tax` — tax from land portion
- `improvement_tax` — tax from improvement portion
- `new_tax_before_credits` — tax before post-tax credits
- `new_tax` — total new tax
- `tax_change` — `new_tax - current_tax`
- `tax_change_pct` — percentage change

**Revenue neutrality check:**
```python
assert abs(df['new_tax'].sum() - current_revenue) / current_revenue < 0.001
```

**Does this jurisdiction need a statutory tax cap?** (e.g., Washington State's 1% cap)
```python
land_millage, improvement_millage, new_revenue, df = model_split_rate_tax(
    ...,
    percentage_cap_col='tax_cap_pct',  # column with max tax as fraction of value (e.g., 0.01)
)
```

```
Statutory tax cap?  [ ] Yes — cap value: ___   [ ] No
```

---

### Q9.3 — Building Exemption (UBE): Manual Calculation

A building exemption exempts some or all of the improvement value from taxation. The remaining taxable base (all land + un-exempted improvements) is then taxed at a single, higher rate to keep revenue neutral. This is not a split-rate system — one rate applies to whatever is left in the tax base.

Just like the split-rate model, the default sequence should be:

1. Start from the current-law land and improvement values
2. Apply existing exemptions / abatements first
3. Apply the reform's building exemption
4. Compute the new tax
5. Apply existing post-tax credits / rollbacks
6. Clip at zero

**Two forms:**

**Form A — Percentage exemption** (e.g., "exempt 50% of building value")
```python
exemption_pct = 0.50  # 50% building exemption (use 1.0 for full/100% UBE)

# Start from current-law taxable components, or compute them first
df['taxable_land_value'] = df['land_value']
df['taxable_improvement_value'] = df['improvement_value']

# Apply existing relief first if needed
if 'existing_exemptions' in df.columns:
    original_improvement = df['taxable_improvement_value'].copy()
    df['taxable_improvement_value'] = (df['taxable_improvement_value'] - df['existing_exemptions']).clip(lower=0)
    remaining_relief = (df['existing_exemptions'] - original_improvement).clip(lower=0)
    df['taxable_land_value'] = (df['taxable_land_value'] - remaining_relief).clip(lower=0)

# Then apply the proposed building exemption
df['new_taxable_base'] = (
    df['taxable_land_value'] + (1 - exemption_pct) * df['taxable_improvement_value']
).clip(lower=0)

# Revenue-neutral rate
total_new_base = df['new_taxable_base'].sum()
new_millage = (current_revenue * 1000) / total_new_base

# New tax per parcel
df['new_tax_before_credits'] = (df['new_taxable_base'] * new_millage / 1000).clip(lower=0)

# Apply post-tax credits if they exist
if 'existing_credit_amount' in df.columns:
    df['new_tax'] = (df['new_tax_before_credits'] - df['existing_credit_amount']).clip(lower=0)
else:
    df['new_tax'] = df['new_tax_before_credits']

df['tax_change'] = df['new_tax'] - df['current_tax']
df['tax_change_pct'] = (df['tax_change'] / df['current_tax'] * 100).where(
    df['current_tax'] > 0, 0
)

print(f"Building exemption: {exemption_pct*100:.0f}% of improvement value exempted")
print(f"Old millage: {old_millage:.4f}")
print(f"New millage: {new_millage:.4f}  ({(new_millage/old_millage - 1)*100:+.1f}% higher)")
print(f"New total revenue: ${df['new_tax'].sum():,.0f}")
```

**Form B — Dollar amount exemption** (e.g., "exempt the first $50,000 of building value")
```python
exemption_base = 50_000  # exempt first $50k of improvement value

# Start from current-law taxable components, or compute them first
df['taxable_land_value'] = df['land_value']
df['taxable_improvement_value'] = df['improvement_value']

# Apply existing relief first if needed
if 'existing_exemptions' in df.columns:
    original_improvement = df['taxable_improvement_value'].copy()
    df['taxable_improvement_value'] = (df['taxable_improvement_value'] - df['existing_exemptions']).clip(lower=0)
    remaining_relief = (df['existing_exemptions'] - original_improvement).clip(lower=0)
    df['taxable_land_value'] = (df['taxable_land_value'] - remaining_relief).clip(lower=0)

df['new_taxable_base'] = (
    df['taxable_land_value'] + (df['taxable_improvement_value'] - exemption_base).clip(lower=0)
).clip(lower=0)

total_new_base = df['new_taxable_base'].sum()
new_millage = (current_revenue * 1000) / total_new_base

df['new_tax_before_credits'] = (df['new_taxable_base'] * new_millage / 1000).clip(lower=0)
if 'existing_credit_amount' in df.columns:
    df['new_tax'] = (df['new_tax_before_credits'] - df['existing_credit_amount']).clip(lower=0)
else:
    df['new_tax'] = df['new_tax_before_credits']
df['tax_change'] = df['new_tax'] - df['current_tax']
df['tax_change_pct'] = (df['tax_change'] / df['current_tax'] * 100).where(
    df['current_tax'] > 0, 0
)
```

```
Building exemption form:  [ ] Percentage (___%)   [ ] Dollar amount ($_____)
```

---

### Q9.4 — Modeling multiple scenarios

It is useful to compare several exemption percentages or split-rate ratios side by side:

```python
# Building exemption: multiple percentages
results = {}
for pct in [0.25, 0.50, 0.75, 1.00]:
    df_s = df.copy()
    df_s['new_taxable_base'] = df_s['land_value'] + (1 - pct) * df_s['improvement_value']
    nm = (current_revenue * 1000) / df_s['new_taxable_base'].sum()
    df_s['new_tax'] = df_s['new_taxable_base'] * nm / 1000
    df_s['tax_change_pct'] = ((df_s['new_tax'] - df_s['current_tax']) / df_s['current_tax'] * 100).where(
        df_s['current_tax'] > 0, 0
    )
    median_sf = df_s[df_s['PROPERTY_CATEGORY'] == 'Single Family Residential']['tax_change_pct'].median()
    results[f'{int(pct*100)}% exemption'] = {'new_millage': nm, 'median_SF_change': median_sf}

import pandas as pd
print(pd.DataFrame(results).T)
```

---

## Section 10 — Demographic & Equity Analysis

**Goal:** Understand how the tax shift affects different property types and communities.

### Q10.1 — Summarize results by property category

```python
from lvt_utils import calculate_category_tax_summary, print_category_tax_summary

summary = calculate_category_tax_summary(
    df=df,
    category_col='PROPERTY_CATEGORY',
    current_tax_col='current_tax',
    new_tax_col='new_tax',
    pct_threshold=10.0,
)
print_category_tax_summary(summary, title="Tax Change by Property Category")
```

### Q10.2 — Join Census demographic data

Use ACS data at the census block group level to analyze equity impacts. After a spatial join of parcels to block groups, `df` should have a `std_geoid` column (11-digit block group FIPS code).

```python
from viz import calculate_block_group_summary

bg_summary = calculate_block_group_summary(
    df=df,
    group_col='std_geoid',
    tax_change_col='tax_change',
    current_tax_col='current_tax',
    new_tax_col='new_tax',
)
```

```
Census analysis needed?  [ ] Yes  [ ] No
ACS variables (typical): median_income, minority_pct, black_pct
```

### Q10.3 — Quintile analysis by income

```python
from viz import create_quintile_summary, plot_quintile_analysis

quintile_summary = create_quintile_summary(
    df=bg_summary,
    group_col='median_income',
    value_col='median_income',
    tax_change_col='tax_change',
    tax_change_pct_col='tax_change_pct',
)
plot_quintile_analysis(quintile_summary, title="Tax Impact by Income Quintile")
```

### Q10.4 — Vacant land and parking lot analysis

```python
from policy_analysis import analyze_vacant_land, print_vacant_land_summary
from policy_analysis import analyze_parking_lots, print_parking_analysis_summary

vacant = analyze_vacant_land(
    df=df,
    land_value_col='land_value',
    property_type_col='PROPERTY_CATEGORY',
    vacant_identifier='Vacant Land',
    improvement_value_col='improvement_value',
    neighborhood_col='neighborhood',    # or None
    owner_col='owner_name',             # or None
    exemption_col='exemptions',         # or None
    exemption_flag_col='full_exmp',     # or None
)
print_vacant_land_summary(vacant)
```

---

## Section 11 — Output & Visualization Checklist

Use this as a final checklist before the notebook is complete.

The best reference for what a finished notebook should look like are the existing examples in `examples/`. In particular, `baltimore.ipynb`, `rochester.ipynb`, and `st_paul_v2.ipynb` have the most complete visualization sections. Study those before building charts for a new city.

### Data validation
- [ ] Row count after filtering is plausible (cross-check against assessor records)
- [ ] Total land value and total improvement value are plausible for the city's size
- [ ] Modeled `current_revenue` matches known city property tax levy (within ~5%)
- [ ] Current tax formula is written out in notebook markdown in the correct legal order
- [ ] `PROPERTY_CATEGORY` has no null values; distribution looks reasonable
- [ ] No fully-exempt parcels remain in `df_model`

### Policy model outputs
- [ ] `current_tax` column computed and validated
- [ ] Existing exemptions / abatements preserved unless user explicitly changed them
- [ ] Existing credits / rollbacks preserved unless user explicitly changed them
- [ ] No parcel has negative taxable value, `current_tax`, or `new_tax`
- [ ] `new_tax` column computed
- [ ] `tax_change` = `new_tax - current_tax`
- [ ] `tax_change_pct` = `(tax_change / current_tax) * 100`
- [ ] Revenue neutrality confirmed: `new_tax.sum() ≈ current_revenue`
- [ ] New rate(s) printed (land millage + improvement millage for split-rate; single new millage for building exemption)

### Key charts (see existing notebooks for code)

**1. Revenue shift by property category — total dollars**
A horizontal bar chart showing the aggregate dollar change in tax burden for each property category. This answers: "Which types of properties pay more and which pay less in total?" Use `calculate_category_tax_summary()` output.

**2. Revenue shift by property category — median % change per parcel**
A bar chart showing the median percentage tax change across parcels within each category. This answers: "What does the typical property of each type experience?" Separates outliers from the central tendency.

**3. Progressivity chart — tax change % by neighborhood income quintile**
A line or bar chart of mean/median tax change percentage grouped by census block group income quintile. This answers: "Is this policy progressive (lower-income areas see lower increases or larger decreases) or regressive?" Use `create_quintile_summary()` and `plot_quintile_analysis()`.

**4. Scatter plot — neighborhood income vs. mean tax change %**
One point per block group, x-axis = median income, y-axis = mean parcel tax change %. Show two versions: all properties, and non-vacant properties only. Use `plot_comparison()` from `viz.py`.

**5. Choropleth map — tax change % by parcel**
A geographic map colored by `tax_change_pct`. Useful for communicating spatial patterns to non-technical audiences. Use `create_map_visualization()` from `viz.py`.

**6. Improvement ratio analysis**
Bar chart or table showing how much of the city's land value sits in parcels with low improvement ratios (i.e., underutilized land). Use `analyze_land_by_improvement_share()` from `policy_analysis.py`.

### Equity narrative (complete in the notebook's markdown cells)
- [ ] Is the shift progressive or regressive overall?
- [ ] What share of single-family homeowners see a tax increase vs. decrease?
- [ ] What is the median tax change for residential parcels?
- [ ] How does the result differ across city neighborhoods?

---

## Appendix: City-by-City Reference

A quick-reference summary of how each existing notebook handles the key decisions.

| City | Data source | Land col | Improvement col | Exemption method | Levy scope | Categories source | Split ratio |
|------|------------|---------|-----------------|-----------------|------------|------------------|-------------|
| **Baltimore** | ArcGIS FeatureServer | `CURRLAND` | `CURRIMPR` | `EXMPFMV` amt; `full_exmp` flag | City levy (derived from `CITY_TAX`) | `ZONECODE` → mapping | 2:1 |
| **Rochester** | ArcGIS MapServer (layers 0 + 8) | `land_value` | `improvement_value` | `total_exemptions` col | City levy; dual rate (homestead 7.05 / non-homestead 15.7) | Use code → mapping | 2:1 |
| **Spokane** | ArcGIS FeatureServer | `land_value` | `improvement_value` | `taxable_amt <= 0` | City levy (scraped by levy code) | Use code → mapping | 2:1 |
| **Chicago** | Cook County MapServer (WHERE CITYNAME) | `CURRENTVALUE_LAND × 3` | `CURRENTVALUE_BLDG × 3` | `major_class_description == 'Exempt'` | City levy (1.612) | `major_class_description` | 4:1 |
| **Cincinnati** | ArcGIS (Baltimore-style schema) | `CURRLAND` | `CURRIMPR` | `EXMPFMV` amt; `full_exmp` flag | City levy (derived from `CITY_TAX`) | Zone code → mapping | 2:1 |
| **Bellingham** | Whatcom County MapServer (WHERE situs_city) | `market_land_val` | `market_improvement_val` | `exp_amt`; `taxable_val_total == 0` | Full stack (`total_millage` col per parcel) | `property_use_description` | 2:1 |
| **South Bend** | ArcGIS FeatureServer (WHERE PROP_CITY + TAXDIST) | `REALLANDVA` | `REALIMPROV` | ExemptAmt1–6 summed; `PROPTYPE` contains 'Exempt' | City levy (3.3) | `PROPTYPE` → mapping | 2:1 |
| **St. Paul** | Ramsey County FeatureServer + MN Dept. of Revenue Excel | `EMVLand1` / `TaxCapacity_Land` | `EMVBuilding1` / `TaxCapacity_Improvements` | `TaxExemptYN == 'Y'`; TIF excluded | City levy (derived from Tax Capacity) | `LandUseCodeDescription` + `UseType1` | 2:1 and 4:1 |
| **Syracuse** | ArcGIS FeatureServer | `Lvalue` | `Fvalue - Lvalue` | `Fvalue - CityTaxabl` | City levy (9.2645) | `LandUse` → mapping | 2:1 |
| **Morgantown** | ArcGIS FeatureServer | `aprland` | `aprbldg` | Not fully documented | Not fully documented | Custom WV land use mapping | 2:1 |
