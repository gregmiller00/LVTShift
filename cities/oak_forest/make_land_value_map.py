"""
Generate a choropleth map of estimated land market value per acre for Oak Forest, IL.
Output: analysis/reports/oak_forest/land_value_map.png
"""
import sqlite3
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import contextily as cx
from shapely import wkt

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SIBLING = Path('C:/projects/oak-forest-profit-loss-map')
PTAXSIM_DB = SIBLING / 'data/ptaxsim/ptaxsim-2024.0.0.db'
CCAO_DIR = SIBLING / 'data/ccao'
OUT_PATH = REPO_ROOT / 'analysis/reports/oak_forest/land_value_map.png'

EQ_FACTOR = 3.0163  # Cook County TY2023 final equalization factor

LOA = {
    'residential': 0.10,
    'commercial':  0.25,
    'industrial':  0.25,
    'vacant':      0.10,
    'other':       0.10,
    'exempt':      0.00,
}

LAND_USE_MAP = {
    '2': 'residential', '3': 'residential', '9': 'residential',
    '5': 'commercial',  '6': 'industrial',
    '0': 'exempt',      '4': 'exempt',  'E': 'exempt', 'X': 'exempt',
    '1': 'vacant',      '8': 'other',
}

def main():
    # ── Load parcel universe (Oak Forest pins + class codes) ─────────────────
    print('Loading parcel universe...')
    universe = pd.read_parquet(CCAO_DIR / 'parcel_universe.parquet')
    universe['pin'] = universe['pin'].astype(str).str.zfill(14)
    universe['pin10'] = universe['pin'].str[:10]
    universe['land_use'] = (
        universe['class'].astype(str).str.strip().str[0].str.upper()
        .map(LAND_USE_MAP).fillna('other')
    )
    print(f'  {len(universe):,} Oak Forest parcels')

    # ── Load CCAO board-certified land AV ────────────────────────────────────
    print('Loading assessed values...')
    av = pd.read_parquet(CCAO_DIR / 'historic_av.parquet')
    av['pin'] = av['pin'].astype(str).str.zfill(14)
    av['board_land'] = pd.to_numeric(av['board_land'], errors='coerce').fillna(0.0)
    av = (
        av.sort_values('board_land', ascending=False)
        .drop_duplicates(subset='pin', keep='first')
        [['pin', 'board_land']]
    )

    # ── Load PTAXSIM parcel geometries ───────────────────────────────────────
    print('Loading PTAXSIM geometries...')
    oak_pin10s = tuple(universe['pin10'].unique())
    placeholders = ','.join('?' * len(oak_pin10s))
    with sqlite3.connect(PTAXSIM_DB) as conn:
        geo_df = pd.read_sql_query(
            f'''
            SELECT pin10, geometry
            FROM pin_geometry_raw
            WHERE pin10 IN ({placeholders})
              AND start_year <= 2023
              AND (end_year >= 2023 OR end_year IS NULL)
            ''',
            conn,
            params=list(oak_pin10s),
        )
    print(f'  {len(geo_df):,} geometry records')

    # Deduplicate pin10 (keep most recent vintage)
    geo_df = geo_df.drop_duplicates(subset='pin10', keep='first')

    # ── Merge ────────────────────────────────────────────────────────────────
    df = universe.merge(av, on='pin', how='left')
    df['board_land'] = df['board_land'].fillna(0.0)
    df = df.merge(geo_df, on='pin10', how='inner')
    print(f'  {len(df):,} parcels with geometry')

    # ── Compute land market value ─────────────────────────────────────────────
    loa_series = df['land_use'].map(LOA).fillna(0.10)
    # Market value = AV / LOA × equalization factor
    df['land_market_value'] = np.where(
        loa_series > 0,
        df['board_land'] * EQ_FACTOR / loa_series,
        0.0,
    )

    # Per-acre land value using residential characteristics lot size
    res_chars = pd.read_parquet(CCAO_DIR / 'res_chars.parquet')
    res_chars['pin'] = res_chars['pin'].astype(str).str.zfill(14)
    res_chars['char_land_sf'] = pd.to_numeric(res_chars['char_land_sf'], errors='coerce').fillna(0)
    res_chars = (
        res_chars.groupby('pin', as_index=False)
        .agg(char_land_sf=('char_land_sf', 'max'))
    )
    com_chars = pd.read_parquet(CCAO_DIR / 'commercial_chars.parquet')
    com_chars['pin'] = com_chars['pin'].astype(str).str.zfill(14)
    com_chars['landsf'] = pd.to_numeric(com_chars['landsf'], errors='coerce').fillna(0)
    com_chars = com_chars[com_chars['landsf'] > 0].drop_duplicates('pin', keep='first')[['pin', 'landsf']]

    df = df.merge(res_chars[['pin', 'char_land_sf']], on='pin', how='left')
    df = df.merge(com_chars, on='pin', how='left')
    df['char_land_sf'] = df['char_land_sf'].fillna(0)
    df['landsf'] = df['landsf'].fillna(0)
    df['land_area_sqft'] = np.where(df['char_land_sf'] > 0, df['char_land_sf'], df['landsf'])

    # Per-sqft value for parcels with known lot area
    has_area = df['land_area_sqft'] > 0
    df['land_value_per_sqft'] = np.where(
        has_area & (df['land_market_value'] > 0),
        df['land_market_value'] / df['land_area_sqft'],
        np.nan,
    )

    # ── Build GeoDataFrame ───────────────────────────────────────────────────
    print('Building GeoDataFrame...')
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
    gdf = gdf.to_crs('EPSG:3857')  # Web Mercator for contextily basemap

    # ── Map: total land market value (exclude exempt/zero) ───────────────────
    plot_df = gdf[
        (gdf['land_market_value'] > 0) &
        (gdf['land_use'] != 'exempt')
    ].copy()

    # Clip top 1% to prevent outliers from washing out the color scale
    vmax = plot_df['land_market_value'].quantile(0.99)
    vmin = plot_df['land_market_value'].quantile(0.01)

    print(f'  Plotting {len(plot_df):,} parcels  (land value ${vmin:,.0f}–${vmax:,.0f} at 1–99th pct)')

    fig, ax = plt.subplots(1, 1, figsize=(12, 10))

    plot_df.plot(
        column='land_market_value',
        ax=ax,
        cmap='YlOrRd',
        vmin=vmin,
        vmax=vmax,
        linewidth=0.05,
        edgecolor='#cccccc',
        legend=True,
        legend_kwds={
            'label': 'Estimated Land Market Value ($)',
            'orientation': 'horizontal',
            'shrink': 0.6,
            'pad': 0.02,
            'format': mticker.FuncFormatter(lambda x, _: f'${x/1000:.0f}K'),
        },
        missing_kwds={'color': '#eeeeee', 'label': 'No data'},
    )

    # Add basemap
    try:
        cx.add_basemap(ax, source=cx.providers.CartoDB.Positron, zoom=13, alpha=0.5)
    except Exception as e:
        print(f'  Basemap skipped: {e}')

    ax.set_axis_off()
    ax.set_title(
        'Oak Forest, IL — Estimated Land Market Value by Parcel\n'
        'Based on CCAO Board-Certified Assessed Value × Equalization Factor ÷ Level of Assessment (TY2023)',
        fontsize=13, pad=14,
    )

    fig.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=180, bbox_inches='tight', facecolor='white')
    print(f'Saved: {OUT_PATH}')


if __name__ == '__main__':
    main()
