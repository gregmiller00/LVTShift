"""Per-city LVT model metrics.

Produces a compact, machine-readable summary of a city's modeled tax shift alongside the
standard report charts. Called automatically by :func:`lvt.viz.create_city_report`, so every
city that runs the standard pipeline writes a metrics summary without any extra notebook code.

For a city's standard export it reports:

- the full modeled tax base (taxable land + improvement, fully-exempt parcels excluded);
- the total dollars changed by the reform (sum of |new - current|), the net amount shifted
  between winners and losers, and both as a share of the modeled levy;
- the value of vacant land and of underdeveloped parcels bucketed by improvement ratio
  (<10%, 10-25%, 25-50%), each as a dollar amount and a share of the full modeled tax base.

Outputs (written to ``{output_dir}/{city}/``):

- ``metrics_summary.md``  — human-readable
- ``metrics_{city}.csv``  — one wide row, for cross-city roll-up (see :func:`rollup_city_metrics`)
"""
import glob
import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Improvement-ratio bucket edges (improvement / (land + improvement)).
# "Vacant" is the 0% bucket; the next three are the underdeveloped buckets.
_BUCKETS = [
    ('vacant', 'Vacant (0% improvement)', lambda r: r <= 0),
    ('underdeveloped_lt10', 'Underdeveloped <10%', lambda r: (r > 0) & (r < 0.10)),
    ('underdeveloped_10_25', 'Underdeveloped 10-25%', lambda r: (r >= 0.10) & (r < 0.25)),
    ('underdeveloped_25_50', 'Underdeveloped 25-50%', lambda r: (r >= 0.25) & (r < 0.50)),
    ('developed_ge50', 'Developed >=50%', lambda r: r >= 0.50),
]


def _money(x: float) -> str:
    if x >= 1e9:
        return f"${x / 1e9:.2f}B"
    if x >= 1e6:
        return f"${x / 1e6:.1f}M"
    return f"${x:,.0f}"


def compute_city_metrics(
    df: pd.DataFrame,
    city: str,
    output_dir: str = '../../analysis/reports',
    *,
    write: bool = True,
    taxable_land_col: str = 'taxable_land_value',
    taxable_improvement_col: str = 'taxable_improvement_value',
    current_tax_col: str = 'current_tax',
    new_tax_col: str = 'new_tax',
    exempt_flag_col: str = 'is_fully_exempt',
) -> Dict[str, object]:
    """Compute and (optionally) save per-city LVT model metrics.

    Parameters
    ----------
    df : pandas.DataFrame
        A city's standard export (output of ``save_standard_export``). Must contain taxable
        land/improvement and current/new tax columns.
    city : str
        City slug used for the output sub-directory and CSV file name, e.g. ``"seattle"``.
    output_dir : str
        Parent directory for the report. A ``{city}`` sub-directory is created. Default
        ``"../../analysis/reports"`` resolves correctly from ``cities/<city>/``.
    write : bool
        When ``True`` (default), write ``metrics_summary.md`` and ``metrics_{city}.csv``.
        When ``False``, compute and return only.
    taxable_land_col, taxable_improvement_col, current_tax_col, new_tax_col, exempt_flag_col : str
        Column-name overrides for jurisdictions whose export differs from the standard schema.

    Returns
    -------
    dict
        Flat metrics dict (also the row written to the CSV): tax base, land/improvement base,
        modeled levy, gross/net dollars changed and their ratios, and per-bucket value + share
        of the tax base.
    """
    df = df.copy()
    if exempt_flag_col in df.columns:                     # exclude fully-exempt (no signal)
        df = df[df[exempt_flag_col] != 1].copy()

    land = pd.to_numeric(df[taxable_land_col], errors='coerce').fillna(0).clip(lower=0)
    imp = pd.to_numeric(df[taxable_improvement_col], errors='coerce').fillna(0).clip(lower=0)
    val = land + imp
    ratio = np.where(val > 0, imp / val, 0.0)
    abschg = (pd.to_numeric(df[new_tax_col], errors='coerce').fillna(0)
              - pd.to_numeric(df[current_tax_col], errors='coerce').fillna(0)).abs()

    tax_base = float(val.sum())
    land_base = float(land.sum())
    imp_base = float(imp.sum())
    modeled_levy = float(pd.to_numeric(df[current_tax_col], errors='coerce').fillna(0).sum())
    gross_changed = float(abschg.sum())
    net_shifted = gross_changed / 2.0                     # neutral: winners' gains == losers' losses
    abschg_total = gross_changed or 1.0
    base_or_1 = tax_base or 1.0
    levy_or_1 = modeled_levy or 1.0

    model_type = str(df['model_type'].iloc[0]) if 'model_type' in df.columns and len(df) else ''

    out: Dict[str, object] = {
        'city': city, 'model_type': model_type, 'parcels_modeled': int(len(df)),
        'tax_base_usd': tax_base, 'land_base_usd': land_base, 'improvement_base_usd': imp_base,
        'modeled_levy_usd': modeled_levy,
        'dollars_changed_gross_usd': gross_changed, 'dollars_shifted_net_usd': net_shifted,
        'dollars_changed_pct_of_levy': gross_changed / levy_or_1 * 100,
        'dollars_shifted_pct_of_levy': net_shifted / levy_or_1 * 100,
        'dollars_changed_bps_of_base': gross_changed / base_or_1 * 1e4,
    }

    bucket_rows: List[Dict[str, object]] = []
    for key, label, fn in _BUCKETS:
        mask = fn(ratio)
        v = float(val[mask].sum())
        row = {
            'key': key, 'label': label, 'parcels': int(mask.sum()), 'value': v,
            'pct_of_tax_base': v / base_or_1 * 100,
            'land_value': float(land[mask].sum()),
            'share_of_dollars_changed': float(abschg[mask].sum()) / abschg_total * 100,
        }
        bucket_rows.append(row)
        out[f'{key}_value_usd'] = v
        out[f'{key}_pct_of_base'] = row['pct_of_tax_base']

    underdev_mask = ratio < 0.50                          # includes vacant
    underdev = {
        'key': 'underdeveloped_subtotal',
        'label': 'Underdeveloped subtotal (<50%, incl. vacant)',
        'parcels': int(underdev_mask.sum()), 'value': float(val[underdev_mask].sum()),
        'pct_of_tax_base': float(val[underdev_mask].sum()) / base_or_1 * 100,
        'land_value': float(land[underdev_mask].sum()),
        'share_of_dollars_changed': float(abschg[underdev_mask].sum()) / abschg_total * 100,
    }
    out['underdeveloped_subtotal_value_usd'] = underdev['value']
    out['underdeveloped_subtotal_pct_of_base'] = underdev['pct_of_tax_base']

    if write:
        city_dir = os.path.join(output_dir, city)
        os.makedirs(city_dir, exist_ok=True)
        pd.DataFrame([out]).to_csv(os.path.join(city_dir, f'metrics_{city}.csv'), index=False)
        _write_markdown(city, model_type, len(df), tax_base, land_base, imp_base, modeled_levy,
                        gross_changed, net_shifted, bucket_rows, underdev,
                        os.path.join(city_dir, 'metrics_summary.md'))
    return out


