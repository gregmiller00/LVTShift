# Pueblo County Parcel Endpoint — Notebook Reference Spec

## Endpoint

```
BASE:    https://services1.arcgis.com/IL17xsvNU5Bmw3RY/arcgis/rest/services/County_Parcels/FeatureServer/0
QUERY:   /query
FORMAT:  f=json  (or f=geojson if you want geometry inline)
```

---

## Fields to Pull

### Identity
| Field | Alias | Type | Notes |
|---|---|---|---|
| `PAR_TXT` | Parcel ID — Text | String(10) | **Primary join key.** Full-text indexed. Use this to join to other layers. |
| `PAR_NUM` | Parcel ID — Number | Double | Numeric version of parcel ID |
| `Fips` | FIPS Code | Integer | County FIPS |

### Ownership
| Field | Alias | Type | Notes |
|---|---|---|---|
| `Owner` | Owner Name | String(60) | Primary owner name |
| `OwnerOverflow` | Owner Overflow | String(1024) | Long-form owner name if truncated |
| `SubOwner1` | Sub Owner 1 | String(60) | |
| `SubOwner2` | Sub Owner 2 | String(60) | |
| `OwnerStreetAddress` | Owner Street Address | String(70) | Mailing address |
| `OwnerCity` | Owner City | String(48) | |
| `OwnerState` | Owner State | String(4) | |
| `OwnerZip` | Owner Zip Code | String(26) | |
| `OwnerCountry` | Owner Country | String(48) | |

### Valuation ✅ (100% populated, no nulls)
| Field | Alias | Type | County Total | Avg/Parcel | Max |
|---|---|---|---|---|---|
| `LandAssessedValue` | Land Assessed Valuation | Integer | $358,864,400 | $3,552 | $2,262,672 |
| `LandActualValue` | Land Estimated Actual Value | Integer | $3,908,966,435 | $38,687 | $55,984,396 |
| `ImprovementsAssessedValue` | Improvements Assessed Valuation | Integer | $1,533,311,434 | $15,175 | $76,232,383 |
| `ImprovementsActualValue` | Improvements Actual Value | Integer | $19,326,093,474 | $191,272 | $282,342,161 |

> **Derived field to compute:** `TotalAssessedValue = LandAssessedValue + ImprovementsAssessedValue`  
> **Derived field to compute:** `TotalActualValue = LandActualValue + ImprovementsActualValue`

### Tax Roll / Exemptions
| Field | Alias | Type | Notes |
|---|---|---|---|
| `TaxDistrict` | Tax District | String(76) | Use this to look up mill levy rate |
| `TaxExempt` | Tax Exempt | String(6) | Flag — filter these out for taxable-only analysis |
| `SeniorExemption` | Senior Exemption | String(6) | Senior homestead exemption flag |
| `Neighborhood` | Assessor's Neighborhood | String(76) | Assessor neighborhood code |

### ❌ Do NOT pull — empty fields
| Field | Reason |
|---|---|
| `Tax` | All zeros — not populated in this layer |

### Property Info
| Field | Alias | Type | Notes |
|---|---|---|---|
| `Zoning` | Zoning | String(72) | |
| `LegalDescription` | Legal Description | String(1024) | |
| `Subdivision` | Subdivision | String(76) | |
| `MobileHomePresent` | Mobile Home Present | String(6) | |

### Reference URLs (per-parcel links)
| Field | Alias | Notes |
|---|---|---|
| `AssessorURL` | Assessor Property Card URL | Direct link to assessor card — use for spot-checking actual billed tax |
| `LevyURL` | Mill Levy Distribution PDF URL | Per-district mill levy — use to derive estimated tax |
| `ZoningURL` | Zoning Code URL | |

### Utilities
| Field | Notes |
|---|---|
| `electric` | Electric provider |
| `gas` | Gas provider |
| `water` | Water provider |
| `telecom` | Telecom provider |
| `Fire` | Fire department jurisdiction |
| `CSEPP` | Within CSEPP Protective Action Zone |

### Editor Tracking (for incremental updates)
| Field | Notes |
|---|---|
| `created_date` | UTC timestamp — use for first-load filtering |
| `last_edited_date` | UTC timestamp — **use this for incremental refresh** |

---

## Pagination Strategy

The service returns **2,000 records per page** with a total of **101,040 parcels**.  
You will need **51 pages** minimum.

```python
TOTAL     = 101_040
PAGE_SIZE = 2_000
PAGES     = math.ceil(TOTAL / PAGE_SIZE)  # 51

# Per-page query
params = {
    "where": "1=1",
    "outFields": "PAR_TXT,PAR_NUM,Fips,Owner,OwnerOverflow,SubOwner1,SubOwner2,"
                 "OwnerStreetAddress,OwnerCity,OwnerState,OwnerZip,OwnerCountry,"
                 "TaxDistrict,TaxExempt,SeniorExemption,Neighborhood,Subdivision,"
                 "Zoning,LegalDescription,MobileHomePresent,"
                 "LandAssessedValue,LandActualValue,"
                 "ImprovementsAssessedValue,ImprovementsActualValue,"
                 "AssessorURL,LevyURL,ZoningURL,"
                 "electric,gas,water,telecom,Fire,CSEPP,"
                 "created_date,last_edited_date",
    "resultOffset": 0,          # increment by 2000 each page
    "resultRecordCount": 2000,
    "returnGeometry": True,     # set False if attributes-only
    "outSR": 4326,              # WGS84 — already native to this layer
    "f": "json"
}
```

### Incremental refresh query
```python
# Only pull parcels edited since your last run
params["where"] = "last_edited_date > DATE '2026-01-29'"
```

---

## Key Facts to Hard-Code

```python
ENDPOINT     = "https://services1.arcgis.com/IL17xsvNU5Bmw3RY/arcgis/rest/services/County_Parcels/FeatureServer/0/query"
LAYER_ID     = 0
TOTAL_PARCS  = 101_040
PAGE_SIZE    = 2_000
CRS          = 4326          # WGS84, no reprojection needed
SNAPSHOT_DT  = "2026-01-29"  # dataLastEditDate from service metadata
JOIN_KEY     = "PAR_TXT"     # join to any other Pueblo County layer on this field

# Derived fields to compute post-fetch
# TotalAssessedValue  = LandAssessedValue + ImprovementsAssessedValue
# TotalActualValue    = LandActualValue   + ImprovementsActualValue
# EstimatedTax        = TotalAssessedValue * (mill_levy / 1000)
#   -- mill_levy varies by TaxDistrict; look up from LevyURL per district
```

---

## Known Limitations

| Issue | Detail |
|---|---|
| `Tax` field empty | Billed tax not stored here. Derive from assessed value × mill levy, or scrape `AssessorURL` per parcel. |
| 2,000 record page limit | Must paginate — 51 pages for full county pull |
| Static snapshot | Layer is a manual export (Jan 29, 2026), not a live feed. No webhook/sync support. Plan for periodic full or incremental refresh using `last_edited_date`. |
| `NoDisplay` flag | Some owners have requested their info not be shown online. Filter with `WHERE NoDisplay IS NULL OR NoDisplay = 'false'` if needed. |
