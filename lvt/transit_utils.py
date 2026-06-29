import os
import zipfile
from typing import Callable, Optional, Tuple, Union

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

MOBILITY_DATABASE_CATALOG_URL = 'https://bit.ly/catalogs-csv'
ACRE_SQM = 4046.86


def download_gtfs_from_mobility_database(
    cache_path: str,
    provider: str,
    subdivision: Optional[str] = None,
    timeout: int = 180,
) -> str:
    """
    Download a GTFS feed via the Mobility Database catalog, cached locally.

    Parameters
    ----------
    cache_path : str
        Local path for the GTFS zip. If it exists, no download happens.
    provider : str
        Substring match against the catalog's provider column
        (e.g. 'Metro Transit', 'SEPTA', 'Valley Metro').
    subdivision : str, optional
        State/province name to disambiguate providers (e.g. 'Minnesota').
    timeout : int
        Request timeout in seconds.

    Returns
    -------
    str
        cache_path, for chaining.
    """
    if os.path.exists(cache_path):
        return cache_path
    catalog = pd.read_csv(MOBILITY_DATABASE_CATALOG_URL, low_memory=False)
    mask = (
        catalog['provider'].str.contains(provider, case=False, na=False)
        & (catalog['data_type'] == 'gtfs')
    )
    if subdivision is not None:
        mask &= catalog['location.subdivision_name'] == subdivision
    matches = catalog[mask]
    if len(matches) == 0:
        raise ValueError(f"No GTFS feed found for provider '{provider}' (subdivision={subdivision})")
    feed = matches.iloc[0]
    url = feed['urls.latest'] if pd.notna(feed['urls.latest']) else feed['urls.direct_download']
    print(f"Downloading GTFS feed mdb-{feed['mdb_source_id']} ({feed['provider']})")
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    with open(cache_path, 'wb') as f:
        f.write(resp.content)
    return cache_path


def gtfs_route_stops(
    gtfs_zip_path: str,
    route_selector: Union[str, Callable[[pd.DataFrame], pd.Series]],
    max_shapes_per_route: int = 6,
) -> dict:
    """
    Extract routes, stops, and alignments for a subset of GTFS routes.

    Parameters
    ----------
    gtfs_zip_path : str
        Path to a GTFS zip file.
    route_selector : str or callable
        If a string, routes whose route_long_name starts with it are kept
        (e.g. 'METRO' selects Twin Cities LRT + BRT). If a callable, it
        receives the routes DataFrame and returns a boolean mask.
    max_shapes_per_route : int
        Number of most-used shape variants merged into each route alignment.

    Returns
    -------
    dict
        routes : DataFrame of selected routes (route_id as str)
        stops : GeoDataFrame of all stops served by those routes (EPSG:4326)
        stop_route_pairs : DataFrame of unique (stop_id, route_id) pairs
        route_lines : GeoDataFrame of route alignments with route_color (EPSG:4326)
    """
    gtfs = zipfile.ZipFile(gtfs_zip_path)
    routes = pd.read_csv(gtfs.open('routes.txt'), dtype={'route_id': str})
    if callable(route_selector):
        selected = routes[route_selector(routes)].copy()
    else:
        selected = routes[routes['route_long_name'].astype(str).str.startswith(route_selector)].copy()

    trips = pd.read_csv(gtfs.open('trips.txt'), usecols=['route_id', 'trip_id', 'shape_id'], dtype=str)
    trip_ids = set(trips.loc[trips['route_id'].isin(selected['route_id']), 'trip_id'])

    stop_times = pd.read_csv(gtfs.open('stop_times.txt'), usecols=['trip_id', 'stop_id'], dtype=str)
    selected_stop_times = stop_times[stop_times['trip_id'].isin(trip_ids)]

    stops = pd.read_csv(gtfs.open('stops.txt'), dtype={'stop_id': str})
    stops = stops[stops['stop_id'].isin(set(selected_stop_times['stop_id']))]
    stops_gdf = gpd.GeoDataFrame(
        stops, geometry=gpd.points_from_xy(stops['stop_lon'], stops['stop_lat']), crs='EPSG:4326'
    )

    stop_route_pairs = (
        selected_stop_times.merge(trips[['trip_id', 'route_id']], on='trip_id')
        [['stop_id', 'route_id']].drop_duplicates()
    )

    shapes = pd.read_csv(gtfs.open('shapes.txt'), dtype={'shape_id': str})
    line_records = []
    for _, rt in selected.iterrows():
        shape_ids = trips.loc[trips['route_id'] == rt['route_id'], 'shape_id'].value_counts()
        geoms = []
        for sid in shape_ids.index[:max_shapes_per_route]:
            pts = shapes[shapes['shape_id'] == sid].sort_values('shape_pt_sequence')
            geoms.append(LineString(zip(pts['shape_pt_lon'], pts['shape_pt_lat'])))
        color = rt.get('route_color')
        line_records.append({
            'route_id': rt['route_id'],
            'route_name': rt['route_long_name'],
            'route_color': f'#{color}' if pd.notna(color) else '#555555',
            'geometry': unary_union(geoms),
        })
    route_lines = gpd.GeoDataFrame(line_records, crs='EPSG:4326')

    return {'routes': selected, 'stops': stops_gdf,
            'stop_route_pairs': stop_route_pairs, 'route_lines': route_lines}


