import requests
import pandas as pd
from io import BytesIO
from datetime import datetime
import json
import time
from shapely.geometry import Polygon
import geopandas as gpd
from azure.storage.blob import BlobServiceClient
import requests
import geopandas as gpd
from shapely.geometry import Polygon
from pyproj import CRS

def get_layer_crs(base_url, dataset_name, layer_id=0, verbose=True):
    """Fetch layer metadata to infer spatial reference."""
    layer_url = f"{base_url}/{dataset_name}/FeatureServer/{layer_id}?f=pjson"
    r = requests.get(layer_url)
    r.raise_for_status()
    meta = r.json()

    wkid = None
    if "extent" in meta and "spatialReference" in meta["extent"]:
        wkid = meta["extent"]["spatialReference"].get("latestWkid") or meta["extent"]["spatialReference"].get("wkid")

    if verbose:
        print("Layer metadata CRS WKID:", wkid)

    return wkid


def get_feature_data_with_geometry(
    dataset_name, base_url, layer_id=0, paginate=False,
    out_epsg=4326, verbose=True
):
    """
    Safer ArcGIS FeatureServer downloader with geometry + CRS awareness.
    
    - Detects layer CRS from metadata
    - Optionally requests output in a known CRS (outSR)
    - Validates CRS assumptions
    """

    url = f"{base_url}/{dataset_name}/FeatureServer/{layer_id}/query"

    # Detect original CRS from layer metadata
    layer_wkid = get_layer_crs(base_url, dataset_name, layer_id, verbose=verbose)

    if layer_wkid is None:
        if verbose:
            print("⚠️ Could not detect layer CRS from metadata. Defaulting to EPSG:3857 (risky).")
        layer_wkid = 3857

    # Count params for pagination
    count_params = {'f': 'json', 'where': '1=1', 'returnCountOnly': 'true'}

    try:
        if paginate:
            total_records = requests.get(url, params=count_params).json().get("count", 0)
            if verbose:
                print(f"Total records in {dataset_name}: {total_records}")
        else:
            total_records = 1000

        all_features = []
        offset = 0
        chunk_size = 1000

        while offset < total_records:
            params = {
                'f': 'json',
                'where': '1=1',
                'outFields': '*',
                'returnGeometry': 'true',
                'resultOffset': offset,
                'resultRecordCount': chunk_size,
                'outSR': out_epsg,               # ✅ request output CRS
                'geometryPrecision': 6
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Print spatialReference info from response
            if verbose and offset == 0:
                sr = data.get("spatialReference", {})
                print("Query response spatialReference:", sr)

            if "features" not in data:
                if verbose:
                    print(f"No features found in response for {dataset_name}")
                break

            num_features = len(data["features"])
            if verbose:
                print(f"Fetched records {offset} to {offset + num_features}")

            # Parse features
            for feature in data["features"]:
                attrs = feature["attributes"]
                geom = feature.get("geometry", None)

                if geom and "rings" in geom:
                    # NOTE: This assumes the first ring is outer boundary.
                    # If holes/multi-polygons exist, this is a simplification.
                    ring = geom["rings"][0]
                    attrs["geometry"] = Polygon(ring)
                    all_features.append(attrs)

            # Stop logic
            if not paginate or num_features < chunk_size:
                break
            offset += num_features

        if not all_features:
            return None

        # ✅ If we requested outSR=4326, then that's what we got back.
        gdf = gpd.GeoDataFrame(all_features, geometry="geometry", crs=f"EPSG:{out_epsg}")

        # A quick sanity check on first geometry bounds
        if verbose:
            b = gdf.total_bounds
            print("Total bounds:", b)
            if abs(b[0]) > 180 or abs(b[1]) > 90:
                print("⚠️ Bounds look non-degree-like even though CRS says degrees. Something may be wrong.")

        return gdf

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {dataset_name}: {e}")
        return None


def get_feature_data(dataset_name, base_url, layer_id=0):
    """
    Get all features from a service using pagination
    
    Args:
        dataset_name (str): Name of the dataset to fetch
        base_url (str): Base URL for the feature service
        layer_id (int, optional): Layer ID to query. Defaults to 0.
    """
    url = f"{base_url}/{dataset_name}/FeatureServer/{layer_id}/query"
    
    # First, get the count of all features
    count_params = {
        'f': 'json',
        'where': '1=1',
        'returnCountOnly': 'true'
    }
    
    try:
        count_response = requests.get(url, params=count_params)
        count_response.raise_for_status()
        total_records = count_response.json().get('count', 0)
        
        print(f"Total records in {dataset_name}: {total_records}")
        
        # Now fetch the actual data in chunks
        all_features = []
        offset = 0
        chunk_size = 2000  # ArcGIS typically limits to 2000 records per request
        
        while offset < total_records:
            params = {
                'f': 'json',
                'where': '1=1',
                'outFields': '*',
                'returnGeometry': 'false',
                'resultOffset': offset,
                'resultRecordCount': chunk_size
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'features' in data:
                features = [feature['attributes'] for feature in data['features']]
                all_features.extend(features)
                
                print(f"Fetched records {offset} to {offset + len(features)} for {dataset_name}")
                
                if len(features) < chunk_size:
                    break
                    
                offset += chunk_size
            else:
                print(f"No features found in response for {dataset_name}")
                break
                
        return pd.DataFrame(all_features)
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {dataset_name}: {e}")
        return None


def get_mapserver_data_with_geometry(dataset_name, base_url, layer_id=0):
    """Get all features from a MapServer service including geometry with pagination"""
    url = f"{base_url}/{dataset_name}/MapServer/{layer_id}/query"
    
    # First, get the count of all features
    count_params = {
        'f': 'json',
        'where': '1=1',
        'returnCountOnly': 'true'
    }
    
    try:
        count_response = requests.get(url, params=count_params)
        count_response.raise_for_status()
        count_data = count_response.json()
        total_records = count_data.get('count', 0)
        
        print(f"Total records in {dataset_name}: {total_records}")
        
        if total_records == 0:
            print("No records found, trying without count check...")
            # Some MapServers don't support count, so try direct query
            params = {
                'f': 'json',
                'where': '1=1',
                'outFields': '*',
                'returnGeometry': 'true',
                'geometryPrecision': 6,
                'resultRecordCount': 2000
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'features' in data and data['features']:
                total_records = len(data['features'])
                print(f"Found {total_records} records in direct query")
            else:
                print("No features found in direct query either")
                return None
        
        # Now fetch the actual data in chunks
        all_features = []
        offset = 0
        chunk_size = 2000  # ArcGIS typically limits to 2000 records per request
        
        while offset < total_records:
            params = {
                'f': 'json',
                'where': '1=1',
                'outFields': '*',
                'returnGeometry': 'true',
                'geometryPrecision': 6,
                'resultOffset': offset,
                'resultRecordCount': chunk_size
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'features' in data and data['features']:
                # Convert ESRI features to GeoDataFrame format
                for feature in data['features']:
                    # Extract attributes
                    attributes = feature['attributes']
                    
                    # Handle geometry - check if it exists and has the expected structure
                    geometry = None
                    if 'geometry' in feature and feature['geometry']:
                        geom_data = feature['geometry']
                        if 'rings' in geom_data and geom_data['rings']:
                            try:
                                # Take the first ring (exterior ring)
                                ring = geom_data['rings'][0]
                                # Create Shapely polygon
                                geometry = Polygon(ring)
                            except Exception as e:
                                print(f"Warning: Could not process geometry for feature: {e}")
                                geometry = None
                        elif 'x' in geom_data and 'y' in geom_data:
                            # Point geometry
                            from shapely.geometry import Point
                            try:
                                geometry = Point(geom_data['x'], geom_data['y'])
                            except Exception as e:
                                print(f"Warning: Could not process point geometry: {e}")
                                geometry = None
                    
                    # Combine attributes and geometry
                    attributes['geometry'] = geometry
                    all_features.append(attributes)
                
                print(f"Fetched records {offset} to {offset + len(data['features'])} of {total_records}")
                
                if len(data['features']) < chunk_size:
                    break
                    
                offset += chunk_size
            else:
                print(f"No features found in response for {dataset_name}")
                break
        
        if all_features:
            # Create GeoDataFrame
            # Cook County uses EPSG:3435 (Illinois State Plane East, NAD83)
            try:
                gdf = gpd.GeoDataFrame(all_features, crs='EPSG:3435')
                
                # Filter out features without geometry if needed
                valid_geom_count = gdf['geometry'].notna().sum()
                print(f"Features with valid geometry: {valid_geom_count} out of {len(gdf)}")
                
                if valid_geom_count > 0:
                    # Convert to WGS84 for compatibility
                    gdf = gdf.to_crs('EPSG:4326')
                    print(f"Successfully loaded {len(gdf)} features")
                    return gdf
                else:
                    print("No features with valid geometry found")
                    # Return as regular DataFrame if no geometry
                    return pd.DataFrame(all_features)
                    
            except Exception as e:
                print(f"Error creating GeoDataFrame: {e}")
                print("Returning as regular DataFrame")
                return pd.DataFrame(all_features)
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {dataset_name}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None



def get_mapserver_data_with_geometry_pa(dataset_name, base_url, layer_id=0, paginate=True, verbose=True):
    """Get all features from a MapServer service for Pennsylvania (uses PA State Plane North projection)"""
    url = f"{base_url}/{dataset_name}/MapServer/{layer_id}/query"
    
    # First, get the count of all features
    count_params = {
        'f': 'json',
        'where': '1=1',
        'returnCountOnly': 'true'
    }
    
    try:
        if paginate:
            count_response = requests.get(url, params=count_params)
            count_response.raise_for_status()
            total_records = count_response.json().get('count', 0)
            if verbose:
                print(f"Total records in {dataset_name}: {total_records}")
        else:
            total_records = 1000
        
        if total_records == 0:
            if verbose:
                print("No records found")
            return None
        
        # Now fetch the actual data in chunks
        all_features = []
        offset = 0
        chunk_size = 1000  # MapServer typically limits to 1000-2000 records per request
        
        while offset < total_records:
            params = {
                'f': 'json',
                'where': '1=1',
                'outFields': '*',
                'returnGeometry': 'true',
                'geometryPrecision': 6,
                'resultOffset': offset,
                'resultRecordCount': chunk_size
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'features' in data and data['features']:
                # Convert ESRI features to GeoDataFrame format
                for feature in data['features']:
                    # Extract attributes
                    attributes = feature['attributes']
                    
                    # Handle geometry - check if it exists and has the expected structure
                    geometry = None
                    if 'geometry' in feature and feature['geometry']:
                        geom_data = feature['geometry']
                        if 'rings' in geom_data and geom_data['rings']:
                            try:
                                # Take the first ring (exterior ring)
                                ring = geom_data['rings'][0]
                                # Create Shapely polygon
                                geometry = Polygon(ring)
                            except Exception as e:
                                if verbose:
                                    print(f"Warning: Could not process geometry for feature: {e}")
                                geometry = None
                        elif 'x' in geom_data and 'y' in geom_data:
                            # Point geometry
                            from shapely.geometry import Point
                            try:
                                geometry = Point(geom_data['x'], geom_data['y'])
                            except Exception as e:
                                if verbose:
                                    print(f"Warning: Could not process point geometry: {e}")
                                geometry = None
                    
                    # Combine attributes and geometry
                    attributes['geometry'] = geometry
                    all_features.append(attributes)
                
                if verbose:
                    print(f"Fetched records {offset} to {offset + len(data['features'])}")
                
                num_features = len(data['features'])
                if not paginate or num_features < chunk_size:
                    break
                offset += num_features
            else:
                if verbose:
                    print(f"No features found in response for {dataset_name}")
                break
        
        if all_features:
            # Pennsylvania State Plane North uses EPSG:2271 (NAD83) or EPSG:2272 (NAD83 HARN)
            # Based on the metadata, this appears to be NAD83, so using EPSG:2271
            try:
                gdf = gpd.GeoDataFrame(all_features, crs='EPSG:2271')
                
                # Filter out features without geometry if needed
                valid_geom_count = gdf['geometry'].notna().sum()
                if verbose:
                    print(f"Features with valid geometry: {valid_geom_count} out of {len(gdf)}")
                
                if valid_geom_count > 0:
                    # Convert to WGS84 for compatibility
                    gdf = gdf.to_crs('EPSG:4326')
                    if verbose:
                        print(f"Successfully loaded {len(gdf)} features")
                        b = gdf.total_bounds
                        print("Total bounds:", b)
                    return gdf
                else:
                    if verbose:
                        print("No features with valid geometry found")
                    # Return as regular DataFrame if no geometry
                    return pd.DataFrame(all_features)
                    
            except Exception as e:
                if verbose:
                    print(f"Error creating GeoDataFrame: {e}")
                    print("Returning as regular DataFrame")
                return pd.DataFrame(all_features)
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {dataset_name}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
