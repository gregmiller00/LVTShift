# Bryan, TX Parcel Endpoint — Notebook Reference Spec

## Primary Data Source: Brazos CAD

Brazos Central Appraisal District (Brazos CAD) is the single authoritative source for parcel-level
property, ownership, and valuation data in Brazos County, which includes the City of Bryan.
There is **no live ArcGIS FeatureServer REST endpoint** for Brazos CAD parcels. Data is distributed
as periodic **shapefile downloads** and flat-file **certified appraisal exports** from the CAD website.

---

## Parcel Geometry — Shapefile Downloads

```text
GIS DATA PAGE:    https://brazoscad.org/gis/
CURRENT MONTHLY:  https://brazoscad.org/wp-content/uploads/2024/03/PUBLIC_PARCEL_BOUNDARY.zip
2025 CERTIFIED:   https://brazoscad.org/wp-content/uploads/2025/11/Public_Parcel_Boundary_certified.zip
2024 CERTIFIED:   https://brazoscad.org/wp-content/uploads/2024/08/Public_Parcel_Boundary_certified.zip
```

These are countywide shapefiles. To isolate Bryan parcels, you must filter after loading —
see **Bryan Filter Strategy** below.

Recommended workflow:
- Download the monthly shapefile (most current geometry) or the most recent certified shapefile.
- Load into GeoPandas, filter to Bryan, cache to `examples/data/bryan/bryan_parcels_<date>.parquet`.
- Join the appraisal export (flat-file) on `GEO_ID` to attach ownership and valuation fields.
- Optionally spatially stamp zoning from the Bryan zoning layer.

---

## Appraisal / Valuation Data — Certified Flat-File Export

The parcel shapefile carries **geometry only** (and a `GEO_ID` join key). All valuation, ownership,
exemption, and classification data lives in the PACS appraisal export files:

```text
CERTIFIED DATA PAGE: https://brazoscad.org/certified-data-downloads/
2025 CERTIFIED ZIP:  https://brazoscad.org/wp-content/uploads/2025/08/2025-CERTIFIED-EXPORT.zip
FILE LAYOUT PDF:     https://brazoscad.org/wp-content/uploads/2021/07/Appraisal-Export-Layout-8.0.25-2.pdf
```

The ZIP contains fixed-width text files. The most important for parcel analysis:

| File | Short Name | Contents |
|---|---|---|
| `APPRAISAL_INFO.TXT` | `PROP.TXT` | Primary property record — one row per property/owner |
| `APPRAISAL_ENTITY_INFO.TXT` | `PROP_ENT.TXT` | Per-entity assessed/taxable values and exemption amounts |
| `APPRAISAL_IMPROVEMENT_INFO.TXT` | `IMP_INFO.TXT` | Improvement (structure) records |
| `APPRAISAL_IMPROVEMENT_DETAIL.TXT` | `IMP_DET.TXT` | Detail records (area, year built, class code) |
| `APPRAISAL_LAND_DETAIL.TXT` | `LAND_DET.TXT` | Land segment records (acres, ag, homesite flag) |
| `APPRAISAL_ABSTRACT_SUBDV.TXT` | `ABS_SUBD.TXT` | Abstract/subdivision code lookup |
| `APPRAISAL_STATE_CODE.TXT` | `STATE_CD.TXT` | State property tax code lookup |

---

## Fields to Pull from `APPRAISAL_INFO.TXT`

### Identity / Keys
| Field | Type | Notes |
|---|---|---|
| `prop_id` | int(12) | **Primary key.** Internal PACS integer ID. Use for joins within export files. |
| `geo_id` | char(50) | **Geographic ID — join key to shapefile.** Equivalent to a parcel or account number. |
| `prop_type_cd` | char(5) | `R`=Real, `P`=Business Personal, `M`=Mobile Home, `MN`=Mineral, `A`=Auto |
| `prop_val_yr` | numeric(5) | Appraisal/tax year |
| `sup_num` | int(12) | Supplement number; `0` = certified data |

