# LVTShift

**LVTShift** is a research toolkit for modeling Land Value Tax (LVT) policy shifts in U.S. cities. Built by the [Center for Land Economics](https://landeconomics.org), it quantifies how shifting from a traditional property tax to a land value tax affects neighborhoods, property types, and demographic groups — and produces publication-ready charts from any city's data.

---

## What is a Land Value Tax?

A Land Value Tax taxes only the value of land, not the buildings on it. This changes the incentive structure of property ownership:

- **Vacant and underutilized land** becomes more expensive to hold → encourages development
- **Dense housing and improvements** are untaxed or lightly taxed → rewards efficient land use
- **Revenue stays the same** → pure shift in *who* pays, not *how much* government collects
- **Land supply is fixed** → unlike building taxes, LVT cannot be passed through to tenants via reduced supply

---

## Architecture

```
lvt/
  lvt_utils.py       Core tax modeling (split-rate, building abatement, exemptions)
  viz.py             Standard charts and city report generation

cloud_utils.py       Fetch parcel data from county ArcGIS FeatureServers
census_utils.py      Fetch ACS demographics and spatial-join to parcels
policy_analysis.py   Vacant land, parking lot, and development barrier analysis

cities/              One notebook per city
  st_paul/
  spokane/
  southbend/
  baltimore/
  pittsburgh/
  rochester/
  ... (13 cities total)

analysis/
  data/              Standard exported CSVs (one per city)
  reports/           PNG charts (one folder per city)
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
Exempt a percentage of improvement value from taxation, with a floor exemption.

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

Both solvers maintain **exact revenue neutrality** and support percentage caps, iterative rate-solving, and per-levy modeling (Spokane runs 8 separate levies independently).

---

## Standard Export & Reports

Every city notebook ends with two calls:

```python
# 1. Write a 16-column standardized CSV
out_df = save_standard_export(df, city='st_paul', output_path='../../analysis/data/st_paul.csv', ...)

# 2. Generate PNG charts into analysis/reports/<city>/
create_city_report(out_df, 'st_paul', show=True)
```

`create_city_report` produces up to 7 charts:

| File | Description |
|---|---|
| `category_impact.png` | Horizontal bar: median % tax change by property category |
| `ten_pct_share.png` | Diverging bar: % of parcels with >10% decrease vs >10% increase |
| `income_quintile_non_vacant.png` | Green-gradient bar: median % change by neighborhood income quintile (all non-vacant) |
| `income_quintile_residential.png` | Same, residential parcels only |
| `minority_quintile_non_vacant.png` | Median % change by neighborhood minority share quintile (all non-vacant) |
| `minority_quintile_residential.png` | Same, residential parcels only |
| `distribution.png` | Histogram of parcel-level tax change % |

Census charts are generated when block-group income and minority data are available. The residential filter defaults to Single Family Residential + Small/Large Multi-Family + Other Residential, and can be overridden per city:

```python
create_city_report(out_df, 'spokane',
    census_categories=['Single Family Residential', 'Small Multi-Family (2-4 units)'])
```

---

## Cities Modeled

| City | State | Model | Key Notes |
|---|---|---|---|
| St. Paul | MN | Split-rate 4:1 (Tax Capacity) | HF 1342; full city tax bill; condo collapse |
| Spokane | WA | Building abatement 75% | 8 levies modeled independently |
| South Bend | IN | Split-rate 4:1 | St. Joseph County ArcGIS |
| Baltimore | MD | Split-rate | Already has a split-rate; models deeper shift |
| Pittsburgh | PA | Split-rate (city only) | WPRDC + Allegheny County GIS |
| Rochester | NY | Split-rate | Homestead/non-homestead split rates |
| Bellingham | WA | Split-rate | Whatcom County |
| Cincinnati | OH | Split-rate | Hamilton County |
| Fort Collins | CO | Split-rate | Larimer County |
| Morgantown | WV | Split-rate | Monongalia County |
| Scranton | PA | Split-rate | Lackawanna County |
| Seattle | WA | Split-rate | King County |
| Syracuse | NY | Split-rate | Onondaga County |

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

The recommended Python environment is 3.11+ with `geopandas`, `pandas`, `matplotlib`, `census`, and `jupyter`.

### Run a city

```bash
cd cities/st_paul
jupyter notebook model.ipynb
```

Each notebook auto-detects locally cached data and skips re-scraping if a recent file exists. Set `scrape_data = True` to force a fresh pull.

### Adding a new city

See `LVT_MODELING_GUIDE.md` for a step-by-step questionnaire covering data sources, column mapping, exemption handling, millage derivation, and standard export wiring.

---

## Key Design Decisions

**Revenue neutrality** — All models maintain identical total revenue. Rate calculation uses `(target_revenue × 1000) / denominator`. An iterative solver (up to 40 iterations) handles percentage caps.

**Flexible column names** — Every function accepts column names as parameters. No hardcoded field names, so the same code works across counties with different schemas.

**Millage rates are per $1,000** — `tax = value × millage / 1000`.

**Centroid-based spatial joins** — Parcels are joined to Census block groups via centroids in EPSG:3857 to avoid boundary edge cases.

**Census fallback chain** — TIGERweb single request → chunked by tract → FTP shapefile download. API calls run in a background thread with a 90-second timeout.

**Condo collapse (St. Paul / Ramsey County)** — Condo units receive token $1,000 land assessments. Before modeling, units are collapsed by PlatID into buildings with imputed land values from neighborhood median improvement ratios.

---

## Output Examples

### Property Category Impact — St. Paul (4:1 split-rate)

Vacant land sees 150%+ tax increases. Small multi-family sees 14% decreases. Single-family sees ~10% decreases.

### Equity Analysis — St. Paul

- Lowest-income neighborhoods (Q1–Q4): 14–16% tax decreases
- Highest-income neighborhoods (Q5): +13% increase
- Highest-minority neighborhoods (Q4–Q5): 19–20% decreases

This reflects the core LVT equity story: low-income neighborhoods tend to have high improvement-to-land ratios (dense housing on modest land), while wealthy neighborhoods often hold high-value land with lower improvement density.

---

## License

MIT License — Copyright (c) 2025 Greg Miller

---

*The Center for Land Economics is a nonprofit research organization dedicated to evidence-based land and housing policy. [landeconomics.org](https://landeconomics.org)*
