# College Station, TX Parcel Endpoint — Notebook Reference Spec

## Primary Data Source: Brazos CAD

Brazos Central Appraisal District (Brazos CAD) is the single authoritative source for parcel-level
property, ownership, and valuation data in Brazos County, which includes the City of College Station.
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

These are countywide shapefiles. To isolate College Station parcels, you must filter after loading —
see **College Station Filter Strategy** below.

Recommended workflow:
- Download the monthly shapefile (most current geometry) or the most recent certified shapefile.
- Load into GeoPandas, filter to College Station, cache to
  `examples/data/college_station/cs_parcels_<date>.parquet`.
- Join the appraisal export (flat-file) on `GEO_ID` to attach ownership and valuation fields.
- Spatially stamp zoning from the College Station open-data zoning layer.
- Build a refined analysis category from the PACS state property code and zoning district,
  accounting for TAMU-related exemptions which are uniquely prevalent in College Station.

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

> **College Station note:** A significant share of parcels within city limits are owned by
> The Texas A&M University System or its component agencies. These carry `ex_exempt = 'T'`
> (total exemption) and `ex_amt` will equal the full appraised value at the entity level.
> Filter them in or out intentionally depending on your analysis scope.

### Situs / Location
| Field | Type | Notes |
|---|---|---|
| `situs_num` | char(15) | Situs street number |
| `situs_unit` | char(5) | Situs unit number |
| `situs_street_prefx` | char(10) | Situs street prefix |
| `situs_street` | char(50) | Situs street name |
| `situs_street_suffix` | char(10) | Situs street suffix |
| `situs_city` | char(30) | **Situs city — use to filter for College Station** |
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
| `ex_exempt` | **Total Exemption** — covers TAMU/state-owned land, churches, nonprofits |
| `ab_exempt` | Abatement |
| `fr_exempt` | Freeport |
| `ch_exempt` | Charitable Exemption |

> **Tip:** The `APPRAISAL_ENTITY_INFO.TXT` file carries per-taxing-entity assessed values,
> taxable values, and exemption dollar amounts. Join on `prop_id + prop_val_yr + sup_num + owner_id`.
> Entity codes for College Station taxing units include `CS` (City of College Station),
> `CSISD` (College Station ISD), `BC` (Brazos County), and `TAMU` (Texas A&M University System,
> which has its own levy authority on some accounts). Filter by `entity_cd` to isolate
> College Station city-jurisdiction values.

---

## College Station Filter Strategy

### Attribute filter (fast, good enough for most work)
```python
# After loading the shapefile into a GeoDataFrame:
gdf_cs = gdf[gdf["SITUS_CITY"].str.upper() == "COLLEGE STATION"]

# Or in the appraisal export flat file:
df_cs = df[df["situs_city"].str.upper() == "COLLEGE STATION"]
```

### Strict municipal-boundary filter
For work that must respect College Station's legal city limits (excluding ETJ parcels that
may carry `situs_city = 'COLLEGE STATION'`), use the city limits layer from College Station's
own open data portal:

```text
OPEN DATA PORTAL:   https://data-cstx.opendata.arcgis.com/
CITY LIMITS ITEM:   https://data-cstx.opendata.arcgis.com/maps/college-station-city-limits
GIS SERVER ROOT:    https://gis.cstx.gov/csgis/rest/services/
```

Workflow: download the city limits polygon from the open data portal, then do a spatial
intersect/clip of your parcel GeoDataFrame.

> **ETJ note:** College Station's extraterritorial jurisdiction (ETJ) extends up to 5 miles
> beyond city limits (per Texas LGC §42) and also borders Bryan's ETJ. Some parcels in the
> ETJ may show `situs_city = 'COLLEGE STATION'` in PACS but fall outside the legal city
> boundary. Use the spatial clip for strict boundary work.

---

## Zoning Layer — City of College Station

College Station publishes a maintained open-data zoning layer with REST query support:

```text
OPEN DATA PORTAL:   https://data-cstx.opendata.arcgis.com/datasets/zoning
CSTX GIS SERVER:    https://gis.cstx.gov/csgis/rest/services/
```