### Ownership / Mailing
| Field | Type | Notes |
|---|---|---|
| `py_owner_name` | char(70) | Property-year owner name |
| `py_addr_line1` | char(60) | Mailing address line 1 |
| `py_addr_line2` | char(60) | Mailing address line 2 |
| `py_addr_city` | char(50) | Mailing city |
| `py_addr_state` | char(50) | Mailing state |
| `py_addr_zip` | char(5) | Mailing ZIP (5-digit) |
| `jan1_owner_name` | char(70) | January 1 owner (tax-lien owner of record) |
| `dba` | char(40) | Doing-business-as name |

### Situs / Location
| Field | Type | Notes |
|---|---|---|
| `situs_num` | char(15) | Situs street number |
| `situs_unit` | char(5) | Situs unit number |
| `situs_street_prefx` | char(10) | Situs street prefix |
| `situs_street` | char(50) | Situs street name |
| `situs_street_suffix` | char(10) | Situs street suffix |
| `situs_city` | char(30) | **Situs city — use to filter for Bryan** |
| `situs_zip` | char(10) | Situs ZIP |

### Legal / Plat
| Field | Type | Notes |
|---|---|---|
| `legal_desc` | char(255) | Legal description |
| `legal_desc2` | char(255) | Additional legal description |
| `legal_acreage` | numeric(16) | Legal acreage (4 decimals) |
| `abs_subdv_cd` | char(10) | Abstract/subdivision code (joins to `ABS_SUBD.TXT`) |
| `hood_cd` | char(10) | Neighborhood code |
| `block` | char(50) | Block |
| `tract_or_lot` | char(50) | Tract or lot |
| `ref_id1` | char(25) | Property reference ID 1 |
| `ref_id2` | char(25) | Property reference ID 2 |

### Valuation
| Field | Type | Notes |
|---|---|---|
| `land_hstd_val` | numeric(15) | Land homestead value |
| `land_non_hstd_val` | numeric(15) | Land non-homestead value |
| `imprv_hstd_val` | numeric(15) | Improvement homestead value |
| `imprv_non_hstd_val` | numeric(15) | Improvement non-homestead value |
| `ag_use_val` | numeric(15) | Agriculture use value |
| `ag_market` | numeric(15) | Agriculture market value |
| `timber_use` | numeric(15) | Timber use value |
| `timber_market` | numeric(15) | Timber market value |
| `appraised_val` | numeric(15) | Appraised value |
| `ten_percent_cap` | numeric(15) | Homestead cap adjustment (appraised − assessed) |
| `assessed_val` | numeric(15) | Assessed value (appraised minus cap) |
| `market_value` | numeric(14) | Property market value |
| `land_acres` | numeric(20) | Sum of acres across all land segments |

### State Property Tax Codes
| Field | Type | Notes |
|---|---|---|
| `imprv_state_cd` | char(10) | State code on improvements |
| `land_state_cd` | char(10) | State code on land |
| `personal_state_cd` | char(10) | State code on personal property |

### Sale / Deed
| Field | Type | Notes |
|---|---|---|
| `deed_book_id` | char(20) | Deed book ID |
| `deed_book_page` | char(20) | Deed book page |
| `deed_dt` | char(25) | Deed date |
| `deed_num` | char(50) | Deed number |

### Key Exemption Flags (all `char(1)`, `T`/`F`)
| Field | Exemption |
|---|---|
| `hs_exempt` | Homestead |
| `ov65_exempt` | Over 65 |
| `dp_exempt` | Disabled Person |
| `dv1_exempt`–`dv4_exempt` | Disabled Veteran (10%–100%) |
| `ex_exempt` | Total Exemption |
| `ab_exempt` | Abatement |
| `fr_exempt` | Freeport |
| `ag_late_loss` | Late ag loss flag |

> **Tip:** The `APPRAISAL_ENTITY_INFO.TXT` file carries per-taxing-entity assessed values,
> taxable values, and exemption dollar amounts. Join on `prop_id + prop_val_yr + sup_num + owner_id`.
> Entity codes for Bryan taxing units include `BCB` (City of Bryan), `BRY` (Bryan ISD), `BC`
> (Brazos County). Filter by `entity_cd` to isolate Bryan city-jurisdiction values.

---

## Bryan Filter Strategy

### Attribute filter (fast, good enough for most work)
```python
# After loading the shapefile into a GeoDataFrame:
gdf_bryan = gdf[gdf["situs_city"].str.upper() == "BRYAN"]

# Or in the appraisal export flat file:
df_bryan = df[df["situs_city"].str.upper() == "BRYAN"]
```

