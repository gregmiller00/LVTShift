from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import geopandas as gpd
from census import Census
from us import states
import requests
from shapely.geometry import Point, Polygon
import json

def get_census_data(fips_code: str, year: int = 2022, api_key: str = None) -> pd.DataFrame:
    """
    Get Census demographic data for block groups in a given FIPS code.
    
    Args:
        fips_code (str): 5-digit FIPS code (state + county)
        year (int): Census year to query (default: 2022)
        api_key (str): Census API key. If None, will raise error.
    
    Returns:
        pd.DataFrame: DataFrame containing Census demographic data
        
    Raises:
        TypeError: If fips_code is not a string or year is not an int
        ValueError: If fips_code is not 5 digits or api_key is not provided
    """
    if not isinstance(fips_code, str):
        raise TypeError("fips_code must be a string")
    if not isinstance(year, int):
        raise TypeError("year must be an integer")
    if len(fips_code) != 5:
        raise ValueError("fips_code must be 5 digits (state + county)")
    if not api_key:
        raise ValueError("Census API key must be provided")

    # Initialize Census API
    c = Census(api_key)
    
    # Split FIPS code into state and county
    state_fips = fips_code[:2]
    county_fips = fips_code[2:]
    
    # Get block group data
    data = c.acs5.state_county_blockgroup(
        fields=['NAME',
                'B19013_001E',  # Median income
                'B01003_001E',  # Total population
                'B03002_003E',  # White alone
                'B03002_004E',  # Black alone
                'B03002_012E'],  # Hispanic/Latino
        state_fips=state_fips,
        county_fips=county_fips,
        blockgroup='*',  # All block groups
        year=year
    )

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Rename columns
    df = df.rename(columns={
        'B19013_001E': 'median_income',
        'B01003_001E': 'total_pop',
        'B03002_003E': 'white_pop',
        'B03002_004E': 'black_pop',
        'B03002_012E': 'hispanic_pop',
        'block group': 'census_block_group'  # Rename block group to census_block_group
    })

    # Create GEOID for block groups (state+county+tract+block group)
    df['state_fips'] = df['state']
    df['county_fips'] = df['county']
    df['tract_fips'] = df['tract']
    df['bg_fips'] = df['census_block_group']  # Use renamed column

    # Create standardized GEOID
    df['std_geoid'] = df['state_fips'] + df['county_fips'] + df['tract_fips'] + df['bg_fips']

    # Calculate minority and black percentages
    df['minority_pct'] = ((df['total_pop'] - df['white_pop']) / df['total_pop'] * 100).round(2)
    df['black_pct'] = (df['black_pop'] / df['total_pop'] * 100).round(2)

    return df

def get_census_blockgroups_shapefile_chunked(fips_code: str, max_retries: int = 3) -> gpd.GeoDataFrame:
    """
    Get Census Block Group shapefiles for large counties by fetching tract by tract.
    This approach handles counties like Cook County that are too large for a single request.
    
    Args:
        fips_code (str): 5-digit FIPS code (state + county)
        max_retries (int): Maximum number of retries for failed requests
    
    Returns:
        gpd.GeoDataFrame: GeoDataFrame containing Census Block Group boundaries
    """
    import time
    from typing import List
    
    if not isinstance(fips_code, str):
        raise TypeError("fips_code must be a string")
    if len(fips_code) != 5:
        raise ValueError("fips_code must be 5 digits (state + county)")

    state_fips = fips_code[:2]
    county_fips = fips_code[2:]
    
    # First, get all census tracts in the county
    tracts_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/8/query"
    tracts_params = {
        'where': f"STATE='{state_fips}' AND COUNTY='{county_fips}'",
        'outFields': 'TRACT',
        'returnGeometry': 'false',
        'f': 'json'
    }
    
    print(f"🔍 Getting census tracts for county {fips_code}...")
    
    try:
        tracts_response = requests.get(tracts_url, params=tracts_params)
        tracts_response.raise_for_status()
        tracts_data = tracts_response.json()
        
        if 'features' not in tracts_data:
            raise ValueError(f"No census tracts found for county {fips_code}")
            
        # Extract tract numbers
        tract_numbers = [feature['attributes']['TRACT'] for feature in tracts_data['features']]
        print(f"📋 Found {len(tract_numbers)} census tracts")
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch census tracts: {str(e)}")

    # Now fetch block groups for each tract
    all_block_groups = []
    bg_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/2/query"
    
    for i, tract in enumerate(tract_numbers):
        retry_count = 0
        while retry_count < max_retries:
            try:
                bg_params = {
                    'where': f"STATE='{state_fips}' AND COUNTY='{county_fips}' AND TRACT='{tract}'",
                    'outFields': '*',
                    'returnGeometry': 'true',
                    'f': 'geojson',
                    'outSR': '4326'  # WGS84
                }
                
                response = requests.get(bg_url, params=bg_params)
                response.raise_for_status()
                
                geojson_data = response.json()
                
                if 'features' in geojson_data and geojson_data['features']:
                    # Convert to GeoDataFrame
                    tract_gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
                    all_block_groups.append(tract_gdf)
                    
                print(f"✅ Tract {tract} ({i+1}/{len(tract_numbers)}): {len(geojson_data.get('features', []))} block groups")
                
                # Small delay to be respectful to the API
                time.sleep(0.1)
                break  # Success, exit retry loop
                
            except requests.RequestException as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"❌ Failed to fetch tract {tract} after {max_retries} retries: {e}")
                    continue  # Skip this tract
                else:
                    print(f"⚠️ Retry {retry_count}/{max_retries} for tract {tract}: {e}")
                    time.sleep(1)  # Wait before retry
    
    if not all_block_groups:
        raise ValueError(f"No block group data successfully fetched for county {fips_code}")
    
    # Combine all block groups
    print(f"🔗 Combining block groups from {len(all_block_groups)} tracts...")
    combined_gdf = gpd.pd.concat(all_block_groups, ignore_index=True)
    
    # Create standardized GEOID components
    combined_gdf['state_fips'] = combined_gdf['STATE']
    combined_gdf['county_fips'] = combined_gdf['COUNTY']  
    combined_gdf['tract_fips'] = combined_gdf['TRACT']
    combined_gdf['bg_fips'] = combined_gdf['BLKGRP']

    # Create standardized GEOID
    combined_gdf['std_geoid'] = combined_gdf['state_fips'] + combined_gdf['county_fips'] + combined_gdf['tract_fips'] + combined_gdf['bg_fips']
    
    print(f"🎉 Successfully fetched {len(combined_gdf)} total block groups for county {fips_code}")
    
    return combined_gdf

