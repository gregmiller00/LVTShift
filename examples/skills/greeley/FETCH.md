# Greeley Parcel Endpoint — Notebook Reference Spec

## Endpoint

```text
BASE:    https://services.arcgis.com/ewjSqmSyHJnkfBLL/ArcGIS/rest/services/Parcels_open_data/FeatureServer/0
QUERY:   /query
FORMAT:  f=json  (or f=geojson if you want geometry inline)
```

## Zoning Layer (City of Greeley)

```text
PORTAL ITEM: https://open-data-greeley.hub.arcgis.com/maps/9074f41dfaa346bba43115abb4e2ac9a/about
ITEM ID:     9074f41dfaa346bba43115abb4e2ac9a
DIRECT LAYER: https://gis.greeleygov.com/arcgis_svr/rest/services/Data_services/Zoning/MapServer/2
QUERY URL:    https://gis.greeleygov.com/arcgis_svr/rest/services/Data_services/Zoning/MapServer/2/query
```

Preferred approach is direct query against the Greeley service URL above. If blocked, fall back to ArcGIS item metadata (`/sharing/rest/content/items/<item_id>/data?f=json`) to resolve operational layer URL, then query with `f=geojson`.

Recommended notebook workflow:
- Download zoning polygons and cache to `examples/data/greeley/greeley_zoning_<date>.parquet`
- Spatially stamp each parcel (centroid-within polygon) with `ZONING_CLASS`
- Build a refined analysis category from both assessor type (`ACCTTYPE`) and zoning class
- Use refined categories for final classification-driven charts/summaries

> **Scope note:** Weld County publishes parcel data countywide. To make this **Greeley-specific**, filter the parcel layer with `LOCCITY = 'GREELEY'` for a fast city-name filter, or use the Weld County city-limits layer (`City_Limits_open_data`, layer 3) with `TOWNNAME = 'GREELEY'` and do a spatial clip/intersects filter for strict municipal-boundary results.

---

## Fields to Pull

### Identity
| Field | Alias | Type | Notes |
|---|---|---|---|
| `PARCEL` | PARCEL | String(18) | **Primary parcel identifier.** Best parcel join key in the open-data layer. |
| `ACCOUNTNO` | ACCOUNTNO | String(30) | Assessor account number. Useful for linking to assessor/property-report tools. |
| `ACCOUNTTYP` | ACCOUNTTYP | String(1) | Account class code used by Weld County tools. |
| `ACCTTYPE` | ACCTTYPE | String(15) | Human-readable account type / category. |
| `MHSPACE` | MHSPACE | String(10) | Manufactured-home space identifier where applicable. |

### Ownership / Mailing
| Field | Alias | Type | Notes |
|---|---|---|---|
| `NAME` | NAME | String(60) | Primary owner / account name. |
| `BUSINESSNA` | BUSINESSNA | String(100) | Business name, if present. |
| `ADDRESS1` | ADDRESS1 | String(50) | Mailing address line 1. |
| `ADDRESS2` | ADDRESS2 | String(50) | Mailing address line 2. |
| `CITY` | CITY | String(40) | **Mailing** city, not necessarily situs city. |
| `STATE` | STATE | String(2) | Mailing state. |
| `ZIPCODE` | ZIPCODE | String(10) | Mailing ZIP. |

### Situs / Location
| Field | Alias | Type | Notes |
|---|---|---|---|
| `SITUS` | SITUS | String(75) | Full property situs string. |
| `LOCCITY` | LOCCITY | String(40) | **Best simple filter for Greeley parcels** in the parcel layer. |
| `STREETNO` | STREETNO | String(15) | Situs street number. |
| `STREETDIR` | STREETDIR | String(2) | Situs street direction. |
| `STREETNAME` | STREETNAME | String(50) | Situs street name. |
| `STREETSUF` | STREETSUF | String(4) | Situs street suffix. |
| `STREETALP` | STREETALP | String(6) | Situs unit / alpha suffix. |
| `AddressPre` | AddressPre | String(4) | Address prefix where present. |
| `latitude` | Latitude | Double | Parcel centroid latitude. |
| `longitude` | Longitude | Double | Parcel centroid longitude. |
| `GIS_Acres` | GIS_Acres | Double | GIS-computed acreage. |

