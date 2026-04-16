# LVTShift Notebook Run Report

Generated: 2026-04-15  
Branch: `restructure/standard-export`

---

## Summary

| Status | Count | Cities |
|---|---|---|
| PASS | 2 | charlottesville, southbend |
| FAIL — PATH_ISSUE | 1 | cincinnati |
| FAIL — API_CHANGE | 1 | cleveland |
| FAIL — SCRAPING (data_scrape=1) | 5 | pittsburgh, rochester, chicago, baltimore, scranton |
| SKIP — Incomplete notebook | 2 | morgantown, scranton |
| NOT RUN — See notes | 6 | st_paul, syracuse, denver, fort_collins, bellingham, seattle, spokane |

> Note: Run report reflects Phase 1 run against original notebooks (before city-subfolder migration). After migration, all notebooks should be re-run from `examples/<city>/` with `data_scrape = 0`.

---

## Per-City Status

### ✓ PASS: charlottesville
- **CSV**: `analysis/data/charlottesville.csv` — 15,150 rows
- **Model**: split_rate:4.0
- **Notes**: Runs cleanly. Multiple scenarios (2:1, 4:1, 10:1) are run; export uses 4:1. Variable name fix applied: `cville_4to1` (not `df_input`).
- **Census**: Not confirmed (no CENSUS_API_KEY in nbconvert environment)

### ✓ PASS: southbend
- **CSV**: `analysis/data/southbend.csv` — 44,362 rows
- **Model**: split_rate:4.0 — land_millage=9.315, improvement_millage=2.329
- **Notes**: Non-standard property categories (South Bend uses "Single Family" not "Single Family Residential") — warned but preserved correctly.
- **Census**: Census columns are null (no CENSUS_API_KEY in nbconvert environment). Needs re-run with key set.

---

### ✗ FAIL: cincinnati
- **Failure category**: `PATH_ISSUE`
- **Error**: `ModuleNotFoundError: No module named 'census_utils'`
- **Cell**: First code cell (import cell)
- **Root cause**: Cincinnati uses `REPO_ROOT = Path.cwd()` with a conditional parent-step. When run via `nbconvert` from `examples/`, `cwd` is `examples/` but the path logic fails to resolve correctly to the repo root.
- **Fix**: After migrating to `examples/cincinnati/model.ipynb`, the path setup is updated to use `sys.path.insert(0, '../..')` explicitly. Re-run should succeed.
- **Export cell**: TODO stub — needs manual completion after notebook is verified

### ✗ FAIL: cleveland
- **Failure category**: `API_CHANGE`
- **Error**: `KeyError: 'features'`
- **Cell**: Early cell fetching levy rates from county ArcGIS endpoint
- **Root cause**: The county levy rate API endpoint returns a response without the expected `features` key. This is a live API call that happens even when `data_scrape = 0`. The endpoint may have changed format or requires authentication.
- **Fix**: Find the current URL for Cuyahoga County levy rates, or download and cache the rate table manually. Check if the Cleveland ArcGIS endpoint still returns levy data in the same format.
- **Export cell**: Ready — will work once the levy fetch is fixed

---

### ⚠ SCRAPING (data_scrape=1, not run in this pass): pittsburgh
- **data_scrape**: 1 — fetches from WPRDC + Allegheny County GIS
- **Failure**: Timed out during scraping (~15 min timeout)
- **Action**: Set `data_scrape = 0` after first successful scrape. Data cached in `examples/pittsburgh/data/`.
- **Export cell**: Ready — `full_exmp` flag, standard column names

### ⚠ NOT RUN: rochester
- **data_scrape**: 1 — fetches from Monroe County ArcGIS
- **Action**: Run with `data_scrape = 1` once to populate cache, then set to 0
- **Export cell**: TODO stub — verify final df variable name (may be `homestead_gdf` or `gdf` after Census join) and confirm land_improvement_ratio used

### ⚠ NOT RUN: chicago
- **data_scrape**: 1 — fetches Cook County FeatureServer
- **Data cache**: `chicago_parcels_2025-06-25.parquet` exists — set `data_scrape = 0`
- **Export cell**: TODO stub — requires PROPERTY_CATEGORY mapping from `major_class_description` first
- **Fix**: Add cell before export that creates PROPERTY_CATEGORY from major_class_description using a mapping dict