### Strict municipal-boundary filter
For work that must respect Bryan's legal city limits (not the broader mailing city pattern),
use the Bryan city limits layer available through the City of College Station's shared GIS server:

```text
CITY LIMITS LAYER (Bryan, hosted on CS GIS server):
  URL: https://gis.cstx.gov/csgis/rest/services/_PublicUse/PublicUse_CityDataFiles/MapServer/17
  Layer ID: 17
  Layer Name: Bryan City Limits - 2023
  Geometry Type: esriGeometryPolygon
  Query:  /query?where=1=1&outFields=*&returnGeometry=true&f=geojson
```

Workflow: fetch that polygon, then do a spatial intersect/clip of your parcel GeoDataFrame.

---

## Zoning Layer — City of Bryan

Bryan publishes its official zoning layer. The preferred current source is via ArcGIS Hub:

```text
HUB ITEM:   https://hub.arcgis.com/datasets/62bb00134ce8476daa0aa1fd37bf5c02
```

Recommended notebook workflow:
- Download Bryan zoning polygons and cache to `examples/data/bryan/bryan_zoning_<date>.parquet`.
- Spatially join parcels (centroid-within polygon) to stamp `ZONING_DISTRICT` onto each parcel.
- Bryan's Unified Development Code zoning categories include SF (single-family), MF (multi-family),
  C (commercial), I (industrial), AG (agricultural), and PD (planned development) families.
- For authoritative zoning queries, confirm against the Development Center at 979-209-5030 or
  Bryan's online mapping tool at `https://maps.bryantx.gov/plan/`.

---

## Property Search / Spot-Check Portal

```text
BRAZOS CAD PROPERTY SEARCH:  https://esearch.brazoscad.org/
BRAZOS CAD INTERACTIVE MAP:  https://gis.bisclient.com/brazoscad/
BRAZOS COUNTY TAX OFFICE:    https://brazostax.org/
```

Use `geo_id` or `prop_id` to look up individual accounts. The property search shows current
certified values, exemptions, and entity levy information not present in the shapefile.

---

## Data Loading Pattern (Python)

```python
import geopandas as gpd
import pandas as pd
import zipfile, io, urllib.request

# --- Step 1: Download & load parcel shapefile ---
SHP_URL = "https://brazoscad.org/wp-content/uploads/2024/03/PUBLIC_PARCEL_BOUNDARY.zip"
# Download zip, extract, read with GeoPandas
# (File names inside the zip vary by release; inspect with zipfile.ZipFile)

gdf = gpd.read_file("PUBLIC_PARCEL_BOUNDARY.shp")

# --- Step 2: Filter to Bryan ---
gdf_bryan = gdf[gdf["SITUS_CITY"].str.upper() == "BRYAN"].copy()

# --- Step 3: Download & parse appraisal export ---
EXPORT_URL = "https://brazoscad.org/wp-content/uploads/2025/08/2025-CERTIFIED-EXPORT.zip"
# The export is fixed-width; use the field layout PDF for byte offsets.
# Key fields for a basic parcel join:
PROP_COLS = {
    "prop_id":         (0, 12),
    "geo_id":          (546, 596),
    "prop_type_cd":    (12, 17),
    "py_owner_name":   (608, 678),
    "situs_city":      (1109, 1139),
    "situs_street":    (1049, 1099),
    "situs_num":       (4459, 4474),
    "assessed_val":    (1945, 1960),
    "appraised_val":   (1915, 1930),
    "market_value":    (4213, 4227),
    "land_hstd_val":   (1795, 1810),
    "imprv_hstd_val":  (1825, 1840),
    "land_acres":      (2771, 2791),
    "hs_exempt":       (2608, 2609),
    "land_state_cd":   (2741, 2751),
    "imprv_state_cd":  (2731, 2741),
}

def parse_fixed_width(filepath, col_specs):
    rows = []
    with open(filepath, "r", encoding="latin-1") as f:
        for line in f:
            row = {k: line[s:e].strip() for k, (s, e) in col_specs.items()}
            rows.append(row)
    return pd.DataFrame(rows)

df_prop = parse_fixed_width("APPRAISAL_INFO.TXT", PROP_COLS)
df_bryan = df_prop[df_prop["situs_city"].str.upper() == "BRYAN"]

# --- Step 4: Join geometry to appraisal data ---
merged = gdf_bryan.merge(df_bryan, left_on="GEO_ID", right_on="geo_id", how="left")
```

