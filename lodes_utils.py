"""
LEHD LODES (Longitudinal Employer-Household Dynamics) helpers.

The LEHD LODES8 series publishes annual block-level job counts by NAICS 2-digit
sector for every U.S. state. The Workplace Area Characteristics (WAC) file is
what you want when you need to know "how many people work in this census block,
broken down by industry."

For LVT analysis, the primary use is spatial allocation of corporate-income-tax
burden: rather than spreading a city-wide corporate-tax replacement burden
flat across all commercial parcels, you can weight by parcel value times block
eligible-jobs count, which concentrates the burden on downtown / high-density
job centers and de-concentrates it from isolated low-density commercial.

Source: https://lehd.ces.census.gov/data/lodes/LODES8/
Documentation: https://lehd.ces.census.gov/data/lodes/LODES8/LODESTechDoc8.0.pdf

Module convention: functions take state + year and return DataFrames. The cache
parameter on `fetch_lodes_wac` is opt-in — pass a directory and the file is
cached there as parquet for re-runs.
"""
from __future__ import annotations

import gzip
import io
from pathlib import Path
from typing import Iterable, List, Optional, Set

import numpy as np
import pandas as pd
import requests


# Sectors dominated by government / nonprofit / public-sector employment
# (which do not meaningfully pay corporate income tax). These are the default
# exclusions when computing "corporate-tax-eligible jobs" — override per-state
# if there are jurisdictional reasons to include them (e.g. some states do tax
# certain nonprofits as unrelated-business-income).
#
# CNS15 - Educational Services      (mostly public K-12 and state universities)
# CNS16 - Health Care and Social Assistance (mostly nonprofit hospitals)
# CNS20 - Public Administration     (federal/state/local government)
DEFAULT_EXCLUDED_SECTORS: Set[str] = {"CNS15", "CNS16", "CNS20"}

# All NAICS-2 sector codes in LODES WAC.
ALL_LODES_SECTORS: List[str] = [f"CNS{i:02d}" for i in range(1, 21)]


def fetch_lodes_wac(
    state: str,
    year: int = 2022,
    segment: str = "S000",
    job_type: str = "JT00",
    cache_dir: Optional[Path] = None,
    timeout: int = 60,
    base_url: str = "https://lehd.ces.census.gov/data/lodes/LODES8",
) -> pd.DataFrame:
    """
    Fetch LEHD LODES Workplace Area Characteristics for one state-year.

    Parameters
    ----------
    state : str
        Two-letter state abbreviation, lowercase ("ia", "ca", "ny").
    year : int, default 2022
        LODES vintage. Latest available is typically year - 2 (e.g. 2022 in
        early 2025). 2022 is conservative; bump up when newer files publish.
    segment : str, default "S000"
        LODES workforce segment. S000 = all workers, SA01 / SA02 / SA03 = age,
        SE01 / SE02 / SE03 = earnings, SI01 / SI02 / SI03 = NAICS supersector.
        S000 is what you almost always want.
    job_type : str, default "JT00"
        Job type. JT00 = all jobs, JT01 = primary jobs only. JT00 is what you
        almost always want for tax-base estimation.
    cache_dir : Path, optional
        If provided, the parsed CSV is saved as parquet here and re-read on
        subsequent calls. Filename:
            lodes_{state}_wac_{segment}_{job_type}_{year}.parquet
    timeout : int, default 60
        HTTP timeout in seconds.
    base_url : str
        LODES base URL. Override for testing only.

    Returns
    -------
    pd.DataFrame
        Block-level table with columns:
            w_geocode (15-digit FIPS block), C000 (total jobs), CNS01..CNS20
            (NAICS 2-digit sector job counts), plus various age/race/earnings
            breakdowns. See LODES tech doc for the full schema.
    """
    state = state.lower()
    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_path = cache_dir / f"lodes_{state}_wac_{segment}_{job_type}_{year}.parquet"
        if cache_path.exists():
            return pd.read_parquet(cache_path)
    else:
        cache_path = None

    url = f"{base_url}/{state}/wac/{state}_wac_{segment}_{job_type}_{year}.csv.gz"
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    df = pd.read_csv(io.BytesIO(gzip.decompress(resp.content)))
    df["w_geocode"] = df["w_geocode"].astype(str).str.zfill(15)

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, index=False)

    return df


