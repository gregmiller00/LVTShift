"""
Philadelphia — LYCD land price per square foot by census tract
-----------------------------------------------------------------
Choropleth of single-family residential land value ($/sqft) implied by our
own LYCD model (GMA zone-median $/sqft x 20% land share), for direct visual
comparison against the FHFA external-benchmark map
(map_philadelphia_fhfa_land_price.py / fhfa_land_price_per_sqft.png).

Same methodology as the FHFA map for apples-to-apples comparison: Single
Family Residential parcels only, land value / lot area (sqft), aggregated
to the tract median. Uses the LYCD pre-abatement export
(analysis/data/philadelphia_lycd.csv), spatially joined to parcel geometry
(cities/philadelphia/data/parcels.gpq) and lot area
(parcel_areas_by_pin.parquet, joined on `pin`).

See analysis/political/philadelphia_mayor_exposure_audit.md (Link 2) for the
LYCD-vs-FHFA-vs-OPA adjudication this pair of maps illustrates.

Output: analysis/reports/philadelphia_lycd/lycd_land_price_per_sqft.png
"""

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

DATA_DIR = REPO_ROOT / "cities/philadelphia/data"
TRACTS_PATH = DATA_DIR / "census_tracts.gpq"
OUTPUT_PATH = REPO_ROOT / "analysis/reports/philadelphia_lycd/lycd_land_price_per_sqft.png"


def load_sfr_land_price_per_parcel() -> gpd.GeoDataFrame:
    parcels = gpd.read_parquet(DATA_DIR / "parcels.gpq").drop_duplicates("parcel_number")
    parcels["parcel_id"] = parcels["parcel_number"].astype(str).str.lstrip("0")
    parcels.loc[parcels["parcel_id"] == "", "parcel_id"] = "0"
    parcels["parcel_id"] = parcels["parcel_id"].astype("Int64")

    areas = pd.read_parquet(DATA_DIR / "parcel_areas_by_pin.parquet")
    areas["pin"] = pd.to_numeric(areas["pin"], errors="coerce").astype("Int64")
    parcels["pin"] = pd.to_numeric(parcels["pin"], errors="coerce").astype("Int64")
    parcels = parcels.merge(areas, on="pin", how="left")

    model = pd.read_csv(
        REPO_ROOT / "analysis/data/philadelphia_lycd.csv",
        usecols=["parcel_id", "property_category", "taxable_land_value"],
    ).drop_duplicates("parcel_id")
    sfr = model[model["property_category"] == "Single Family Residential"]

    gdf = parcels.merge(sfr, on="parcel_id", how="inner")
    gdf = gdf[gdf["pin_area_sqft"].notna() & (gdf["pin_area_sqft"] > 0)]
    gdf["land_price_psf"] = gdf["taxable_land_value"] / gdf["pin_area_sqft"]
    # Drop implausible outliers (sliver lots, data artifacts) — same spirit as the FHFA map's
    # 2nd/98th percentile color clamp, but here applied to the underlying per-parcel figure
    # before tract aggregation so a handful of bad parcels can't skew a tract median.
    lo, hi = gdf["land_price_psf"].quantile([0.01, 0.99])
    gdf = gdf[(gdf["land_price_psf"] >= lo) & (gdf["land_price_psf"] <= hi)]
    return gdf


def main():
    print("Loading LYCD SFR land values + lot areas...")
    gdf = load_sfr_land_price_per_parcel()
    print(f"  {len(gdf):,} SFR parcels with land price computed")

    print("Loading census tract boundaries...")
    tracts = gpd.read_parquet(TRACTS_PATH)

    gdf_proj = gdf.to_crs("EPSG:2272")
    cent = gpd.GeoDataFrame(
        gdf[["land_price_psf"]], geometry=gdf_proj.geometry.centroid, crs="EPSG:2272"
    ).to_crs(tracts.crs)

    joined = gpd.sjoin(cent, tracts[["tract_geoid", "geometry"]], how="left", predicate="within")
    tract_stats = joined.groupby("tract_geoid").agg(
        n=("land_price_psf", "size"),
        land_price_psf=("land_price_psf", "median"),
    ).reset_index()
    # Require a minimum sample per tract, same spirit as FHFA's own minimum-sales threshold
    tract_stats = tract_stats[tract_stats["n"] >= 10]

    tract_plot = tracts.merge(tract_stats, on="tract_geoid", how="left")
    matched = tract_plot["land_price_psf"].notna().sum()
    print(f"  {matched} of {len(tract_plot)} tracts with >=10 SFR parcels")

    tract_plot = tract_plot.to_crs("EPSG:3857")

    cmap = matplotlib.colormaps.get_cmap("YlOrRd")
    vals = tract_plot["land_price_psf"].dropna()
    vmin, vmax = vals.quantile(0.02), vals.quantile(0.98)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    fig, ax = plt.subplots(figsize=(10, 11))

    tract_plot.plot(
        column="land_price_psf",
        cmap=cmap,
        norm=norm,
        linewidth=0.3,
        edgecolor="white",
        ax=ax,
        missing_kwds={"color": "#e5e5e5", "hatch": "///", "edgecolor": "#bbbbbb", "linewidth": 0.3},
    )

    ax.set_axis_off()

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.02, shrink=0.7)
    cbar.set_label("Single-family land price ($/sqft)\nOur LYCD model (GMA zone-median x 20%)", fontsize=9)

    ax.set_title(
        "Philadelphia — residential land price per square foot\n(our LYCD model, not FHFA)",
        fontsize=13,
        fontweight="bold",
    )

    n_missing = tract_plot["land_price_psf"].isna().sum()
    fig.text(
        0.5, 0.02,
        f"Median ${vals.median():.0f}/sqft (p10 ${vals.quantile(.1):.0f}, p90 ${vals.quantile(.9):.0f}) "
        f"across {matched} tracts. Hatched = fewer than 10 SFR parcels in tract ({n_missing} tracts).",
        fontsize=8.5,
        va="bottom",
        ha="center",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    print(f"Saved: {OUTPUT_PATH}")
    print(f"  $/sqft: min ${vals.min():.0f}, p25 ${vals.quantile(.25):.0f}, median ${vals.median():.0f}, "
          f"p75 ${vals.quantile(.75):.0f}, max ${vals.max():.0f}")


if __name__ == "__main__":
    main()