### ⚠ NOT RUN: baltimore
- **data_scrape**: 0 — cache exists
- **Export cell**: TODO stub — uses scenarios list; fix to use `baltimore_2to1` or canonical scenario
- **Fix**: Determine which scenario (2:1 or 4:1) is the canonical export, access millage from scenarios list

### ⚠ NOT RUN: st_paul
- **data_scrape**: 0 — cache exists
- **Export cell**: Ready — uses `new_tax_tc`, `tax_change_tc`, `st_paul_city` df
- **Notes**: Should work. Re-run to verify.

### ⚠ NOT RUN: syracuse
- **data_scrape**: 0 — cache exists
- **Export cell**: Ready — `gdf` variable, standard columns
- **Notes**: Failed test with `KeyError: 'property_tax'` — verify column mapping in notebook

### ⚠ NOT RUN: denver
- **data_scrape**: 0 — **no data directory!** Must scrape fresh.
- **Export cell**: TODO stub — dual-levy structure; verify combined current_tax/new_tax and averaged millage expressions
- **Action**: Run with `data_scrape = 1` to populate cache

### ⚠ NOT RUN: fort_collins
- **data_scrape**: 0 — cache exists (CSV-based, not parquet)
- **Export cell**: Ready — `df` variable, standard columns
- **Notes**: First solo run failed (event loop issue from parallel runs). Run alone to verify.

### ⚠ NOT RUN: bellingham
- **Export cell**: TODO stub — building abatement model; determine abatement % and millage equivalents
- **Note**: Notebook filename typo: `belligham.ipynb` (two 'g's) but data dir is `bellingham/`. Fixed in migration.

### ⚠ NOT RUN: seattle
- **Export cell**: TODO stub — per-levy structure; determine combined tax columns and effective millage
- **data_scrape**: 1

### ⚠ NOT RUN: spokane
- **Export cell**: TODO stub — per-levy structure
- **data_scrape**: 1 (but cached data exists)

### ✗ SKIP: scranton
- **Reason**: Notebook only has 1 code cell — data fetch only. No tax modeling implemented.
- **Action**: Complete the modeling before adding export cell. See `skills/model-tax.md`.

### ✗ SKIP: morgantown
- **Reason**: Notebook is incomplete / in development.
- **Action**: Complete notebook, then add export cell.

---

## Environment Notes

Notebooks run via:
```bash
/opt/homebrew/Caskroom/miniconda/base/bin/jupyter nbconvert \
  --ExecutePreprocessor.kernel_name=py311 \
  --ExecutePreprocessor.timeout=900
```

**Key issue**: `CENSUS_API_KEY` is not passed to the nbconvert kernel, so Census join fails silently and demographic columns remain null in all CSVs. Re-run with:
```bash
CENSUS_API_KEY=<your_key> jupyter nbconvert ...
```
or set the key in the notebook environment before the Census import cell.

---

## Next Steps (for engineers)

1. **Fix cincinnati** — Re-run `examples/cincinnati/model.ipynb` after migration (path fix applied). Should pass.

2. **Fix cleveland** — Find the current Cuyahoga County levy rate endpoint. Replace the failing API call with cached data or updated URL.

3. **Fix baltimore / chicago** — Complete TODO export cell stubs:
   - Baltimore: choose 4:1 as canonical, extract millage from `scenarios` list
   - Chicago: add `major_class_description` → `PROPERTY_CATEGORY` mapping cell

4. **Run with data_scrape=0** — All cities with cached data: re-run with `data_scrape = 0` to get CSVs. Set `CENSUS_API_KEY` in environment.

5. **Run scraping cities** — Denver (no cache), Pittsburgh, Rochester, Seattle, Spokane: run with `data_scrape = 1` once.

6. **Complete morgantown and scranton** — These need modeling work before export is possible.

7. **After all CSVs exist** — Run `analysis/validate_all.ipynb` to establish baseline in `analysis/expected_metrics.json`.

8. **Cross-city** — Run `analysis/cross_city.ipynb` once ≥ 5 cities have CSVs.
