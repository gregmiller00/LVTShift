"""Geographic choropleth builder for reproducible Beamer decks.

Companion to ``deck_helpers`` for the one chart type that can't be hand-rolled TikZ: a
region/ZIP **choropleth** (e.g. "members per ZIP code"). Unlike the bar/KPI builders --
which return TikZ strings saved as ``charts/*.tex`` and ``\\input`` -- a map is a matplotlib
figure saved as a vector ``figures/*.pdf`` and pulled in with ``\\includegraphics``. It is
still single-source-of-truth: the counts come from the analysis, the PDF is regenerated, and
no number is typed onto the slide.

``geo_choropleth(...)`` builds the figure; ``save_figure(...)`` writes the PDF (mirroring the
``hbar_chart`` / ``save_chart`` build-then-save split). The look matches the deck theme: a
teal ramp keyed to the palette (``decktint`` -> ``deckfg`` -> ``deckbg``) over a CartoDB
Positron basemap, with the top areas labeled by count.

The heavy geo stack (geopandas, contextily, matplotlib, shapely/pyproj/fiona underneath) is
imported lazily *inside* the functions, so a deck with no map -- or an environment without
those packages -- imports ``deck_helpers`` exactly as before. Install only when you need a
map:  ``pip install geopandas contextily matplotlib``  (or the conda-forge equivalents).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Deck palette teal ramp (light card tint -> primary accent -> dark frame bg). Matches
# beamer-theme.tex so the map re-tones with the rest of the deck when the palette changes.
DECK_TEAL = ("#E8F2F3", "#0E7C86", "#0E3D49")   # decktint, deckfg, deckbg
DECK_INK = "#1A2B33"                            # deckink -- label text


def _default_fmt(v) -> str:
    """Thousands-separated count; integers stay integer, fractions get one decimal."""
    v = float(v)
    return f"{v:,.0f}" if abs(v - round(v)) < 1e-9 else f"{v:,.1f}"


def geo_choropleth(
    boundary_geojson_path,
    counts: dict,
    id_field: str,
    *,
    value_label: str = "count",
    cmap_colors=DECK_TEAL,
    basemap: bool = True,
    basemap_source=None,
    label_top: int = 5,
    label_field: str | None = None,
    value_fmt=None,
    alpha: float = 0.78,
    edgecolor: str = "white",
    linewidth: float = 0.4,
    legend: bool = True,
    figsize=(7.0, 7.5),
    pad_frac: float = 0.05,
    label_fontsize: float = 8.0,
    assume_epsg: int = 4326,
):
    """Build a region/ZIP choropleth as a matplotlib ``Figure`` (does not save).

    ``boundary_geojson_path``  path to a GeoJSON of region polygons. Cache this file in the
        repo (e.g. ``deck/data/zips.geojson``) so the map regenerates offline and the same
        boundaries are used every run -- don't fetch it live at generate time.
    ``counts``  ``{id_value: count}`` from the analysis, e.g. ``{"19104": 37, "19146": 21}``.
        Keys are matched to ``id_field`` as **strings** (both sides are ``str``-ed and
        stripped), so ``19104`` and ``"19104"`` both work. ZIP gotcha: a key ``8401`` will
        NOT match a GeoJSON value ``"08401"`` -- zero-pad your keys to match the file.
    ``id_field``  the GeoJSON property that holds the region id the ``counts`` keys refer to.

    Regions absent from ``counts`` (or NaN) are left unfilled so the basemap shows through;
    the axes are cropped to the bounding box of the regions that *have* a nonzero count (plus
    ``pad_frac`` padding), so a few far-flung members don't zoom the whole map out. The
    ``label_top`` highest areas are annotated with "id / count" (white-haloed for legibility
    over any fill). The colour scale is fixed at ``vmin=0`` so the light end always reads as
    zero. Returns the ``Figure``; pass it to ``save_figure(FIGURES / "map.pdf", fig)``.

    Requires geopandas + matplotlib (and contextily for the basemap); raises ``RuntimeError``
    with an install hint if they're missing. The basemap fetch is wrapped in try/except, so a
    missing contextily or no network degrades to a clean no-basemap map rather than failing.
    """
    try:
        import geopandas as gpd  # noqa: F401  (also pulls shapely/pyproj/fiona)
        import matplotlib
        matplotlib.use("Agg")    # headless: we only ever savefig (PDF/PNG), never show()
        import matplotlib.pyplot as plt
        from matplotlib.colors import LinearSegmentedColormap
        import matplotlib.patheffects as pe
    except Exception as e:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "geo_choropleth requires geopandas + matplotlib. "
            "Install: pip install geopandas contextily matplotlib"
        ) from e

    label_field = label_field or id_field
    value_fmt = value_fmt or _default_fmt

    gdf = gpd.read_file(boundary_geojson_path)
    if id_field not in gdf.columns:
        raise ValueError(
            f"id_field {id_field!r} not in GeoJSON properties {list(gdf.columns)!r}"
        )

    # Join counts by normalized string key, so int/str and stray whitespace both match.
    norm = {str(k).strip(): float(v) for k, v in counts.items()}
    keys = gdf[id_field].astype(str).str.strip()
    gdf["_value"] = keys.map(norm)
    matched = int(gdf["_value"].notna().sum())
    unmatched = [k for k in norm if k not in set(keys)]
    print(f"  geo_choropleth: matched {matched}/{len(gdf)} regions; "
          f"{len(unmatched)} count keys unmatched"
          + (f" (e.g. {unmatched[:5]})" if unmatched else ""))

    # Project to Web Mercator so the choropleth aligns with raster basemap tiles.
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=assume_epsg)
    gdf = gdf.to_crs(epsg=3857)

    vmax = gdf["_value"].max()
    if vmax is None or not (vmax > 0):
        vmax = 1.0  # degenerate (no/zero counts): keep a valid colour scale
    cmap = LinearSegmentedColormap.from_list("deckteal", list(cmap_colors))

    fig, ax = plt.subplots(figsize=figsize)
    # NaN regions are simply not drawn (basemap shows through). Fixed vmin=0 -> light=zero.
    gdf.plot(
        column="_value", ax=ax, cmap=cmap, vmin=0, vmax=vmax,
        alpha=alpha, edgecolor=edgecolor, linewidth=linewidth,
        legend=legend,
        legend_kwds={"label": value_label, "shrink": 0.5} if legend else None,
    )

    # Crop to the nonzero data footprint (fall back to all geometry if nothing matched).
    nz = gdf[gdf["_value"].fillna(0) > 0]
    xmin, ymin, xmax, ymax = (nz if len(nz) else gdf).total_bounds
    padx = max((xmax - xmin) * pad_frac, 1.0)
    pady = max((ymax - ymin) * pad_frac, 1.0)
    ax.set_xlim(xmin - padx, xmax + padx)
    ax.set_ylim(ymin - pady, ymax + pady)

    if basemap:
        try:
            import contextily as cx
            src = basemap_source or cx.providers.CartoDB.Positron
            cx.add_basemap(ax, crs=gdf.crs, source=src)
        except Exception as e:  # tiles unavailable / contextily missing -> degrade cleanly
            print(f"  geo_choropleth: basemap unavailable ({type(e).__name__}: {e}); "
                  f"rendering without it", file=sys.stderr)

    # Label the top-N nonzero areas with id + count, haloed so they read over any fill.
    if label_top and len(nz):
        top = nz.sort_values("_value", ascending=False).head(label_top)
        for _, row in top.iterrows():
            pt = row.geometry.representative_point()  # guaranteed inside the polygon
            ax.annotate(
                f"{row[label_field]}\n{value_fmt(row['_value'])}",
                xy=(pt.x, pt.y), ha="center", va="center",
                fontsize=label_fontsize, color=DECK_INK, fontweight="bold",
                path_effects=[pe.withStroke(linewidth=2.5, foreground="white")],
            )

    ax.set_axis_off()
    fig.tight_layout(pad=0.4)
    return fig


def save_figure(path, fig, *, dpi: int = 200, transparent: bool = False):
    """Write a matplotlib ``Figure`` (from ``geo_choropleth``) to ``path`` and close it.

    Use a ``.pdf`` path for the vector figure a slide ``\\includegraphics``-es; the choropleth
    stays vector while the basemap is an embedded raster, so ``dpi`` controls only the basemap
    sharpness (200 is plenty for projection). The format follows the file extension, so the
    same call writes a ``.png`` if you want a quick proof to eyeball. Closes ``fig`` so a
    generator that builds many maps doesn't leak figures.
    """
    import matplotlib.pyplot as plt

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, bbox_inches="tight", pad_inches=0.02, dpi=dpi, transparent=transparent)
    plt.close(fig)
    return p
