r"""Generate all chart fragments, tables, and headline macros for the Philadelphia LVT deck.

SINGLE SOURCE OF NUMERICAL CONTENT for Deck.tex. Re-run after any data change:

    C:/Users/druss/miniconda3/python.exe deck/scripts/generate_deck_assets.py

Then rebuild the PDF. Never type a result number into Deck.tex -- add it here as a macro
(\PhlName) or a generated chart/table/figure fragment, regenerate, and reference it.

Reads directly from the repo's already-audited model exports (analysis/data/*.csv) and
political briefs -- nothing here re-derives a number a source file already has authoritative.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deck_helpers import (  # noqa: E402
    Headlines, hbar_chart, kpi_board, save_chart, save_table,
    num, money, pct, ratio, text,
)

DECK = Path(__file__).resolve().parents[1]              # .../philadelphia_lvt_deck/deck
REPO = DECK.parents[3]                                    # C:/projects/LVTShift
DATA_DIR = REPO / "analysis" / "data"
PHL_DATA_DIR = REPO / "cities" / "philadelphia" / "data"
CHARTS = DECK / "charts"
TABLES = DECK / "tables"
FIGURES = DECK / "figures"
for d in (CHARTS, TABLES, FIGURES):
    d.mkdir(parents=True, exist_ok=True)

PREFIX = "Phl"
NORTHEAST_DISTRICTS = [6, 9, 10]


# --------------------------------------------------------------------------- #
# Data loading -- one place, reused by headlines/charts/tables/figures
# --------------------------------------------------------------------------- #
def _load():
    import pandas as pd

    base = pd.read_csv(
        DATA_DIR / "philadelphia_lycd.csv",
        usecols=["parcel_id", "property_category", "current_tax", "new_tax", "tax_change",
                  "tax_change_pct", "taxable_land_value", "taxable_improvement_value",
                  "is_fully_exempt"],
    ).drop_duplicates("parcel_id")

    refined = pd.read_csv(
        DATA_DIR / "philadelphia_lycd_refined_prototype.csv",
        usecols=["parcel_id", "property_category", "current_tax", "new_tax", "tax_change",
                  "tax_change_pct", "is_fully_exempt"],
    ).drop_duplicates("parcel_id")

    post = pd.read_csv(
        DATA_DIR / "philadelphia_lycd_post_abatement.csv",
        usecols=["parcel_id", "current_tax"],
    ).drop_duplicates("parcel_id")

    return base, refined, post


def _district_join(par_ids_and_values, value_col):
    """Spatial-join a (parcel_id, value_col) frame to council districts; return per-district
    median. par_ids_and_values: DataFrame with columns parcel_id, value_col."""
    import geopandas as gpd
    import pandas as pd

    parcels = gpd.read_parquet(PHL_DATA_DIR / "parcels.gpq").drop_duplicates("parcel_number")
    parcels["parcel_id"] = parcels["parcel_number"].astype(str).str.lstrip("0")
    parcels.loc[parcels["parcel_id"] == "", "parcel_id"] = "0"
    parcels["parcel_id"] = parcels["parcel_id"].astype("Int64")

    cd = gpd.read_parquet(PHL_DATA_DIR / "council_districts.gpq")
    cd["DISTRICT"] = cd["DISTRICT"].astype(int)

    merged = parcels.merge(par_ids_and_values, on="parcel_id", how="inner")
    merged = merged.to_crs(cd.crs)
    sj = gpd.sjoin(merged[[value_col, "geometry"]], cd[["DISTRICT", "geometry"]],
                   how="left", predicate="within")
    return sj.groupby("DISTRICT")[value_col].median()


# --------------------------------------------------------------------------- #
# Headline macros
# --------------------------------------------------------------------------- #
def headlines(base, refined, post) -> None:
    import pandas as pd

    H = Headlines(prefix=PREFIX, out_path=TABLES / "headlines.tex")

    # --- Revenue neutrality (both models, by construction) ---
    base_taxable = base[~base["is_fully_exempt"]]
    gap = (base_taxable["new_tax"].sum() - base_taxable["current_tax"].sum())
    H.add("RevenueGapDollars", abs(gap), money)
    H.add("RevenueGapPct", abs(gap) / base_taxable["current_tax"].sum() * 100, lambda x: f"{x:.4f}%")

    # --- Citywide SFR: baseline vs refined ---
    sfr_base = base[base["property_category"] == "Single Family Residential"]
    sfr_refined = refined[refined["property_category"] == "Single Family Residential"]
    H.add("SfrMedianBaseline", sfr_base["tax_change_pct"].median(), pct)
    H.add("SfrMedianRefined", sfr_refined["tax_change_pct"].median(), pct)
    H.add("SfrWinRateBaseline", (sfr_base["tax_change_pct"] < 0).mean() * 100, pct)
    H.add("SfrWinRateRefined", (sfr_refined["tax_change_pct"] < 0).mean() * 100, pct)

    # --- Decile progressivity (top vs bottom decile, refined model shift vs baseline) ---
    m = base.merge(refined, on="parcel_id", suffixes=("_base", "_refined"))
    sfr = m[m["property_category_base"] == "Single Family Residential"].copy()
    sfr["total_value"] = sfr["taxable_land_value"] + sfr["taxable_improvement_value"]
    sfr["decile"] = pd.qcut(sfr["total_value"], 10, labels=False, duplicates="drop")
    dec = sfr.groupby("decile").agg(
        base_chg=("tax_change_pct_base", "median"),
        refined_chg=("tax_change_pct_refined", "median"),
        median_value=("total_value", "median"),
    )
    H.add("DecileTopBaseline", dec.loc[9, "base_chg"], pct)
    H.add("DecileTopRefined", dec.loc[9, "refined_chg"], pct)
    H.add("DecileTopValue", dec.loc[9, "median_value"], money)
    H.add("DecileBottomRefined", dec.loc[0, "refined_chg"], pct)
    H.add("DecileBottomValue", dec.loc[0, "median_value"], money)

    # --- Vacant land (refined model) ---
    vac = refined[refined["property_category"] == "Vacant Land"]
    H.add("VacantLandMedianRefined", vac["tax_change_pct"].median(), pct)
    vac_base = base[base["property_category"] == "Vacant Land"]
    H.add("VacantLandMedianBaseline", vac_base["tax_change_pct"].median(), pct)

    # --- Abatement cliff: currently-abated parcels, actual bill vs same system w/ abatement
    # expired (post-abatement counterfactual). This isolates the STATUS QUO's cliff effect,
    # independent of LVT -- both current_tax columns are pre-reform, current-system bills.
    abated_ids = base.loc[base["property_category"] == "Abated / Construction Exemption", "parcel_id"]
    cliff = base[base["parcel_id"].isin(abated_ids)][["parcel_id", "current_tax"]].rename(
        columns={"current_tax": "cur_actual"})
    cliff = cliff.merge(post.rename(columns={"current_tax": "cur_post_abate"}), on="parcel_id")
    cliff["cliff_pct"] = (cliff["cur_post_abate"] - cliff["cur_actual"]) / cliff["cur_actual"].replace(0, pd.NA) * 100
    H.add("AbatementCliffMedian", cliff["cliff_pct"].median(), pct)
    H.add("AbatedParcelCount", len(abated_ids), num)

    # --- Abated parcels under LVT reform (currently near-zero bill -> full LVT bill) ---
    abated_base = base[base["property_category"] == "Abated / Construction Exemption"]
    H.add("AbatedReformMedian", abated_base["tax_change_pct"].median(), pct)

    # --- Northeast districts: baseline vs refined (SFR median % change) ---
    sfr_base_geo = sfr_base[["parcel_id", "tax_change_pct"]]
    sfr_ref_geo = sfr_refined[["parcel_id", "tax_change_pct"]]
    dist_base = _district_join(sfr_base_geo, "tax_change_pct")
    dist_ref = _district_join(sfr_ref_geo, "tax_change_pct")

    dist_names = {6: "DSix", 9: "DNine", 10: "DTen"}
    for d, label in dist_names.items():
        H.add(f"{label}Baseline", dist_base.loc[d], pct)
        H.add(f"{label}Refined", dist_ref.loc[d], pct)

    citywide_base_median = sfr_base["tax_change_pct"].median()
    citywide_ref_median = sfr_refined["tax_change_pct"].median()
    H.add("CitywideDistrictMedianBaseline", citywide_base_median, pct)
    H.add("CitywideDistrictMedianRefined", citywide_ref_median, pct)

    # Save the full district table (all 10) for the appendix
    all_dist = pd.DataFrame({
        "District": dist_base.index,
        "BaselineMedian": dist_base.values,
        "RefinedMedian": [dist_ref.loc[d] for d in dist_base.index],
    }).sort_values("District")
    all_dist.to_csv(TABLES / "_district_full.csv", index=False)

    H.write()
    print(f"  wrote {H.out_path}")
    return dec  # returned for chart-building reuse


# --------------------------------------------------------------------------- #
# Charts (TikZ fragments)
# --------------------------------------------------------------------------- #
def charts() -> None:
    # KPI board -- "at a glance" -- cards take headline MACROS
    save_chart(CHARTS / "kpis.tex", kpi_board([
        (r"\PhlRevenueGapDollars", "net revenue change (by construction)"),
        (r"\PhlSfrWinRateRefined", "homeowners citywide see a tax cut", "deckfg"),
        (r"\PhlAbatementCliffMedian", "median status-quo abatement cliff", "deckhi"),
    ], cols=3))
    print("  wrote charts/kpis.tex")


# --------------------------------------------------------------------------- #
# Tables (tabularx fragments)
# --------------------------------------------------------------------------- #
def tables() -> None:
    import pandas as pd

    # Northeast district snapshot for slide 10
    ne_rows = []
    names = {6: "District 6 (Lower NE)", 9: "District 9 (Near NE)", 10: "District 10 (Far NE)"}
    dist_full = pd.read_csv(TABLES / "_district_full.csv")
    for d in NORTHEAST_DISTRICTS:
        row = dist_full[dist_full["District"] == d].iloc[0]
        ne_rows.append((names[d], f"{row['BaselineMedian']:.1f}\\%", f"{row['RefinedMedian']:.1f}\\%"))
    df = pd.DataFrame(ne_rows, columns=["District", "Baseline LYCD", "Refined LYCD"])
    save_table(TABLES / "ne_district_table.tex", df, col_format="X r r", escape=False)
    print("  wrote tables/ne_district_table.tex")

    # Full 10-district appendix table
    full_rows = []
    for _, row in dist_full.sort_values("District").iterrows():
        full_rows.append((f"District {int(row['District'])}", f"{row['BaselineMedian']:.1f}\\%",
                           f"{row['RefinedMedian']:.1f}\\%"))
    df_full = pd.DataFrame(full_rows, columns=["District", "Baseline LYCD (median SFR)", "Refined LYCD (median SFR)"])
    save_table(TABLES / "appendix_district_table.tex", df_full, col_format="X r r", escape=False)
    print("  wrote tables/appendix_district_table.tex")


# --------------------------------------------------------------------------- #
# Figures (vector PDFs via matplotlib -- the one case TikZ can't hand-roll)
# --------------------------------------------------------------------------- #
def figure_decile_progressivity(base, refined) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np
    import pandas as pd

    m = base.merge(refined, on="parcel_id", suffixes=("_base", "_refined"))
    sfr = m[m["property_category_base"] == "Single Family Residential"].copy()
    sfr["total_value"] = sfr["taxable_land_value"] + sfr["taxable_improvement_value"]
    sfr["decile"] = pd.qcut(sfr["total_value"], 10, labels=False, duplicates="drop")
    tab = sfr.groupby("decile").agg(
        median_value=("total_value", "median"),
        base_chg=("tax_change_pct_base", "median"),
        refined_chg=("tax_change_pct_refined", "median"),
    ).reset_index()

    color_base, color_refined = "#5B7682", "#0E7C86"  # deckmuted, deckfg

    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    x = np.arange(len(tab))
    width = 0.38
    b1 = ax.bar(x - width / 2, tab["base_chg"], width, label="Baseline LYCD (flat 20% land share)",
                color=color_base, edgecolor="white", linewidth=0.5)
    b2 = ax.bar(x + width / 2, tab["refined_chg"], width, label="Refined (FHFA land share + stratified pricing)",
                color=color_refined, edgecolor="white", linewidth=0.5)
    ax.axhline(0, color="#333333", linewidth=1)
    ax.set_ylabel("Median SFR tax change (%)", fontsize=11)
    ax.set_xlabel("Home value decile (0 = cheapest, 9 = priciest)", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([f"D{int(r.decile)}\n${r.median_value/1000:,.0f}K" for r in tab.itertuples()], fontsize=8.5)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100, decimals=0))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dddddd", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            va = "bottom" if h >= 0 else "top"
            offset = 0.6 if h >= 0 else -0.6
            ax.text(bar.get_x() + bar.get_width() / 2, h + offset, f"{h:+.0f}%",
                     ha="center", va=va, fontsize=7, color="#333333")
    ax.legend(loc="lower left", fontsize=8.5, frameon=True)
    fig.tight_layout()

    out = FIGURES / "decile_progressivity.pdf"
    fig.savefig(out, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"  wrote {out}")


def figure_fhfa_land_price() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import geopandas as gpd
    import pandas as pd

    fhfa_csv = PHL_DATA_DIR / "fhfa_land_share_by_tract.csv"
    tracts_path = PHL_DATA_DIR / "census_tracts.gpq"
    if not fhfa_csv.exists() or not tracts_path.exists():
        print("  SKIPPED fhfa_land_price figure (missing cached fhfa_land_share_by_tract.csv "
              "or census_tracts.gpq -- run scripts/map_philadelphia_fhfa_land_price.py's data "
              "prep first)")
        return

    # Reconstruct $/sqft from the audit's cached FHFA land-price workbook if present, else
    # fall back to plotting land SHARE (still sourced, just a different FHFA column).
    land_price_xlsx = None
    for cand in Path.home().glob("AppData/Local/Temp/claude/**/land_prices_2024.xlsx"):
        land_price_xlsx = cand
        break

    tracts = gpd.read_parquet(tracts_path)
    if land_price_xlsx and land_price_xlsx.exists():
        x = pd.read_excel(land_price_xlsx, sheet_name="Cross-Section Census Tracts", header=1)
        phl = x[(x["State"] == "Pennsylvania") & (x["County"] == "Philadelphia County")].copy()
        phl["tract_geoid"] = phl["Census Tract"].astype("int64").astype(str).str.zfill(11)
        phl["value"] = phl["Land Value\n(Per Acre, As-Is)"] / 43_560
        label = "Single-family land price ($/sqft)"
    else:
        phl = pd.read_csv(fhfa_csv, dtype={"tract_geoid": str})
        phl["value"] = phl["fhfa_land_share"] * 100
        label = "Single-family land share of value (%)"

    gdf = tracts.merge(phl[["tract_geoid", "value"]], on="tract_geoid", how="left")
    gdf = gdf.to_crs("EPSG:3857")

    cmap = matplotlib.colormaps.get_cmap("YlOrRd")
    vals = gdf["value"].dropna()
    norm = mcolors.Normalize(vmin=vals.quantile(0.02), vmax=vals.quantile(0.98))

    fig, ax = plt.subplots(figsize=(6.4, 7.0))
    gdf.plot(column="value", cmap=cmap, norm=norm, linewidth=0.2, edgecolor="white", ax=ax,
              missing_kwds={"color": "#e5e5e5", "hatch": "///", "edgecolor": "#bbbbbb", "linewidth": 0.2})
    ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02, shrink=0.65)
    cbar.set_label(label, fontsize=8)
    fig.tight_layout(pad=0.3)

    out = FIGURES / "fhfa_land_price.pdf"
    fig.savefig(out, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"  wrote {out}")


def figures(base, refined) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    figure_decile_progressivity(base, refined)
    figure_fhfa_land_price()


# --------------------------------------------------------------------------- #
def main() -> None:
    base, refined, post = _load()
    headlines(base, refined, post)
    charts()
    tables()
    figures(base, refined)
    print("Assets generated. Inspect them, THEN compose/refresh the slides.")


if __name__ == "__main__":
    main()
