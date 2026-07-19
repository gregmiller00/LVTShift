"""
Philadelphia — SFR progressivity, baseline LYCD vs. refined LYCD prototype
------------------------------------------------------------------------------
Grouped bar chart: median SFR tax change % by home-value decile, comparing the
baseline LYCD model (flat 20% land share, pooled zone pricing) against the
refined prototype (FHFA tract land share for core residential + category-
stratified zone pricing). See
cities/philadelphia/model_lycd_refined_prototype.ipynb and the chat discussion
this chart came out of for the full methodology.

The point of the figure: the citywide SFR median looks *worse* under the
refinement (smaller aggregate cut), but that hides the real story — expensive
homes (which were getting an oversized cut because their true land share is
higher than the flat 20% assumption) lose most of their windfall, while cheap
and modest homes are barely affected. This is the progressivity argument for
using better land-value data, and it does not show up in the aggregate median.

Output: analysis/reports/philadelphia_lycd_refined_prototype/sfr_decile_progressivity.png
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

OUTPUT_PATH = REPO_ROOT / "analysis/reports/philadelphia_lycd_refined_prototype/sfr_decile_progressivity.png"

# Categorical pair, fixed assignment (not cycled): baseline = blue, refined = orange
COLOR_BASELINE = "#4C72B0"
COLOR_REFINED = "#DD8452"


def main():
    print("Loading baseline and refined LYCD exports...")
    base = pd.read_csv(
        REPO_ROOT / "analysis/data/philadelphia_lycd.csv",
        usecols=["parcel_id", "property_category", "tax_change_pct", "taxable_land_value", "taxable_improvement_value"],
    ).drop_duplicates("parcel_id")
    refined = pd.read_csv(
        REPO_ROOT / "analysis/data/philadelphia_lycd_refined_prototype.csv",
        usecols=["parcel_id", "property_category", "tax_change_pct"],
    ).drop_duplicates("parcel_id")

    m = base.merge(refined, on="parcel_id", suffixes=("_base", "_refined"))
    sfr = m[m["property_category_base"] == "Single Family Residential"].copy()
    sfr["total_value"] = sfr["taxable_land_value"] + sfr["taxable_improvement_value"]
    sfr["decile"] = pd.qcut(sfr["total_value"], 10, labels=False, duplicates="drop")

    tab = sfr.groupby("decile").agg(
        n=("parcel_id", "size"),
        value_lo=("total_value", "min"),
        value_hi=("total_value", "max"),
        median_value=("total_value", "median"),
        base_chg=("tax_change_pct_base", "median"),
        refined_chg=("tax_change_pct_refined", "median"),
    ).reset_index()
    print(tab.to_string(index=False))

    fig, ax = plt.subplots(figsize=(11, 6.5))

    x = np.arange(len(tab))
    width = 0.38

    b1 = ax.bar(x - width / 2, tab["base_chg"], width, label="Baseline LYCD (flat 20% land share)",
                color=COLOR_BASELINE, edgecolor="white", linewidth=0.5)
    b2 = ax.bar(x + width / 2, tab["refined_chg"], width, label="Refined prototype (FHFA land share + stratified pricing)",
                color=COLOR_REFINED, edgecolor="white", linewidth=0.5)

    ax.axhline(0, color="#333333", linewidth=1)
    ax.set_ylabel("Median SFR tax change (%)", fontsize=11)
    ax.set_xlabel("Home value decile (0 = cheapest, 9 = priciest)", fontsize=11)
    ax.set_xticks(x)
    xlabels = [f"D{int(r.decile)}\n${r.median_value/1000:,.0f}K" for r in tab.itertuples()]
    ax.set_xticklabels(xlabels, fontsize=9)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100, decimals=0))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dddddd", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)

    # Direct value labels on each bar
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            va = "bottom" if h >= 0 else "top"
            offset = 0.6 if h >= 0 else -0.6
            ax.text(bar.get_x() + bar.get_width() / 2, h + offset, f"{h:+.0f}%",
                     ha="center", va=va, fontsize=7.5, color="#333333")

    ax.legend(loc="lower left", fontsize=9.5, frameon=True)

    ax.set_title(
        "Correcting a flat 20% land-share assumption is progressive within homeowners\n"
        "Philadelphia Single Family Residential, median tax change by home-value decile",
        fontsize=13, fontweight="bold",
    )

    fig.text(
        0.5, 0.005,
        "Expensive homes (D8–D9) lose most of an oversized cut driven by underpriced land; cheap and modest homes (D0–D2) are essentially unaffected.\n"
        "Citywide SFR median looks smaller under the refinement (−23.0% → −18.3%) — that number alone hides this decile-level pattern.",
        fontsize=8.5, va="bottom", ha="center", color="#444444",
    )

    fig.tight_layout(rect=[0, 0.035, 1, 1])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