Recommended notebook workflow:
- Download the zoning polygons from the open data portal and cache to
  `examples/data/college_station/cs_zoning_<date>.parquet`.
- Spatially join parcels (centroid-within polygon) to stamp `ZONING_DISTRICT` onto each parcel.
- The zoning map is updated as rezonings are processed; see Articles 4 and 5 of College Station's
  Unified Development Ordinance (UDO) for district definitions.

College Station UDO zoning district families (not exhaustive):
| Family | Examples | Notes |
|---|---|---|
| Single-family residential | `R`, `RS`, `GS` | Ranging from rural to general suburban |
| Multi-family residential | `D`, `T`, `MF` | Duplex through high-density MF |
| Mixed-use | `MH`, `MU` | Mixed-use districts near TAMU corridor |
| Commercial | `SC`, `GC`, `CI`, `BP` | Suburban, General, Industrial, Business Park |
| Industrial | `BPI`, `M-1`, `M-2` | Light through heavy industrial |
| Agricultural | `A-O` | Agricultural-open with limited residential |
| Planned Development | `PDD`, `P-MUD` | Planned districts (require PD review for use) |

> **College Station note:** A substantial share of CS parcels zoned or used as student
> housing (MF, PDD, T) concentrate around the Texas A&M campus. Flag these separately
> if conducting rental-market or student-housing analyses.

---

## Texas A&M University — Special Considerations

Texas A&M University and its affiliated agencies own a very large fraction of land within
College Station city limits. These parcels typically:
- Have `ex_exempt = 'T'` (total exemption — state institution)
- Have `assessed_val = 0` and `market_value` set to CAD's estimated value
- May have owner names matching patterns like `TEXAS A&M`, `TAMU`, `TEXAS A & M`, or
  component agency names (`TEXAS ENGINEERING EXPERIMENT STATION`, `TEXAS FOREST SERVICE`, etc.)
- Show up in the zoning layer under university-specific districts or as A-O/PDD

Filter them out for taxable-property-only analyses:
```python
df_taxable = df_cs[df_cs["ex_exempt"] != "T"]
```

---

## Property Search / Spot-Check Portal

```text
BRAZOS CAD PROPERTY SEARCH:  https://esearch.brazoscad.org/
BRAZOS CAD INTERACTIVE MAP:  https://gis.bisclient.com/brazoscad/
BRAZOS COUNTY TAX OFFICE:    https://brazostax.org/
CSTX PLANNING & DEV MAP:     https://www.cstx.gov/business-development/maps-and-gis/
```

Use `geo_id` or `prop_id` to look up individual accounts. The property search shows current
certified values, exemptions, and entity levy information not present in the shapefile.
The CSTX Planning & Development Map is the best tool for confirming current zoning, platting,
and subdivision status for a specific College Station address.

---

## Data Loading Pattern (Python)

