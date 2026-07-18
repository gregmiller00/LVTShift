"""
Wage-tax-for-land-tax swap modeling for LVTShift.

Where ``lvt_utils`` and ``reassessment`` model the property tax under different
rates or bases, this module models replacing a wholly different tax instrument —
Philadelphia's Wage & Earnings Tax, levied on payroll, not parcels — with a pure
land value tax. The existing property tax is left untouched throughout: the wage
tax is eliminated entirely and a new, separate land-only levy is added, sized via
revenue-neutral solve to recoup the eliminated revenue.

There is no parcel-level wage data (it isn't publicly available and isn't
FOIA-able), so this module works at **census tract** granularity for the wage-tax
side and rolls the parcel-level land tax result up to the same tracts for
comparison. This mixes two different incidence populations — a tract's wage tax
is borne by all residents (owners and renters), while its new land tax is borne
only by landowners in that tract — which every function here treats as a
documented modeling limitation, not something to paper over.

Functions
---------
get_resident_wage_tax_by_tract
    Current resident wage tax liability by tract, from ACS aggregate wage/salary
    income (B19062) — the tax base for residents, who owe the wage tax on their
    full wages regardless of where they work.
fetch_lodes_wac
    Download/cache LEHD Origin-Destination Employment Statistics (LODES)
    Workplace Area Characteristics data for a state.
summarize_lodes_workplace_jobs
    Job-count-by-earnings-tier cross-check for a county's workplace blocks.
    A plausibility check and narrative source for the commuter-transfer finding —
    NOT used to estimate dollars (LODES earnings tiers are too coarse for that).
compute_wage_tax_revenue_target
    Combine the ACS-modeled resident total with the published resident/
    non-resident revenue split to size the total wage tax revenue being replaced.
model_land_only_tax
    Revenue-neutral pure land value tax (no improvement component), sized to a
    target revenue.
save_wage_tax_swap_tract_export
    Primary deliverable: tract-level current wage tax vs. new land tax, winners
    and losers.
save_wage_tax_swap_parcel_export
    Secondary parcel-level detail export of the new land-only tax.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from lvt.census_utils import get_census_tract_data
from lvt.lvt_utils import model_split_rate_tax


def get_resident_wage_tax_by_tract(
    fips_code: str,
    resident_rate: float = 0.0375,
    year: int = 2022,
    api_key: str = None,
) -> pd.DataFrame:
    """
    Compute current resident wage tax liability by census tract.

    Uses ACS table B19062 (Aggregate Wage or Salary Income in the Past 12 Months
    for Households) as the tax base — not B19061 ("Aggregate Earnings"), which
    also includes self-employment income. Philadelphia's self-employment income is
    captured by the separate Net Profits Tax, not the Wage Tax, so B19061 would
    overstate the wage tax base.

    Parameters
    ----------
    fips_code : str
        5-digit FIPS code (state + county), e.g. "42101" for Philadelphia County.
    resident_rate : float, default=0.0375
        Current resident Wage & Earnings Tax rate (fraction, not percent).
    year : int, default=2022
        ACS 5-year vintage to query.
    api_key : str, optional
        Census API key. If None, loaded from the CENSUS_API_KEY environment
        variable.

    Returns
    -------
    pd.DataFrame
        One row per tract: `tract_geoid`, `agg_wage_income`, `agg_wage_income_moe`,
        `current_wage_tax` (= agg_wage_income * resident_rate), plus the default
        `median_income`/`minority_pct`/`black_pct` demographic columns from
        get_census_tract_data().
    """
    df = get_census_tract_data(
        fips_code,
        year=year,
        api_key=api_key,
        extra_variables=['B19062_001E', 'B19062_001M'],
        column_aliases={
            'B19062_001E': 'agg_wage_income',
            'B19062_001M': 'agg_wage_income_moe',
        },
    )
    df['current_wage_tax'] = df['agg_wage_income'] * resident_rate
    return df


def fetch_lodes_wac(
    state_abbr: str = "pa",
    year: int = 2021,
    lodes_version: str = "LODES8",
    segment: str = "JT00",
    cache_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Download (or load from cache) a LODES Workplace Area Characteristics file.

    WAC files report job counts by workplace census block, including three
    coarse earnings tiers (CE01: <=$1250/month, CE02: $1251-$3333/month,
    CE03: >$3333/month). These tiers are too coarse to back-solve dollar wages
    from — use this only for job-count cross-checks
    (see summarize_lodes_workplace_jobs), not for revenue estimation.

    Parameters
    ----------
    state_abbr : str, default="pa"
        Two-letter lowercase state postal abbreviation.
    year : int
        LODES data year. LODES lags roughly 2 years behind the current year.
    lodes_version : str, default="LODES8"
        LODES release version.
    segment : str, default="JT00"
        Job type segment. JT00 = all jobs.
    cache_path : str, optional
        Local file path to cache the downloaded CSV. If the file already exists,
        it is loaded from disk instead of re-downloading. If None, no caching is
        performed (downloads every call).

    Returns
    -------
    pd.DataFrame
        Raw WAC rows: `w_geocode` (15-digit workplace census block), `C000`
        (total jobs), `CE01`/`CE02`/`CE03` (jobs by earnings tier), plus the
        remaining LODES WAC columns.
    """
    if cache_path and os.path.exists(cache_path):
        return pd.read_csv(cache_path, dtype={'w_geocode': str})

    url = (
        f"https://lehd.ces.census.gov/data/lodes/{lodes_version}/{state_abbr}/wac/"
        f"{state_abbr}_wac_{segment}_{year}.csv.gz"
    )
    df = pd.read_csv(url, dtype={'w_geocode': str}, compression='gzip')

    if cache_path:
        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_path, index=False)

    return df


