# Skill: Discover Data

Sub-skill called from `add-city.md` Step 1.

This skill covers finding the county ArcGIS endpoint, inspecting its schema, downloading parcel data, filtering to the city, and validating the result.

---

## Step 1 — Find the ArcGIS Endpoint

### Where to look

1. **County GIS portal** — Google `"[County Name] County GIS ArcGIS REST services"` or `"[County] open data portal"`
2. **State open data hubs** — many states aggregate county GIS (e.g., Ohio Hub, Pennsylvania PASDA)
3. **WPRDC** (Western PA) — Allegheny County uses `data.wprdc.org` for attributes + separate GIS for geometry
4. **Direct REST URL pattern**: `https://[county-gis-domain]/arcgis/rest/services/[ServiceName]/FeatureServer/0`

### How to inspect the service

```bash
# Get layer metadata (field names, geometry type, record count)
curl "https://[base-url]/FeatureServer/0?f=json" | python3 -m json.tool | head -100

# Get a sample of 5 records to see actual values
curl "https://[base-url]/FeatureServer/0/query?where=1=1&outFields=*&resultRecordCount=5&f=json" | python3 -m json.tool
```

Key things to confirm from metadata:
- `geometryType` — should be `esriGeometryPolygon` (parcel boundaries)
- `maxRecordCount` — typically 1000 or 2000 (controls pagination)
- Field list — look for land value, improvement value, total value, use code, tax/exempt info

---

## Step 2 — Download the Data

Use `get_feature_data_with_geometry()` from `lvt.cloud_utils`. It handles ArcGIS pagination, CRS detection, and geometry conversion automatically.

```python
from lvt.cloud_utils import get_feature_data_with_geometry
from pathlib import Path

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

PARCEL_PATH = DATA_DIR / 'parcels.gpq'

if PARCEL_PATH.exists():
    import geopandas as gpd
    gdf = gpd.read_parquet(PARCEL_PATH)
    print(f"Loaded {len(gdf):,} parcels from cache")
else:
    gdf = get_feature_data_with_geometry(
        dataset_name='county_parcels',
        base_url='https://[county-gis-domain]/arcgis/rest/services/[ServiceName]/FeatureServer',
        layer_id=0,
        paginate=True,
    )
    gdf.to_parquet(PARCEL_PATH)
    print(f"Downloaded {len(gdf):,} parcels")
```

### Common variations

**County uses MapServer instead of FeatureServer:**
```python
from lvt.cloud_utils import get_feature_data
gdf = get_feature_data(base_url='...MapServer', layer_id=0)
```

**Attributes and geometry are separate sources (Pittsburgh / Allegheny County):**
```python
import pandas as pd
import geopandas as gpd

# Attributes from CSV (WPRDC)
df_attr = pd.read_csv('https://data.wprdc.org/dataset/property-assessments/...')

# Geometry from ArcGIS
gdf_geo = get_feature_data_with_geometry(
    dataset_name='allegheny_parcels',
    base_url='https://gisdata.alleghenycounty.us/arcgis/rest/services/OPENDATA/Parcels/MapServer',
    layer_id=0,
)

# Join on normalized parcel ID
df_attr['PARID_clean'] = df_attr['PARID'].str.replace(r'\W', '', regex=True)
gdf_geo['PIN_clean'] = gdf_geo['PIN'].str.replace(r'\W', '', regex=True)
gdf = gdf_geo.merge(df_attr, left_on='PIN_clean', right_on='PARID_clean', how='inner')
```

---

## Step 3 — Filter to the City

County datasets include all municipalities. Filter to city parcels only.

### By city name field
```python
gdf = gdf[gdf['MUNICIPALITY'].str.upper() == 'SPOKANE'].copy()
```

### By numeric municipality code
```python
# Pittsburgh: wards 101–132
gdf = gdf[gdf['MUNICODE'].between(101, 132)].copy()
```

### By tax district string
```python
# Cincinnati: filter to city tax district
gdf = gdf[gdf['TAX_DISTRICT'] == 'CINTI CORP-CINTI CSD'].copy()
```

### By city site address field
```python
# Ramsey County / St. Paul
gdf = gdf[gdf['SiteCityName'] == 'SAINT PAUL'].copy()
```

### By spatial join (if no attribute filter exists)
```python
# Download city boundary from Census TIGER
import requests
city_boundary = gpd.read_file('https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/14/query?where=NAME+%3D+%27Springfield%27+AND+STATEFP+%3D+%2717%27&outFields=*&f=geojson')
gdf = gpd.sjoin(gdf, city_boundary[['geometry']], how='inner', predicate='within')
```

---

## Step 4 — Validate the Download

Run all three checks before proceeding.

### Check 1: Parcel count
Look up the city's official parcel count (county assessor website or city open data). Should be within 5%.

```python
print(f"City parcels in GDF: {len(gdf):,}")
# Expected: ~XX,000 per research
assert len(gdf) > 5_000, "Too few parcels — filter may be wrong"
```

### Check 2: Column inventory
```python
print("Columns:", list(gdf.columns))
print("\nValue columns (sample):")
print(gdf[['LAND_VALUE', 'IMPROVEMENT_VALUE', 'TOTAL_VALUE']].describe())
```

Confirm you can identify:
- [ ] Land value column
- [ ] Improvement value column  
- [ ] Total value column
- [ ] Use/class code column
- [ ] Exemption indicator (flag column or dollar amount column)
- [ ] Tax district / municipality column (for filtering)

### Check 3: Value ranges
```python
print(f"Parcels with $0 land value: {(gdf['LAND_VALUE'] == 0).sum():,}")
print(f"Parcels with $0 improvement: {(gdf['IMPROVEMENT_VALUE'] == 0).sum():,}")
print(f"Parcels with $0 total: {(gdf['TOTAL_VALUE'] == 0).sum():,}")
print(f"Median land value: ${gdf['LAND_VALUE'].median():,.0f}")
print(f"Median improvement value: ${gdf['IMPROVEMENT_VALUE'].median():,.0f}")
```

Red flags:
- > 30% of parcels with $0 land value → likely exempt parcels mixed in, or wrong column
- Negative values → need to clip to 0 before modeling
- Land > Total → data error, investigate

---

## Step 5 — Column Mapping Table

Fill this in before writing any modeling code. Keep it in a notebook markdown cell.

```markdown
| Concept | Column Name | Notes |
|---|---|---|
| Land value | `LAND_VALUE` | Market value, not assessed |
| Improvement value | `IMPROVEMENT_VALUE` | Buildings + structures |
| Total value | `TOTAL_VALUE` | Land + improvement |
| Use/class code | `CLASSCD` | 3-digit NYS code |
| Exemption flag | `full_exmp` | 1 = fully exempt |
| Dollar exemption | `EXEMPTION_AMT` | Applied to improvement first |
| Tax district | `TAX_DISTRICT` | Used for city filter |
| Parcel ID | `PARID` | For joins and deduplication |
| Municipality | `MUNI_CODE` | 101-132 = Pittsburgh wards |
```

**Assessment ratio**: [35% Ohio / 100% full value / Tax Capacity (MN) / other]  
**Millage source**: [city budget doc / county levy table / derived from CITY_TAX column]

---

## Output Checklist

- [ ] GeoDataFrame `gdf` loaded with correct city parcels
- [ ] Parcel count matches official source within 5%
- [ ] All value columns identified and named
- [ ] Exemption mechanism understood
- [ ] Column mapping table documented in notebook markdown cell
- [ ] Data cached to `cities/<city>/data/` as `.gpq`