def get_walk_network(
    boundary_geom,
    boundary_crs: str,
    graph_path: str,
    buffer_m: float = 1000,
    to_crs: str = 'EPSG:26915',
):
    """
    Download (or load cached) the OSM walking network covering a boundary.

    Parameters
    ----------
    boundary_geom : shapely geometry
        Area the network must cover (e.g. city boundary), in a projected CRS.
    boundary_crs : str
        CRS of boundary_geom. Must be projected (meters) so buffer_m is honest.
    graph_path : str
        GraphML cache path. Downloaded once from Overpass, reloaded after.
    buffer_m : float
        Extra margin around the boundary so sheds near the edge can route outward.
    to_crs : str
        Projected CRS for the returned graph (use the city's UTM zone).

    Returns
    -------
    networkx.MultiDiGraph
        Walking network projected to to_crs, edge lengths in meters.
    """
    import osmnx as ox

    if os.path.exists(graph_path):
        G = ox.io.load_graphml(graph_path)
    else:
        poly_4326 = gpd.GeoSeries(
            [boundary_geom.buffer(buffer_m)], crs=boundary_crs
        ).to_crs(epsg=4326).iloc[0]
        G = ox.graph.graph_from_polygon(poly_4326, network_type='walk', simplify=True, retain_all=True)
        ox.io.save_graphml(G, graph_path)
    return ox.projection.project_graph(G, to_crs=to_crs)


def route_walk_sheds(
    G,
    stops_gdf: gpd.GeoDataFrame,
    id_col: str = 'stop_id',
    cutoff_m: float = 800,
    street_buffer_m: float = 60,
) -> gpd.GeoDataFrame:
    """
    Network-routed isochrone polygon around each stop.

    Each stop snaps to its nearest network node; Dijkstra walks cutoff_m of
    network distance outward; the reachable streets are buffered by
    street_buffer_m to cover the parcels fronting them.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        Projected walking network from get_walk_network (edge length in meters).
    stops_gdf : GeoDataFrame
        Stop points in the same CRS as G.
    id_col : str
        Stop identifier column carried into the result.
    cutoff_m : float
        Maximum network walking distance in meters (800 m ~ 10 minutes).
    street_buffer_m : float
        Buffer around reachable streets, roughly one parcel depth.

    Returns
    -------
    GeoDataFrame
        One isochrone polygon per stop with its id_col, in stops_gdf's CRS.
    """
    import networkx as nx
    import osmnx as ox

    stop_nodes = ox.distance.nearest_nodes(G, stops_gdf.geometry.x.values, stops_gdf.geometry.y.values)
    edges = ox.convert.graph_to_gdfs(G, nodes=False, edges=True)
    edge_u = edges.index.get_level_values('u')
    edge_v = edges.index.get_level_values('v')
    shed_geoms = []
    for node in stop_nodes:
        reach = set(nx.single_source_dijkstra_path_length(G, node, cutoff=cutoff_m, weight='length'))
        sub = edges[edge_u.isin(reach) & edge_v.isin(reach)]
        shed_geoms.append(unary_union(sub.geometry.values).buffer(street_buffer_m))
    return gpd.GeoDataFrame({id_col: stops_gdf[id_col].values}, geometry=shed_geoms, crs=stops_gdf.crs)