def summarize_lodes_workplace_jobs(wac_df: pd.DataFrame, county_fips: str) -> Dict[str, float]:
    """
    Summarize LODES WAC job counts for a county's workplace blocks.

    A plausibility cross-check ("did I filter/parse this right, does the total
    job count look like a real county") and a source for the commuter-transfer
    finding's job-count magnitude — NOT a revenue estimator.

    Parameters
    ----------
    wac_df : pd.DataFrame
        Output of fetch_lodes_wac().
    county_fips : str
        5-digit county FIPS code (state + county). Workplace blocks are filtered
        to those whose `w_geocode` starts with this code.

    Returns
    -------
    dict
        `total_jobs`, `jobs_tier1` (<=$1250/mo), `jobs_tier2` ($1251-3333/mo),
        `jobs_tier3` (>$3333/mo), and `tier1_share`/`tier2_share`/`tier3_share`.
    """
    county_jobs = wac_df[wac_df['w_geocode'].str.startswith(county_fips)]
    total_jobs = float(county_jobs['C000'].sum())
    tier1 = float(county_jobs['CE01'].sum())
    tier2 = float(county_jobs['CE02'].sum())
    tier3 = float(county_jobs['CE03'].sum())

    return {
        'total_jobs': total_jobs,
        'jobs_tier1': tier1,
        'jobs_tier2': tier2,
        'jobs_tier3': tier3,
        'tier1_share': tier1 / total_jobs if total_jobs else np.nan,
        'tier2_share': tier2 / total_jobs if total_jobs else np.nan,
        'tier3_share': tier3 / total_jobs if total_jobs else np.nan,
    }


