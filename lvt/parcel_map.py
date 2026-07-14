"""Parcel-level interactive map exports for LVTShift.

Two public functions, both fully generic (no city-specific logic):

- ``save_parcel_map_export`` — take the modeled GeoDataFrame and write a
  GeoParquet to ``analysis/maps/<city>.parquet`` carrying geometry plus the
  standard tax-outcome columns and, when available, per-parcel identity fields
  (parcel number, a link to the county record, owner name, owner address).
- ``create_parcel_map`` — read that GeoParquet and emit a self-contained
  interactive HTML map (``analysis/reports/<city>/parcel_map.html``) coloring
  parcels by tax change so a reader can see who gains and who loses, zoom in,
  and click a parcel for its details.

The GeoParquet deliberately carries MORE per-parcel columns than the flat
``analysis/data/<city>.csv`` standard export — geometry, parcel_id, parcel_url,
owner_name, owner_address — because a map needs identity and shape that the
cross-city CSV omits. The shared tax-outcome columns are built by
``lvt.lvt_utils.build_standard_export_frame`` so the two exports never drift.
"""

import base64
import glob
import html
import json
import os
import shutil
import subprocess
import tempfile
from typing import Optional
from urllib.parse import quote

import geopandas as gpd
import numpy as np
import pandas as pd

from lvt.lvt_utils import build_standard_export_frame

WGS84 = 'EPSG:4326'
WEB_MERCATOR = 'EPSG:3857'


def _build_parcel_urls(
    parcel_ids: pd.Series,
    parcel_url_template: Optional[str],
) -> pd.Series:
    """Format a per-parcel record URL from a template containing ``{parcel_id}``.

    Returns an all-null Series when no template is supplied. The parcel id is
    URL-encoded so ids with spaces or slashes stay valid.
    """
    if not parcel_url_template:
        return pd.Series(np.nan, index=parcel_ids.index, dtype=object)

    def _fmt(pid) -> Optional[str]:
        if pd.isna(pid) or str(pid).strip() == '':
            return np.nan
        return parcel_url_template.format(parcel_id=quote(str(pid), safe=''))

    return parcel_ids.map(_fmt)


