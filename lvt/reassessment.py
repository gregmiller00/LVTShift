"""
Revenue-neutral reassessment modeling for LVTShift.

Where ``lvt_utils`` models tax RATE shifts (split-rate, building abatement) that
hold revenue constant while changing *how* the rate is structured, this module
models tax BASE shifts: replacing stale assessed values with fresh ones (an AVM,
market sales, or a manual factor) and rolling the millage back so the total levy
is unchanged. This is the "revenue-neutral reassessment" baseline — who wins and
who loses purely from updating assessments, before any policy change — and it is
what an LVT shift then layers on top of.

The module is agnostic to how the new values were produced: callers supply a
"new assessed value" column. Value GENERATION (AVM ensembles, hedonic land
models, LYCD land allocation) lives in the sibling ``berks_open_avmkit`` project
and the city notebooks, not here.

Functions
---------
model_revenue_neutral_reassessment
    Single jurisdiction. One flat millage rolled back to revenue neutrality on
    the new base.
model_multi_district_reassessment
    Overlapping taxing districts (county / municipality / school) each rolled
    back to revenue neutrality *within itself* — the Pennsylvania anti-windfall
    method (53 Pa.C.S. s 8823). A parcel's bill is summed across the districts
    it belongs to.
decompose_reassessment_and_lvt
    Split a stacked reassess-then-LVT shift into a reassessment component and a
    policy (LVT) component. Generalizes the inline prototype in
    ``cities/reading/model_lycd.ipynb`` Section 7b.
save_reassessment_export
    ``save_standard_export`` plus the reassessment / decomposition / per-district
    columns.

Output columns reuse the names ``lvt_utils.save_standard_export`` and ``lvt.viz``
already consume — ``current_tax`` / ``new_tax`` / ``tax_change`` /
``tax_change_pct`` / ``taxable_land_value`` / ``taxable_improvement_value`` — so a
single-district reassessment flows through the existing export and report path
unchanged.
"""

import pandas as pd
import numpy as np
from typing import Union, List, Tuple, Optional, Dict, Any

from lvt.lvt_utils import _coerce_numeric, _compute_adjusted_tax_components


def _is_mapping(obj: Any) -> bool:
    """True if ``obj`` is a per-key lookup (dict or Series), not a scalar."""
    return isinstance(obj, (dict, pd.Series))


