# Skill: Fetch Parcel Data

## Goal
Download and cache parcel data for a new city. At the end of this skill, you have a GeoDataFrame (or regular DataFrame) saved locally that contains every parcel in the city with assessed land value, improvement value, and enough identifying fields to compute taxes.

---

## Step 1 — Find the data source

Property assessment data for U.S. cities comes from the county assessor, not the city. Start there.

**Questions to answer before writing any code:**

- What county is the city in?
- Does the county publish an ArcGIS REST service (FeatureServer or MapServer)? Search: `"<County> county assessor arcgis rest services"`
- Is the data a full county-wide layer, or city-filtered? Most counties publish county-wide data; you'll filter to the city after downloading.
- If no ArcGIS service exists, is there a downloadable CSV, Shapefile, or GeoJSON? (Check the county's open data portal, or state-level repositories like WPRDC for PA counties.)
- Does a separate geometry layer exist? (Some jurisdictions publish attribute data and geometry in separate endpoints.)

**Known patterns by state:**
- **Minnesota counties**: Use county ArcGIS services; geometry sometimes requires separate geometry layer join.
- **Pennsylvania counties**: Use WPRDC or county-specific ArcGIS; state plane CRS (EPSG:2271) common.
- **Cook County (IL)**: Large dataset — use chunked fetching.
- **California counties**: Often downloadable CSV/shapefile from county assessor.
- **Washington state**: County GIS portals typically have ArcGIS FeatureServer.

---

## Step 2 — Inspect the service before coding

Before writing data-fetch code, inspect the service manually.

**For ArcGIS endpoints:**
1. Browse to the service URL and add `/layers` to see available layers.
2. Click a layer → look at Fields to identify: parcel ID, land value, improvement value, total value, owner name, property use code, exemption fields.
3. Note the `maxRecordCount` — this determines pagination chunk size (usually 1,000 or 2,000).
4. Check `supportsPagination` in the layer capabilities.
5. Check the spatial reference — note the WKID for CRS handling.

**Questions to answer:**
- What is the parcel ID field name?
- What are the land value, improvement value, and total value field names?
- Is there a "use code" or "property class" field? What are its values?
- Is there an exemption amount field? An exemption flag field?
- Is there a city/municipality filter field? What values identify your city?

---

## Step 3 — Choose the right fetch function

From `cloud_utils.py`:

| Situation | Function |
|---|---|
| ArcGIS FeatureServer, geometry included | `get_feature_data_with_geometry()` |
| ArcGIS FeatureServer, attributes only | `get_feature_data()` |
| ArcGIS MapServer | `get_mapserver_data_with_geometry()` |
| Pennsylvania state plane CRS | `get_mapserver_data_with_geometry_pa()` |
| Large download prone to failures | `get_mapserver_data_with_resume()` |
| Need to explore available cities in a county layer | `explore_cities_in_dataset()` |

**Parameters to configure:**
- `dataset_name`: local cache file prefix (e.g., `"chicago_parcels"`)
- `base_url`: the ArcGIS service URL root
- `layer_id`: integer layer number
- `where_clause`: SQL filter, e.g., `"CITY = 'CHICAGO'"` or `"MUNICODE BETWEEN 101 AND 132"`
- `out_fields`: comma-separated field list, or `"*"` for all
- `paginate`: True for most datasets

---

## Step 4 — Handle the data directory

Each city stores its data at `examples/<city>/data/`. This path is relative to the notebook location.

Standard cache pattern in notebooks:
```
data_scrape = 0  # Set to 1 to fetch fresh data, 0 to load from cache
```

When `data_scrape = 1`, fetch and save with a datestamped filename (e.g., `chicago_parcels_2026_04_15.parquet`). When `data_scrape = 0`, glob for the most recent file and load it.

---

## Step 5 — Filter to city boundary

If the data is county-wide:
- Find the city/municipality field name and its value(s) for your city.
- Filter: `df = df[df['CITY'] == 'CHICAGO']`
- Check the count before and after — understand how many parcels to expect from the official assessor report.

---

## Step 6 — Validate data completeness

After fetching, confirm:
- Parcel count is in the right order of magnitude (compare to county assessor summary report).
- Land value, improvement value, and total value fields are non-null for most rows.
- The value distribution makes sense (look at percentiles).
- The city filter captured the right area (use `.describe()` and spot-check a few addresses).

**Verification criteria for this skill:**
- [ ] Data is saved to `examples/<city>/data/` as `.parquet` or `.gpq`
- [ ] Parcel count within 5% of official assessor count
- [ ] Land value and improvement value columns are non-null for >90% of taxable parcels
- [ ] `data_scrape = 0` loads from cache successfully
