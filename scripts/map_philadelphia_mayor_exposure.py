"""
Philadelphia — Mayor's Political Exposure Under LVT Reform
------------------------------------------------------------
Precinct-level choropleth of the % of Single Family Residential parcels
seeing a tax DECREASE under the LYCD (pre-abatement) split-rate model,
with Mayor Parker's 2023 Democratic primary electoral stronghold (top
quartile of her vote share) outlined, and the three Northeast-adjacent
council districts (6, 9, 10) outlined separately.

Point of the figure: Northeast Philadelphia (districts 6/9/10) shows the
weakest SFR win rates in the city, but Parker's own electoral stronghold
sits mostly in strongly-winning territory rather than in the Northeast —
her personal political exposure to this reform is limited even though the
Northeast, as a whole, benefits least.

Data sources (all pre-cached under cities/philadelphia/data/):
  - parcels.gpq                              parcel geometry + assessed values
  - analysis/data/philadelphia_lycd.csv       LYCD pre-abatement model export
  - elections/political_ward_divisions.geojson  1,703 ward-division precincts (OpenDataPhilly)
  - elections/2023_Primary_Results.xlsx       Philadelphia City Commissioners' official returns
  - council_districts.gpq                    council district boundaries

Output: analysis/reports/philadelphia_lycd/mayor_political_exposure_map.png
"""

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import numpy as np
import openpyxl
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

DATA_DIR = REPO_ROOT / "cities/philadelphia/data"
ELECTIONS_DIR = DATA_DIR / "elections"

NORTHEAST_DISTRICTS = [6, 9, 10]
STRONGHOLD_QUANTILE = 0.75  # top-quartile vote-share precincts = Parker's stronghold

# Model variant to use — pass as argv[1], defaults to LYCD pre-abatement
VARIANT_LABELS = {
    "philadelphia_lycd": "LYCD pre-abatement",
    "philadelphia_lycd_post_abatement": "LYCD post-abatement",
    "philadelphia": "OPA pre-abatement",
    "philadelphia_post_abatement": "OPA post-abatement",
}
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "philadelphia_lycd"
VARIANT_LABEL = VARIANT_LABELS.get(VARIANT, VARIANT)
MODEL_CSV = REPO_ROOT / f"analysis/data/{VARIANT}.csv"
OUTPUT_PATH = REPO_ROOT / f"analysis/reports/{VARIANT}/mayor_political_exposure_map.png"