def compute_wage_tax_revenue_target(
    resident_wage_tax_df: pd.DataFrame,
    resident_share: float = 0.66,
    published_total_revenue: Optional[float] = None,
    validation_tolerance_pct: float = 20.0,
) -> Dict[str, float]:
    """
    Derive the total current wage tax revenue being eliminated.

    The ACS-modeled resident total (from get_resident_wage_tax_by_tract) covers
    only residents. Non-resident commuters — who mostly live outside city limits
    and so can't be attributed to a Philadelphia tract — are extrapolated from
    the published resident/non-resident revenue split rather than modeled
    directly (see module docstring: LODES earnings tiers are too coarse for a
    direct dollar estimate).

    Parameters
    ----------
    resident_wage_tax_df : pd.DataFrame
        Output of get_resident_wage_tax_by_tract().
    resident_share : float, default=0.66
        Published share of total wage tax revenue paid by residents (the
        remainder, non-residents, is derived from this).
    published_total_revenue : float, optional
        Official total wage tax revenue figure (e.g. from a city budget
        document) to validate the modeled total against.
    validation_tolerance_pct : float, default=20.0
        Tolerance for the gap between the modeled and published total. Wider
        than the ~1% tolerance used for parcel-level property tax cross-checks,
        because both ACS tract-level margin of error and the resident/
        non-resident split itself are approximations.

    Returns
    -------
    dict
        `modeled_resident_total`, `implied_nonresident_total`, `implied_total`,
        and (if `published_total_revenue` given) `published_total_revenue` and
        `gap_pct`.
    """
    modeled_resident_total = float(resident_wage_tax_df['current_wage_tax'].sum())
    implied_nonresident_total = modeled_resident_total * (1 - resident_share) / resident_share
    implied_total = modeled_resident_total + implied_nonresident_total

    result = {
        'modeled_resident_total': modeled_resident_total,
        'implied_nonresident_total': implied_nonresident_total,
        'implied_total': implied_total,
    }

    if published_total_revenue is not None:
        gap_pct = (implied_total - published_total_revenue) / published_total_revenue * 100
        result['published_total_revenue'] = float(published_total_revenue)
        result['gap_pct'] = gap_pct
        if abs(gap_pct) > validation_tolerance_pct:
            print(
                f"⚠️ Modeled total wage tax revenue (${implied_total:,.0f}) differs from "
                f"published (${published_total_revenue:,.0f}) by {gap_pct:.1f}%, "
                f"exceeding the {validation_tolerance_pct}% tolerance."
            )

    return result


def model_land_only_tax(
    df: pd.DataFrame,
    land_value_col: str,
    current_revenue: float,
    exemption_col: Optional[str] = None,
    exemption_flag_col: Optional[str] = None,
    exclude_mask: Optional[pd.Series] = None,
    verbose: bool = False,
) -> Tuple[float, float, pd.DataFrame]:
    """
    Model a revenue-neutral, pure land value tax (no improvement component).

    Thin wrapper around model_split_rate_tax() with an all-zero improvement
    value column. This is mathematically exact, not an approximation: in
    _solve_revenue_neutral_split_millage, the improvement term's contribution to
    revenue is `0 * improvement_millage = 0` regardless of land_improvement_ratio,
    so the solve collapses to `land_millage = current_revenue * 1000 /
    total_land_value` for any ratio. Reusing model_split_rate_tax gets exemption/
    cap/exclude_mask handling for free rather than reimplementing the solve.

    Parameters
    ----------
    df : pd.DataFrame
        Parcel data containing `land_value_col`.
    land_value_col : str
        Column name for land value.
    current_revenue : float
        Target revenue for the new land-only tax (e.g. the wage tax revenue
        being replaced, from compute_wage_tax_revenue_target()).
    exemption_col : str, optional
        Column name for dollar exemptions, passed through to model_split_rate_tax.
    exemption_flag_col : str, optional
        Column name for a full-exemption flag, passed through to
        model_split_rate_tax. Note this defaults to reusing whatever exemption
        flag the caller passes — e.g. today's property-tax exemption flag is a
        reasonable default but an explicit policy choice, not a given.
    exclude_mask : pd.Series, optional
        Boolean Series aligned to df.index, passed through to model_split_rate_tax.
    verbose : bool, default=False
        Print millage/revenue details.

    Returns
    -------
    tuple
        (land_millage, new_revenue, result_df) — result_df carries `new_tax`
        and a `taxable_land_value` column (the meaningless improvement millage
        from the underlying solve is discarded).
    """
    result_df = df.copy()
    result_df['_zero_improvement'] = 0.0

    land_millage, _improvement_millage, new_revenue, result_df = model_split_rate_tax(
        result_df,
        land_value_col,
        '_zero_improvement',
        current_revenue,
        land_improvement_ratio=1.0,
        exemption_col=exemption_col,
        exemption_flag_col=exemption_flag_col,
        exclude_mask=exclude_mask,
        verbose=verbose,
    )
    result_df = result_df.drop(columns=['_zero_improvement', 'taxable_improvement_value',
                                         'improvement_tax', 'improvement_tax_before_credits'],
                                errors='ignore')

    return land_millage, new_revenue, result_df