def get_census_blockgroups_shapefile(fips_code: str) -> gpd.GeoDataFrame:
    """
    Get Census Block Group shapefiles for a given FIPS code from the Census TIGERweb service.
    Automatically handles large counties (like Cook County) by using a chunked approach.
    
    Args:
        fips_code (str): 5-digit FIPS code (state + county)
    
    Returns:
        gpd.GeoDataFrame: GeoDataFrame containing Census Block Group boundaries
        
    Raises:
        TypeError: If fips_code is not a string
        ValueError: If fips_code is not 5 digits
        requests.RequestException: If API request fails
    """
    if not isinstance(fips_code, str):
        raise TypeError("fips_code must be a string")
    if len(fips_code) != 5:
        raise ValueError("fips_code must be 5 digits (state + county)")

    # Large counties that need chunked approach
    # Cook County, IL (17031) and other large metropolitan counties
    large_counties = [
        '17031',  # Cook County, IL (Chicago)
        '06037',  # Los Angeles County, CA
        '48201',  # Harris County, TX (Houston)  
        '04013',  # Maricopa County, AZ (Phoenix)
        '06073',  # San Diego County, CA
        '06059',  # Orange County, CA
        '36081',  # Queens County, NY
        '36047',  # Kings County, NY (Brooklyn)
        '12086',  # Miami-Dade County, FL
        '53033',  # King County, WA (Seattle)
    ]
    
    if fips_code in large_counties:
        print(f"🔧 Using chunked approach for large county {fips_code}")
        return get_census_blockgroups_shapefile_chunked(fips_code)

    # TIGERweb REST API endpoint
    base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/2/query"
    
    # Query parameters
    params = {
        'where': f"STATE='{fips_code[:2]}' AND COUNTY='{fips_code[2:]}'",
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'geojson',
        'outSR': '4326'  # WGS84
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        # Check if we got a rejection message (usually HTML error page)
        content_type = response.headers.get('content-type', '').lower()
        if 'html' in content_type:
            print(f"⚠️ Received HTML response instead of JSON - likely request rejected")
            print(f"🔧 Falling back to chunked approach for county {fips_code}")
            return get_census_blockgroups_shapefile_chunked(fips_code)
        
        geojson_data = response.json()
        
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        
        # Create standardized GEOID components
        gdf['state_fips'] = gdf['STATE']
        gdf['county_fips'] = gdf['COUNTY']
        gdf['tract_fips'] = gdf['TRACT']
        gdf['bg_fips'] = gdf['BLKGRP']

        # Create standardized GEOID
        gdf['std_geoid'] = gdf['state_fips'] + gdf['county_fips'] + gdf['tract_fips'] + gdf['bg_fips']
        
        return gdf
        
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"⚠️ Direct request failed: {str(e)}")
        print(f"🔧 Falling back to chunked approach for county {fips_code}")
        return get_census_blockgroups_shapefile_chunked(fips_code)