def compute_eligible_jobs(
    wac_df: pd.DataFrame,
    excluded_sectors: Optional[Iterable[str]] = None,
    out_col: str = "eligible_jobs",
) -> pd.DataFrame:
    """
    Add an `eligible_jobs` column summing the corporate-tax-eligible sectors.

    Sectors in `excluded_sectors` (default: educational services, health care,
    public administration) are dropped from the sum. The remaining sectors
    proxy "private-sector for-profit employment" — the population that
    actually pays corporate income tax at meaningful scale.

    Parameters
    ----------
    wac_df : pd.DataFrame
        Output of `fetch_lodes_wac`, or any DataFrame with CNS01..CNS20 columns.
    excluded_sectors : iterable of str, optional
        Sector codes to exclude. Defaults to DEFAULT_EXCLUDED_SECTORS.
    out_col : str, default "eligible_jobs"
        Name of the added column.

    Returns
    -------
    pd.DataFrame
        A copy of `wac_df` with the additional column.
    """
    excluded = set(excluded_sectors) if excluded_sectors is not None else set(DEFAULT_EXCLUDED_SECTORS)
    available = [c for c in wac_df.columns if c.startswith("CNS")]
    included = [c for c in available if c not in excluded]
    out = wac_df.copy()
    out[out_col] = out[included].sum(axis=1)
    return out


def allocate_by_jobs_and_value(
    parcels_df: pd.DataFrame,
    lodes_df: pd.DataFrame,
    total_dollars: float,
    parcel_value_col: str,
    target_mask: Optional[pd.Series] = None,
    parcel_block_col: str = "GEOID",
    lodes_block_col: str = "w_geocode",
    lodes_jobs_col: str = "eligible_jobs",
    flat_fallback: bool = True,
) -> pd.Series:
    """
    Allocate a citywide dollar pool across parcels weighted by
    `parcel_value × block_eligible_jobs`, restricted to a target subset.

    This is the spatial corporate-income-tax allocation pattern: commercial
    parcels in high-job-density blocks (downtown, business parks) absorb a
    proportionally larger share of the corporate-tax replacement burden than
    commercial parcels in mostly-residential blocks where the building happens
    to be commercial but few people work nearby.

    Parameters
    ----------
    parcels_df : pd.DataFrame
        Parcel-level data with a 15-digit block FIPS code and a parcel value.
    lodes_df : pd.DataFrame
        Block-level LODES table with a jobs-count column. Typically the output
        of `compute_eligible_jobs` over a `fetch_lodes_wac` table.
    total_dollars : float
        Dollar pool to allocate.
    parcel_value_col : str
        Per-parcel weight (usually full_market_value or land_value).
    target_mask : pd.Series, optional
        Boolean mask, True where parcel is eligible (e.g. commercial + utility).
        Non-target parcels receive 0. If None, all parcels are eligible.
    parcel_block_col : str, default "GEOID"
        Parcel-side column with the 15-digit block FIPS. Must match
        `lodes_block_col` types.
    lodes_block_col : str, default "w_geocode"
        LODES-side column with the 15-digit block FIPS.
    lodes_jobs_col : str, default "eligible_jobs"
        LODES-side column with the per-block jobs count.
    flat_fallback : bool, default True
        If the joined eligible-jobs sum is zero (e.g. LODES merge failed,
        cache empty), fall back to a flat-by-value allocation across target
        parcels so callers don't silently get a zero allocation.

    Returns
    -------
    pd.Series
        Same index as parcels_df, float. Sums to total_dollars (modulo
        floating-point) when allocation succeeds.
    """
    if target_mask is None:
        target_mask = pd.Series(True, index=parcels_df.index)
    else:
        target_mask = target_mask.reindex(parcels_df.index, fill_value=False).astype(bool)

    # Merge block-level jobs onto parcels.
    parcel_blocks = parcels_df[parcel_block_col].astype(str)
    lodes_subset = lodes_df[[lodes_block_col, lodes_jobs_col]].copy()
    lodes_subset[lodes_block_col] = lodes_subset[lodes_block_col].astype(str)
    block_jobs = (
        pd.DataFrame({parcel_block_col: parcel_blocks})
        .merge(lodes_subset, left_on=parcel_block_col, right_on=lodes_block_col, how="left")
        [lodes_jobs_col]
        .fillna(0.0)
        .to_numpy()
    )

    value = pd.to_numeric(parcels_df[parcel_value_col], errors="coerce").fillna(0.0).clip(lower=0.0).to_numpy()
    weight = np.where(target_mask.to_numpy(), value * block_jobs, 0.0)
    total_weight = float(weight.sum())

    if total_weight <= 0:
        if not flat_fallback:
            return pd.Series(0.0, index=parcels_df.index)
        flat_weight = np.where(target_mask.to_numpy(), value, 0.0)
        flat_total = float(flat_weight.sum())
        if flat_total <= 0:
            return pd.Series(0.0, index=parcels_df.index)
        return pd.Series(flat_weight / flat_total * float(total_dollars), index=parcels_df.index)

    return pd.Series(weight / total_weight * float(total_dollars), index=parcels_df.index)