def load_parker_vote_share() -> pd.DataFrame:
    wb = openpyxl.load_workbook(ELECTIONS_DIR / "2023_Primary_Results.xlsx", read_only=True)
    ws = wb["Totals"]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    df = pd.DataFrame(rows[1:], columns=header)

    mayor_dem_cols = [c for c in df.columns if c and "MAYOR" in str(c).upper() and "DEM" in str(c).upper()]
    df[mayor_dem_cols] = df[mayor_dem_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    df["mayor_dem_total"] = df[mayor_dem_cols].sum(axis=1)
    df["parker_votes"] = df["MAYOR \nDEM - CHERELLE L PARKER"]
    df["parker_share"] = df["parker_votes"] / df["mayor_dem_total"].replace(0, pd.NA)
    return df[["PRECINCT NAME", "parker_share"]]


def load_precinct_boundaries_with_vote_share() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(ELECTIONS_DIR / "political_ward_divisions.geojson")
    gdf["precinct_name"] = gdf["DIVISION_NUM"].str[:2] + "-" + gdf["SHORT_DIV_NUM"].str.zfill(2)
    vote_share = load_parker_vote_share()
    merged = gdf.merge(vote_share, left_on="precinct_name", right_on="PRECINCT NAME", how="left")
    return merged[["precinct_name", "parker_share", "geometry"]]


def compute_precinct_sfr_win_rate(precincts: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    parcels = gpd.read_parquet(DATA_DIR / "parcels.gpq")
    parcels["parcel_id"] = parcels["parcel_number"].astype(str).str.lstrip("0")
    parcels.loc[parcels["parcel_id"] == "", "parcel_id"] = "0"
    parcels["parcel_id"] = parcels["parcel_id"].astype("Int64")

    model_df = pd.read_csv(MODEL_CSV)
    sfr = model_df[model_df["property_category"] == "Single Family Residential"][["parcel_id", "tax_change_pct"]]

    parcels_sfr = parcels.merge(sfr, on="parcel_id", how="inner")
    parcels_sfr["centroid"] = parcels_sfr.geometry.centroid
    cent = gpd.GeoDataFrame(
        parcels_sfr[["parcel_id", "tax_change_pct", "centroid"]], geometry="centroid", crs=parcels_sfr.crs
    ).to_crs(precincts.crs)

    joined = gpd.sjoin(cent, precincts, how="left", predicate="within")

    stats = (
        joined.groupby("precinct_name")
        .agg(
            n_sfr=("tax_change_pct", "size"),
            pct_sfr_decreasing=("tax_change_pct", lambda x: (x < 0).mean() * 100),
        )
        .reset_index()
    )
    return precincts.merge(stats, on="precinct_name", how="left")


def load_council_districts() -> gpd.GeoDataFrame:
    gdf = gpd.read_parquet(DATA_DIR / "council_districts.gpq")
    gdf["DISTRICT"] = gdf["DISTRICT"].astype(int)
    return gdf.to_crs("EPSG:4326")


def main():
    print("Loading precinct boundaries + Parker vote share...")
    precincts = load_precinct_boundaries_with_vote_share()

    print(f"Computing precinct-level SFR win rate ({VARIANT_LABEL} model)...")
    gdf = compute_precinct_sfr_win_rate(precincts)
    gdf = gdf.dropna(subset=["pct_sfr_decreasing"])

    stronghold_cutoff = gdf["parker_share"].quantile(STRONGHOLD_QUANTILE)
    stronghold = gdf[gdf["parker_share"] >= stronghold_cutoff]
    print(f"  Parker stronghold cutoff (top quartile vote share): {stronghold_cutoff:.1%}")
    print(f"  Stronghold precincts: {len(stronghold)} of {len(gdf)}")
    print(f"  Stronghold median SFR win rate: {stronghold['pct_sfr_decreasing'].median():.1f}%")
    print(f"  Citywide median SFR win rate:   {gdf['pct_sfr_decreasing'].median():.1f}%")

    districts = load_council_districts()
    ne_districts = districts[districts["DISTRICT"].isin(NORTHEAST_DISTRICTS)]

    # Project everything to a metric CRS for clean plotting
    gdf_plot = gdf.to_crs("EPSG:3857")
    stronghold_plot = stronghold.to_crs("EPSG:3857")
    districts_plot = districts.to_crs("EPSG:3857")
    ne_plot = ne_districts.to_crs("EPSG:3857")

    # Diverging colormap centered at 50% (the "does the median homeowner win?" threshold)
    cmap = matplotlib.colormaps.get_cmap("RdBu")
    norm = mcolors.TwoSlopeNorm(vmin=0, vcenter=50, vmax=100)

    fig, ax = plt.subplots(figsize=(10, 11))

    gdf_plot.plot(
        column="pct_sfr_decreasing",
        cmap=cmap,
        norm=norm,
        linewidth=0.05,
        edgecolor="white",
        ax=ax,
    )

    # All council district boundaries, faint
    districts_plot.boundary.plot(ax=ax, color="black", linewidth=0.6, alpha=0.5)

    # Northeast districts (6, 9, 10) — bold dashed outline
    ne_plot.boundary.plot(ax=ax, color="#222222", linewidth=2.4, linestyle=(0, (5, 3)))

    # Parker's electoral stronghold — bold solid outline (dissolve to one boundary)
    stronghold_union = gpd.GeoDataFrame(geometry=[stronghold_plot.union_all()], crs=stronghold_plot.crs)
    stronghold_union.boundary.plot(ax=ax, color="#00A651", linewidth=2.2, linestyle="-")

    # Label council districts at centroid
    for _, row in districts_plot.iterrows():
        c = row.geometry.centroid
        ax.annotate(
            str(row["DISTRICT"]),
            xy=(c.x, c.y),
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="black",
            alpha=0.75,
        )

    ax.set_axis_off()

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.02, shrink=0.7)
    cbar.set_label(f"% of SFR parcels with a tax DECREASE\n(precinct level, {VARIANT_LABEL} model)", fontsize=9)

    legend_handles = [
        mpatches.Patch(facecolor="none", edgecolor="#222222", linewidth=2.4, linestyle=(0, (5, 3)),
                       label="Northeast council districts (6, 9, 10)"),
        mpatches.Patch(facecolor="none", edgecolor="#00A651", linewidth=2.2,
                       label=f"Mayor Parker's 2023 primary stronghold\n(top-quartile vote-share precincts, ≥{stronghold_cutoff:.0%} vote share)"),
    ]
    ax.legend(handles=legend_handles, loc="upper left", fontsize=8, frameon=True, framealpha=0.9)

    ax.set_title(
        f"Philadelphia LVT reform ({VARIANT_LABEL}) — where the Mayor's political base sits\n"
        f"relative to the reform's homeowner winners and losers",
        fontsize=13,
        fontweight="bold",
    )
    fig.text(
        0.5, 0.015,
        f"Blue = majority of homeowners win (tax decrease) · Red = majority lose · white = 50/50\n"
        f"Citywide median precinct SFR win rate: {gdf['pct_sfr_decreasing'].median():.0f}%   ·   "
        f"Parker stronghold median: {stronghold['pct_sfr_decreasing'].median():.0f}%",
        fontsize=9,
        va="bottom",
        ha="center",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