def match_to_census_blockgroups(
    gdf: gpd.GeoDataFrame,
    census_gdf: gpd.GeoDataFrame,
    join_type: str = "left"
) -> gpd.GeoDataFrame:
    """
    Match each row in a GeoDataFrame to its corresponding Census Block Group using spatial join.
    
    Args:
        gdf (gpd.GeoDataFrame): Input GeoDataFrame to match
        census_gdf (gpd.GeoDataFrame): Census Block Group boundaries GeoDataFrame
        join_type (str): Type of join to perform ('left', 'right', 'inner', 'outer')
    
    Returns:
        gpd.GeoDataFrame: Input GeoDataFrame with Census Block Group data appended
        
    Raises:
        TypeError: If inputs are not GeoDataFrames
        ValueError: If join_type is invalid
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError("gdf must be a GeoDataFrame")
    if not isinstance(census_gdf, gpd.GeoDataFrame):
        raise TypeError("census_gdf must be a GeoDataFrame")
    if join_type not in ['left', 'right', 'inner', 'outer']:
        raise ValueError("join_type must be one of: 'left', 'right', 'inner', 'outer'")

    # Ensure both GDFs have same CRS
    if gdf.crs != census_gdf.crs:
        census_gdf = census_gdf.to_crs(gdf.crs)

    # Use centroid of each geometry for the join to avoid issues with overlapping boundaries
    gdf_centroids = gdf.copy()
    gdf_centroids.geometry = gdf_centroids.geometry.centroid

    # Perform spatial join
    joined = gpd.sjoin(gdf_centroids, census_gdf, how=join_type, predicate='within')

    # Drop unnecessary columns from the join
    if 'index_right' in joined.columns:
        joined = joined.drop(columns=['index_right'])

    return joined

def get_census_data_with_boundaries(
    fips_code: str,
    year: int = 2022,
    api_key: str = None
) -> Tuple[pd.DataFrame, gpd.GeoDataFrame]:
    """
    Get both Census demographic data and boundary files for block groups in a FIPS code.
    
    Args:
        fips_code (str): 5-digit FIPS code (state + county)
        year (int): Census year to query (default: 2022)
        api_key (str): Census API key
    
    Returns:
        Tuple[pd.DataFrame, gpd.GeoDataFrame]: 
            - Census demographic data DataFrame
            - Census Block Group boundaries GeoDataFrame
            
    Raises:
        TypeError: If inputs have wrong types
        ValueError: If inputs have invalid values
        requests.RequestException: If API requests fail
    """
    # Get demographic data
    census_data = get_census_data(fips_code, year, api_key)
    
    # Get boundary files
    census_boundaries = get_census_blockgroups_shapefile(fips_code)
    
    # Merge demographic data with boundaries
    # Use suffixes to avoid duplicate column names
    census_boundaries = census_boundaries.merge(
        census_data,
        on='std_geoid',
        how='left',
        suffixes=('', '_census')
    )
    
    # Drop duplicate columns that might have been created with the _census suffix
    census_boundaries = census_boundaries.loc[:, ~census_boundaries.columns.str.endswith('_census')]
    
    return census_data, census_boundaries

def enrich_shapefile_with_census(
    shapefile: Union[str, gpd.GeoDataFrame],
    fips_code: str,
    year: int = 2022,
    api_key: str = None
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Takes a shapefile (or GeoDataFrame) and enriches it with Census Block Group data.
    Also returns the Census Block Group data separately.
    
    Args:
        shapefile (Union[str, gpd.GeoDataFrame]): Either a path to a shapefile or a GeoDataFrame
        fips_code (str): 5-digit FIPS code (state + county)
        year (int): Census year to query (default: 2022)
        api_key (str): Census API key
    
    Returns:
        Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
            - Original shapefile enriched with Census Block Group data
            - Census Block Group boundaries with demographic data
            
    Raises:
        TypeError: If inputs have wrong types
        ValueError: If inputs have invalid values
        requests.RequestException: If API requests fail
        FileNotFoundError: If shapefile path is invalid
    """
    # Input validation
    if not isinstance(fips_code, str):
        raise TypeError("fips_code must be a string")
    if not isinstance(year, int):
        raise TypeError("year must be an integer")
    if len(fips_code) != 5:
        raise ValueError("fips_code must be 5 digits (state + county)")
    if not api_key:
        raise ValueError("Census API key must be provided")

    # Load the shapefile if string path provided
    if isinstance(shapefile, str):
        try:
            gdf = gpd.read_file(shapefile)
        except Exception as e:
            raise FileNotFoundError(f"Failed to read shapefile at {shapefile}: {str(e)}")
    elif isinstance(shapefile, gpd.GeoDataFrame):
        gdf = shapefile.copy()
    else:
        raise TypeError("shapefile must be either a file path (str) or a GeoDataFrame")
    
    # Check if the GeoDataFrame has a CRS and set one if it doesn't
    if gdf.crs is None:
        raise ValueError("Input GeoDataFrame must have a coordinate reference system (CRS) defined. "
                         "Use gdf.set_crs() to set a CRS before calling this function.")

    # Get census data and boundaries
    census_data, census_boundaries = get_census_data_with_boundaries(
        fips_code=fips_code,
        year=year,
        api_key=api_key
    )
    
    # Ensure census boundaries have a CRS
    if census_boundaries.crs is None:
        # Set a default CRS (EPSG:4326 - WGS84) if none exists
        census_boundaries = census_boundaries.set_crs("EPSG:4326")

    # Match shapefile to census block groups
    # Use a list of columns to keep from census_boundaries to avoid duplicates
    census_cols_to_keep = ['std_geoid', 'median_income', 'total_pop', 'white_pop', 
                          'black_pop', 'hispanic_pop']
    
    # First perform the spatial join
    enriched_gdf = match_to_census_blockgroups(
        gdf=gdf,
        census_gdf=census_boundaries[['geometry', 'std_geoid'] + 
                                    [col for col in census_cols_to_keep if col != 'std_geoid']],
        join_type="left"
    )

    return enriched_gdf, census_boundaries