### Valuation
| Field | Alias | Type | Notes |
|---|---|---|---|
| `LANDACT` | LANDACT | Double | Land actual value. |
| `IMPACT` | IMPACT | Double | Improvement actual value. |
| `TOTALACT` | TOTALACT | Double | Total actual value. Already provided. |
| `LANDASD` | LANDASD | Double | Land assessed value. |
| `IMPASD` | IMPASD | Double | Improvement assessed value. |
| `TOTALASD` | TOTALASD | Double | Total assessed value. Already provided. |
| `LGLANDASD` | LGLANDASD | Double | Local-government land assessed value. |
| `LGIMPASD` | LGIMPASD | Double | Local-government improvement assessed value. |
| `TOTALLGASD` | TOTALLGASD | Double | Total local-government assessed value. |
| `SCLANDASD` | SCLANDASD | Double | School land assessed value. |
| `SCIMPASD` | SCIMPASD | Double | School improvement assessed value. |
| `TOTALSCASD` | TOTALSCASD | Double | Total school assessed value. |

> **Good default:** pull both the classic assessed/actual fields (`LANDACT`, `IMPACT`, `TOTALACT`, `LANDASD`, `IMPASD`, `TOTALASD`) and the 2026 local-government / school assessed splits.

### Legal / Plat / Map Reference
| Field | Alias | Type | Notes |
|---|---|---|---|
| `LEGAL` | LEGAL | String(254) | Legal description. |
| `AREAID` | AREAID | String(10) | Assessor area code. |
| `MAPNO` | MAPNO | String(40) | Map number. |
| `SUBCODE` | SUBCODE | Double | Subdivision code. |
| `SUBNAME` | SUBNAME | String(100) | Subdivision name. |
| `BLOCK` | BLOCK | String(20) | Block. |
| `LOT` | LOT | String(20) | Lot. |
| `SUB_BLK_LT` | SUB_BLK_LT | String(125) | Combined subdivision / block / lot string. |
| `TOWNSHIP` | TOWNSHIP | String(15) | PLSS township. |
| `RANGE` | RANGE | String(15) | PLSS range. |
| `SECTION` | SECTION | String(15) | PLSS section. |
| `QTRSECTION` | QTRSECTION | String(4) | Quarter section. |
| `STR` | STR | String(10) | Township-range-section shorthand. |
| `PARC3` | PARC3 | String(3) | Short parcel fragment. |
| `SBR_NUM` | SBR_NUM | String(10) | Survey / reception-related reference field. |
| `RECEPTION_` | RECEPTION_ | String(10) | Reception number reference field. |

### Sale / Classification
| Field | Alias | Type | Notes |
|---|---|---|---|
| `SALEP` | SALEP | Double | Sale price. |
| `SALEDT` | SALEDT | Date | Sale date. |
| `DEEDTYPE` | DEEDTYPE | String(50) | Deed type. |
| `ASSRCODE` | ASSRCODE | String(4) | Assessor classification code. |
| `BORDERINGC` | BORDERINGC | String(50) | Bordering city / place field when present. |

### Geometry / Shape
| Field | Alias | Type | Notes |
|---|---|---|---|
| `Shape__Area` | Shape__Area | Double | Polygon area in service units. |
| `Shape__Length` | Shape__Length | Double | Polygon perimeter in service units. |

### Usually safe to skip
| Field | Reason |
|---|---|
| `OBJECTID` | Internal feature-layer object id only. |
| `Shape_Leng` | Legacy duplicate-ish length field; prefer `Shape__Length`. |
| `STR2` | Auxiliary STR field with unclear incremental value for most workflows. |

---

## Greeley Filter Strategy

### Fast attribute filter
```python
params["where"] = "LOCCITY = 'GREELEY'"
```

Use this first. It is simple, transparent, and uses a parcel-layer field that reflects the property location city.

### Strict municipal-boundary filter
When you need parcels strictly **inside the City of Greeley boundary**, first query:

```text
https://services.arcgis.com/ewjSqmSyHJnkfBLL/ArcGIS/rest/services/City_Limits_open_data/FeatureServer/3/query
where=TOWNNAME='GREELEY'
```

Then use that polygon as an `esriSpatialRelIntersects` geometry filter against the parcel layer.

This avoids edge cases where a mailing city, unincorporated address convention, or nearby place name could leak into a simple attribute-only filter.

---

## Pagination Strategy

The parcel service advertises a **2,000 record max page size**. Public Weld GIS Hub metadata shows **162,539 records** in the countywide parcel dataset. For **Greeley-only** pulls, do **not** hard-code the record count; first call `returnCountOnly=true` with your city filter, then paginate from there.