def model_revenue_neutral_reassessment(
    df: pd.DataFrame,
    new_value_col: Optional[str] = None,
    current_revenue: Optional[float] = None,
    *,
    new_land_col: Optional[str] = None,
    new_improvement_col: Optional[str] = None,
    old_value_col: Optional[str] = None,
    current_millage: Optional[float] = None,
    exemption_col: Optional[str] = None,
    exemption_flag_col: Optional[str] = None,
    exclude_mask: Optional[pd.Series] = None,
    compute_current_tax: bool = True,
    verbose: bool = False,
) -> Tuple[float, float, pd.DataFrame]:
    """
    Model a revenue-neutral reassessment for a single taxing jurisdiction.

    The tax BASE changes (old assessed value -> a caller-supplied new assessed
    value) and the flat millage is rolled back so the total levy is held
    constant (Pennsylvania anti-windfall logic, 53 Pa.C.S. s 8823, single-district
    case). The function never generates values — that lives in the sibling
    ``berks_open_avmkit`` project — it only computes the tax impact of a new base.

    Over the parcels that participate in the solve, the rolled-back rate is

        new_millage = current_revenue * 1000 / sum(taxable_new_value)

    and ``new_tax_i = taxable_new_value_i * new_millage / 1000``, which is
    revenue-neutral by construction. A parcel wins (its bill falls) iff its
    reassessment ratio (new / old) is below the jurisdiction-average ratio
    (sum_new / sum_old over taxable parcels).

    Parameters
    ----------
    df : pandas.DataFrame
        Parcel-level data.
    new_value_col : str, optional
        Column holding the caller-supplied NEW total assessed value per parcel.
        Required unless both ``new_land_col`` and ``new_improvement_col`` are
        given. A pure (total-value) reassessment has no land/building split, so
        the taxable total is written to ``taxable_improvement_value`` with
        ``taxable_land_value = 0`` (the flat rate applies to the total either way;
        the split does not affect a flat-rate bill).
    current_revenue : float, optional
        Target levy to hold constant. If None, it is derived from the current
        tax (see ``old_value_col`` / ``current_millage`` / an existing
        ``current_tax`` column).
    new_land_col, new_improvement_col : str, optional
        Supply BOTH to carry an explicit land/improvement split of the new base
        (e.g. an AVM + LYCD allocation). When given, the taxable land and
        improvement values are taken from these columns (exemption-adjusted) and
        the taxable total is their sum. The flat reassessment rate still applies
        to the total; the split only populates the export columns.
    old_value_col : str, optional
        Column holding the OLD (pre-reassessment) assessed value. Used to derive
        ``current_revenue``, populate ``current_tax`` (with ``current_millage``),
        and compute ``reassessment_ratio``.
    current_millage : float, optional
        Current flat millage (per $1,000). Required when deriving
        ``current_revenue`` or ``current_tax`` from ``old_value_col``.
    exemption_col : str, optional
        Partial dollar-relief column. Applied to both the new and old bases via
        ``_compute_adjusted_tax_components`` (improvements first, then land).
    exemption_flag_col : str, optional
        Fully-exempt flag column (non-zero = exempt). Exempt parcels get
        ``new_tax = 0`` and are excluded from the rolled-back denominator.
    exclude_mask : pandas.Series, optional
        Boolean Series aligned to ``df.index``. Parcels where True are held out
        of the solve, the target is reduced by their ``current_tax`` sum, and
        they are re-inserted with ``new_tax = current_tax`` (unchanged). Mirrors
        ``model_split_rate_tax``. Requires a current tax to be available.
    compute_current_tax : bool, default True
        When True and ``old_value_col`` + ``current_millage`` are given, writes a
        ``current_tax`` column = adjusted old value * current_millage / 1000.
        When False, an existing ``current_tax`` column is used as-is.
    verbose : bool, default False
        Print the rolled-back millage and a revenue check.

    Returns
    -------
    tuple of (float, float, pandas.DataFrame)
        ``(new_millage, new_revenue, result_df)`` — matching the 3-tuple shape of
        ``model_full_building_abatement``. ``result_df`` is a copy of ``df`` with
        added columns: ``taxable_new_value``, ``taxable_land_value``,
        ``taxable_improvement_value``, ``current_tax`` (if computed/derived),
        ``new_tax``, ``tax_change`` / ``tax_change_pct`` (if a current tax is
        available), and ``reassessment_ratio`` (if ``old_value_col`` is given).
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    split_mode = new_land_col is not None and new_improvement_col is not None
    if (new_land_col is None) != (new_improvement_col is None):
        raise ValueError("Provide BOTH new_land_col and new_improvement_col, or neither")
    if not split_mode and new_value_col is None:
        raise ValueError("Provide new_value_col, or both new_land_col and new_improvement_col")

    # Column existence checks
    for col in [new_value_col, new_land_col, new_improvement_col, old_value_col,
                exemption_col, exemption_flag_col]:
        if col is not None and col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
    if current_millage is not None and not isinstance(current_millage, (int, float)):
        raise TypeError("current_millage must be a number or None")
    if exclude_mask is not None and not isinstance(exclude_mask, pd.Series):
        raise TypeError("exclude_mask must be a pandas Series or None")

    result_df = df.copy()

    # Taxable new base (exemption-adjusted), plus the land/improvement split for export.
    if split_mode:
        adj_land, adj_impr = _compute_adjusted_tax_components(
            result_df, new_land_col, new_improvement_col, exemption_col, exemption_flag_col,
        )
        taxable_new = adj_land + adj_impr
        new_total_raw = _coerce_numeric(result_df[new_land_col]) + _coerce_numeric(result_df[new_improvement_col])
    else:
        _zero, adj_new = _compute_adjusted_tax_components(
            result_df, None, new_value_col, exemption_col, exemption_flag_col,
        )
        adj_land = pd.Series(0.0, index=result_df.index)
        adj_impr = adj_new
        taxable_new = adj_new
        new_total_raw = _coerce_numeric(result_df[new_value_col])

    # Current tax (for tax_change, target derivation, and exclude_mask).
    have_old = old_value_col is not None and current_millage is not None
    if compute_current_tax and have_old:
        _z, adj_old = _compute_adjusted_tax_components(
            result_df, None, old_value_col, exemption_col, exemption_flag_col,
        )
        result_df['current_tax'] = adj_old * float(current_millage) / 1000.0
    elif 'current_tax' in result_df.columns:
        result_df['current_tax'] = _coerce_numeric(result_df['current_tax'])
    has_current = 'current_tax' in result_df.columns

    # Target levy to hold constant.
    if current_revenue is not None:
        target = float(current_revenue)
    elif has_current:
        target = float(result_df['current_tax'].sum())
    else:
        raise ValueError(
            "Cannot determine target revenue: pass current_revenue, or "
            "old_value_col + current_millage, or a current_tax column."
        )

    # Hold-out parcels keep their current tax; reduce the target by their levy.
    if exclude_mask is not None:
        excl = exclude_mask.reindex(result_df.index, fill_value=False).astype(bool)
    else:
        excl = pd.Series(False, index=result_df.index)
    if excl.any() and not has_current:
        raise ValueError("exclude_mask requires a current_tax (held-out parcels keep their current tax)")
    excl_current = float(result_df.loc[excl, 'current_tax'].sum()) if (excl.any() and has_current) else 0.0

    denom = float(taxable_new[~excl].sum())
    if denom <= 0:
        raise ValueError("Total taxable new value is zero or negative; cannot roll back millage")
    new_millage = (target - excl_current) * 1000.0 / denom

    new_tax = (taxable_new * new_millage / 1000.0).clip(lower=0)
    if excl.any():
        new_tax = new_tax.where(~excl, result_df['current_tax'])

    # Output columns
    result_df['taxable_new_value'] = taxable_new
    result_df['taxable_land_value'] = adj_land
    result_df['taxable_improvement_value'] = adj_impr
    result_df['new_tax'] = new_tax
    if old_value_col is not None:
        old_raw = _coerce_numeric(result_df[old_value_col])
        result_df['reassessment_ratio'] = np.where(old_raw > 0, new_total_raw / old_raw, np.nan)
    if has_current:
        result_df['tax_change'] = result_df['new_tax'] - result_df['current_tax']
        result_df['tax_change_pct'] = np.where(
            result_df['current_tax'] > 0,
            result_df['tax_change'] / result_df['current_tax'] * 100,
            0,
        )

    new_revenue = float(result_df['new_tax'].sum())

    if verbose:
        print("Revenue-neutral reassessment (single district)")
        print(f"Rolled-back millage: {new_millage:.4f} per $1,000")
        print(f"New revenue: ${new_revenue:,.2f}   Target: ${target:,.2f}")
        if target != 0:
            print(f"Revenue difference: ${new_revenue - target:,.2f} ({(new_revenue / target - 1) * 100:.4f}%)")

    return new_millage, new_revenue, result_df


def model_multi_district_reassessment(
    df: pd.DataFrame,
    new_value_col: str,
    old_value_col: str,
    districts: List[Dict[str, Any]],
    *,
    exemption_col: Optional[str] = None,
    exemption_flag_col: Optional[str] = None,
    crosscheck: bool = True,
    crosscheck_tol: float = 1e-6,
    verbose: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Model a revenue-neutral reassessment across overlapping taxing districts.

    This is the Pennsylvania anti-windfall method (53 Pa.C.S. s 8823): each
    taxing district is rolled back to revenue neutrality SEPARATELY within
    itself. For each district ``d``,

        new_millage_d = current_revenue_d * 1000 / sum_{i in d, taxable}(new_value_i)

    where ``current_revenue_d`` is that district's current levy (derived as
    ``sum_{i in d} old_value_i * current_millage_d / 1000`` unless supplied).
    A parcel's bills are summed across the districts it belongs to::

        current_tax_i = sum_{d ni i} old_value_i * current_millage_d / 1000
        new_tax_i     = sum_{d ni i} new_value_i * new_millage_d     / 1000

    Actual per-parcel dollar columns are produced (not just a percent change) so
    the existing export and viz, which consume ``current_tax`` / ``new_tax``,
    work unchanged. The combined-percent identity

        combined_pct = sum_d [ w_d * (pr / ratio_d - 1) ] / sum_d w_d

    (``pr`` = taxable_new / taxable_old per parcel, ``ratio_d`` = sum_new_d /
    sum_old_d, ``w_d`` = current_millage_d) falls out algebraically and is used
    only as a correctness cross-check.

    Parameters
    ----------
    df : pandas.DataFrame
        Parcel-level data.
    new_value_col, old_value_col : str
        New (caller-supplied) and old total assessed value columns.
    districts : list of dict
        One spec per overlapping taxing district. Keys:

        ``name`` (str)
            Used as the column prefix for diagnostics, e.g. ``county_ratio``.
        ``id_col`` (str or None)
            Column identifying which (sub)district a parcel belongs to. ``None``
            means every parcel belongs to one district (e.g. a single county).
            Each distinct value of ``id_col`` is rolled back as its own district.
        ``millage`` (float or mapping)
            Current millage per $1,000. A scalar applies one rate; a mapping
            (dict or Series keyed by ``id_col`` values) gives a rate per
            (sub)district. Parcels with no rate are non-members of this district.
        ``revenue`` (float, mapping, or None; optional)
            Explicit current levy per (sub)district. If omitted, derived from
            ``old_value * millage``. A scalar is only valid for a single group.
    exemption_col, exemption_flag_col : str, optional
        Exemption handling, applied once to the new and old bases (same
        semantics as ``model_revenue_neutral_reassessment``).
    crosscheck : bool, default True
        Verify the per-parcel ``tax_change_pct`` matches the combined-percent
        identity within ``crosscheck_tol``; raise ``AssertionError`` otherwise.
    crosscheck_tol : float, default 1e-6
        Tolerance for the identity cross-check.
    verbose : bool, default False
        Print each district's rolled-back levy and ratio.

    Returns
    -------
    tuple of (pandas.DataFrame, pandas.DataFrame)
        ``(result_df, district_summary)``. ``result_df`` is a copy of ``df`` with
        ``taxable_new_value``, ``taxable_land_value`` (= 0), ``taxable_improvement_value``,
        ``current_tax``, ``new_tax``, ``tax_change``, ``tax_change_pct``,
        ``reassessment_ratio``, and per district ``<name>_ratio``,
        ``<name>_current_millage``, ``<name>_new_millage`` (NaN for non-members).
        ``district_summary`` has one row per district (rates, revenues, ratio,
        parcel count, taxable base).
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    for col in [new_value_col, old_value_col]:
        if not isinstance(col, str) or col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
    if exemption_col is not None and exemption_col not in df.columns:
        raise ValueError(f"Exemption column '{exemption_col}' not found in DataFrame")
    if exemption_flag_col is not None and exemption_flag_col not in df.columns:
        raise ValueError(f"Exemption flag column '{exemption_flag_col}' not found in DataFrame")
    if not districts:
        raise ValueError("districts must be a non-empty list of district specs")

    result_df = df.copy()
    _z1, taxable_new = _compute_adjusted_tax_components(
        result_df, None, new_value_col, exemption_col, exemption_flag_col)
    _z2, taxable_old = _compute_adjusted_tax_components(
        result_df, None, old_value_col, exemption_col, exemption_flag_col)

    current_tax = pd.Series(0.0, index=result_df.index)
    new_tax = pd.Series(0.0, index=result_df.index)
    summary_rows = []

    for spec in districts:
        if 'name' not in spec or 'millage' not in spec:
            raise ValueError("each district spec needs at least 'name' and 'millage'")
        name = spec['name']
        id_col = spec.get('id_col')
        millage = spec['millage']
        revenue = spec.get('revenue')

        if id_col is not None and id_col not in result_df.columns:
            raise ValueError(f"District '{name}': id_col '{id_col}' not found in DataFrame")

        if id_col is None:
            grp = pd.Series('__all__', index=result_df.index)
        else:
            grp = result_df[id_col]

        if _is_mapping(millage):
            cm = grp.map(dict(millage) if isinstance(millage, pd.Series) else millage).astype(float)
        else:
            cm = pd.Series(float(millage), index=result_df.index)

        members = grp.notna() & cm.notna()
        if not members.any():
            raise ValueError(f"District '{name}': no parcels have a rate / membership")

        gidx = grp.where(members)
        sum_old = taxable_old.where(members, 0.0).groupby(gidx).sum()
        sum_new = taxable_new.where(members, 0.0).groupby(gidx).sum()

        if revenue is None:
            rev_g = (taxable_old.where(members, 0.0) * cm).groupby(gidx).sum() / 1000.0
        elif _is_mapping(revenue):
            rev_g = pd.Series(revenue, dtype=float)
        else:
            groups = list(sum_new.index)
            if len(groups) != 1:
                raise ValueError(
                    f"District '{name}': scalar revenue requires a single group "
                    f"(id_col=None or constant); got {len(groups)} groups — pass a "
                    f"mapping or omit revenue to derive it."
                )
            rev_g = pd.Series({groups[0]: float(revenue)})

        ratio_g = sum_new / sum_old.replace(0, np.nan)
        new_mill_g = rev_g * 1000.0 / sum_new.replace(0, np.nan)

        nm_p = gidx.map(new_mill_g)
        rd_p = gidx.map(ratio_g)
        cur_contrib = (taxable_old * cm / 1000.0).where(members, 0.0).fillna(0.0)
        new_contrib = (taxable_new * nm_p / 1000.0).where(members, 0.0).fillna(0.0)
        current_tax = current_tax + cur_contrib
        new_tax = new_tax + new_contrib

        result_df[f'{name}_current_millage'] = cm.where(members, np.nan)
        result_df[f'{name}_new_millage'] = nm_p.where(members, np.nan)
        result_df[f'{name}_ratio'] = rd_p.where(members, np.nan)

        tot_old = float(taxable_old[members].sum())
        tot_new = float(taxable_new[members].sum())
        summary_rows.append({
            'name': name,
            'current_millage': (float(millage) if not _is_mapping(millage) else 'varies'),
            'current_revenue': float(rev_g.sum()),
            'new_revenue': float(new_contrib.sum()),
            'new_millage': (float(new_mill_g.iloc[0]) if len(new_mill_g) == 1 else 'varies'),
            'ratio': (tot_new / tot_old if tot_old > 0 else np.nan),
            'n_parcels': int(members.sum()),
            'taxable_new_base': tot_new,
        })
        if verbose:
            r = tot_new / tot_old if tot_old > 0 else float('nan')
            print(f"  [{name}] groups={len(sum_new)}  current ${float(rev_g.sum()):,.0f}  "
                  f"new ${float(new_contrib.sum()):,.0f}  ratio={r:.4f}")

    result_df['taxable_new_value'] = taxable_new
    result_df['taxable_land_value'] = 0.0
    result_df['taxable_improvement_value'] = taxable_new
    result_df['current_tax'] = current_tax
    result_df['new_tax'] = new_tax
    result_df['tax_change'] = new_tax - current_tax
    result_df['tax_change_pct'] = np.where(
        current_tax > 0, (new_tax - current_tax) / current_tax * 100, 0)
    old_raw = _coerce_numeric(result_df[old_value_col])
    new_raw = _coerce_numeric(result_df[new_value_col])
    result_df['reassessment_ratio'] = np.where(old_raw > 0, new_raw / old_raw, np.nan)

    district_summary = pd.DataFrame(summary_rows)

    if crosscheck:
        _crosscheck_combined_identity(result_df, districts, taxable_new, taxable_old, crosscheck_tol)

    if verbose:
        tc, tn = float(current_tax.sum()), float(new_tax.sum())
        delta = (tn / tc - 1) * 100 if tc else float('nan')
        print(f"  multi-district total: current ${tc:,.0f} -> new ${tn:,.0f} ({delta:.4f}%)")

    return result_df, district_summary


def _crosscheck_combined_identity(result_df, districts, taxable_new, taxable_old, tol):
    """Assert summed per-parcel tax_change_pct equals the weighted-ratio identity."""
    old = taxable_old.values
    pr = np.where(old > 0, taxable_new.values / np.where(old > 0, old, 1.0), np.nan)
    num = np.zeros(len(result_df))
    den = np.zeros(len(result_df))
    for spec in districts:
        name = spec['name']
        cm = result_df[f'{name}_current_millage'].values
        rd = result_df[f'{name}_ratio'].values
        member = ~np.isnan(cm) & ~np.isnan(rd) & (rd != 0)
        term = np.where(member, cm * (pr / np.where(rd != 0, rd, np.nan) - 1.0), 0.0)
        num += np.nan_to_num(term)
        den += np.where(member, np.nan_to_num(cm), 0.0)
    combined = np.where(den > 0, num / den * 100.0, np.nan)
    actual = result_df['tax_change_pct'].values
    mask = (result_df['current_tax'].values > 0) & np.isfinite(pr) & np.isfinite(combined)
    if mask.any():
        max_dev = float(np.nanmax(np.abs(combined[mask] - actual[mask])))
        if max_dev > tol:
            raise AssertionError(
                f"Multi-district combined-% identity cross-check failed: "
                f"max deviation {max_dev:.3e} > tol {tol:.1e}"
            )


def decompose_reassessment_and_lvt(
    df: pd.DataFrame,
    *,
    current_tax_col: str = 'current_tax',
    reassessed_tax_col: str = 'avm_flat_tax',
    final_tax_col: str = 'new_tax',
    out_prefix: str = '',
    inplace: bool = False,
) -> pd.DataFrame:
    """
    Decompose a stacked reassess-then-LVT shift into its two components.

    Generalizes the inline anti-windfall decomposition in
    ``cities/reading/model_lycd.ipynb`` Section 7b. Three tax points per parcel:

      (1) current        = old base x current flat rate          [current_tax_col]
      (2) reassessed     = new base x rolled-back flat rate       [reassessed_tax_col]
                           (revenue-neutral vs 1)
      (3) reassessed+LVT = new base split land/impr x split-rate  [final_tax_col]
                           (revenue-neutral vs 2)

    Emits ``reassess_change`` = (2) - (1), ``lvt_change`` = (3) - (2),
    ``total_change`` = (3) - (1), and the matching ``*_pct`` columns (NaN where
    the denominator is zero). By construction
    ``reassess_change + lvt_change == total_change``.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain the three tax columns.
    current_tax_col, reassessed_tax_col, final_tax_col : str
        Column names for tax points (1), (2), (3).
    out_prefix : str, default ''
        Prefix prepended to every emitted column name.
    inplace : bool, default False
        Mutate ``df`` in place vs. return a copy.

    Returns
    -------
    pandas.DataFrame
        ``df`` (or a copy) with the six decomposition columns added.
    """
    for col in [current_tax_col, reassessed_tax_col, final_tax_col]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")

    out = df if inplace else df.copy()
    cur = _coerce_numeric(out[current_tax_col])
    rea = _coerce_numeric(out[reassessed_tax_col])
    fin = _coerce_numeric(out[final_tax_col])
    p = out_prefix

    out[f'{p}reassess_change'] = rea - cur
    out[f'{p}reassess_change_pct'] = np.where(cur > 0, (rea - cur) / cur * 100, np.nan)
    out[f'{p}lvt_change'] = fin - rea
    out[f'{p}lvt_change_pct'] = np.where(rea > 0, (fin - rea) / rea * 100, np.nan)
    out[f'{p}total_change'] = fin - cur
    out[f'{p}total_change_pct'] = np.where(cur > 0, (fin - cur) / cur * 100, np.nan)
    return out


# Decomposition columns appended by save_reassessment_export when present in df.
_REASSESSMENT_EXTRA_COLS = [
    'reassessment_ratio',
    'reassess_change', 'reassess_change_pct',
    'lvt_change', 'lvt_change_pct',
    'total_change', 'total_change_pct',
]


def save_reassessment_export(
    df: pd.DataFrame,
    city: str,
    output_path: str,
    model_type: str,
    land_millage: float,
    improvement_millage: float,
    *,
    extra_cols: Optional[List[str]] = None,
    district_names: Optional[List[str]] = None,
    **standard_kwargs,
) -> pd.DataFrame:
    """
    Standard cross-city export plus reassessment / decomposition columns.

    Calls ``lvt_utils.save_standard_export`` (keeping the canonical fixed schema
    stable for cross-city consumers), then appends the reassessment-specific
    columns and re-writes the CSV.

    Parameters
    ----------
    df : pandas.DataFrame
        Modeled dataframe (output of a reassessment / decomposition run).
    city, output_path, model_type, land_millage, improvement_millage
        Passed through to ``save_standard_export``. For a flat reassessment,
        set both millages to the rolled-back rate and ``model_type`` to e.g.
        ``"reassessment:flat"``.
    extra_cols : list of str, optional
        Columns to append. Defaults to the reassessment / decomposition columns
        present in ``df`` (ratio and the six decomposition columns).
    district_names : list of str, optional
        For multi-district runs, the district ``name`` values whose
        ``<name>_ratio`` / ``<name>_current_millage`` / ``<name>_new_millage``
        columns should be appended.
    **standard_kwargs
        Forwarded to ``save_standard_export`` (e.g. ``parcel_id_col``,
        ``exempt_flag_col``, demographic column overrides).

    Returns
    -------
    pandas.DataFrame
        The exported dataframe (standard columns plus the appended extras).
    """
    from lvt.lvt_utils import save_standard_export

    out = save_standard_export(
        df, city, output_path, model_type, land_millage, improvement_millage,
        **standard_kwargs,
    )

    cols = extra_cols if extra_cols is not None else [c for c in _REASSESSMENT_EXTRA_COLS if c in df.columns]
    for c in cols:
        if c in df.columns:
            out[c] = df[c].values

    if district_names:
        for name in district_names:
            for suffix in ('_ratio', '_current_millage', '_new_millage'):
                col = f'{name}{suffix}'
                if col in df.columns:
                    out[col] = df[col].values

    out.to_csv(output_path, index=False)
    return out
