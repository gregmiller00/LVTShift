"""
Philadelphia Tax Change Choropleth Maps
---------------------------------------
Produces block-group-level choropleth maps of median tax_change_pct for all
four Philadelphia model variants, with council district boundaries overlaid.

Outputs: analysis/reports/<variant>/map_tax_change_pct.png  (city-wide all parcels)
         analysis/reports/<variant>/map_sfr_tax_change_pct.png  (SFR only)
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
import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

VARIANTS = [
    "philadelphia",
    "philadelphia_lycd",
    "philadelphia_post_abatement",
    "philadelphia_lycd_post_abatement",
]

VARIANT_LABELS = {
    "philadelphia":                    "Philadelphia — 4:1 Split Rate (OPA land values)",
    "philadelphia_lycd":               "Philadelphia — 4:1 Split Rate (LYCD land values)",
    "philadelphia_post_abatement":     "Philadelphia — 4:1 Split Rate, Post-Abatement (OPA land values)",
    "philadelphia_lycd_post_abatement": "Philadelphia — 4:1 Split Rate, Post-Abatement (LYCD land values)",
}

# Exclude fully exempt and zero-current-tax parcels from median calculations
EXCLUDE_EXEMPT = True

# Clamp percentile range for colour scale (avoids extreme outliers dominating)
PCT_CLAMP = (5, 95)   # percentiles used to set vmin/vmax


# ---------------------------------------------------------------------------
# 1. Download / cache block group boundaries (Philadelphia County = FIPS 42101)
# ---------------------------------------------------------------------------

def _arcgis_rings_to_shapely(rings):
    """Convert ArcGIS REST API rings list to a Shapely geometry."""
    from shapely.geometry import Polygon, MultiPolygon
    from shapely.ops import unary_union

    if not rings:
        return None
    exterior = rings[0]
    holes = rings[1:]
    try:
        poly = Polygon(exterior, holes)
        return poly if poly.is_valid else poly.buffer(0)
    except Exception:
        return None


def _fetch_arcgis_features(url: str, where: str, out_fields: str, out_sr: str = "4326") -> list:
    """Paginate through an ArcGIS REST query and return all features."""
    all_features = []
    offset = 0
    page_size = 1000
    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "outSR": out_sr,
            "returnGeometry": "true",
            "f": "json",
            "resultRecordCount": page_size,
            "resultOffset": offset,
        }
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        feats = data.get("features", [])
        all_features.extend(feats)
        if not data.get("exceededTransferLimit", False) or len(feats) < page_size:
            break
        offset += page_size
    return all_features


def fetch_block_group_boundaries() -> gpd.GeoDataFrame:
    cache = REPO_ROOT / "cities/philadelphia/data/block_groups.gpq"
    if cache.exists():
        print("  Loading cached block group boundaries...")
        return gpd.read_parquet(cache)

    print("  Fetching block group boundaries from TIGERweb...")
    url = (
        "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
        "tigerWMS_Current/MapServer/10/query"
    )
    features = _fetch_arcgis_features(url, "STATE='42' AND COUNTY='101'", "GEOID,NAME")

    records = []
    for feat in features:
        geom = _arcgis_rings_to_shapely(feat["geometry"].get("rings", []))
        records.append({
            "GEOID": feat["attributes"]["GEOID"],
            "NAME": feat["attributes"]["NAME"],
            "geometry": geom,
        })

    gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf.to_parquet(cache)
    print(f"  Cached {len(gdf)} block groups.")
    return gdf


def fetch_council_districts() -> gpd.GeoDataFrame:
    cache = REPO_ROOT / "cities/philadelphia/data/council_districts.gpq"
    if cache.exists():
        print("  Loading cached council district boundaries...")
        return gpd.read_parquet(cache)

    print("  Fetching council district boundaries from OpenDataPhilly...")
    url = "https://opendata.arcgis.com/datasets/9298c2f3fa3241fbb176ff1e84d33360_0.geojson"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    import io
    gdf = gpd.read_file(io.StringIO(r.text))
    gdf = gdf[["DISTRICT", "geometry"]].copy()
    gdf["DISTRICT"] = gdf["DISTRICT"].astype(int)
    gdf.to_parquet(cache)
    print(f"  Cached {len(gdf)} council districts.")
    return gdf


# ---------------------------------------------------------------------------
# 2. Aggregate model CSV to block groups
# ---------------------------------------------------------------------------

def aggregate_to_block_groups(
    csv_path: Path,
    bg_gdf: gpd.GeoDataFrame,
    exclude_exempt: bool = True,
    category_filter: str | None = None,
) -> gpd.GeoDataFrame:
    df = pd.read_csv(csv_path)

    if exclude_exempt:
        df = df[~df["is_fully_exempt"]]
        # Also exclude zero-current-tax parcels (can't compute meaningful %)
        df = df[df["current_tax"] > 0]

    if category_filter:
        df = df[df["property_category"].str.startswith(category_filter)]

    df = df[df["std_geoid"].notna()].copy()
    df["GEOID"] = df["std_geoid"].apply(lambda x: f"{int(x):012d}")

    agg = (
        df.groupby("GEOID")
        .agg(
            median_tax_change_pct=("tax_change_pct", "median"),
            parcel_count=("tax_change_pct", "count"),
            median_current_tax=("current_tax", "median"),
        )
        .reset_index()
    )

    merged = bg_gdf.merge(agg, on="GEOID", how="left")
    return merged


# ---------------------------------------------------------------------------
# 3. Plotting
# ---------------------------------------------------------------------------

def diverging_cmap():
    """Red (tax increase) → white → blue (tax decrease), centred at 0."""
    return matplotlib.colormaps.get_cmap("RdBu_r")


def plot_choropleth(
    gdf: gpd.GeoDataFrame,
    districts: gpd.GeoDataFrame,
    value_col: str,
    title: str,
    output_path: Path,
    vmin: float | None = None,
    vmax: float | None = None,
):
    gdf_plot = gdf.to_crs("EPSG:3857")
    dist_plot = districts.to_crs("EPSG:3857")

    # Compute symmetric colour limits if not provided
    vals = gdf_plot[value_col].dropna()
    if vmin is None or vmax is None:
        lo = np.percentile(vals, PCT_CLAMP[0])
        hi = np.percentile(vals, PCT_CLAMP[1])
        # Make symmetric around 0 so the diverging map is centred
        abs_max = max(abs(lo), abs(hi))
        vmin = -abs_max
        vmax = abs_max

    norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    cmap = diverging_cmap()

    fig, ax = plt.subplots(figsize=(10, 11))
    ax.set_aspect("equal")
    ax.axis("off")

    # Block groups (fill = median tax change %)
    gdf_plot.plot(
        ax=ax,
        column=value_col,
        cmap=cmap,
        norm=norm,
        linewidth=0,
        missing_kwds={"color": "#e0e0e0", "label": "No taxable parcels"},
    )

    # Council districts (outline only)
    dist_plot.boundary.plot(ax=ax, color="black", linewidth=1.2, alpha=0.85)

    # Label each district at its centroid
    for _, row in dist_plot.iterrows():
        cx, cy = row.geometry.centroid.x, row.geometry.centroid.y
        ax.annotate(
            str(int(row["DISTRICT"])),
            (cx, cy),
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="black",
        )

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.02, shrink=0.7)
    cbar.set_label("Median tax change (%)", fontsize=10)
    cbar.ax.tick_params(labelsize=9)

    ax.set_title(title, fontsize=11, pad=10, wrap=True)

    # Note
    ax.text(
        0.5, -0.01,
        "Block groups coloured by median % tax change. Council districts outlined in black.\n"
        "Red = tax increases, Blue = tax decreases. Fully exempt and zero-tax parcels excluded.",
        transform=ax.transAxes,
        ha="center",
        fontsize=7.5,
        color="#444444",
    )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path.relative_to(REPO_ROOT)}")


def build_parcel_district_gdf(
    csv_path: Path,
    parcels_gpq: Path,
    districts: gpd.GeoDataFrame,
    exclude_exempt: bool = True,
    category_filter: str | None = None,
) -> gpd.GeoDataFrame:
    """
    Join parcel-level CSV to parcel centroids, then spatial-join to council
    districts. Returns a GeoDataFrame with one row per parcel and a DISTRICT column.
    """
    df = pd.read_csv(csv_path)
    parcels = gpd.read_parquet(parcels_gpq)[["parcel_number", "geometry"]].copy()
    # parcel_number in parcels.gpq is a string; parcel_id in CSV is int (OPA drops leading zeros)
    parcels["parcel_id"] = parcels["parcel_number"].astype(str).str.lstrip("0").astype("Int64")
    # Drop duplicates arising from leading-zero collisions (keep first geometry)
    parcels = parcels.drop_duplicates(subset="parcel_id", keep="first")

    merged = df.merge(parcels, on="parcel_id", how="inner")
    gdf = gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:4326")

    if exclude_exempt:
        gdf = gdf[~gdf["is_fully_exempt"]]
        gdf = gdf[gdf["current_tax"] > 0]

    if category_filter:
        gdf = gdf[gdf["property_category"].str.startswith(category_filter)]

    dist_proj = districts.to_crs("EPSG:4326")[["DISTRICT", "geometry"]]
    joined = gpd.sjoin(gdf, dist_proj, how="left", predicate="within")
    return joined


def plot_district_summary(
    csv_path: Path,
    parcels_gpq: Path,
    districts: gpd.GeoDataFrame,
    title: str,
    output_path: Path,
    category_filter: str | None = None,
):
    """Bar chart: true parcel-level median tax change % per council district."""
    print("  Building parcel->district spatial join...")
    joined = build_parcel_district_gdf(csv_path, parcels_gpq, districts, category_filter=category_filter)

    agg = (
        joined[joined["tax_change_pct"].notna() & joined["DISTRICT"].notna()]
        .groupby("DISTRICT")["tax_change_pct"]
        .median()
        .reset_index()
        .rename(columns={"tax_change_pct": "median_pct"})
        .sort_values("DISTRICT")
    )
    counts = (
        joined[joined["DISTRICT"].notna()]
        .groupby("DISTRICT")
        .size()
        .reset_index(name="n_parcels")
    )
    agg = agg.merge(counts, on="DISTRICT")

    agg["DISTRICT"] = agg["DISTRICT"].astype(int)

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#d73027" if v > 0 else "#4575b4" for v in agg["median_pct"]]
    ax.bar(agg["DISTRICT"].astype(str), agg["median_pct"], color=colors, width=0.6)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Council District", fontsize=11)
    ax.set_ylabel("Median tax change (%)", fontsize=11)
    ax.set_title(title, fontsize=11)
    ax.tick_params(axis="both", labelsize=10)

    y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
    label_pad = y_range * 0.02
    for bar, (_, row) in zip(ax.patches, agg.iterrows()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            row["median_pct"] + (label_pad if row["median_pct"] >= 0 else -label_pad),
            f"{row['median_pct']:+.1f}%",
            ha="center",
            va="bottom" if row["median_pct"] >= 0 else "top",
            fontsize=8,
        )

    ax.text(
        0.5, -0.14,
        "True parcel-level median. Fully exempt and zero-tax parcels excluded.",
        transform=ax.transAxes,
        ha="center",
        fontsize=8,
        color="#555555",
    )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# 4. Main
# ---------------------------------------------------------------------------

def main():
    print("Fetching boundary data...")
    bg_gdf = fetch_block_group_boundaries()
    dist_gdf = fetch_council_districts()
    parcels_gpq = REPO_ROOT / "cities/philadelphia/data/parcels.gpq"

    for variant in VARIANTS:
        csv_path = REPO_ROOT / f"analysis/data/{variant}.csv"
        if not csv_path.exists():
            print(f"Skipping {variant}: CSV not found.")
            continue

        report_dir = REPO_ROOT / f"analysis/reports/{variant}"
        label = VARIANT_LABELS[variant]
        print(f"\n--- {variant} ---")

        # All non-exempt taxable parcels — choropleth uses block group aggregates
        print("  Aggregating all taxable parcels (block groups)...")
        all_bg = aggregate_to_block_groups(csv_path, bg_gdf)
        plot_choropleth(
            all_bg, dist_gdf,
            value_col="median_tax_change_pct",
            title=f"{label}\nMedian tax change % by block group (all taxable parcels)",
            output_path=report_dir / "map_tax_change_pct.png",
        )

        # District summary — true parcel-level medians via spatial join
        plot_district_summary(
            csv_path, parcels_gpq, dist_gdf,
            title=f"{label}\nMedian tax change % by council district",
            output_path=report_dir / "map_district_summary.png",
        )

        # SFR only
        print("  Aggregating SFR parcels (block groups)...")
        sfr_bg = aggregate_to_block_groups(csv_path, bg_gdf, category_filter="Single Family Residential")
        plot_choropleth(
            sfr_bg, dist_gdf,
            value_col="median_tax_change_pct",
            title=f"{label}\nMedian tax change % by block group (Single Family Residential)",
            output_path=report_dir / "map_sfr_tax_change_pct.png",
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