def fetch_osm_parking(
    boundary_gdf: gpd.GeoDataFrame,
    cache_path: str,
    to_crs: str = 'EPSG:26915',
    exclude_types: Tuple[str, ...] = ('underground', 'lane'),
    timeout: int = 180,
) -> gpd.GeoDataFrame:
    """
    Fetch OSM amenity=parking polygons covering a boundary via Overpass, cached.

    Assessor land-use codes often only flag structured ramps/garages; OSM is
    typically the only source that captures surface parking lots.

    Parameters
    ----------
    boundary_gdf : GeoDataFrame
        Area of interest (any CRS); its bounding box scopes the Overpass query
        and results are clipped to features intersecting the boundary.
    cache_path : str
        GeoPackage cache path. The cache stores all parking types; exclusions
        are applied after load so they can be changed without re-fetching.
    to_crs : str
        Projected CRS for the returned GeoDataFrame.
    exclude_types : tuple of str
        OSM parking= values to drop (default: underground garages, on-street lanes).
    timeout : int
        Request timeout in seconds.

    Returns
    -------
    GeoDataFrame
        Parking polygons with osm_id and parking_type columns, in to_crs.
    """
    if os.path.exists(cache_path):
        parking = gpd.read_file(cache_path).to_crs(to_crs)
    else:
        minx, miny, maxx, maxy = boundary_gdf.to_crs(epsg=4326).total_bounds
        bbox = f'{miny},{minx},{maxy},{maxx}'
        query = (
            '[out:json][timeout:120];\n'
            f'(way["amenity"="parking"]({bbox});\n'
            f' relation["amenity"="parking"]({bbox}););\n'
            'out geom;'
        )
        resp = requests.post('https://overpass-api.de/api/interpreter', data=query.encode(),
                             headers={'User-Agent': 'LVTShift/1.0'}, timeout=timeout)
        resp.raise_for_status()
        polys = []
        for el in resp.json()['elements']:
            if el['type'] == 'way' and 'geometry' in el:
                rings = [el['geometry']]
            elif el['type'] == 'relation':
                rings = [m['geometry'] for m in el.get('members', [])
                         if m.get('role') == 'outer' and 'geometry' in m]
            else:
                rings = []
            for ring in rings:
                coords = [(p['lon'], p['lat']) for p in ring]
                if len(coords) >= 4 and coords[0] == coords[-1]:
                    polys.append({'osm_id': el['id'],
                                  'parking_type': el.get('tags', {}).get('parking', ''),
                                  'geometry': Polygon(coords)})
        parking = gpd.GeoDataFrame(polys, crs='EPSG:4326')
        parking['geometry'] = parking['geometry'].buffer(0)
        parking = parking.to_crs(to_crs)
        boundary_union = boundary_gdf.to_crs(to_crs).union_all()
        parking = parking[parking.intersects(boundary_union)]
        parking.to_file(cache_path)
    return parking[~parking['parking_type'].isin(list(exclude_types))]


def flag_parking_parcels(
    parcels_gdf: gpd.GeoDataFrame,
    parking_union,
    category_col: Optional[str] = None,
    parking_category: str = 'Parking',
    coverage_threshold: float = 0.5,
) -> gpd.GeoDataFrame:
    """
    Flag parcels that are parking lots, by assessor category or OSM coverage.

    Adds parcel_sqm, parking_overlap_sqm, and is_parking_lot columns.

    Parameters
    ----------
    parcels_gdf : GeoDataFrame
        Parcels in a projected CRS matching parking_union.
    parking_union : shapely geometry
        Union of OSM parking polygons (same CRS as parcels_gdf).
    category_col : str, optional
        Property category column; values equal to parking_category flag the
        parcel regardless of OSM coverage (catches ramps OSM may map as buildings).
    parking_category : str
        Value in category_col identifying parking.
    coverage_threshold : float
        Minimum share of the parcel covered by OSM parking to flag it.

    Returns
    -------
    GeoDataFrame
        Copy of parcels_gdf with the three added columns.
    """
    out = parcels_gdf.copy()
    out['geometry'] = out.geometry.buffer(0)
    out['parcel_sqm'] = out.geometry.area
    out['parking_overlap_sqm'] = out.geometry.intersection(parking_union).area
    coverage = out['parking_overlap_sqm'] / out['parcel_sqm'].replace(0, np.nan)
    out['is_parking_lot'] = coverage >= coverage_threshold
    if category_col is not None:
        out['is_parking_lot'] |= out[category_col] == parking_category
    return out