```python
import geopandas as gpd
import pandas as pd

# --- Step 1: Download & load parcel shapefile ---
SHP_URL = "https://brazoscad.org/wp-content/uploads/2024/03/PUBLIC_PARCEL_BOUNDARY.zip"
# Download zip, extract, read with GeoPandas
# (File names inside the zip vary by release; inspect with zipfile.ZipFile)

gdf = gpd.read_file("PUBLIC_PARCEL_BOUNDARY.shp")

# --- Step 2: Filter to College Station ---
gdf_cs = gdf[gdf["SITUS_CITY"].str.upper() == "COLLEGE STATION"].copy()

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
    "ex_exempt":       (2670, 2671),   # total exemption — flags TAMU/state land
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
df_cs = df_prop[df_prop["situs_city"].str.upper() == "COLLEGE STATION"]

# Filter to taxable parcels only (exclude TAMU/state/total-exempt)
df_cs_taxable = df_cs[df_cs["ex_exempt"] != "T"]

# --- Step 4: Join geometry to appraisal data ---
merged = gdf_cs.merge(df_cs, left_on="GEO_ID", right_on="geo_id", how="left")
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
CITY_FILTER_VALUE    = "COLLEGE STATION"
JOIN_KEY             = "geo_id"              # shapefile field name may vary (check caps)
PRIMARY_KEY          = "prop_id"

CS_OPEN_DATA_PORTAL   = "https://data-cstx.opendata.arcgis.com/"
CS_ZONING_DATASET     = "https://data-cstx.opendata.arcgis.com/datasets/zoning"
CS_GIS_SERVER         = "https://gis.cstx.gov/csgis/rest/services/"
CS_PLANNING_MAP       = "https://www.cstx.gov/business-development/maps-and-gis/"
COUNTY_TAX_OFFICE     = "https://brazostax.org/"

# Texas-specific state property type codes (from PACS STATE_CD.TXT / Comptroller table)
# Common codes for College Station analysis:
# A1 = Single-family residence
# A2 = Single-family residence (mobile home)
# B1 = Multi-family (apartments, > 4 units)
# B2 = Multi-family (duplex)
# C1 = Vacant lot
# D1 = Qualified open space / ag land
# F1 = Commercial real property
# F2 = Industrial real property
# X  = Totally exempt (TAMU, churches, nonprofits, government)

# College Station-specific entity codes (in APPRAISAL_ENTITY_INFO.TXT)
# CS     = City of College Station
# CSISD  = College Station Independent School District
# BC     = Brazos County
# (TAMU has levy authority on some accounts — verify entity_cd in your data)

# Derived / computed fields useful in analysis
# TotalMarketValue       = market_value (from APPRAISAL_INFO)
# TotalAssessedValue     = assessed_val (appraised_val minus ten_percent_cap)
# AssessedToMarket       = assessed_val / market_value (when market_value > 0)
# ImprovementRatio       = (imprv_hstd_val + imprv_non_hstd_val) / market_value
# IsTAMU                 = ex_exempt == 'T' AND owner matches TAMU pattern
# IsStudentHousing       = ZONING_DISTRICT in MF/T/PDD families + imprv_state_cd == 'B1'
# ZONING_DISTRICT        = stamped from CS zoning polygons (centroid within)
# ANALYSIS_CATEGORY      = refined from prop_type_cd + imprv_state_cd + zoning + ex_exempt
```

---

## Known Limitations

| Issue | Detail |
|---|---|
| No live REST endpoint | Brazos CAD distributes data as shapefile + flat-file downloads only; there is no public ArcGIS FeatureServer for parcel queries. |
| Geometry and appraisal are separate files | The shapefile carries geometry and `GEO_ID`; all valuation fields require downloading and parsing the PACS fixed-width export. |
| Fixed-width format | The export uses byte-offset fixed-width fields, not CSV. Use the official layout PDF for field positions. |
| Countywide shapefile | Includes all Brazos County parcels; filter to College Station by `situs_city = 'COLLEGE STATION'` or by spatial clip against the city limits layer. |
| Situs-city vs. legal-boundary mismatch | `situs_city` is a text attribute, not a spatial filter. College Station's ETJ is large; use the CS city limits polygon for strict boundary work. |
| TAMU land dominance | Texas A&M owns a large share of CS parcels. These are total-exempt (`ex_exempt = 'T'`), assessed at zero, and skew valuation statistics if not excluded intentionally. |
| No per-row edit timestamps | The public shapefile does not expose row-level last-edited timestamps. |
| Certified vs. monthly | The monthly shapefile has the most current geometry but may not be certified for tax purposes; the certified ZIP (released ~August each year) is the official annual snapshot. |
| PACS multi-owner properties | `APPRAISAL_INFO.TXT` can contain multiple rows per `prop_id` if a property has multiple owners (UDI group). Deduplicate or aggregate as needed. |
| No billed tax in open data | Tax levy and bill amounts are not in the shapefile or certified export; use `https://brazostax.org/` for levy details. |
| Zoning data currency | The College Station open-data zoning layer is updated as rezonings are processed. For legally definitive zoning, confirm via the CSTX planning portal or Planning & Development Services at 979-764-3570. |
