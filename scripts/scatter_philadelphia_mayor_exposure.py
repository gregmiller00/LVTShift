"""
Philadelphia — Mayor's Political Exposure Under LVT Reform (scatter view)
--------------------------------------------------------------------------
Precinct-level scatter of Mayor Parker's 2023 Democratic primary vote share
vs. the % of Single Family Residential parcels seeing a tax DECREASE under
the LYCD (pre-abatement) split-rate model. Companion to the choropleth in
map_philadelphia_mayor_exposure.py — this is the more rigorous, defensible
version of the same finding (the correlation itself, not just a spatial
impression), useful for a written brief or if the map's story is questioned.

Point of the figure: there is no meaningful relationship between where
Parker ran strongest and whether that precinct's homeowners win or lose
under the reform — the trend line is nearly flat, and her stronghold
(top-quartile vote-share precincts) sits at a median win rate in line
with the citywide median. Her electoral base is not disproportionately
exposed to this reform's losers.

Reuses the data-loading functions from map_philadelphia_mayor_exposure.py
so the two figures are guaranteed to be built from the identical
precinct-level dataset.

Output: analysis/reports/philadelphia_lycd/mayor_political_exposure_scatter.png
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from map_philadelphia_mayor_exposure import (
    load_precinct_boundaries_with_vote_share,
    compute_precinct_sfr_win_rate,
    STRONGHOLD_QUANTILE,
    VARIANT,
    VARIANT_LABEL,
)

OUTPUT_PATH = REPO_ROOT / f"analysis/reports/{VARIANT}/mayor_political_exposure_scatter.png"


def main():
    print("Loading precinct boundaries + Parker vote share...")
    precincts = load_precinct_boundaries_with_vote_share()

    print(f"Computing precinct-level SFR win rate ({VARIANT_LABEL} model)...")
    gdf = compute_precinct_sfr_win_rate(precincts)
    gdf = gdf.dropna(subset=["pct_sfr_decreasing", "parker_share"])
    gdf = gdf[gdf["n_sfr"] >= 10]  # drop precincts with too few SFR parcels for a stable win rate

    x = gdf["parker_share"].astype(float).to_numpy() * 100
    y = gdf["pct_sfr_decreasing"].astype(float).to_numpy()

    r, p = pearsonr(x, y)
    slope, intercept = np.polyfit(x, y, 1)

    stronghold_cutoff = gdf["parker_share"].quantile(STRONGHOLD_QUANTILE) * 100
    stronghold = gdf[gdf["parker_share"] * 100 >= stronghold_cutoff]
    stronghold_median = stronghold["pct_sfr_decreasing"].median()
    citywide_median = gdf["pct_sfr_decreasing"].median()

    fig, ax = plt.subplots(figsize=(9, 7))

    ax.scatter(x, y, s=14, alpha=0.45, color="#3B6FA0", edgecolor="none", label="Precinct (ward division)")

    xs = np.linspace(x.min(), x.max(), 100)
    ax.plot(xs, slope * xs + intercept, color="#B33018", linewidth=2.2,
             label=f"Trend line (r = {r:.2f}, p = {p:.2f})")

    ax.axhline(50, color="black", linewidth=1, linestyle=":", alpha=0.6)
    ax.text(x.min(), 51, "50% — median homeowner breakeven", fontsize=8, va="bottom", ha="left", alpha=0.7)

    ax.axvline(stronghold_cutoff, color="#00A651", linewidth=1.4, linestyle="--", alpha=0.8)
    ax.text(stronghold_cutoff + 0.5, 3, f"Parker stronghold\ncutoff ({stronghold_cutoff:.0f}%+ vote share)",
             fontsize=8, color="#00A651", va="bottom", ha="left")

    ax.set_xlabel("Mayor Parker's vote share in precinct (2023 Democratic primary, 9-candidate field)", fontsize=10)
    ax.set_ylabel(f"% of SFR parcels with a tax decrease ({VARIANT_LABEL} model)", fontsize=10)
    ax.set_title(
        "No relationship between Parker's electoral strength and reform winners/losers\n"
        f"Philadelphia precincts, LVT split-rate reform ({VARIANT_LABEL})",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_ylim(-2, 102)

    ax.legend(loc="lower left", fontsize=9, frameon=True)

    fig.text(
        0.5, 0.01,
        f"Citywide median precinct SFR win rate: {citywide_median:.0f}%   ·   "
        f"Parker stronghold (top-quartile precincts) median: {stronghold_median:.0f}%   ·   "
        f"n = {len(gdf)} precincts",
        fontsize=9,
        va="bottom",
        ha="center",
    )

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    print(f"Saved: {OUTPUT_PATH}")
    print(f"  r = {r:.3f}, p = {p:.3f}")
    print(f"  Stronghold cutoff: {stronghold_cutoff:.1f}% vote share, n={len(stronghold)}")
    print(f"  Stronghold median win rate: {stronghold_median:.1f}%  |  Citywide median: {citywide_median:.1f}%")


if __name__ == "__main__":
    main()