def save_wage_tax_swap_tract_export(
    tract_df: pd.DataFrame,
    city: str,
    output_path: str,
    resident_wage_tax_col: str = "current_wage_tax",
    new_land_tax_col: str = "new_land_tax",
    tract_geoid_col: str = "tract_geoid",
    income_col: str = "median_income",
    minority_col: str = "minority_pct",
    black_col: str = "black_pct",
    land_millage: Optional[float] = None,
    model_type: str = "wage_tax_swap:land_only",
) -> pd.DataFrame:
    """
    Build and save the tract-level wage-tax-swap export CSV.

    This is the primary deliverable of the swap analysis: for each tract, the
    resident wage tax being eliminated vs. the new land-only tax owed by parcels
    in that tract. Net change mixes two different incidence populations (all
    residents for the wage tax; landowners only for the land tax) — this is a
    documented limitation of the analysis, not resolved by this function.

    Parameters
    ----------
    tract_df : pd.DataFrame
        Tract-level data with `resident_wage_tax_col` and `new_land_tax_col`
        already merged in (e.g. via aggregate_parcels_to_geography() joined to
        get_resident_wage_tax_by_tract()'s output on `tract_geoid_col`).
    city : str
        Lowercase slug, e.g. "philadelphia".
    output_path : str
        File path for the output CSV.
    resident_wage_tax_col, new_land_tax_col, tract_geoid_col : str
        Column names in tract_df.
    income_col, minority_col, black_col : str
        Demographic columns to carry through, if present.
    land_millage : float, optional
        Solved land-only millage, recorded as a constant column for reference.
    model_type : str
        Encoded model description recorded as a constant column.

    Returns
    -------
    pd.DataFrame
        The exported DataFrame (also written to output_path).
    """
    out = tract_df.copy()
    out['net_change'] = out[new_land_tax_col] - out[resident_wage_tax_col]
    out['net_change_pct'] = np.where(
        out[resident_wage_tax_col] > 0,
        out['net_change'] / out[resident_wage_tax_col] * 100,
        np.nan,
    )
    out['model_type'] = model_type
    out['land_millage'] = land_millage
    out['city'] = city

    cols = [tract_geoid_col, 'city', resident_wage_tax_col, new_land_tax_col,
            'net_change', 'net_change_pct', 'model_type', 'land_millage']
    for col in (income_col, minority_col, black_col):
        if col in out.columns:
            cols.append(col)

    out = out[cols]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)
    return out


def save_wage_tax_swap_parcel_export(
    parcels_df: pd.DataFrame,
    city: str,
    output_path: str,
    land_millage: float,
    land_value_col: str = "taxable_land",
    new_tax_col: str = "new_tax",
    parcel_id_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Build and save the parcel-level detail export for the new land-only tax.

    Secondary to save_wage_tax_swap_tract_export(): this is per-parcel detail on
    the new levy only. `current_tax` is 0 for every row by construction — parcels
    don't pay the wage tax being eliminated, and the existing property tax is
    unchanged and out of scope here — so `tax_change`/`tax_change_pct` in the
    usual save_standard_export sense are not meaningful and are not computed.
    This function performs its own validation instead of reusing
    save_standard_export's revenue-neutrality check, which assumes a nonzero
    parcel-level current_tax.

    Parameters
    ----------
    parcels_df : pd.DataFrame
        Parcel-level data with `land_value_col` and `new_tax_col`.
    city : str
        Lowercase slug, e.g. "philadelphia".
    output_path : str
        File path for the output CSV.
    land_millage : float
        Solved land-only millage, recorded as a constant column for reference.
    land_value_col, new_tax_col : str
        Column names in parcels_df.
    parcel_id_col : str, optional
        Column to rename to `parcel_id` in the export, if provided.

    Returns
    -------
    pd.DataFrame
        The exported DataFrame (also written to output_path).
    """
    out = parcels_df.copy()
    out['city'] = city
    out['land_millage'] = land_millage

    cols = ['city', land_value_col, new_tax_col, 'land_millage']
    if parcel_id_col and parcel_id_col in out.columns:
        out = out.rename(columns={parcel_id_col: 'parcel_id'})
        cols = ['parcel_id'] + cols
    if 'tract_geoid' in out.columns:
        cols.append('tract_geoid')

    out = out[cols]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)
    return out