def get_census_blockgroups_from_ftp(fips_code: str, year: int = 2022) -> gpd.GeoDataFrame:
    """
    Alternative method: Download Census Block Group shapefiles from the Census FTP server.
    Useful for very large counties where the TIGERweb API fails.
    
    Args:
        fips_code (str): 5-digit FIPS code (state + county)
        year (int): Census year (default: 2022)
    
    Returns:
        gpd.GeoDataFrame: GeoDataFrame containing Census Block Group boundaries
    """
    import zipfile
    import tempfile
    import urllib.request
    import os
    
    if not isinstance(fips_code, str):
        raise TypeError("fips_code must be a string")
    if len(fips_code) != 5:
        raise ValueError("fips_code must be 5 digits (state + county)")

    state_fips = fips_code[:2]
    
    # Census FTP URL for block groups by state
    ftp_url = f"https://www2.census.gov/geo/tiger/TIGER{year}/BG/tl_{year}_{state_fips}_bg.zip"
    
    print(f"📥 Downloading block groups for state {state_fips} from Census FTP...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, f"tl_{year}_{state_fips}_bg.zip")
        
        try:
            # Download the zip file
            urllib.request.urlretrieve(ftp_url, zip_path)
            print(f"✅ Downloaded {os.path.getsize(zip_path):,} bytes")
            
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the shapefile
            shp_files = [f for f in os.listdir(temp_dir) if f.endswith('.shp')]
            if not shp_files:
                raise FileNotFoundError("No shapefile found in downloaded zip")
            
            shp_path = os.path.join(temp_dir, shp_files[0])
            
            # Read the shapefile
            print(f"📊 Reading shapefile: {shp_files[0]}")
            gdf = gpd.read_file(shp_path)
            
            # Filter to the specific county
            county_fips = fips_code[2:]
            filtered_gdf = gdf[gdf['COUNTYFP'] == county_fips].copy()
            
            print(f"🎯 Filtered to {len(filtered_gdf)} block groups in county {fips_code}")
            
            if len(filtered_gdf) == 0:
                raise ValueError(f"No block groups found for county {fips_code}")
            
            # Rename columns to match TIGERweb format
            filtered_gdf = filtered_gdf.rename(columns={
                'STATEFP': 'STATE',
                'COUNTYFP': 'COUNTY', 
                'TRACTCE': 'TRACT',
                'BLKGRPCE': 'BLKGRP'
            })
            
            # Create standardized GEOID components
            filtered_gdf['state_fips'] = filtered_gdf['STATE']
            filtered_gdf['county_fips'] = filtered_gdf['COUNTY']
            filtered_gdf['tract_fips'] = filtered_gdf['TRACT']
            filtered_gdf['bg_fips'] = filtered_gdf['BLKGRP']

            # Create standardized GEOID
            filtered_gdf['std_geoid'] = filtered_gdf['state_fips'] + filtered_gdf['county_fips'] + filtered_gdf['tract_fips'] + filtered_gdf['bg_fips']
            
            # Ensure CRS is WGS84
            if filtered_gdf.crs != 'EPSG:4326':
                filtered_gdf = filtered_gdf.to_crs('EPSG:4326')
            
            return filtered_gdf
            
        except Exception as e:
            raise Exception(f"Failed to download/process Census data from FTP: {str(e)}")
