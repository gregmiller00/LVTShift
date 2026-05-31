"""
Cross-city LVT analysis figures.
Run from analysis/: python cross_city_figures.py
Saves figures to analysis/figures/cross_city/
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path("..").resolve()))
from lvt.style import apply_lvt_style, INCREASE_COLOR, DECREASE_COLOR

apply_lvt_style()

OUT_DIR = Path("figures/cross_city")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Load data — exclude Philadelphia variants for city-level charts,
# but include the primary Philadelphia model for comparison.
# ---------------------------------------------------------------------------
dfs = []
for csv_path in sorted(Path("data").glob("*.csv")):
    if csv_path.name == ".gitkeep":
        continue
    df = pd.read_csv(csv_path)
    dfs.append(df)

all_cities = pd.concat(dfs, ignore_index=True)

# Primary set: one row per city (exclude Philly variants)
PHILLY_VARIANTS = {"philadelphia_lycd", "philadelphia_lycd_post_abatement", "philadelphia_post_abatement"}
primary = all_cities[~all_cities["city"].isin(PHILLY_VARIANTS)].copy()
cities_sorted_alpha = sorted(primary["city"].unique())

CITY_LABELS = {
    "baltimore": "Baltimore",
    "bellingham": "Bellingham",
    "bryan": "Bryan",
    "charlottesville": "Charlottesville",
    "cleveland": "Cleveland",
    "college_station": "College Station",
    "fort_collins": "Fort Collins",
    "greeley": "Greeley",
    "highlands_ranch": "Highlands Ranch",
    "philadelphia": "Philadelphia",
    "pueblo": "Pueblo",
    "rochester": "Rochester",
    "southbend": "South Bend",
    "st_paul": "St. Paul",
    "syracuse": "Syracuse",
}


def label(city):
    return CITY_LABELS.get(city, city.replace("_", " ").title())


# ---------------------------------------------------------------------------
# Figure 1: Tax change direction by city
# Sorted horizontal bars: % going up (red, right) vs % going down (blue, left)
# Dot overlay for median SFR % change
# ---------------------------------------------------------------------------
taxable = primary[primary["current_tax"] > 0].copy()

direction = (
    taxable.groupby("city")
    .agg(
        pct_increase=("tax_change", lambda x: (x > 0).mean() * 100),
        pct_decrease=("tax_change", lambda x: (x < 0).mean() * 100),
        median_change=("tax_change_pct", "median"),
        n=("tax_change", "count"),
    )
    .reset_index()
    .sort_values("pct_increase")
)

fig, ax = plt.subplots(figsize=(11, 7))
y = np.arange(len(direction))

ax.barh(y, direction["pct_increase"], color=INCREASE_COLOR, alpha=0.85, label="% parcels increasing")
ax.barh(y, -direction["pct_decrease"], color=DECREASE_COLOR, alpha=0.85, label="% parcels decreasing")
ax.axvline(0, color="black", linewidth=0.8)

ax.set_yticks(y)
ax.set_yticklabels([label(c) for c in direction["city"]], fontsize=11)
ax.set_xlabel("Share of taxable parcels (%)", fontsize=11)
ax.set_title("4:1 Split-Rate LVT: Share of Parcels Paying More vs. Less", fontsize=13, fontweight="bold", pad=12)

# Label the bars
for i, row in enumerate(direction.itertuples()):
    ax.text(row.pct_increase + 0.8, i, f"{row.pct_increase:.0f}%", va="center", fontsize=8.5, color=INCREASE_COLOR)
    ax.text(-row.pct_decrease - 0.8, i, f"{row.pct_decrease:.0f}%", va="center", ha="right", fontsize=8.5, color=DECREASE_COLOR)

ax.legend(loc="lower right", fontsize=10)
ax.set_xlim(-105, 105)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

plt.tight_layout()
plt.savefig(OUT_DIR / "1_tax_direction.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: 1_tax_direction.png")


# ---------------------------------------------------------------------------
# Figure 2: Property category heatmap — median % change, city × category
# ---------------------------------------------------------------------------
FOCUS_CATS = [
    "Single Family Residential",
    "Small Multi-Family (2-4 units)",
    "Large Multi-Family (5+ units)",
    "Commercial",
    "Vacant Land",
]

cat_pivot = (
    taxable[taxable["property_category"].isin(FOCUS_CATS)]
    .groupby(["city", "property_category"])["tax_change_pct"]
    .median()
    .unstack("property_category")
    .reindex(columns=FOCUS_CATS)
)
# Sort cities by SFR median change
cat_pivot = cat_pivot.sort_values("Single Family Residential", ascending=True)

CAT_LABELS = {
    "Single Family Residential": "Single\nFamily",
    "Small Multi-Family (2-4 units)": "Small\nMulti-Family",
    "Large Multi-Family (5+ units)": "Large\nMulti-Family",
    "Commercial": "Commercial",
    "Vacant Land": "Vacant\nLand",
}

fig, ax = plt.subplots(figsize=(10, 8))
vals = cat_pivot.values.astype(float)
vmax = 80
norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
im = ax.imshow(vals, cmap="RdYlGn_r", norm=norm, aspect="auto")

ax.set_xticks(range(len(FOCUS_CATS)))
ax.set_xticklabels([CAT_LABELS[c] for c in FOCUS_CATS], fontsize=11)
ax.set_yticks(range(len(cat_pivot)))
ax.set_yticklabels([label(c) for c in cat_pivot.index], fontsize=11)
ax.set_title("Median Tax Change (%) by Property Category\n4:1 Split-Rate LVT", fontsize=13, fontweight="bold", pad=12)

for i in range(vals.shape[0]):
    for j in range(vals.shape[1]):
        v = vals[i, j]
        if not np.isnan(v):
            txt = f"{v:+.0f}%"
            brightness = norm(v)
            color = "white" if abs(brightness - 0.5) > 0.25 else "black"
            ax.text(j, i, txt, ha="center", va="center", fontsize=9.5, fontweight="bold", color=color)
        else:
            ax.text(j, i, "—", ha="center", va="center", fontsize=9, color="#aaaaaa")

cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cbar.set_label("Median tax change (%)", fontsize=10)
plt.tight_layout()
plt.savefig(OUT_DIR / "2_category_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: 2_category_heatmap.png")


# ---------------------------------------------------------------------------
# Figure 3: Income quintile equity heatmap
# ---------------------------------------------------------------------------
with_income = primary[
    primary["median_income"].notna()
    & (primary["current_tax"] > 0)
].copy()

with_income["income_quintile"] = with_income.groupby("city")["median_income"].transform(
    lambda x: pd.qcut(x, 5, labels=["Q1\n(lowest)", "Q2", "Q3", "Q4", "Q5\n(highest)"], duplicates="drop")
)

income_pivot = (
    with_income.groupby(["city", "income_quintile"])["tax_change_pct"]
    .median()
    .unstack("income_quintile")
)
# Sort by regressive-to-progressive: difference between Q1 and Q5
income_pivot = income_pivot.loc[income_pivot.index.isin(cat_pivot.index)]
q_cols = ["Q1\n(lowest)", "Q2", "Q3", "Q4", "Q5\n(highest)"]
income_pivot = income_pivot.reindex(columns=q_cols)
income_pivot["_slope"] = income_pivot.get("Q5\n(highest)", 0) - income_pivot.get("Q1\n(lowest)", 0)
income_pivot = income_pivot.sort_values("_slope", ascending=False).drop(columns=["_slope"])

fig, ax = plt.subplots(figsize=(9, 8))
vals = income_pivot.values.astype(float)
abs_max = np.nanpercentile(np.abs(vals[~np.isnan(vals)]), 95)
norm = mcolors.TwoSlopeNorm(vmin=-abs_max, vcenter=0, vmax=abs_max)
im = ax.imshow(vals, cmap="RdYlGn_r", norm=norm, aspect="auto")

ax.set_xticks(range(len(q_cols)))
ax.set_xticklabels(q_cols, fontsize=11)
ax.set_yticks(range(len(income_pivot)))
ax.set_yticklabels([label(c) for c in income_pivot.index], fontsize=11)
ax.set_title("Median Tax Change (%) by Neighborhood Income Quintile\n4:1 Split-Rate LVT  ·  Q1 = Lowest Income", fontsize=12, fontweight="bold", pad=12)

for i in range(vals.shape[0]):
    for j in range(vals.shape[1]):
        v = vals[i, j]
        if not np.isnan(v):
            brightness = norm(v)
            color = "white" if abs(brightness - 0.5) > 0.25 else "black"
            ax.text(j, i, f"{v:+.1f}%", ha="center", va="center", fontsize=9.5, fontweight="bold", color=color)

cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cbar.set_label("Median tax change (%)", fontsize=10)
ax.set_xlabel("← More progressive          More regressive →", fontsize=9, color="#666666", labelpad=6)
plt.tight_layout()
plt.savefig(OUT_DIR / "3_income_quintile_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: 3_income_quintile_heatmap.png")


# ---------------------------------------------------------------------------
# Figure 4: Minority quintile equity heatmap
# ---------------------------------------------------------------------------
with_minority = primary[
    primary["minority_pct"].notna()
    & (primary["current_tax"] > 0)
].copy()

with_minority["minority_quintile"] = with_minority.groupby("city")["minority_pct"].transform(
    lambda x: pd.qcut(x, 5, labels=["Q1\n(least)", "Q2", "Q3", "Q4", "Q5\n(most)"], duplicates="drop")
)

min_pivot = (
    with_minority.groupby(["city", "minority_quintile"])["tax_change_pct"]
    .median()
    .unstack("minority_quintile")
)
mq_cols = ["Q1\n(least)", "Q2", "Q3", "Q4", "Q5\n(most)"]
min_pivot = min_pivot.reindex(columns=mq_cols)
min_pivot["_slope"] = min_pivot.get("Q5\n(most)", 0) - min_pivot.get("Q1\n(least)", 0)
min_pivot = min_pivot.sort_values("_slope").drop(columns=["_slope"])

fig, ax = plt.subplots(figsize=(9, 8))
vals = min_pivot.values.astype(float)
abs_max = np.nanpercentile(np.abs(vals[~np.isnan(vals)]), 95)
norm = mcolors.TwoSlopeNorm(vmin=-abs_max, vcenter=0, vmax=abs_max)
im = ax.imshow(vals, cmap="RdYlGn_r", norm=norm, aspect="auto")

ax.set_xticks(range(len(mq_cols)))
ax.set_xticklabels(mq_cols, fontsize=11)
ax.set_yticks(range(len(min_pivot)))
ax.set_yticklabels([label(c) for c in min_pivot.index], fontsize=11)
ax.set_title("Median Tax Change (%) by Neighborhood Minority-Share Quintile\n4:1 Split-Rate LVT  ·  Q1 = Least Minority", fontsize=12, fontweight="bold", pad=12)

for i in range(vals.shape[0]):
    for j in range(vals.shape[1]):
        v = vals[i, j]
        if not np.isnan(v):
            brightness = norm(v)
            color = "white" if abs(brightness - 0.5) > 0.25 else "black"
            ax.text(j, i, f"{v:+.1f}%", ha="center", va="center", fontsize=9.5, fontweight="bold", color=color)

cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cbar.set_label("Median tax change (%)", fontsize=10)
ax.set_xlabel("← More progressive (minority areas benefit)       More regressive →", fontsize=9, color="#666666", labelpad=6)
plt.tight_layout()
plt.savefig(OUT_DIR / "4_minority_quintile_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: 4_minority_quintile_heatmap.png")


# ---------------------------------------------------------------------------
# Table 1: City summary statistics — saved as CSV
# ---------------------------------------------------------------------------
sfr_median = (
    taxable[taxable["property_category"] == "Single Family Residential"]
    .groupby("city")["tax_change_pct"]
    .median()
    .rename("sfr_median_change_pct")
)

vacant_median = (
    taxable[taxable["property_category"] == "Vacant Land"]
    .groupby("city")["tax_change_pct"]
    .median()
    .rename("vacant_median_change_pct")
)

summary = (
    taxable.groupby("city")
    .agg(
        parcels=("current_tax", "count"),
        current_revenue_M=("current_tax", lambda x: x.sum() / 1e6),
        pct_increasing=("tax_change", lambda x: (x > 0).mean() * 100),
        pct_decreasing=("tax_change", lambda x: (x < 0).mean() * 100),
        median_all_pct=("tax_change_pct", "median"),
    )
    .join(sfr_median)
    .join(vacant_median)
    .reset_index()
)

# Add land and improvement millage from CSV metadata
meta = (
    primary.groupby("city")[["land_millage", "improvement_millage"]]
    .first()
    .reset_index()
)
summary = summary.merge(meta, on="city")
summary["city_label"] = summary["city"].map(label)
summary = summary.sort_values("pct_increasing")

col_order = [
    "city_label", "parcels", "current_revenue_M",
    "pct_increasing", "pct_decreasing", "median_all_pct",
    "sfr_median_change_pct", "vacant_median_change_pct",
    "land_millage", "improvement_millage",
]
display_names = {
    "city_label": "City",
    "parcels": "Taxable Parcels",
    "current_revenue_M": "Current Revenue ($M)",
    "pct_increasing": "% Parcels Increasing",
    "pct_decreasing": "% Parcels Decreasing",
    "median_all_pct": "Median Tax Change (%)",
    "sfr_median_change_pct": "Median SFR Change (%)",
    "vacant_median_change_pct": "Median Vacant Land Change (%)",
    "land_millage": "Land Millage",
    "improvement_millage": "Improvement Millage",
}
out_table = summary[col_order].rename(columns=display_names)
for col in ["Current Revenue ($M)", "Median Tax Change (%)", "Median SFR Change (%)",
            "Median Vacant Land Change (%)", "Land Millage", "Improvement Millage"]:
    if col in out_table.columns:
        out_table[col] = out_table[col].round(1)
for col in ["% Parcels Increasing", "% Parcels Decreasing"]:
    out_table[col] = out_table[col].round(1)

out_table.to_csv(OUT_DIR / "city_summary_table.csv", index=False)
print("Saved: city_summary_table.csv")
print()
print(out_table.to_string(index=False))

print(f"\nAll figures saved to {OUT_DIR.resolve()}")