def save_parcel_map_export(
    gdf: gpd.GeoDataFrame,
    city: str,
    output_path: str,
    model_type: str,
    land_millage: float,
    improvement_millage: float,
    geometry_col: str = 'geometry',
    parcel_id_col: Optional[str] = None,
    parcel_url_template: Optional[str] = None,
    owner_name_col: Optional[str] = None,
    owner_address_col: Optional[str] = None,
    property_category_col: str = 'PROPERTY_CATEGORY',
    current_tax_col: str = 'current_tax',
    new_tax_col: str = 'new_tax',
    tax_change_col: str = 'tax_change',
    tax_change_pct_col: str = 'tax_change_pct',
    taxable_land_col: str = 'taxable_land_value',
    taxable_improvement_col: str = 'taxable_improvement_value',
    exempt_flag_col: Optional[str] = None,
    geoid_col: str = 'std_geoid',
    income_col: str = 'median_income',
    minority_col: str = 'minority_pct',
    black_col: str = 'black_pct',
    simplify_tolerance_m: Optional[float] = None,
) -> gpd.GeoDataFrame:
    """Build and write the per-parcel GeoParquet map export.

    The output holds the same tax-outcome columns as ``save_standard_export``
    plus geometry (reprojected to WGS84) and optional identity columns. All
    identity columns are optional: a city with only a parcel id — or none at
    all — still produces a valid geometry + tax map.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        The final modeled GeoDataFrame (same object passed to
        ``save_standard_export``), still carrying geometry.
    city, output_path, model_type, land_millage, improvement_millage
        As in ``save_standard_export``. ``output_path`` should end in
        ``.parquet`` (e.g. ``"../../analysis/maps/newport_news.parquet"``).
    geometry_col : str
        Name of the geometry column in ``gdf``.
    parcel_id_col : str, optional
        Column holding the parcel/account number shown to users. Null column
        name → ``parcel_id`` is emitted as null.
    parcel_url_template : str, optional
        A template with a ``{parcel_id}`` placeholder pointing at the county's
        public record for the parcel, e.g.
        ``"https://gis.example.gov/parcel?pin={parcel_id}"``. The id is
        URL-encoded before substitution. Omit when the assessor portal has no
        stable per-parcel deep link.
    owner_name_col, owner_address_col : str, optional
        Columns holding owner name and owner/site address.
    simplify_tolerance_m : float, optional
        If set, geometries are simplified with this tolerance in meters
        (via EPSG:3857) to shrink the file for large cities. Topology is
        preserved. ``None`` keeps full-resolution geometry.

    Returns
    -------
    gpd.GeoDataFrame
        The written frame, in WGS84.
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError('save_parcel_map_export requires a GeoDataFrame')
    if geometry_col not in gdf.columns:
        raise ValueError(f"geometry column '{geometry_col}' not found in gdf")

    out = build_standard_export_frame(
        gdf, city, model_type, land_millage, improvement_millage,
        property_category_col=property_category_col,
        current_tax_col=current_tax_col,
        new_tax_col=new_tax_col,
        tax_change_col=tax_change_col,
        tax_change_pct_col=tax_change_pct_col,
        taxable_land_col=taxable_land_col,
        taxable_improvement_col=taxable_improvement_col,
        exempt_flag_col=exempt_flag_col,
        geoid_col=geoid_col,
        income_col=income_col,
        minority_col=minority_col,
        black_col=black_col,
    )

    # Identity columns — optional, null-filled when the source column is absent.
    if parcel_id_col is not None and parcel_id_col in gdf.columns:
        out['parcel_id'] = gdf[parcel_id_col].astype('string')
    else:
        out['parcel_id'] = pd.Series(pd.NA, index=out.index, dtype='string')

    out['parcel_url'] = _build_parcel_urls(out['parcel_id'], parcel_url_template)

    for out_col, src_col in [('owner_name', owner_name_col), ('owner_address', owner_address_col)]:
        if src_col is not None and src_col in gdf.columns:
            out[out_col] = gdf[src_col].astype('string')
        else:
            out[out_col] = pd.Series(pd.NA, index=out.index, dtype='string')

    # Attach geometry (aligned by index) and normalize to WGS84.
    geom = gpd.GeoSeries(gdf[geometry_col].values, index=gdf.index, crs=gdf.crs)
    map_gdf = gpd.GeoDataFrame(out, geometry=geom, crs=gdf.crs)
    map_gdf = map_gdf[map_gdf.geometry.notna() & ~map_gdf.geometry.is_empty].copy()

    if simplify_tolerance_m:
        merc = map_gdf.geometry.to_crs(WEB_MERCATOR)
        merc = merc.simplify(simplify_tolerance_m, preserve_topology=True)
        map_gdf = map_gdf.set_geometry(gpd.GeoSeries(merc, crs=WEB_MERCATOR))

    if map_gdf.crs is None or map_gdf.crs.to_epsg() != 4326:
        map_gdf = map_gdf.to_crs(WGS84)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    map_gdf.to_parquet(output_path)
    n_url = int(map_gdf['parcel_url'].notna().sum())
    print(
        f"  ✓ {city}: {len(map_gdf):,} parcels → {output_path}  "
        f"[map export; {n_url:,} with record links]"
    )
    return map_gdf


# ---------------------------------------------------------------------------
# Interactive HTML viewer
# ---------------------------------------------------------------------------

# Diverging steps on tax_change_pct (%). Negative = pays less (green),
# positive = pays more (red). Grey for parcels with no current tax to compare.
_COLOR_STOPS = [
    (-30, '#1a9850'),
    (-15, '#66bd63'),
    (-5,  '#a6d96a'),
    (5,   '#ffffbf'),
    (15,  '#fdae61'),
    (30,  '#f46d43'),
    (float('inf'), '#d73027'),
]
_NO_DATA_COLOR = '#bdbdbd'


def _color_for(pct: Optional[float]) -> str:
    if pct is None or (isinstance(pct, float) and np.isnan(pct)):
        return _NO_DATA_COLOR
    for threshold, color in _COLOR_STOPS:
        if pct <= threshold:
            return color
    return _COLOR_STOPS[-1][1]


def create_parcel_map(
    source,
    city: str,
    output_dir: str = '../../analysis/reports',
    coord_precision: int = 5,
    simplify_tolerance_m: Optional[float] = 2.0,
    title: Optional[str] = None,
    tile_threshold: Optional[int] = 120_000,
) -> str:
    """Render an interactive HTML parcel map.

    For most cities this is a single self-contained Leaflet HTML with the parcel
    geometry embedded inline. For very large cities (more than ``tile_threshold``
    parcels) it instead builds vector tiles (a ``<city>.pmtiles`` file via
    tippecanoe) and a MapLibre GL viewer, so the map stays fast — see
    ``create_parcel_tile_map``. That tiled viewer must be opened over a local
    web server (the PMTiles protocol uses HTTP range requests); the file does
    not work via a ``file://`` double-click. Set ``tile_threshold=None`` to force
    the inline path, or lower it to force tiles.

    Colors each parcel by ``tax_change_pct`` (green = pays less under the
    reform, red = pays more), zoomable, click a parcel for its details and a
    link to the county record when available. Written to
    ``{output_dir}/{city}/parcel_map.html``.

    Parameters
    ----------
    source : str | gpd.GeoDataFrame
        Path to a GeoParquet written by ``save_parcel_map_export``, or the
        GeoDataFrame it returned.
    city : str
        City slug, used for the output sub-directory and default title.
    output_dir : str
        Parent directory. A ``{city}`` sub-directory is created automatically.
        Default resolves correctly from ``cities/<city>/``.
    coord_precision : int
        Decimal places to round coordinates to (smaller → smaller file).
        5 ≈ 1 m, plenty for parcels.
    simplify_tolerance_m : float, optional
        Geometry simplification tolerance in meters applied only to the map's
        embedded geometry (the source GeoParquet keeps full resolution). This
        keeps the HTML small without degrading the stored data. ``None`` to
        embed full-resolution geometry.
    title : str, optional
        Map heading. Defaults to a generated title.

    Returns
    -------
    str
        Path to the written HTML file.

    Notes
    -----
    The HTML embeds all parcel geometry and data inline (no server needed).
    The Leaflet library and OpenStreetMap base tiles load from their public
    CDNs, so the file needs internet access to render the base map. For very
    large cities pass ``simplify_tolerance_m`` to ``save_parcel_map_export``
    first to keep the embedded GeoJSON small.
    """
    if isinstance(source, (str, os.PathLike)):
        gdf = gpd.read_parquet(source)
    else:
        gdf = source
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(WGS84)

    # Large cities → vector tiles (PMTiles) + MapLibre, if tippecanoe is available.
    if tile_threshold and len(gdf) > tile_threshold:
        if _have_tippecanoe():
            return create_parcel_tile_map(gdf, city, output_dir=output_dir, title=title)
        print(
            f"  [warn] {city}: {len(gdf):,} parcels exceeds tile_threshold "
            f"({tile_threshold:,}) but tippecanoe is not installed — falling back "
            f"to the inline Leaflet map (this file will be large)."
        )

    if simplify_tolerance_m:
        merc = gdf.geometry.to_crs(WEB_MERCATOR).simplify(
            simplify_tolerance_m, preserve_topology=True)
        gdf = gdf.set_geometry(gpd.GeoSeries(merc, crs=WEB_MERCATOR)).to_crs(WGS84)

    features = []
    for row in gdf.itertuples(index=False):
        geom = getattr(row, 'geometry')
        if geom is None or geom.is_empty:
            continue
        pct = getattr(row, 'tax_change_pct', None)
        pct = None if pct is None or (isinstance(pct, float) and np.isnan(pct)) else float(pct)
        props = {
            'pid': _clean(getattr(row, 'parcel_id', None)),
            'url': _clean(getattr(row, 'parcel_url', None)),
            'own': _clean(getattr(row, 'owner_name', None)),
            'adr': _clean(getattr(row, 'owner_address', None)),
            'cat': _clean(getattr(row, 'property_category', None)),
            'land': _num(getattr(row, 'taxable_land_value', None)),
            'imp': _num(getattr(row, 'taxable_improvement_value', None)),
            'cur': _num(getattr(row, 'current_tax', None)),
            'new': _num(getattr(row, 'new_tax', None)),
            'chg': _num(getattr(row, 'tax_change', None)),
            'pct': None if pct is None else round(pct, 1),
            'c': _color_for(pct),
        }
        features.append({
            'type': 'Feature',
            'properties': props,
            'geometry': _round_geometry(geom.__geo_interface__, coord_precision),
        })

    fc = {'type': 'FeatureCollection', 'features': features}
    bounds = gdf.total_bounds  # minx, miny, maxx, maxy
    center = [float((bounds[1] + bounds[3]) / 2), float((bounds[0] + bounds[2]) / 2)]

    city_name = city.replace('_', ' ').title()
    model_type = ''
    if 'model_type' in gdf.columns and len(gdf):
        model_type = str(gdf['model_type'].iloc[0] or '')
    model_label = _model_label(model_type)

    heading = title or f"{city_name} — who pays less, who pays more under {model_label}"
    subtitle = (
        f"Every modeled parcel, colored by how its property-tax bill changes under "
        f"a revenue-neutral {model_label}. Green = pays less, red = pays more. "
        f"Toggle the road / satellite base map, and click a parcel to inspect it."
    )
    out_city_dir = os.path.join(output_dir, city)
    os.makedirs(out_city_dir, exist_ok=True)
    out_path = os.path.join(out_city_dir, 'parcel_map.html')

    # Click-through gallery of the report PNGs sitting alongside this HTML.
    # create_city_report runs before create_parcel_map in the notebook, so they exist.
    gallery = _build_gallery(out_city_dir)

    html_doc = (
        _HTML_TEMPLATE
        .replace('__TITLE__', html.escape(heading))
        .replace('__SUBTITLE__', html.escape(subtitle))
        .replace('__GEOJSON__', json.dumps(fc, separators=(',', ':')))
        .replace('__CENTER__', json.dumps(center))
        .replace('__GALLERY__', gallery)
    )
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(html_doc)
    print(f"  ✓ {city}: interactive map → {out_path}  [{len(features):,} parcels]")
    return out_path


def _clean(value):
    if value is None or (isinstance(value, float) and np.isnan(value)) or value is pd.NA:
        return None
    s = str(value).strip()
    return s or None


def _num(value):
    if value is None or (isinstance(value, float) and np.isnan(value)) or value is pd.NA:
        return None
    return round(float(value), 2)


def _model_label(model_type: str) -> str:
    """Turn a model_type slug into a human label, e.g.
    'split_rate_4to1' → '4:1 split-rate'; 'abatement_75pct' → '75% building abatement'.
    Falls back to a generic phrase when the slug is empty or unrecognized."""
    mt = (model_type or '').strip().lower()
    if not mt:
        return 'land value tax'
    import re
    m = re.match(r'split_rate_(\d+)to(\d+)', mt)
    if m:
        return f"{m.group(1)}:{m.group(2)} split-rate"
    m = re.match(r'abatement_(\d+)pct', mt)
    if m:
        return f"{m.group(1)}% building abatement"
    return mt.replace('_', ' ')


_CHART_TITLES = {
    'category_impact': 'Median tax change by property category',
    'ten_pct_share': 'Share of parcels with a >10% change',
    'distribution': 'Distribution of parcel-level tax change',
    'income_quintile_non_vacant': 'Tax change by income quintile — non-vacant',
    'income_quintile_residential': 'Tax change by income quintile — residential',
    'minority_quintile_non_vacant': 'Tax change by minority quintile — non-vacant',
    'minority_quintile_residential': 'Tax change by minority quintile — residential',
    'income_decile_non_vacant': 'Tax change by income decile — non-vacant',
    'income_decile_residential': 'Tax change by income decile — residential',
    'minority_decile_non_vacant': 'Tax change by minority decile — non-vacant',
    'minority_decile_residential': 'Tax change by minority decile — residential',
    'sfr_breakdown': 'Single-family residential breakdown',
    'category_preview': 'Category preview',
}


def _pretty_chart_title(filename: str) -> str:
    """Human caption for a report PNG filename (falls back to a prettified slug)."""
    stem = os.path.splitext(os.path.basename(filename))[0]
    if stem in _CHART_TITLES:
        return _CHART_TITLES[stem]
    words = stem.replace('_', ' ').replace('pct', '%').replace('sfr', 'SFR')
    words = words.replace('non vacant', 'non-vacant')
    return words[:1].upper() + words[1:]


def _build_gallery(city_dir: str, exclude: Optional[set] = None) -> str:
    """Build the click-through chart-gallery HTML fragment by embedding every PNG in
    ``city_dir`` as a data URI. Returns '' when no charts are present so the section
    is omitted entirely."""
    exclude = exclude or set()
    pngs = sorted(
        p for p in glob.glob(os.path.join(city_dir, '*.png'))
        if os.path.basename(p) not in exclude
    )
    if not pngs:
        return ''
    thumbs = []
    for i, png in enumerate(pngs):
        with open(png, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode('ascii')
        title = html.escape(_pretty_chart_title(png))
        active = ' active' if i == 0 else ''
        thumbs.append(
            f'<img class="gv-thumb{active}" src="data:image/png;base64,{b64}" '
            f'data-title="{title}" alt="{title}" loading="lazy"/>'
        )
    return (
        '<section class="gallery" aria-label="Modeling analysis charts">'
        '<h2 class="gv-h">Modeling analysis charts</h2>'
        '<p class="gv-sub">The standard report charts for this city. '
        'Use the arrows or thumbnails to click through them.</p>'
        '<div class="gv-stage">'
        '<button class="gv-arrow" id="gv-prev" aria-label="Previous chart">&#8249;</button>'
        '<img id="gv-main" alt="Selected modeling chart"/>'
        '<button class="gv-arrow" id="gv-next" aria-label="Next chart">&#8250;</button>'
        '</div>'
        '<div class="gv-bar"><span id="gv-cap" class="gv-cap"></span>'
        '<span id="gv-count" class="gv-count"></span></div>'
        '<div class="gv-thumbs">' + ''.join(thumbs) + '</div>'
        '</section>'
    )


def _round_geometry(geo, precision: int):
    """Round coordinates in a GeoJSON geometry dict in place-ish."""
    def _round(coords):
        if isinstance(coords[0], (int, float)):
            return [round(coords[0], precision), round(coords[1], precision)]
        return [_round(c) for c in coords]

    geo = dict(geo)
    geo['coordinates'] = _round(geo['coordinates'])
    return geo


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>__TITLE__</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  :root{
    --ground:#f4f6f7; --panel:#ffffff; --ink:#16202a; --muted:#5c6b78; --line:#dde3e8;
    --accent:#0f766e; --pos:#c0392b; --neg:#1a7d46;
    --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}
  html,body{margin:0}
  .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);border:0}
  .wrap{font-family:var(--sans);color:var(--ink);background:var(--ground);
    max-width:1180px;margin:0 auto;padding:22px 20px 28px;line-height:1.5}
  .eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600}
  h1{font-size:clamp(20px,2.4vw,27px);line-height:1.18;margin:.35em 0 .3em;font-weight:650;
    letter-spacing:-.01em;text-wrap:balance;max-width:30ch}
  .sub{margin:0;color:var(--muted);font-size:14px;max-width:76ch}
  .sub b{color:var(--ink);font-weight:600}
  .stats{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 14px}
  .chip{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:9px 13px;min-width:110px}
  .chip .k{font-size:11px;letter-spacing:.03em;text-transform:uppercase;color:var(--muted)}
  .chip .v{font-size:19px;font-weight:650;font-variant-numeric:tabular-nums;margin-top:1px}
  .stage{display:grid;grid-template-columns:1fr 300px;gap:16px;align-items:start}
  @media(max-width:800px){.stage{grid-template-columns:1fr}}
  .mapbox{position:relative;background:#eef1f3;border:1px solid var(--line);border-radius:12px;overflow:hidden}
  #map{height:640px;width:100%}
  .mapbox:fullscreen{border-radius:0;border:0}
  .mapbox:fullscreen #map{height:100vh}
  .mapbox:-webkit-full-screen #map{height:100vh}
  .fsbtn{position:absolute;z-index:1000;left:52px;top:12px;font-family:var(--sans);font-size:12.5px;
    font-weight:600;color:var(--ink);background:rgba(255,255,255,.95);border:1px solid var(--line);
    border-radius:8px;padding:7px 11px;cursor:pointer;display:flex;align-items:center;gap:6px;
    box-shadow:0 1px 5px rgba(20,32,42,.12)}
  .fsbtn:hover{border-color:var(--accent);color:var(--accent)}
  .fsbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .leaflet-control-layers{border-radius:10px !important;border:1px solid var(--line) !important;
    box-shadow:0 1px 6px rgba(20,32,42,.1) !important;font-family:var(--sans);font-size:13px}
  .legend{line-height:1.65;color:var(--ink);background:rgba(255,255,255,.95);
    padding:9px 11px;border-radius:10px;border:1px solid var(--line);
    box-shadow:0 1px 6px rgba(20,32,42,.1);font-size:11.5px}
  .legend .lt{font-weight:650;margin-bottom:5px;font-size:11px;letter-spacing:.03em;text-transform:uppercase;color:var(--muted)}
  .legend .row{display:flex;align-items:center;gap:7px}
  .legend i{width:15px;height:12px;border-radius:2px;flex:none;border:1px solid rgba(0,0,0,.12)}
  .inspector{background:var(--panel);border:1px solid var(--line);border-radius:12px;
    padding:16px 16px 18px;position:sticky;top:12px;min-height:220px}
  .hint{color:var(--muted);font-size:13px}.hint b{color:var(--ink);font-weight:600}
  .ins-cat{font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--accent);font-weight:650}
  .ins-id{font-size:18px;font-weight:650;font-variant-numeric:tabular-nums;margin:2px 0 1px}
  .ins-adr{color:var(--muted);font-size:13.5px}.ins-own{color:var(--muted);font-size:12.5px;margin-top:1px}
  .pill{display:inline-flex;align-items:center;gap:6px;font-weight:650;font-size:13px;
    border-radius:999px;padding:4px 11px;margin:13px 0 4px}
  .pill.up{background:#fbeaea;color:var(--pos)}.pill.dn{background:#e7f5ec;color:var(--neg)}
  .pill.flat{background:#eef1f3;color:var(--muted)}
  table.kv{width:100%;border-collapse:collapse;margin-top:8px;font-size:13.5px}
  table.kv td{padding:6px 0;border-top:1px solid var(--line)}
  table.kv td.k{color:var(--muted)}
  table.kv td.v{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--mono)}
  .rec{margin-top:12px;font-size:12.5px}.rec a{color:var(--accent);font-weight:600;text-decoration:none}
  .rec a:hover{text-decoration:underline}
  .ft{margin-top:16px;color:var(--muted);font-size:12px;max-width:84ch}.ft b{color:var(--ink);font-weight:600}
  .gallery{margin-top:26px;border-top:1px solid var(--line);padding-top:20px}
  .gv-h{font-size:16px;font-weight:650;margin:0;letter-spacing:-.01em}
  .gv-sub{margin:.3em 0 14px;color:var(--muted);font-size:13px}
  .gv-stage{display:flex;align-items:center;gap:10px;justify-content:center;
    background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px}
  #gv-main{max-width:100%;max-height:520px;object-fit:contain;flex:1;min-width:0}
  .gv-arrow{flex:none;width:38px;height:38px;border-radius:50%;border:1px solid var(--line);
    background:var(--panel);color:var(--ink);font-size:20px;line-height:1;cursor:pointer}
  .gv-arrow:hover{border-color:var(--accent);color:var(--accent)}
  .gv-arrow:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .gv-bar{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:10px 2px 12px}
  .gv-cap{font-size:14px;font-weight:600;color:var(--ink)}
  .gv-count{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums;flex:none}
  .gv-thumbs{display:flex;flex-wrap:wrap;gap:8px}
  .gv-thumb{height:58px;width:auto;border-radius:6px;border:1px solid var(--line);
    background:var(--panel);cursor:pointer;object-fit:cover;opacity:.72;transition:opacity .1s,border-color .1s}
  .gv-thumb:hover{opacity:1}
  .gv-thumb.active{opacity:1;border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
</style>
</head>
<body>
<h2 class="sr-only">Interactive map of every modeled parcel, colored by how its property-tax bill changes under the reform. Toggle the road or satellite base map and click a parcel for its details.</h2>
<div class="wrap">
  <div class="eyebrow">Center for Land Economics &middot; LVTShift</div>
  <h1>__TITLE__</h1>
  <p class="sub">__SUBTITLE__</p>
  <div class="stats" id="stats"></div>
  <div class="stage">
    <div class="mapbox" id="mapbox">
      <div id="map"></div>
      <button class="fsbtn" id="fsbtn" aria-label="Toggle full screen">&#9974; Full screen</button>
    </div>
    <aside class="inspector" id="insp">
      <div class="hint"><b>Click any parcel</b> to see its parcel number, owner, address, and how its tax bill changes under the reform. Use the layer control to switch between road and satellite.</div>
    </aside>
  </div>
  <p class="ft"><b>How to read it.</b> Parcels with little building value relative to land (vacant lots, parking) tend to pay more; building-heavy parcels (apartments, offices) tend to pay less. Green = pays less, red = pays more, grey = no current tax to compare. Base maps: OpenStreetMap (road) and Esri World Imagery (satellite).</p>
  __GALLERY__
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA = __GEOJSON__;
const CENTER = __CENTER__;

const map = L.map('map', { preferCanvas: true }).setView(CENTER, 13);
const roadLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'
});
const satelliteLayer = L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  maxZoom: 19,
  attribution: 'Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community'
});
roadLayer.addTo(map);
L.control.layers({ 'Road': roadLayer, 'Satellite': satelliteLayer }, null,
  { collapsed: false, position: 'topright' }).addTo(map);

const money = v => v == null ? '\\u2014' : '$' + Math.round(v).toLocaleString();
const clsOf = p => p == null ? 'flat' : (p > 1 ? 'up' : (p < -1 ? 'dn' : 'flat'));
const insp = document.getElementById('insp');

let selected = null;
function inspect(p, lyr) {
  if (selected) layer.resetStyle(selected);
  selected = lyr; lyr.setStyle({ stroke: true, weight: 2.4, color: '#0b1116' }); lyr.bringToFront();
  const c = clsOf(p.pct);
  const pct = p.pct == null ? 'no current bill' : (p.pct >= 0 ? '+' : '') + p.pct + '%';
  const chg = p.chg == null ? '\\u2014' : (p.chg >= 0 ? '+' : '\\u2212') + money(Math.abs(p.chg));
  const label = c === 'up' ? 'Pays more' : (c === 'dn' ? 'Pays less' : '~ Neutral');
  const chgColor = c === 'up' ? 'var(--pos)' : (c === 'dn' ? 'var(--neg)' : 'inherit');
  let h = '<div class="ins-cat">' + (p.cat || '') + '</div>' +
    '<div class="ins-id">Parcel ' + (p.pid || '\\u2014') + '</div>';
  if (p.adr) h += '<div class="ins-adr">' + p.adr + '</div>';
  if (p.own) h += '<div class="ins-own">' + p.own + '</div>';
  h += '<div class="pill ' + c + '">' + label + ' \\u00b7 ' + pct + '</div>' +
    '<table class="kv"><tbody>' +
    '<tr><td class="k">Land value</td><td class="v">' + money(p.land) + '</td></tr>' +
    '<tr><td class="k">Building value</td><td class="v">' + money(p.imp) + '</td></tr>' +
    '<tr><td class="k">Current bill</td><td class="v">' + money(p.cur) + '</td></tr>' +
    '<tr><td class="k">Under reform</td><td class="v">' + money(p.new) + '</td></tr>' +
    '<tr><td class="k">Change</td><td class="v" style="color:' + chgColor + '">' + chg + '</td></tr>' +
    '</tbody></table>';
  if (p.url) h += '<div class="rec"><a href="' + p.url + '" target="_blank" rel="noopener">View county record &rarr;</a></div>';
  else h += '<div class="rec" style="color:var(--muted)">No public record link for this jurisdiction.</div>';
  insp.innerHTML = h;
}

const layer = L.geoJSON(DATA, {
  style: f => ({ stroke: false, fillColor: f.properties.c, fillOpacity: 0.85 }),
  onEachFeature: (f, lyr) => {
    lyr.on('click', () => inspect(f.properties, lyr));
    lyr.on('mouseover', () => { if (lyr !== selected) lyr.setStyle({ stroke: true, weight: 1.4, color: '#0b1116' }); });
    lyr.on('mouseout', () => { if (lyr !== selected) layer.resetStyle(lyr); });
  }
}).addTo(map);
try { map.fitBounds(layer.getBounds(), { padding: [20, 20] }); } catch (e) {}

const legend = L.control({ position: 'bottomright' });
legend.onAdd = function () {
  const div = L.DomUtil.create('div', 'legend');
  const rows = [
    ['#1a9850', 'Pays &ge;30% less'], ['#66bd63', '15\\u201330% less'], ['#a6d96a', '5\\u201315% less'],
    ['#ffffbf', '\\u00b15% (neutral)'], ['#fdae61', '5\\u201315% more'], ['#f46d43', '15\\u201330% more'],
    ['#d73027', '&ge;30% more'], ['#bdbdbd', 'No current bill']
  ];
  div.innerHTML = '<div class="lt">Change in tax bill</div>' +
    rows.map(r => '<div class="row"><i style="background:' + r[0] + '"></i>' + r[1] + '</div>').join('');
  return div;
};
legend.addTo(map);

// summary chips computed from the embedded data
const priced = DATA.features.map(f => f.properties.pct).filter(v => v != null).sort((a, b) => a - b);
const med = priced.length ? priced[Math.floor(priced.length / 2)] : 0;
const up = priced.length ? Math.round(priced.filter(v => v > 5).length / priced.length * 100) : 0;
const dn = priced.length ? Math.round(priced.filter(v => v < -5).length / priced.length * 100) : 0;
const chips = [
  ['Parcels', DATA.features.length.toLocaleString()],
  ['Median change', (med >= 0 ? '+' : '') + med.toFixed(1) + '%'],
  ['Pay less (>5%)', dn + '%'], ['Pay more (>5%)', up + '%']
];
document.getElementById('stats').innerHTML = chips.map(
  c => '<div class="chip"><div class="k">' + c[0] + '</div><div class="v">' + c[1] + '</div></div>').join('');

// full-screen toggle
const mapbox = document.getElementById('mapbox');
const fsbtn = document.getElementById('fsbtn');
fsbtn.addEventListener('click', () => {
  const fsEl = document.fullscreenElement || document.webkitFullscreenElement;
  if (fsEl) { (document.exitFullscreen || document.webkitExitFullscreen).call(document); }
  else { (mapbox.requestFullscreen || mapbox.webkitRequestFullscreen).call(mapbox); }
});
function onFsChange() {
  const on = !!(document.fullscreenElement || document.webkitFullscreenElement);
  fsbtn.innerHTML = on ? '\\u2715 Exit full screen' : '\\u26F6 Full screen';
  setTimeout(() => map.invalidateSize(), 120);
}
document.addEventListener('fullscreenchange', onFsChange);
document.addEventListener('webkitfullscreenchange', onFsChange);

// chart gallery — click through the report PNGs
const gvThumbs = Array.from(document.querySelectorAll('.gv-thumb'));
if (gvThumbs.length) {
  const gvMain = document.getElementById('gv-main');
  const gvCap = document.getElementById('gv-cap');
  const gvCount = document.getElementById('gv-count');
  let gi = 0;
  function showChart(i) {
    gi = (i + gvThumbs.length) % gvThumbs.length;
    gvMain.src = gvThumbs[gi].src;
    gvCap.textContent = gvThumbs[gi].dataset.title;
    gvCount.textContent = (gi + 1) + ' / ' + gvThumbs.length;
    gvThumbs.forEach((t, k) => t.classList.toggle('active', k === gi));
    gvThumbs[gi].scrollIntoView({ block: 'nearest', inline: 'nearest' });
  }
  document.getElementById('gv-prev').addEventListener('click', () => showChart(gi - 1));
  document.getElementById('gv-next').addEventListener('click', () => showChart(gi + 1));
  gvThumbs.forEach((t, k) => t.addEventListener('click', () => showChart(k)));
  showChart(0);
}
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Vector-tile (PMTiles + MapLibre) viewer for large cities
# ---------------------------------------------------------------------------

def _have_tippecanoe() -> bool:
    """True when both tippecanoe and ogr2ogr are on PATH (needed to build tiles)."""
    return shutil.which('tippecanoe') is not None and shutil.which('ogr2ogr') is not None


_TILE_ATTRS = [
    'parcel_id', 'tax_change_pct', 'current_tax', 'new_tax', 'tax_change',
    'taxable_land_value', 'taxable_improvement_value', 'owner_name',
    'owner_address', 'parcel_url', 'property_category',
]


def _build_pmtiles(gdf: gpd.GeoDataFrame, out_pmtiles: str, layer: str = 'parcels') -> str:
    """Build a PMTiles vector-tile archive from the parcel frame.

    Pipeline: write a lean GeoParquet (tile attributes + geometry) → ogr2ogr to
    GeoJSONSeq → tippecanoe to PMTiles. Requires tippecanoe + ogr2ogr on PATH.
    """
    keep = [c for c in _TILE_ATTRS if c in gdf.columns]
    g = gdf[keep + [gdf.geometry.name]].copy()
    if g.crs is None or g.crs.to_epsg() != 4326:
        g = g.to_crs(WGS84)
    tmpdir = tempfile.mkdtemp(prefix='pmtiles_')
    try:
        pq = os.path.join(tmpdir, 'src.parquet')
        gj = os.path.join(tmpdir, 'src.geojsonl')
        g.to_parquet(pq)
        subprocess.run(['ogr2ogr', '-f', 'GeoJSONSeq', gj, pq],
                       check=True, capture_output=True, text=True)
        os.makedirs(os.path.dirname(os.path.abspath(out_pmtiles)), exist_ok=True)
        subprocess.run(
            ['tippecanoe', '-o', out_pmtiles, '-l', layer, '-zg',
             '--drop-densest-as-needed', '--extend-zooms-if-still-dropping',
             '--read-parallel', '--force', '--quiet', gj],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"vector-tile build failed ({e.cmd[0]}): {e.stderr or e.stdout}") from e
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return out_pmtiles


def create_parcel_tile_map(
    source,
    city: str,
    output_dir: str = '../../analysis/reports',
    title: Optional[str] = None,
) -> str:
    """Build vector tiles + a MapLibre GL viewer for a (large) city.

    Writes ``{output_dir}/{city}/{city}.pmtiles`` and ``.../parcel_map.html``.
    Unlike the inline Leaflet map, this viewer MUST be opened over a local web
    server — the PMTiles protocol uses HTTP range requests, so a ``file://``
    double-click will not load the tiles. Run ``python3 -m http.server`` in the
    city report folder and open ``http://localhost:8000/parcel_map.html``.
    """
    if isinstance(source, (str, os.PathLike)):
        gdf = gpd.read_parquet(source)
    else:
        gdf = source
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(WGS84)

    out_city_dir = os.path.join(output_dir, city)
    os.makedirs(out_city_dir, exist_ok=True)
    pmtiles_name = f'{city}.pmtiles'
    _build_pmtiles(gdf, os.path.join(out_city_dir, pmtiles_name))

    bounds = gdf.total_bounds  # minx, miny, maxx, maxy
    center = [float((bounds[0] + bounds[2]) / 2), float((bounds[1] + bounds[3]) / 2)]  # lng, lat
    model_type = str(gdf['model_type'].iloc[0]) if 'model_type' in gdf.columns and len(gdf) else ''
    model_label = _model_label(model_type)
    city_name = city.replace('_', ' ').title()
    heading = title or f"{city_name} — who pays less, who pays more under {model_label}"
    subtitle = (
        f"All {len(gdf):,} modeled parcels as vector tiles, colored by how each parcel's "
        f"property-tax bill changes under a revenue-neutral {model_label}. Green = pays less, "
        f"red = pays more. Toggle the road / satellite base map and click a parcel to inspect it."
    )

    pct = pd.to_numeric(gdf['tax_change_pct'], errors='coerce').dropna() \
        if 'tax_change_pct' in gdf.columns else pd.Series([], dtype=float)
    med = float(pct.median()) if len(pct) else 0.0
    up = round(float((pct > 5).mean()) * 100) if len(pct) else 0
    dn = round(float((pct < -5).mean()) * 100) if len(pct) else 0
    chips = [('Parcels', f'{len(gdf):,}'), ('Median change', f'{med:+.1f}%'),
             ('Pay less (>5%)', f'{dn}%'), ('Pay more (>5%)', f'{up}%')]
    stats_html = ''.join(
        f'<div class="chip"><div class="k">{k}</div><div class="v">{v}</div></div>'
        for k, v in chips)

    gallery = _build_gallery(out_city_dir)
    out_path = os.path.join(out_city_dir, 'parcel_map.html')
    html_doc = (
        _PMTILES_HTML_TEMPLATE
        .replace('__TITLE__', html.escape(heading))
        .replace('__SUBTITLE__', html.escape(subtitle))
        .replace('__PMTILES__', pmtiles_name)
        .replace('__CITYPATH__', city)
        .replace('__CENTER__', json.dumps(center))
        .replace('__STATS__', stats_html)
        .replace('__GALLERY__', gallery)
    )
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(html_doc)
    sz = os.path.getsize(os.path.join(out_city_dir, pmtiles_name)) / 1e6
    print(f"  ✓ {city}: vector-tile map → {out_path}  "
          f"[{len(gdf):,} parcels; {pmtiles_name} {sz:.1f} MB; serve over http]")
    return out_path


_PMTILES_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>__TITLE__</title>
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet"/>
<style>
  :root{
    --ground:#f4f6f7; --panel:#ffffff; --ink:#16202a; --muted:#5c6b78; --line:#dde3e8;
    --accent:#0f766e; --pos:#c0392b; --neg:#1a7d46;
    --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box} html,body{margin:0}
  .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);border:0}
  .wrap{font-family:var(--sans);color:var(--ink);background:var(--ground);max-width:1180px;margin:0 auto;padding:22px 20px 28px;line-height:1.5}
  .eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600}
  h1{font-size:clamp(20px,2.4vw,27px);line-height:1.18;margin:.35em 0 .3em;font-weight:650;letter-spacing:-.01em;text-wrap:balance;max-width:30ch}
  .sub{margin:0;color:var(--muted);font-size:14px;max-width:76ch}.sub b{color:var(--ink);font-weight:600}
  .serve{margin:12px 0 0;background:#fff8e6;border:1px solid #f0d98c;color:#6b5600;border-radius:8px;padding:8px 12px;font-size:12.5px}
  .serve code{font-family:var(--mono);background:rgba(0,0,0,.06);padding:1px 5px;border-radius:4px}
  .stats{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}
  .chip{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:9px 13px;min-width:110px}
  .chip .k{font-size:11px;letter-spacing:.03em;text-transform:uppercase;color:var(--muted)}
  .chip .v{font-size:19px;font-weight:650;font-variant-numeric:tabular-nums;margin-top:1px}
  .stage{display:grid;grid-template-columns:1fr 300px;gap:16px;align-items:start}
  @media(max-width:800px){.stage{grid-template-columns:1fr}}
  .mapbox{position:relative;background:#eef1f3;border:1px solid var(--line);border-radius:12px;overflow:hidden}
  #map{height:640px;width:100%}
  .toggle{position:absolute;z-index:2;right:10px;top:10px;display:flex;background:rgba(255,255,255,.95);border:1px solid var(--line);border-radius:8px;overflow:hidden;box-shadow:0 1px 5px rgba(20,32,42,.12)}
  .toggle button{font-family:var(--sans);font-size:12.5px;font-weight:600;color:var(--ink);background:transparent;border:0;padding:7px 11px;cursor:pointer}
  .toggle button.active{background:var(--accent);color:#fff}
  .legend{position:absolute;z-index:2;right:10px;bottom:10px;background:rgba(255,255,255,.95);border:1px solid var(--line);border-radius:10px;padding:9px 11px;font-size:11.5px;box-shadow:0 1px 6px rgba(20,32,42,.1)}
  .legend .lt{font-weight:650;margin-bottom:5px;font-size:11px;letter-spacing:.03em;text-transform:uppercase;color:var(--muted)}
  .legend .row{display:flex;align-items:center;gap:7px;line-height:1.6}
  .legend i{width:15px;height:12px;border-radius:2px;flex:none;border:1px solid rgba(0,0,0,.12)}
  .inspector{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;position:sticky;top:12px;min-height:220px}
  .hint{color:var(--muted);font-size:13px}.hint b{color:var(--ink);font-weight:600}
  .ins-cat{font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--accent);font-weight:650}
  .ins-id{font-size:18px;font-weight:650;font-variant-numeric:tabular-nums;margin:2px 0 1px}
  .ins-adr{color:var(--muted);font-size:13.5px}.ins-own{color:var(--muted);font-size:12.5px;margin-top:1px}
  .pill{display:inline-flex;align-items:center;gap:6px;font-weight:650;font-size:13px;border-radius:999px;padding:4px 11px;margin:13px 0 4px}
  .pill.up{background:#fbeaea;color:var(--pos)}.pill.dn{background:#e7f5ec;color:var(--neg)}.pill.flat{background:#eef1f3;color:var(--muted)}
  table.kv{width:100%;border-collapse:collapse;margin-top:8px;font-size:13.5px}
  table.kv td{padding:6px 0;border-top:1px solid var(--line)}
  table.kv td.k{color:var(--muted)}table.kv td.v{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--mono)}
  .rec{margin-top:12px;font-size:12.5px}.rec a{color:var(--accent);font-weight:600;text-decoration:none}.rec a:hover{text-decoration:underline}
  .ft{margin-top:16px;color:var(--muted);font-size:12px;max-width:84ch}.ft b{color:var(--ink);font-weight:600}
  .gallery{margin-top:26px;border-top:1px solid var(--line);padding-top:20px}
  .gv-h{font-size:16px;font-weight:650;margin:0;letter-spacing:-.01em}
  .gv-sub{margin:.3em 0 14px;color:var(--muted);font-size:13px}
  .gv-stage{display:flex;align-items:center;gap:10px;justify-content:center;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px}
  #gv-main{max-width:100%;max-height:520px;object-fit:contain;flex:1;min-width:0}
  .gv-arrow{flex:none;width:38px;height:38px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--ink);font-size:20px;line-height:1;cursor:pointer}
  .gv-arrow:hover{border-color:var(--accent);color:var(--accent)}
  .gv-bar{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:10px 2px 12px}
  .gv-cap{font-size:14px;font-weight:600;color:var(--ink)}.gv-count{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums;flex:none}
  .gv-thumbs{display:flex;flex-wrap:wrap;gap:8px}
  .gv-thumb{height:58px;width:auto;border-radius:6px;border:1px solid var(--line);background:var(--panel);cursor:pointer;object-fit:cover;opacity:.72;transition:opacity .1s,border-color .1s}
  .gv-thumb:hover{opacity:1}.gv-thumb.active{opacity:1;border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
</style>
</head>
<body>
<h2 class="sr-only">Interactive vector-tile map of every modeled parcel, colored by how its property-tax bill changes under the reform. Toggle road or satellite and click a parcel for details.</h2>
<div class="wrap">
  <div class="eyebrow">Center for Land Economics &middot; LVTShift</div>
  <h1>__TITLE__</h1>
  <p class="sub">__SUBTITLE__</p>
  <p class="serve">This large-city map uses vector tiles and needs a <b>range-capable</b> web server (plain <code>python3 -m http.server</code> will <b>not</b> work — it can't byte-serve the tiles). From the repo root run <code>python3 scripts/serve_maps.py</code>, then open <code>http://localhost:8000/analysis/reports/__CITYPATH__/parcel_map.html</code>.</p>
  <div class="stats">__STATS__</div>
  <div class="stage">
    <div class="mapbox">
      <div id="map"></div>
      <div class="toggle"><button id="t-road" class="active">Road</button><button id="t-sat">Satellite</button></div>
      <div class="legend" id="legend"></div>
    </div>
    <aside class="inspector" id="insp">
      <div class="hint"><b>Click any parcel</b> to see its parcel number, owner, address, land/building values, and how its tax bill changes under the reform.</div>
    </aside>
  </div>
  <p class="ft"><b>How to read it.</b> Parcels with little building value relative to land (vacant lots, parking) tend to pay more; building-heavy parcels (apartments, offices) tend to pay less. Green = pays less, red = pays more, grey = no current tax. Base maps: OpenStreetMap (road) and Esri World Imagery (satellite).</p>
  __GALLERY__
</div>
<script src="https://unpkg.com/pmtiles@3.2.0/dist/pmtiles.js"></script>
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script>
const CENTER = __CENTER__;
const COLOR = ['case', ['!', ['has', 'tax_change_pct']], '#bdbdbd',
  ['step', ['to-number', ['get', 'tax_change_pct']],
    '#1a9850', -30, '#66bd63', -15, '#a6d96a', -5, '#ffffbf', 5, '#fdae61', 15, '#f46d43', 30, '#d73027']];

let protocol = new pmtiles.Protocol();
maplibregl.addProtocol('pmtiles', protocol.tile);

const map = new maplibregl.Map({
  container: 'map', center: CENTER, zoom: 11,
  style: {
    version: 8,
    sources: {
      osm: { type: 'raster', tileSize: 256, attribution: '&copy; OpenStreetMap contributors',
        tiles: ['https://a.tile.openstreetmap.org/{z}/{x}/{y}.png', 'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png', 'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'] },
      esri: { type: 'raster', tileSize: 256, attribution: 'Tiles &copy; Esri, Maxar, Earthstar Geographics',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'] },
      parcels: { type: 'vector', url: 'pmtiles://./__PMTILES__' }
    },
    layers: [
      { id: 'osm', type: 'raster', source: 'osm' },
      { id: 'esri', type: 'raster', source: 'esri', layout: { visibility: 'none' } },
      { id: 'parcels-fill', type: 'fill', source: 'parcels', 'source-layer': 'parcels',
        paint: { 'fill-color': COLOR, 'fill-opacity': 0.75 } },
      { id: 'parcels-selected', type: 'line', source: 'parcels', 'source-layer': 'parcels',
        paint: { 'line-color': '#0b1116', 'line-width': 2 }, filter: ['==', ['get', 'parcel_id'], '__none__'] }
    ]
  }
});
map.addControl(new maplibregl.NavigationControl(), 'top-left');
map.addControl(new maplibregl.FullscreenControl(), 'top-left');

// base-map toggle
const bRoad = document.getElementById('t-road'), bSat = document.getElementById('t-sat');
bRoad.onclick = () => { map.setLayoutProperty('osm', 'visibility', 'visible'); map.setLayoutProperty('esri', 'visibility', 'none'); bRoad.classList.add('active'); bSat.classList.remove('active'); };
bSat.onclick = () => { map.setLayoutProperty('osm', 'visibility', 'none'); map.setLayoutProperty('esri', 'visibility', 'visible'); bSat.classList.add('active'); bRoad.classList.remove('active'); };

const insp = document.getElementById('insp');
const money = v => (v == null || v === '' || isNaN(Number(v))) ? '\\u2014' : '$' + Math.round(Number(v)).toLocaleString();
const clsOf = p => (p == null || p === '') ? 'flat' : (Number(p) > 1 ? 'up' : (Number(p) < -1 ? 'dn' : 'flat'));

map.on('click', 'parcels-fill', (e) => {
  if (!e.features.length) return;
  const p = e.features[0].properties;
  const pctv = (p.tax_change_pct === undefined || p.tax_change_pct === null || p.tax_change_pct === '') ? null : Number(p.tax_change_pct);
  const c = clsOf(pctv);
  const pct = pctv == null ? 'no current bill' : (pctv >= 0 ? '+' : '') + pctv.toFixed(1) + '%';
  const chgn = (p.tax_change == null || p.tax_change === '') ? null : Number(p.tax_change);
  const chg = chgn == null ? '\\u2014' : (chgn >= 0 ? '+' : '\\u2212') + money(Math.abs(chgn));
  const label = c === 'up' ? 'Pays more' : (c === 'dn' ? 'Pays less' : '~ Neutral');
  const chgColor = c === 'up' ? 'var(--pos)' : (c === 'dn' ? 'var(--neg)' : 'inherit');
  let h = '<div class="ins-cat">' + (p.property_category || '') + '</div>' +
    '<div class="ins-id">Parcel ' + (p.parcel_id || '\\u2014') + '</div>';
  if (p.owner_address) h += '<div class="ins-adr">' + p.owner_address + '</div>';
  if (p.owner_name) h += '<div class="ins-own">' + p.owner_name + '</div>';
  h += '<div class="pill ' + c + '">' + label + ' \\u00b7 ' + pct + '</div>' +
    '<table class="kv"><tbody>' +
    '<tr><td class="k">Land value</td><td class="v">' + money(p.taxable_land_value) + '</td></tr>' +
    '<tr><td class="k">Building value</td><td class="v">' + money(p.taxable_improvement_value) + '</td></tr>' +
    '<tr><td class="k">Current bill</td><td class="v">' + money(p.current_tax) + '</td></tr>' +
    '<tr><td class="k">Under reform</td><td class="v">' + money(p.new_tax) + '</td></tr>' +
    '<tr><td class="k">Change</td><td class="v" style="color:' + chgColor + '">' + chg + '</td></tr>' +
    '</tbody></table>';
  if (p.parcel_url) h += '<div class="rec"><a href="' + p.parcel_url + '" target="_blank" rel="noopener">View county record &rarr;</a></div>';
  insp.innerHTML = h;
  map.setFilter('parcels-selected', ['==', ['get', 'parcel_id'], p.parcel_id == null ? '__none__' : p.parcel_id]);
});
map.on('mouseenter', 'parcels-fill', () => { map.getCanvas().style.cursor = 'pointer'; });
map.on('mouseleave', 'parcels-fill', () => { map.getCanvas().style.cursor = ''; });

const L = [['#1a9850', 'Pays \\u226530% less'], ['#66bd63', '15\\u201330% less'], ['#a6d96a', '5\\u201315% less'],
  ['#ffffbf', '\\u00b15% (neutral)'], ['#fdae61', '5\\u201315% more'], ['#f46d43', '15\\u201330% more'],
  ['#d73027', '\\u226530% more'], ['#bdbdbd', 'No current bill']];
document.getElementById('legend').innerHTML = '<div class="lt">Change in tax bill</div>' +
  L.map(r => '<div class="row"><i style="background:' + r[0] + '"></i>' + r[1] + '</div>').join('');

// chart gallery — click through the report PNGs
const gvThumbs = Array.from(document.querySelectorAll('.gv-thumb'));
if (gvThumbs.length) {
  const gvMain = document.getElementById('gv-main'), gvCap = document.getElementById('gv-cap'), gvCount = document.getElementById('gv-count');
  let gi = 0;
  function showChart(i) {
    gi = (i + gvThumbs.length) % gvThumbs.length;
    gvMain.src = gvThumbs[gi].src; gvCap.textContent = gvThumbs[gi].dataset.title;
    gvCount.textContent = (gi + 1) + ' / ' + gvThumbs.length;
    gvThumbs.forEach((t, k) => t.classList.toggle('active', k === gi));
  }
  document.getElementById('gv-prev').addEventListener('click', () => showChart(gi - 1));
  document.getElementById('gv-next').addEventListener('click', () => showChart(gi + 1));
  gvThumbs.forEach((t, k) => t.addEventListener('click', () => showChart(k)));
  showChart(0);
}
</script>
</body>
</html>
"""
