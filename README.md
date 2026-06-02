# LVTShift

**LVTShift** is a research toolkit for modeling Land Value Tax (LVT) policy shifts in U.S. cities. Built by the [Center for Land Economics](https://landeconomics.org), it quantifies how shifting from a traditional property tax to a land value tax affects neighborhoods, property types, and demographic groups — and produces publication-ready charts from any city's data.

This repository is designed to be operated by AI agents. Adding a new city is a single natural-language command.

---

## What is a Land Value Tax?

A Land Value Tax taxes only the value of land, not the buildings on it. This changes the incentive structure of property ownership:

- **Vacant and underutilized land** becomes more expensive to hold → encourages development
- **Dense housing and improvements** are untaxed or lightly taxed → rewards efficient land use
- **Revenue stays the same** → pure shift in *who* pays, not *how much* government collects
- **Land supply is fixed** → unlike building taxes, LVT cannot be passed through to tenants via reduced supply

---

## Adding a City (Agent Workflow)

Say to your agent:

> **"Add [city] to LVTShift"** or **"Model LVT for [city]"**

The agent reads `.claude/skills/model-city/SKILL.md` (or you can invoke `/lvt-city`) and runs the full pipeline:

1. Asks five policy questions (levy scope, reform type, exemptions, county/state, official revenue figure)
2. Finds the county ArcGIS endpoint and downloads parcel data
3. Models the current tax system — handling assessment ratios, millage sources, and exemptions correctly for that jurisdiction
4. Implements the split-rate or building abatement scenario
5. Joins Census block-group demographics (income, race)
6. Exports a standardized 16-column CSV and generates 7 publication-ready PNGs
7. Re-runs the cross-city comparison analysis
8. Commits the result

The five upfront questions matter because they cannot be changed midway:

```
1. Which government body? (city only / full stack / specific levies)
2. Which reform? (split-rate N:1 / building abatement X% / both)
3. Keep existing exemptions? (yes / no — what changes?)
4. County and state? (for Census FIPS code)
5. Official revenue figure to validate against?
```

If any answer is unclear, the agent defaults to: city levy only, 4:1 split-rate, preserve all existing exemptions.

### Skills Reference

Skills live in `.claude/skills/`. Each is a reference card the agent reads during its assigned step.

**Modeling pipeline skills:**

| Skill | Step | What it covers |
|---|---|---|
| `model-city/SKILL.md` | Master | Policy questions, 7-step pipeline, canonical closing pattern (also `/lvt-city`) |
| `discover-data.md` | Step 1 | Finding ArcGIS endpoints, pagination, city filtering, column mapping |
| `model-policy.md` | Step 2 | Assessment ratios, millage derivation, exemptions, all 6 real modeling patterns |
| `build-notebook.md` | Step 3 | 7-section notebook template, kernelspec, census+export closing cells |
| `validate.md` | Step 5 | Revenue gate, distribution sanity, census coverage, PNG output |

**Policy analysis skills** (run after the model, each produces a local-only `.md` output in `analysis/`):

| Skill | Command | What it produces |
|---|---|---|
| `legality-analyzer/SKILL.md` | `/legality-analyzer [city]` | Citation-heavy legal brief: 8 legal vehicles scored, pathway tier (1–8), primary sources; saved to `analysis/legal/<city>.md` |
| `explain-model/SKILL.md` | `/explain-model [city]` | Plain-language methodology explainer: data sources, levies modeled, exemptions, limitations; saved to `analysis/explainers/<city>.md` |
| `political-viability/SKILL.md` | `/political-viability [city]` | Political brief: current officials scored, electoral math from model CSV, coalition map, viability tier; saved to `analysis/political/<city>.md` |

Recommended order: model the city → run `/legality-analyzer` (which officials hold the key votes depends on the legal pathway) → run `/political-viability` (uses legal brief to scope the right actors).

For a thorough walkthrough of the modeling decisions — assessment ratios, per-levy abatements, Tax Capacity, derived millage, dual homestead rates — read **[docs/LVT_MODELING_GUIDE.md](docs/LVT_MODELING_GUIDE.md)**.

---

## Architecture

```
lvt/
  lvt_utils.py       Core tax modeling (split-rate, building abatement, exemptions)
  viz.py             Standard charts and city report generation
  cloud_utils.py     Fetch parcel data from county ArcGIS FeatureServers
  census_utils.py    Fetch ACS demographics and spatial-join to parcels
  policy_analysis.py Vacant land, parking lot, and development barrier analysis

cities/              One notebook per city
  st_paul/
  spokane/
  southbend/
  baltimore/
  ...

analysis/
  data/                  Standard exported CSVs (one per city)
  reports/               PNG charts (one folder per city)
  figures/cross_city/    Cross-city summary figures (4 PNGs + CSV table)
  cross_city.ipynb       Cross-city equity comparison (interactive)
  cross_city_figures.py  Script to regenerate cross-city figures
  legal/                 LVT legal briefs per city (gitignored — local only)
  explainers/            Model methodology explainers per city (gitignored — local only)
  political/             Political viability briefs per city (gitignored — local only)

scripts/
  run_all_cities.py      Batch notebook runner (patches scrape flags, reports pass/fail)
  patch_notebooks.py     Idempotent patches for ratio harmonization and bug fixes

docs/
  LVT_MODELING_GUIDE.md   Full modeling reference

.claude/skills/      Agent skill files (read by Claude during pipeline execution)
```

**Data flow:**

```
Fetch parcels (cloud_utils)
  → Classify property types → Calculate current tax
  → Model LVT scenario (lvt_utils) → Merge Census demographics (census_utils)
  → save_standard_export() → create_city_report()
```

---

## Modeling Approaches

Two primary LVT scenarios are implemented, both revenue-neutral:

### Split-Rate Tax
Tax land and improvements at different millage rates. A 4:1 ratio means land is taxed at four times the rate of buildings.

```python
from lvt.lvt_utils import model_split_rate_tax

land_mill, imp_mill, revenue, df = model_split_rate_tax(
    df=parcels,
    land_value_col='EMVLand1',
    improvement_value_col='EMVBuilding1',
    current_revenue=current_revenue,
    land_improvement_ratio=4.0,
)
```

### Building Abatement / Stacking Exemption
Exempt a percentage of improvement value from taxation, with a floor exemption. Used in Spokane, modeled per-levy.

```python
from lvt.lvt_utils import model_stacking_improvement_exemption

df = model_stacking_improvement_exemption(
    df=parcels,
    land_col='land_value',
    improvement_col='improvement_value',
    current_revenue=target_revenue,
    improvement_exemption_pct=0.75,
    building_abatement_floor=100_000,
)
```

Both solvers maintain **exact revenue neutrality** and support percentage caps, iterative rate-solving, and per-levy modeling.

### Jurisdiction-Specific Patterns

Cities require different treatment of the tax base before modeling. Examples:

| Pattern | Cities | Notes |
|---|---|---|
| Full market value | South Bend, Baltimore | Millage × market value / 1000 |
| Assessment ratio | Cincinnati | Ohio taxes at 35% of market value |
| Tax Capacity | St. Paul | Minnesota class-rate schedule pre-computes taxable capacity |
| Derived millage | Baltimore | Back-calculated from observed tax bills in parcel file |
| Dual millage | Rochester | Separate homestead and non-homestead rates |
| Per-levy abatement | Spokane | 8 levies modeled independently |

See `model-policy.md` or `docs/LVT_MODELING_GUIDE.md` for code examples of each.

---

## Standard Export & Reports

Every city notebook ends with:

```python
# 1. Write a 16-column standardized CSV
out_df = save_standard_export(df, city='st_paul', output_path='../../analysis/data/st_paul.csv', ...)

# 2. Generate PNG charts into analysis/reports/<city>/
create_city_report(out_df, 'st_paul', show=False)
```

`create_city_report` produces up to 7 charts:

| File | Description |
|---|---|
| `category_impact.png` | Horizontal bar: median % tax change by property category |
| `ten_pct_share.png` | Diverging bar: % of parcels with >10% decrease vs >10% increase |
| `distribution.png` | Histogram of parcel-level tax change % |
| `income_quintile_non_vacant.png` | Median % change by neighborhood income quintile (all non-vacant) |
| `income_quintile_residential.png` | Same, residential parcels only |
| `minority_quintile_non_vacant.png` | Median % change by neighborhood minority share quintile |
| `minority_quintile_residential.png` | Same, residential parcels only |

Census charts are generated when block-group income and minority data are available (≥ 70% Census join rate).

---

## Cities Modeled

All runnable cities use a harmonized **4:1 split-rate** scenario (land taxed at 4× the improvement rate, revenue-neutral).

| City | State | Parcels | Status | Key Notes |
|---|---|---|---|---|
| Baltimore | MD | 238K | ✓ CSV | Derived millage from tax bills |
| Bellingham | WA | 41K | ✓ CSV | Whatcom County ArcGIS |
| Bryan | TX | 30K | ✓ CSV | Brazos County |
| Charlottesville | VA | 15K | ✓ CSV | Independent city (no county) |
| Cleveland | OH | 158K | ✓ CSV | 35% Ohio assessment ratio |
| College Station | TX | 28K | ✓ CSV | Brazos County |
| Fort Collins | CO | 71K | ✓ CSV | Larimer County; per-tax-area modeling |
| Greeley | CO | 33K | ✓ CSV | Weld County |
| Highlands Ranch | CO | 16K | ✓ CSV | Douglas County |
| Oak Forest | IL | 10.7K | ✓ CSV | Cook County PTAXSIM + CCAO AV; city levy only; data from sibling project |
| Philadelphia | PA | 580K | ✓ CSV (4 variants) | OPA via Carto; city+school levy; 2024 vintage |
| Pueblo | CO | 47K | ✓ CSV | Pueblo County |
| Rochester | NY | 58K | ✓ CSV | Homestead/non-homestead dual millage |
| South Bend | IN | 44K | ✓ CSV | St. Joseph County |
| St. Paul | MN | 72K | ✓ CSV | Full tax bill; Tax Capacity; condo collapse by PlatID |
| Syracuse | NY | 42K | ✓ CSV | Onondaga County |
| Cincinnati | OH | — | ✗ Blocked | CAGIS ArcGIS source gone; no current endpoint with land values |
| Spokane | WA | — | ✗ Blocked | Needs `charge_info_1/2.xlsx` manually downloaded from Spokane County |
| Denver | CO | — | ✗ Stub | Depends on manually-assembled data files not in repo |
| Morgantown | WV | — | ✗ Stub | Modeling section incomplete |
| Scranton | PA | — | ✗ Stub | Data fetch only; no modeling |

---

## Getting Started

### Environment

```bash
git clone https://github.com/gregmiller00/LVTShift.git
cd LVTShift
pip install -r requirements.txt

cp env.template .env
# Add your Census API key (free at api.census.gov/data/key_signup.html)
```

The recommended Python environment is 3.11+ with `geopandas`, `pandas`, `matplotlib`, `census`, and `jupyter`. The Jupyter kernel is `python3` (miniconda default on Windows).

### Run all cities (batch)

```bash
python scripts/run_all_cities.py                   # all 16 runnable cities
python scripts/run_all_cities.py st_paul cleveland  # specific cities
```

The runner auto-detects missing data caches and patches `data_scrape = 0 → 1` when needed, so it always fetches fresh data on first run then uses the cache on subsequent runs.

### Run a city manually

```bash
cd cities/st_paul
jupyter nbconvert --to notebook --execute \
  --output _executed.ipynb \
  --ExecutePreprocessor.timeout=600 \
  --ExecutePreprocessor.kernel_name=python3 \
  model.ipynb
```

Each notebook auto-detects locally cached data and skips re-scraping if a recent file exists.

### Cross-city analysis

After CSVs exist in `analysis/data/`:

```bash
cd analysis
python cross_city_figures.py   # saves 4 figures + summary table to figures/cross_city/
jupyter nbconvert --to notebook --execute cross_city.ipynb  # full interactive analysis
```

---

## Key Design Decisions

**Revenue neutrality** — All models maintain identical total revenue. Rate calculation uses `(target_revenue × 1000) / denominator`. An iterative solver (up to 40 iterations) handles percentage caps.

**Flexible column names** — Every function accepts column names as parameters. No hardcoded field names, so the same code works across counties with different schemas.

**Millage rates are per $1,000** — `tax = value × millage / 1000`.

**Centroid-based spatial joins** — Parcels are joined to Census block groups via centroids in EPSG:3857 to avoid boundary edge cases.

**Census fallback chain** — TIGERweb single request → chunked by tract → FTP shapefile download. API calls run in a background thread with a 90-second timeout.

**Condo collapse (St. Paul / Ramsey County)** — Condo units receive token $1,000 land assessments. Before modeling, units are collapsed by PlatID into buildings with imputed land values from neighborhood median improvement ratios.

---

## License

MIT License — Copyright (c) 2025 Greg Miller

---

*The Center for Land Economics is a nonprofit research organization dedicated to evidence-based land and housing policy. [landeconomics.org](https://landeconomics.org)*