def walk_shed_stats(
    shed,
    all_parcels_gdf: gpd.GeoDataFrame,
    value_parcels_gdf: gpd.GeoDataFrame,
    parking_union,
    label: str,
    n_stops: int,
    taxable_flag_col: str = 'pays_city_tax',
    parking_flag_col: str = 'is_parking_lot',
    land_value_col: str = 'EMVLand1',
    total_value_col: str = 'EMVTotal1',
    current_tax_col: str = 'current_tax',
    new_tax_col: str = 'new_tax_tc',
    parcel_area_col: str = 'parcel_sqm',
) -> dict:
    """
    Land composition and parking value shares for one walk shed union.

    Any value parcel that intersects the shed is included in the value
    calculations; land composition uses geometric unions clipped to the
    shed to avoid double counting stacked/overlapping parcels.

    Parameters
    ----------
    shed : shapely geometry
        Walk shed union, in the same projected CRS as the parcel layers.
    all_parcels_gdf : GeoDataFrame
        Every parcel (taxable and exempt) with valid geometry, for land
        composition. Must contain taxable_flag_col.
    value_parcels_gdf : GeoDataFrame
        Modeled taxable parcels (e.g. condo-collapsed city parcels) from
        flag_parking_parcels, for value shares.
    parking_union : shapely geometry
        Union of OSM parking polygons.
    label : str
        Row label (e.g. route name).
    n_stops : int
        Number of stops whose sheds form this union.
    taxable_flag_col, parking_flag_col, land_value_col, total_value_col,
    current_tax_col, new_tax_col, parcel_area_col : str
        Column names in the parcel layers.

    Returns
    -------
    dict
        One summary row; collect into a DataFrame across lines.
    """
    shed = shed.buffer(0)
    shed_acres = shed.area / ACRE_SQM
    parking_in_shed = parking_union.intersection(shed)
    near = all_parcels_gdf.iloc[all_parcels_gdf.sindex.query(shed, predicate='intersects')]
    taxable_geom = near.loc[near[taxable_flag_col]].geometry.union_all().intersection(shed)
    parcel_geom = near.geometry.union_all().intersection(shed)
    in_shed = value_parcels_gdf.iloc[value_parcels_gdf.sindex.query(shed, predicate='intersects')]
    g = in_shed.groupby(parking_flag_col).agg(
        n=(land_value_col, 'size'), land_value=(land_value_col, 'sum'),
        total_value=(total_value_col, 'sum'),
        acres=(parcel_area_col, lambda s: s.sum() / ACRE_SQM),
        current_tax=(current_tax_col, 'sum'), new_tax=(new_tax_col, 'sum')
    )
    pk, npk = g.loc[True], g.loc[False]
    return {
        'line': label,
        'stops': n_stops,
        'shed_acres': shed_acres,
        'parking_pct_of_shed': parking_in_shed.area / ACRE_SQM / shed_acres * 100,
        'taxable_pct_of_shed': taxable_geom.area / ACRE_SQM / shed_acres * 100,
        'exempt_pct_of_shed': (parcel_geom.area - taxable_geom.area) / ACRE_SQM / shed_acres * 100,
        'row_other_pct_of_shed': (shed.area - parcel_geom.area) / ACRE_SQM / shed_acres * 100,
        'parking_pct_of_taxable_land': taxable_geom.intersection(parking_in_shed).area / taxable_geom.area * 100,
        'parking_lots': int(pk['n']),
        'taxable_parcels': int(g['n'].sum()),
        'parking_pct_of_parcel_land': pk['acres'] / g['acres'].sum() * 100,
        'parking_pct_of_land_value': pk['land_value'] / g['land_value'].sum() * 100,
        'parking_pct_of_total_emv': pk['total_value'] / g['total_value'].sum() * 100,
        'parking_lv_per_acre': pk['land_value'] / pk['acres'],
        'nonparking_lv_per_acre': npk['land_value'] / npk['acres'],
        'parking_tax_change_pct': (pk['new_tax'] / pk['current_tax'] - 1) * 100,
        'nonparking_tax_change_pct': (npk['new_tax'] / npk['current_tax'] - 1) * 100,
    }