def _write_markdown(city, model_type, n, tax_base, land_base, imp_base, levy, gross, net,
                    buckets, underdev, path) -> None:
    base = tax_base or 1.0
    levy_or_1 = levy or 1.0
    L = [
        f"# {city.replace('_', ' ').title()} — LVT model metrics\n",
        f"*Model: `{model_type}` · {n:,} modeled parcels (fully-exempt excluded).*\n",
        "## Headline\n",
        "| Metric | Value |", "|---|---|",
        f"| **Full modeled tax base** (taxable land + improvement) | **{_money(tax_base)}** |",
        f"| — of which land | {_money(land_base)} ({land_base / base * 100:.1f}%) |",
        f"| — of which improvements | {_money(imp_base)} ({imp_base / base * 100:.1f}%) |",
        f"| Modeled levy (revenue held neutral) | {_money(levy)} |",
        f"| **Total dollars changed** (Σ\\|new − current\\|, gross) | **{_money(gross)}** |",
        f"| — net dollars shifted (winners ⇄ losers) | {_money(net)} |",
        f"| — gross as % of the modeled levy | **{gross / levy_or_1 * 100:.1f}%** |",
        f"| — net as % of the modeled levy | {net / levy_or_1 * 100:.1f}% |",
        f"| — gross as bps of the tax base | {gross / base * 1e4:.1f} bps |",
        "",
        "## Land use by improvement ratio (value as % of the full modeled tax base)\n",
        "| Bucket | Parcels | Value | % of tax base | Land value | % of $ changed |",
        "|---|---|---|---|---|---|",
    ]
    for b in buckets:
        L.append(f"| {b['label']} | {b['parcels']:,} | {_money(b['value'])} | "
                 f"{b['pct_of_tax_base']:.1f}% | {_money(b['land_value'])} | "
                 f"{b['share_of_dollars_changed']:.1f}% |")
    L.append(f"| **{underdev['label']}** | **{underdev['parcels']:,}** | **{_money(underdev['value'])}** | "
             f"**{underdev['pct_of_tax_base']:.1f}%** | **{_money(underdev['land_value'])}** | "
             f"**{underdev['share_of_dollars_changed']:.1f}%** |")
    L.append("")
    L.append("> *Improvement ratio = taxable improvement ÷ (taxable land + improvement). "
             "\"Vacant\" here = literally 0% improvement (pure land) — slightly narrower than the "
             "chart's \"Vacant Land\" category, which also counts a few nominally-vacant-use parcels "
             "carrying a small structure (those fall in the <10% bucket here). "
             "\"% of $ changed\" = each bucket's share of the gross dollars redistributed.*")
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write("\n".join(L) + "\n")


def rollup_city_metrics(
    reports_dir: str = '../../analysis/reports',
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """Concatenate every city's ``metrics_{city}.csv`` into one cross-city comparison table.

    Parameters
    ----------
    reports_dir : str
        Directory holding the per-city report sub-directories (each with a ``metrics_*.csv``).
    output_path : str, optional
        When given, also write the combined table to this CSV path.

    Returns
    -------
    pandas.DataFrame
        One row per city; empty DataFrame if no metrics files are found.
    """
    paths = sorted(glob.glob(os.path.join(reports_dir, '*', 'metrics_*.csv')))
    frames = [pd.read_csv(p) for p in paths]
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if output_path and not combined.empty:
        combined.to_csv(output_path, index=False)
    return combined
