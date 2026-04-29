# Highlands Ranch Parcel Endpoint — Notebook Reference Spec

## Context: Why This Is Different From Greeley

Highlands Ranch is **not an incorporated municipality**. It is a census-designated place (CDP)
entirely within unincorporated Douglas County. There is no city government and no dedicated
municipal parcel layer. All parcel data flows through Douglas County, which means:

- There is no `LOCCITY = 'HIGHLANDS RANCH'` equivalent that cleanly isolates it (unlike
  Greeley's `LOCCITY = 'GREELEY'` in the Weld County layer).
- The correct filter strategy uses **`City_Name`** from the assessor's Property Location
  flat file, or a **spatial clip** against the Highlands Ranch CDP or Metro District boundary.
- The ZIP code envelope (80126, 80129, 80130, 80163) is a useful rough filter but bleeds
  into adjacent unincorporated areas outside HR proper.

---

## Open Data Portal

```text
PORTAL:       https://dcdata-dougco.opendata.arcgis.com/
ALT HUB:      https://gis-dougco.opendata.arcgis.com/
GIS MAPS PAGE: https://www.douglas.co.us/information-technology/gis-maps-apps/
```

Douglas County runs two parallel open-data surfaces — the newer DougCo Hub (`dcdata-`) and
an older ArcGIS Hub (`gis-dougco`). Both point to the same underlying services.

---

## Parcel Geometry Endpoint

```text
SERVICE:  Parcels/Parcel (MapServer)
HOST:     https://apps.douglas.co.us/geopendata/rest/services/Parcels/Parcel/MapServer
LAYER 0:  Parcels (polygon, geometry)
LAYER 1:  Account Ownership Table (non-spatial join table)
QUERY:    /0/query
FORMAT:   f=json  (or f=geojson)
MAX REC:  1,000 per page (advertised MaxRecordCount)
SRID:     102100 / 3857 (service native); request outSR=4326 for WGS84
```

> **Stability note:** The `apps.douglas.co.us/geopendata` hostname has shown intermittent
> 502 errors. If unavailable, fall back to the `Map_WFL1` hosted feature service on
> ArcGIS Online (see Zoning Layer section below) which also contains a parcel layer,
> or pull the flat-file downloads directly from the assessor site.

### Parcel Layer Fields (Layer 0)

| Field | Alias | Type | Notes |
|---|---|---|---|
| `PARCEL_SPN` | Parcel SPN | String(15) | **Primary parcel identifier.** State Parcel Number — best join key. Equivalent to `State_Parcel_No` in flat files. |
| `DEEDED_AREA` | Deeded Area (Acres) | Double | Recorded deed acreage. |
| `CALC_AREA` | Calculated Area (Acres) | Double | GIS-computed acreage. Prefer over `DEEDED_AREA` for spatial analysis. |
| `LEGAL_DESCR` | Legal Description | String(255) | Legal description (truncated in GIS layer; full text in flat file). |
| `PARCEL_NAME` | Parcel Name | String(64) | Human-readable parcel label where present. |
| `BLOCK_NO` | Block Number | String(64) | Subdivision block number. |
| `Shape__Area` | Shape Area | Double | Polygon area in service units (sq meters in SRID 3857). |
| `Shape__Length` | Shape Length | Double | Polygon perimeter in service units. |
| `OBJECTID` | OBJECTID | OID | Internal feature-layer object ID. Use for pagination via `objectIds`; do not treat as a stable key. |

> The geometry layer is intentionally lean — owner, address, valuation, and sale fields
> live in the assessor flat files (see below), joined on `PARCEL_SPN` ↔ `State_Parcel_No`.

---

## Assessor Flat File Downloads

These are the authoritative tabular records. Updated on the **first Sunday of each month**.

```text
BASE URL: https://apps.douglas.co.us/realware/datadownloads/
PORTAL:   https://www.douglas.co.us/assessor/data-downloads/
LAST UPDATED: 4/1/2026   NEXT UPDATE: 5/4/2026
```

All files are pipe-delimited `.txt`. Fields marked **bold** below are primary or foreign keys.

### Property Location (`Property_Location.txt`)
Primary attribute file. Contains the **Highlands Ranch filter field** (`City_Name`).

| Field | Notes |
|---|---|
| **`Account_No`** | Assessor account number. Primary join key across all flat files. |
| `Account_Type_Code` | Single-character property class code (see Classification section). |
| **`State_Parcel_No`** | Links to `PARCEL_SPN` in the geometry layer. |
| `Address_No` | Situs street number. |
| `Pre_Directional_Code` | Situs street direction prefix. |
| `Street_Name` | Situs street name. |
| `Street_Type_Code` | Situs street suffix (RD, DR, CT, etc.). |
| `Unit_No` | Unit number for condos/townhomes. |
| `Location_Zip_Code` | Situs ZIP code. Useful rough filter; HR ZIPs are 80126, 80129, 80130, 80163. |
| **`City_Name`** | **Best simple filter for Highlands Ranch parcels.** See Filter Strategy. |
| `Legal_Descr` | Full legal description text (longer than GIS truncation). |
| `Section` | PLSS section. |
| `Township` | PLSS township. |
| `Range` | PLSS range. |
| `Quarter` | Quarter section. |
| `Land_Economic_Area_Code` | Assessor land economic area (neighborhood-level). |
| `Vacant_Flag` | `Y` / `N` — whether the parcel is considered vacant land. |
| `Total_Net_Acres` | Net acreage from assessor records. |
| `Tax_District_No` | Tax district number — unique combination of taxing authorities for this parcel. |
| `Neighborhood_Code` | Assessor neighborhood code (used for mass appraisal groupings). |
| `Neighborhood_Extension` | Extension suffix for neighborhood code. |

### Property Ownership (`Property_Ownership.txt`)

| Field | Notes |
|---|---|
| **`Account_No`** | Join key. |
| `Owner_Name` | Primary owner name. |
| `Mailing_Address_Line_1` | Owner mailing address line 1. |
| `Mailing_Address_Line_2` | Owner mailing address line 2. |
| `Mailing_City_Name` | Owner mailing city (not situs city). |
| `Mailing_State` | Owner mailing state. |
| `Mailing_Zip_Code` | Owner mailing ZIP. |

### Property Subdivision (`Property_Subdivision.txt`)

| Field | Notes |
|---|---|
| **`Account_No`** | Join key. |
| **`Sub_Filing_Recording_No`** | Subdivision filing recording number. Join key into subdivision layer. |
| `Subdivision_Name` | Full subdivision name (e.g., `HIGHLANDS RANCH`, `HIGHLANDS RANCH FILING 122`). Useful secondary HR filter and for sub-neighborhood analysis. |
| `Lot_No` | Lot number. |
| `Block_No` | Block number. |
| `Tract_No` | Tract number where applicable. |

### Property Value (`Property_Value.txt`)

| Field | Notes |
|---|---|
| **`Account_No`** | Join key. |
| `Actual_Value` | Total actual (market) value. Equivalent to Weld County's `TOTALACT`. |
| `Assessed_Value` | Total assessed value. Equivalent to Weld County's `TOTALASD`. |
| `Valuation_Class_Code` | Numeric class code describing property use (also called Building Use, Land Use, or Abstract Code). See Classification section. |
| `Valuation_Description` | Human-readable label for `Valuation_Class_Code`. |
| `Exempt_Flag` | Exemption flag (also carries `Account_Subtype_Code` in some exports). |
| `Valuation_Type_Code` | Single-letter segment type: `I` = improvement, `L` = land. |
| `Account_Type_Code` | Repeated here from Location file; property class code. |

### Property Sales (`Property_Sales.txt`)

| Field | Notes |
|---|---|
| **`Account_No`** | Join key. |
| `Sale_Price` | Recorded sale price. |
| `Sale_Date` | Sale date. |
| `Deed_Type` | Deed type code. |
| `Reception_No` | Reception number from County Clerk & Recorder. |

### Property Improvements (`Property_Improvements.txt`)
Building-level detail. One account may have multiple improvement rows.

| Field | Notes |
|---|---|
| **`Account_No`** | Join key. |
| `Built_SF` | Above-grade finished square footage. |
| `Built_As_Code` | Structure style/type (ranch, two-story, fast-food, etc.). |
| `Year_Built` | Year of construction. |
| `HVAC` | Heating/cooling type. |
| `Fireplace_Count` | Number of fireplaces. |
| `Basement_SF` | Total basement square footage. |
| `Finished_Basement_SF` | Finished portion of basement. |
| `Completion_Pct` | Percent complete (for under-construction properties). |
| `Valuation_Class_Code` | Class code for this improvement segment. |

---

## Zoning Layer (Douglas County)

```text
PORTAL ITEM: https://gis-dougco.opendata.arcgis.com/
FEATURE SERVER: https://services5.arcgis.com/JlofwxJO3RD8jjJH/arcgis/rest/services/Map_WFL1/FeatureServer
ZONING LAYER:   .../FeatureServer/13
QUERY URL:      https://services5.arcgis.com/JlofwxJO3RD8jjJH/arcgis/rest/services/Map_WFL1/FeatureServer/13/query
DISPLAY FIELD:  ZONE_TYPE
MAX RECORD COUNT: 2,000
SRID:           102100 (3857)
```

### Zoning Layer Fields

| Field | Type | Notes |
|---|---|---|
| `ZONE_TYPE` | String(4) | **Primary classification field.** Code value; see unique values below. |
| `ZONE_DATE` | Date | Date zone designation was applied. |
| `FIRST_DESC` | String(32) | Full zone description label. |
| `last_edited_date` | Date | Row-level last edit timestamp — exposed in this layer (unlike the parcel polygon layer). |
| `Shape__Area` | Double | Polygon area. |
| `Shape__Length` | Double | Polygon perimeter. |

### `ZONE_TYPE` Unique Values (complete, from service renderer)

| Code | Label |
|---|---|
| `A1` | Agricultural One |
| `B` | Business |
| `C` | Commercial |
| `CMTY` | Sedalia Community |
| `CTY` | CTY (county designation) |
| `D` | Sedalia Downtown |
| `ER` | Estate Residential |
| `GI` | General Industrial |
| `HC` | Sedalia Highway Commercial |
| `LI` | Light Industrial |
| `LRR` | Large Rural Residential |
| `LSB` | Limited Service Business |
| `MF` | Multifamily |
| `MI` | Sedalia Mixed Industrial |
| `NF` | National Forest |
| `OS` | Open Space Conservation |
| `PD` | Planned Development |
| `RR` | Rural Residential |
| `SR` | Suburban Residential |

> **Highlands Ranch context:** The vast majority of HR parcels fall under `PD` (Planned
> Development) — the county zoning designation for master-planned communities. `SR`
> (Suburban Residential) and `OS` (Open Space Conservation) also appear within the
> HR boundary. Industrial and agricultural codes are essentially absent from HR proper.
> Sedalia-specific codes (`CMTY`, `D`, `HC`, `MI`) will not appear in HR results.

Recommended notebook workflow:
- Download zoning polygons and cache to `examples/data/douglas/douglas_zoning_<date>.parquet`
- Spatially stamp each parcel (centroid-within polygon) with `ZONE_TYPE`
- Build a refined analysis category from both `Account_Type_Code` / `Valuation_Class_Code`
  and `ZONE_TYPE`

---

## Classification Fields

Douglas County uses a **two-tier** classification system. Use both for maximum resolution.

### Tier 1: `Account_Type_Code` (Property Location & Value files)
Single-character code indicating the broad property class:

| Code | Meaning |
|---|---|
| `R` | Residential |
| `C` | Commercial |
| `I` | Industrial |
| `A` | Agricultural |
| `V` | Vacant Land |
| `M` | Mobile Home / Manufactured Housing |
| `X` | Exempt (religious, charitable, governmental) |
| `P` | Business Personal Property |

> Note: Douglas County Assessor documentation describes the major parcel categories as
> residential improved, commercial improved (includes industrial), vacant land, mobile homes,
> agricultural improved, and business personal property. The codes above reflect those
> groupings. Verify exact single-character values against a live data pull — the county
> uses "Account_Type_Code" as the field name consistently across all flat files.

### Tier 2: `Valuation_Class_Code` (Property Value file)
Numeric code (also called Building Use, Land Use, or Abstract Code) describing the
**specific use** of each valuation segment. This is the finer-grained field for
distinguishing, e.g., single-family from condo from retail from office. Douglas County
publishes the full code list in the Assessor Data Dictionary:

```text
https://www.douglas.co.us/assessor/assessor-data-dictionary
```

Common Highlands Ranch-relevant codes include single-family residential, condominium,
townhouse, apartment/multifamily, office, retail, and open space. Pull the distinct
values from a live data extract for a current enumeration.

### `Vacant_Flag` (Property Location file)
`Y` or `N`. A direct, simple boolean for vacant vs. improved parcel analysis.

---

## Highlands Ranch Filter Strategy

### Critical context
Highlands Ranch has **no incorporated city boundary** and no `LOCCITY`-style field
that cleanly isolates it. The county's parcel data covers all of Douglas County
(~170,000+ parcels). Multiple strategies are available; use the one matching your
tolerance for edge cases.

### Strategy 1 — Attribute filter on `City_Name` (fast, recommended first pass)
```python
# In Property_Location.txt flat file
df = df[df["City_Name"].str.upper() == "HIGHLANDS RANCH"]
```
This is the direct equivalent of Greeley's `LOCCITY = 'GREELEY'`. In the GIS parcel
layer itself, there is no single equivalent field in the geometry schema — join to the
flat file first, then filter, then spatially join back to geometry via `State_Parcel_No`.

### Strategy 2 — ZIP code pre-filter (faster, less precise)
```python
HR_ZIPS = {"80126", "80129", "80130", "80163"}
df = df[df["Location_Zip_Code"].isin(HR_ZIPS)]
```
Useful as a first-pass narrowing step before a spatial clip. Some parcels in adjacent
unincorporated areas share these ZIPs.

### Strategy 3 — Spatial clip against CDP/Metro District boundary (strict)
When you need parcels strictly inside the Highlands Ranch CDP or Metro District footprint:

```python
# Highlands Ranch Metro District boundary — query from Douglas County open data
# Or use the US Census TIGER CDP boundary for "Highlands Ranch CDP"
# Then do a centroid-within or intersects spatial filter against the parcel layer
```

The Census TIGER 2020 CDP boundary for Highlands Ranch is the most standardized option.
The Highlands Ranch Metro District boundary (available via DougCo Hub) is slightly
different — it is the governing authority boundary and is the preferred choice for
property-tax-district-level analysis.

### Strategy 4 — `Subdivision_Name` contains filter (sub-neighborhood work)
```python
df = df[df["Subdivision_Name"].str.contains("HIGHLANDS RANCH", na=False)]
```
Captures the dozens of "HIGHLANDS RANCH FILING N" subdivision names. Misses parcels
platted under community/park/commercial names that don't carry the HR prefix. Best
used in combination with Strategy 1.

**Recommended workflow:** Strategy 1 (`City_Name`) for the fast attribute filter;
fall back to Strategy 3 (spatial clip) for strict boundary work.

---

## Pagination Strategy

The parcel geometry service advertises **1,000 records per page** (lower than Weld
County's 2,000). The Douglas County assessor flat files are **full-county downloads**
with no built-in pagination — you download the whole file and filter locally.

```python
PAGE_SIZE = 1_000   # geometry layer
HR_ZIPS   = {"80126", "80129", "80130", "80163"}

# For the geometry MapServer layer — first get count within HR ZIP envelope:
count_params = {
    "where": "1=1",      # refine with spatial or other filter
    "returnCountOnly": True,
    "f": "json",
}

# Then paginate:
params = {
    "where": "1=1",
    "outFields": "PARCEL_SPN,DEEDED_AREA,CALC_AREA,LEGAL_DESCR,PARCEL_NAME,BLOCK_NO,Shape__Area,Shape__Length",
    "resultOffset": 0,          # increment by 1,000 each page
    "resultRecordCount": 1_000,
    "returnGeometry": True,
    "outSR": 4326,
    "f": "json",
}

# Recommended: Download flat files directly (no pagination needed), filter to HR,
# then join geometry on PARCEL_SPN == State_Parcel_No.
```

**Preferred pattern for Highlands Ranch analysis:**
1. Download `Property_Location.txt` → filter to `City_Name == 'HIGHLANDS RANCH'`
2. Extract the `State_Parcel_No` list
3. Paginate the geometry layer with `where=PARCEL_SPN IN ('...','...',...)` in chunks
4. Join valuation, ownership, sales flat files on `Account_No`

---

## Assessor / Property Search Reference

```text
ASSESSOR PORTAL:   https://apps.douglas.co.us/assessor/web/
ADVANCED SEARCH:   https://apps.douglas.co.us/assessor/advanced-search/
DATA DOWNLOADS:    https://www.douglas.co.us/assessor/data-downloads/
DATA DICTIONARY:   https://www.douglas.co.us/assessor/assessor-data-dictionary
TAX CALCULATOR:    https://dougco.maps.arcgis.com/apps/webappviewer/index.html?id=2cf071f44a724c45b7f8a1c189c931b3
```

Use `Account_No` as the handoff key into the assessor portal for spot-checking individual
parcels, reviewing levy/tax tabs, and appeal status.

---

## Key Facts to Hard-Code

```python
# Geometry layer
PARCEL_ENDPOINT   = "https://apps.douglas.co.us/geopendata/rest/services/Parcels/Parcel/MapServer/0/query"
FALLBACK_FS       = "https://services5.arcgis.com/JlofwxJO3RD8jjJH/arcgis/rest/services/Map_WFL1/FeatureServer"
PAGE_SIZE         = 1_000
SERVICE_SRID      = 3857
OUTPUT_SRID       = 4326
JOIN_KEY_GIS      = "PARCEL_SPN"      # geometry layer field
JOIN_KEY_FLAT     = "State_Parcel_No" # flat file equivalent of PARCEL_SPN
ACCOUNT_KEY       = "Account_No"      # primary key across all assessor flat files

# Flat file downloads
FLAT_FILE_BASE    = "https://apps.douglas.co.us/realware/datadownloads/"
LOCATION_FILE     = FLAT_FILE_BASE + "Property_Location.txt"
OWNERSHIP_FILE    = FLAT_FILE_BASE + "Property_Ownership.txt"
SUBDIVISION_FILE  = FLAT_FILE_BASE + "Property_Subdivision.txt"
VALUE_FILE        = FLAT_FILE_BASE + "Property_Value.txt"
SALES_FILE        = FLAT_FILE_BASE + "Property_Sales.txt"
IMPROVEMENTS_FILE = FLAT_FILE_BASE + "Property_Improvements.txt"
FLAT_FILE_UPDATED = "2026-04-01"   # last updated; next update 2026-05-04

# Highlands Ranch filter
HR_CITY_FILTER    = "City_Name == 'HIGHLANDS RANCH'"   # flat file filter
HR_ZIPS           = {"80126", "80129", "80130", "80163"}
HR_UNINC          = True   # reminder: no incorporated city; this is unincorporated Douglas County

# Zoning layer
ZONING_FS_URL     = "https://services5.arcgis.com/JlofwxJO3RD8jjJH/arcgis/rest/services/Map_WFL1/FeatureServer/13/query"
ZONING_TYPE_FIELD = "ZONE_TYPE"
DOMINANT_HR_ZONES = ["PD", "SR", "OS"]   # zones predominantly found within HR boundary

# Optional derived fields
# CalcPricePerAcre     = Sale_Price / CALC_AREA          (when CALC_AREA > 0)
# AssessedToActualRatio = Assessed_Value / Actual_Value  (when Actual_Value > 0)
# ZONE_TYPE            = stamped from county zoning polygons (centroid within)
# ANALYSIS_CATEGORY    = refined classification built from Account_Type_Code + ZONE_TYPE
# IsVacant             = Vacant_Flag == 'Y'
```

---

## Known Limitations

| Issue | Detail |
|---|---|
| No incorporated city | Highlands Ranch has no city government. `City_Name` filter reflects mailing/situs convention, not a legal boundary. Use a spatial clip for strict boundary analysis. |
| Countywide geometry layer | The parcel geometry endpoint covers all of Douglas County (~170,000+ parcels). No geometry-layer field cleanly pre-filters to HR — you must join from flat files or use a spatial filter. |
| Geometry layer field sparsity | The GIS polygon layer has very few attribute fields (SPN, acreage, legal desc, block). All ownership, valuation, and address data must come from flat file joins. |
| Flat files are full-county, uncompressed | `Property_Location.txt` and others cover all Douglas County accounts. Filter locally after download. File sizes are significant. |
| 1,000 record geometry page limit | Lower than Weld County's 2,000. Must paginate more frequently when querying geometry. |
| `apps.douglas.co.us` service instability | The GeoOpenData MapServer host has shown intermittent 502 errors. Build retry logic; fall back to the ArcGIS Online `Map_WFL1` FeatureServer or flat-file-only workflow. |
| HR ZIP bleed | ZIPs 80126/80129/80130/80163 include some non-HR unincorporated parcels at the edges. ZIP filter alone is not sufficient for precise boundary work. |
| No parcel-row edit timestamps in geometry layer | The geometry layer does not expose `last_edited_date` per row (unlike the zoning layer, which does). You have service-level metadata only. |
| Subdivision name fragmentation | HR is composed of 100+ named filings (e.g., `HIGHLANDS RANCH FILING 47 AMENDMENT 1`). `Subdivision_Name` is useful for sub-area analysis but requires wildcard matching. |
| Flat file update cadence | Files are refreshed once per month (first Sunday). Intra-month sales, value changes, and ownership transfers will not appear until the next release. |
| No billed tax field in open data | Use the Tax Calculator / Assessor portal for levy and net tax due. `Assessed_Value` in the flat file is pre-levy. |
