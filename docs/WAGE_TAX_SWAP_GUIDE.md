# Wage-Tax-for-Land-Tax Swap Guide

This guide documents a different modeling paradigm from the rest of `docs/LVT_MODELING_GUIDE.md`.
Every other reform in this repo changes the *rate* or *base* of the property tax. This one
eliminates a completely different tax instrument — a payroll tax — and replaces its revenue
with a new, separate land value tax. The existing property tax is left untouched throughout.

Worked example: `cities/philadelphia/model_wage_tax_swap.ipynb`, modeling Philadelphia's Wage &
Earnings Tax (3.75% resident / 3.44% non-resident, ~$2.5B/yr, roughly two-thirds of all
city-generated revenue).

## Why this needs a different approach

Every property-tax reform in this repo works at the parcel level: fetch parcel data, model a new
tax per parcel, compare to the current per-parcel tax. A wage tax has no parcel — it's owed by a
person on their wages, and there is no public, FOIA-able parcel-level (or person-level) wage
dataset to build a "current wage tax per parcel" column from.

Instead, this module works at **census tract** granularity for the wage-tax side (the finest
geography with a reliable public *aggregate dollar* proxy — ACS margins of error at block-group
level are too large for aggregate income) and rolls the parcel-level modeled land tax up to the
same tracts for comparison. The "winners and losers" table this produces is tract-level, not
parcel-level or household-level.

## Data sources

**Resident wage tax base — ACS table B19062, not B19061.** `B19062` is "Aggregate Wage or Salary
Income in the Past 12 Months for Households" — the correct base, because it isolates wages from
self-employment income. `B19061` ("Aggregate Earnings") includes both. Philadelphia's
self-employment income is captured by a separate levy, the Net Profits Tax, not the Wage Tax, so
using `B19061` would overstate the wage tax base. `lvt.wage_tax_utils.get_resident_wage_tax_by_tract`
pulls `B19062_001E`/`_001M` via `lvt.census_utils.get_census_tract_data` and multiplies by the
resident rate — this directly proxies resident liability, since residents owe the tax on their
full wages regardless of where they work.

**Tract boundaries — TIGERweb `Tracts_Blocks/MapServer/4`.** This is "Census Tracts" (polygon
geometry, STATE/COUNTY/TRACT fields), the direct sibling of the block-group Layer 1 already used
by `get_census_blockgroups_shapefile()`. Note Layer 8 in the same service (used elsewhere in
`census_utils.py` for block-group chunking) returns tract *numbers* only, not tract polygons —
don't reuse it for boundaries.

**Non-resident/commuter wage tax — Census LODES, used only as a cross-check.** LODES Workplace
Area Characteristics (WAC) data reports job counts by workplace census block, including 3 coarse
earnings tiers. These tiers are too coarse to back-solve dollars from reliably, and most
commuters working in Philadelphia live outside city limits — so their tax liability can't be
attributed to a Philadelphia tract in the first place. `summarize_lodes_workplace_jobs` uses
LODES only for a job-count plausibility check ("does the filtered county total look like a real
county") and as the narrative source for the commuter-transfer finding's job-count magnitude.
LODES data lags roughly 2 years behind the current year.

**Revenue-target derivation.** The non-resident total is instead extrapolated from the published
resident/non-resident revenue split (`RESIDENT_REVENUE_SHARE`, e.g. ~66% resident / ~34%
non-resident per a 2024 Pew brief on Philadelphia's wage tax):

```
implied_nonresident_total = modeled_resident_total * (1 - resident_share) / resident_share
implied_total = modeled_resident_total + implied_nonresident_total
```

`compute_wage_tax_revenue_target` does this and validates the modeled total against a published
figure, printing a warning (not raising) if the gap exceeds a tolerance — wider than the ~1%
tolerance used for parcel-level property-tax cross-checks, because both ACS tract-level margin of
error and the resident/non-resident split itself are approximations.

## The land-only tax solve

`model_land_only_tax` is a thin wrapper around `lvt.lvt_utils.model_split_rate_tax` with an
all-zero improvement-value column. This is mathematically exact, not an approximation: in
`_solve_revenue_neutral_split_millage`, the improvement term's contribution to revenue is
`0 * improvement_millage = 0` regardless of `land_improvement_ratio`, so the solve collapses to

```
land_millage = current_revenue * 1000 / total_land_value
```

for any ratio. Reusing `model_split_rate_tax` gets exemption/cap/`exclude_mask` handling for free
rather than reimplementing the solve.

## Limitations (read before trusting the winners/losers table)

1. **Mixed incidence.** A tract's current wage tax is borne by *all residents* — owners and
   renters alike. Its new land tax is borne only by *landowners* in that tract. "Net change" per
   tract blends two different incidence populations; it is not a household-level guarantee.
2. **The commuter transfer is a first-order finding, not a footnote.** Roughly a third of current
   wage tax revenue is paid by non-resident commuters, who mostly live outside city limits.
   Eliminating the wage tax and replacing it entirely with a land tax shifts that share of the
   burden onto *city landowners* — a real, sizeable transfer, made visible in the
   `incidence_shift.png` chart from `lvt.viz.create_wage_tax_swap_report` rather than left as a
   number buried in a table.
3. **Data-quality caveats.** ACS aggregate-income carries genuine tract-level margin of error
   (`agg_wage_income_moe`). LODES earnings tiers are 3 coarse buckets and the data lags.
4. **Open question, not resolved by this module:** whether the Wage Tax's revenue splits between
   the City General Fund and School District, the way the real estate tax splits
   0.6317%/0.7681%. If it does, decide which figure(s) to validate against before treating the
   revenue-neutrality check as final — check City of Philadelphia budget documents, not just a
   secondary summary.
5. **Policy default, not a given.** The new land tax's default exemption criterion is whatever
   `exemption_flag_col` the caller passes into `model_land_only_tax` — reusing today's
   property-tax full-exemption flag is a reasonable default, but an explicit policy choice.

## Functions

See docstrings in `lvt/wage_tax_utils.py` and the tract-level additions to `lvt/census_utils.py`
(`get_census_tract_data`, `get_census_tracts_shapefile`, `get_census_tract_data_with_boundaries`,
`match_to_census_tracts`, `aggregate_parcels_to_geography`) for full parameter documentation.