```python
PAGE_SIZE = 2_000

# First get Greeley count
count_params = {
    "where": "LOCCITY = 'GREELEY'",
    "returnCountOnly": True,
    "f": "json",
}

# Then page through results
params = {
    "where": "LOCCITY = 'GREELEY'",
    "outFields": (
        "PARCEL,ACCOUNTNO,ACCOUNTTYP,ACCTTYPE,MHSPACE,"
        "NAME,BUSINESSNA,ADDRESS1,ADDRESS2,CITY,STATE,ZIPCODE,"
        "SITUS,LOCCITY,STREETNO,STREETDIR,STREETNAME,STREETSUF,STREETALP,AddressPre,"
        "LEGAL,AREAID,MAPNO,SUBCODE,SUBNAME,BLOCK,LOT,SUB_BLK_LT,"
        "TOWNSHIP,RANGE,SECTION,QTRSECTION,STR,PARC3,SBR_NUM,RECEPTION_,"
        "LANDACT,IMPACT,TOTALACT,LANDASD,IMPASD,TOTALASD,"
        "LGLANDASD,LGIMPASD,TOTALLGASD,SCLANDASD,SCIMPASD,TOTALSCASD,"
        "SALEP,SALEDT,DEEDTYPE,ASSRCODE,BORDERINGC,"
        "latitude,longitude,GIS_Acres,Shape__Area,Shape__Length"
    ),
    "resultOffset": 0,          # increment by 2000 each page
    "resultRecordCount": 2000,
    "returnGeometry": True,     # set False if attributes-only
    "outSR": 4326,              # request WGS84 output
    "f": "json"
}
```

---

## Assessor / Tax / Property-Report Reference

Weld County also publishes a Property Portal and parcel-level Property Report pages that can be used for spot checks, valuations, levy/tax tabs, and ownership verification.

```text
PROPERTY PORTAL: https://apps.weld.gov/propertyportal/index.cfm
PROPERTY REPORT: https://propertyreport.weld.gov/?account=<ACCOUNTNO>&defaultsection=valuation
```

Use `ACCOUNTNO` as your handoff key into those tools.

---

## Key Facts to Hard-Code

```python
ENDPOINT        = "https://services.arcgis.com/ewjSqmSyHJnkfBLL/ArcGIS/rest/services/Parcels_open_data/FeatureServer/0/query"
LAYER_ID        = 0
PAGE_SIZE       = 2_000
SERVICE_SRID    = 3857          # service native spatial reference
OUTPUT_SRID     = 4326          # request WGS84 in your query
COUNTY_TOTAL    = 162_539       # countywide dataset metadata, not Greeley-only
JOIN_KEY        = "PARCEL"
ACCOUNT_KEY     = "ACCOUNTNO"
CITY_FILTER     = "LOCCITY = 'GREELEY'"
CITY_LIMITS_URL = "https://services.arcgis.com/ewjSqmSyHJnkfBLL/ArcGIS/rest/services/City_Limits_open_data/FeatureServer/3/query"
CITY_NAME_FIELD = "TOWNNAME"
CITY_NAME_VALUE = "GREELEY"
SNAPSHOT_DT     = "2026-04-08" # parcel layer data last edit date from service metadata
ZONING_ITEM_ID  = "9074f41dfaa346bba43115abb4e2ac9a"

# Optional derived fields
# ImprovementActualValue = IMPACT
# ImprovementAssessedValue = IMPASD
# PricePerAcre = SALEP / GIS_Acres            (when both present and GIS_Acres > 0)
# AssessedToActualRatio = TOTALASD / TOTALACT (when TOTALACT > 0)
# ZONING_CLASS = stamped from city zoning polygons (centroid within)
# ANALYSIS_CATEGORY = refined classification built from assessor + zoning
```

---

## Known Limitations

| Issue | Detail |
|---|---|
| Countywide base layer | The parcel endpoint is for all of Weld County, so you must explicitly filter to Greeley. |
| No parcel-level tax bill field in open layer | Use the Property Portal / Property Report for levy and tax details rather than expecting billed tax in the polygon layer. |
| 2,000 record page limit | Must paginate. |
| Greeley count not published as a fixed metadata stat | Compute it with `returnCountOnly=true` using your chosen Greeley filter at runtime. |
| Attribute-city vs legal-boundary mismatch | `LOCCITY='GREELEY'` is convenient but not identical to a municipal-boundary clip; use the city-limits layer for strict boundary work. |
| No exposed per-row editor tracking fields in the public parcel schema | You have service-level last-edit metadata, but not parcel-row `last_edited_date` fields like some other counties expose. |
| Schema changes do occur | Weld’s hub notes a schema update on 2026-03-25 adding local-government and school assessed-value splits, so keep field lists version-aware. |