---

## Key Facts to Hard-Code

```python
CAD_NAME             = "Brazos Central Appraisal District"
CAD_GIS_URL          = "https://brazoscad.org/gis/"
CAD_CERT_URL         = "https://brazoscad.org/certified-data-downloads/"
CAD_PROPERTY_SEARCH  = "https://esearch.brazoscad.org/"
CAD_EXPORT_LAYOUT    = "https://brazoscad.org/wp-content/uploads/2021/07/Appraisal-Export-Layout-8.0.25-2.pdf"
PACS_VERSION         = "8.0.25"              # layout version as of 2021 PDF

COUNTY               = "Brazos County"
CITY_FILTER_FIELD    = "situs_city"
CITY_FILTER_VALUE    = "BRYAN"
JOIN_KEY             = "geo_id"              # shapefile field name may vary (check caps)
PRIMARY_KEY          = "prop_id"

BRYAN_CITY_LIMITS_URL = (
    "https://gis.cstx.gov/csgis/rest/services/_PublicUse/"
    "PublicUse_CityDataFiles/MapServer/17/query"
)
BRYAN_ZONING_HUB     = "https://hub.arcgis.com/datasets/62bb00134ce8476daa0aa1fd37bf5c02"
COUNTY_TAX_OFFICE    = "https://brazostax.org/"

# Texas-specific state property type codes (from PACS STATE_CD.TXT / Comptroller table)
# Common codes for Bryan residential analysis:
# A1 = Single-family residence
# A2 = Single-family residence (mobile home)
# B1 = Multi-family (apartments, > 4 units)
# C1 = Vacant lot
# D1 = Qualified open space / ag land
# D2 = Farm and ranch improvements
# F1 = Commercial real property
# F2 = Industrial real property
# J = Utilities

# Derived / computed fields useful in analysis
# TotalMarketValue    = market_value (from APPRAISAL_INFO)
# TotalAssessedValue  = assessed_val (appraised_val minus ten_percent_cap)
# AssessedToMarket    = assessed_val / market_value (when market_value > 0)
# ImprovementRatio    = (imprv_hstd_val + imprv_non_hstd_val) / market_value
# ZONING_DISTRICT     = stamped from Bryan zoning polygons (centroid within)
# ANALYSIS_CATEGORY   = refined from prop_type_cd + imprv_state_cd + zoning
```

---

## Known Limitations

| Issue | Detail |
|---|---|
| No live REST endpoint | Brazos CAD distributes data as shapefile + flat-file downloads only; there is no public ArcGIS FeatureServer for parcel queries. |
| Geometry and appraisal are separate files | The shapefile carries geometry and `GEO_ID`; all valuation fields require downloading and parsing the PACS fixed-width export. |
| Fixed-width format | The export uses byte-offset fixed-width fields, not CSV. Use the official layout PDF for field positions. |
| Countywide shapefile | Includes all Brazos County parcels; filter to Bryan by `situs_city = 'BRYAN'` or by spatial clip against the city limits layer. |
| Situs-city vs. legal-boundary mismatch | `situs_city` is a text attribute, not a spatial filter. Use the Bryan city limits polygon for strict ETJ/boundary work. |
| No per-row edit timestamps | The public shapefile does not expose row-level last-edited timestamps. |
| Certified vs. monthly | The monthly shapefile has the most current geometry but may not be certified for tax purposes; the certified ZIP (released ~August each year) is the official annual snapshot. |
| PACS multi-owner properties | `APPRAISAL_INFO.TXT` can contain multiple rows per `prop_id` if a property has multiple owners (UDI group). Deduplicate or aggregate as needed. |
| No billed tax in open data | Tax levy and bill amounts are not in the shapefile or certified export; use `https://brazostax.org/` for levy details. |
| Bryan ETJ parcels | Some Bryan-adjacent parcels in the extraterritorial jurisdiction (ETJ) carry `situs_city = 'BRYAN'` but are outside city limits. Use the spatial city limits layer to exclude them if needed. |
