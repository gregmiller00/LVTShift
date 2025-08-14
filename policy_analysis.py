import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, Union, List


def _compute_adjusted_values(
    df: pd.DataFrame,
    land_value_col: str,
    improvement_value_col: Optional[str] = None,
    exemption_col: Optional[str] = None,
    exemption_flag_col: Optional[str] = None,
) -> Tuple[pd.Series, Optional[pd.Series]]:
    """
    Compute non-exempt (taxable) land and improvement values.
    - Fully exempt rows (flag == 1) are set to 0 for both land and improvements
    - Partial exemptions are applied to improvements first, then remaining to land
    """
    # Start with numeric, non-null base values
    land = pd.to_numeric(df.get(land_value_col, 0), errors='coerce').fillna(0)
    improvements = None
    if improvement_value_col is not None and improvement_value_col in df.columns:
        improvements = pd.to_numeric(df[improvement_value_col], errors='coerce').fillna(0)

    # Handle fully exempt properties
    if exemption_flag_col is not None and exemption_flag_col in df.columns:
        flag = pd.to_numeric(df[exemption_flag_col], errors='coerce').fillna(0)
    else:
        flag = None

    # Start with base values
    adj_land = land.copy()
    adj_impr = improvements.copy() if improvements is not None else None

    # If there is a partial exemption column, prepare it
    if exemption_col is not None and exemption_col in df.columns:
        exempt_amt = pd.to_numeric(df[exemption_col], errors='coerce').fillna(0)
    else:
        exempt_amt = None

    # Apply partial exemptions: buildings first, then land
    if exempt_amt is not None:
        if adj_impr is not None:
            # Save original improvements to compute remaining exemption portion
            original_impr = adj_impr.copy()
            adj_impr = (adj_impr - exempt_amt).clip(lower=0)
            remaining_exemption = (exempt_amt - original_impr).clip(lower=0)
            adj_land = (adj_land - remaining_exemption).clip(lower=0)
        else:
            # No improvements provided; all exemption comes from land
            adj_land = (adj_land - exempt_amt).clip(lower=0)

    # Apply full exemption flag last (dominates partial logic)
    if flag is not None:
        fully_exempt_mask = flag != 0
        adj_land = adj_land.where(~fully_exempt_mask, 0)
        if adj_impr is not None:
            adj_impr = adj_impr.where(~fully_exempt_mask, 0)

    return adj_land, adj_impr


def analyze_vacant_land(df: pd.DataFrame, 
                       land_value_col: str = 'land_value',
                       property_type_col: str = 'prop_use_desc',
                       neighborhood_col: Optional[str] = None,
                       zoning_col: Optional[str] = None,
                       owner_col: Optional[str] = None,
                       vacant_identifier: str = 'Vacant Land',
                       improvement_value_col: str = 'improvement_value',
                       exemption_col: Optional[str] = None,
                       exemption_flag_col: Optional[str] = None) -> Dict:
    """
    Analyze vacant land patterns including total values, concentration, and geographic distribution.

    If exemptions are provided, all dollar amounts and percentages are computed using
    non-exempt values (partial exemptions subtract from improvements first, then land;
    fully exempt parcels contribute $0).
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing property data
    land_value_col : str
        Column name for land values
    property_type_col : str
        Column name for property use/type classification
    neighborhood_col : str, optional
        Column name for neighborhood grouping
    zoning_col : str, optional  
        Column name for zoning classification
    owner_col : str, optional
        Column name for property owner information
    vacant_identifier : str
        Value in property_type_col that identifies vacant land
    improvement_value_col : str
        Column name for improvement values (used to allocate partial exemptions first)
    exemption_col : str, optional
        Column name for exemption amounts
    exemption_flag_col : str, optional
        Column name for full exemption flag (1 fully exempt, 0 otherwise)
        
    Returns:
    --------
    dict
        Dictionary containing various vacant land analyses
    """
    
    # Filter to vacant land only
    vacant_mask = df[property_type_col] == vacant_identifier
    vacant_df = df[vacant_mask].copy()
    
    if len(vacant_df) == 0:
        return {"error": f"No properties found with {property_type_col} == '{vacant_identifier}'"}
    
    analysis_results = {}

    # Compute adjusted values for both overall city and vacant subset
    city_adj_land, _ = _compute_adjusted_values(
        df, land_value_col, improvement_value_col, exemption_col, exemption_flag_col
    )
    vacant_adj_land, _ = _compute_adjusted_values(
        vacant_df, land_value_col, improvement_value_col, exemption_col, exemption_flag_col
    )
    
    # Overall totals (non-exempt if exemptions provided)
    analysis_results['total_vacant_parcels'] = len(vacant_df)
    analysis_results['total_vacant_land_value'] = float(vacant_adj_land.sum())
    analysis_results['average_vacant_land_value'] = float(vacant_adj_land.mean())
    analysis_results['median_vacant_land_value'] = float(vacant_adj_land.median())
    
    # Percentage of total city land value that is vacant (non-exempt base)
    total_city_land_value = float(city_adj_land.sum())
    analysis_results['vacant_land_pct_of_total'] = (
        (analysis_results['total_vacant_land_value'] / total_city_land_value) * 100
        if total_city_land_value > 0 else 0.0
    )
    
    # By neighborhood analysis
    if neighborhood_col and neighborhood_col in df.columns:
        tmp = vacant_df[[neighborhood_col]].copy()
        tmp['adj_land_value'] = vacant_adj_land.values
        neighborhood_analysis = tmp.groupby(neighborhood_col).agg({
            'adj_land_value': ['count', 'sum', 'mean', 'median']
        }).round(2)
        neighborhood_analysis.columns = ['count', 'total_value', 'avg_value', 'median_value']
        neighborhood_analysis = neighborhood_analysis.sort_values('total_value', ascending=False)
        analysis_results['by_neighborhood'] = neighborhood_analysis
    
    # By zoning analysis  
    if zoning_col and zoning_col in df.columns:
        tmp = vacant_df[[zoning_col]].copy()
        tmp['adj_land_value'] = vacant_adj_land.values
        zoning_analysis = tmp.groupby(zoning_col).agg({
            'adj_land_value': ['count', 'sum', 'mean', 'median']
        }).round(2)
        zoning_analysis.columns = ['count', 'total_value', 'avg_value', 'median_value']
        zoning_analysis = zoning_analysis.sort_values('total_value', ascending=False)
        analysis_results['by_zoning'] = zoning_analysis
    
    # Owner concentration analysis
    if owner_col and owner_col in df.columns:
        tmp = vacant_df[[owner_col]].copy()
        tmp['adj_land_value'] = vacant_adj_land.values
        owner_analysis = tmp.groupby(owner_col).agg({
            'adj_land_value': ['count', 'sum']
        }).round(2)
        owner_analysis.columns = ['parcel_count', 'total_land_value']
        owner_analysis = owner_analysis.sort_values('total_land_value', ascending=False)
        
        # Top 10 owners by value
        analysis_results['top_10_owners_by_value'] = owner_analysis.head(10)
        
        # Concentration metrics
        # Use head(k) where k is 5% or 10% of number of owners (at least 1)
        num_owners = max(len(owner_analysis), 1)
        top_5_count = max(int(num_owners * 0.05), 1)
        top_10_count = max(int(num_owners * 0.10), 1)
        top_5_value = owner_analysis['total_land_value'].head(top_5_count).sum()
        top_10_value = owner_analysis['total_land_value'].head(top_10_count).sum()
        
        analysis_results['concentration_metrics'] = {
            'top_5_percent_owners_control_value': float(top_5_value),
            'top_5_percent_share': (
                (top_5_value / analysis_results['total_vacant_land_value']) * 100
                if analysis_results['total_vacant_land_value'] > 0 else 0.0
            ),
            'top_10_percent_owners_control_value': float(top_10_value),
            'top_10_percent_share': (
                (top_10_value / analysis_results['total_vacant_land_value']) * 100
                if analysis_results['total_vacant_land_value'] > 0 else 0.0
            )
        }
    
    return analysis_results


def analyze_parking_lots(df: pd.DataFrame,
                        land_value_col: str = 'land_value',
                        improvement_value_col: str = 'improvement_value', 
                        property_type_col: str = 'prop_use_desc',
                        parking_identifier: str = 'Trans - Parking',
                        min_land_value_threshold: float = 50000,
                        max_improvement_ratio: float = 0.1,
                        exemption_col: Optional[str] = None,
                        exemption_flag_col: Optional[str] = None) -> Dict:
    """
    Analyze parking lots to identify inefficient land use on valuable property.

    If exemptions are provided, all dollar amounts and percentages are computed using
    non-exempt values (partial exemptions subtract from improvements first, then land;
    fully exempt parcels contribute $0).
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing property data
    land_value_col : str
        Column name for land values
    improvement_value_col : str
        Column name for improvement/building values
    property_type_col : str
        Column name for property use/type classification
    parking_identifier : str
        Value in property_type_col that identifies parking lots
    min_land_value_threshold : float
        Minimum land value to consider for analysis (focuses on valuable land)
    max_improvement_ratio : float
        Maximum ratio of improvement value to land value to be considered underutilized
    exemption_col : str, optional
        Column name for exemption amounts
    exemption_flag_col : str, optional
        Column name for full exemption flag (1 fully exempt, 0 otherwise)
        
    Returns:
    --------
    dict
        Dictionary containing parking lot efficiency analysis
    """
    
    # Filter to parking lots
    parking_mask = df[property_type_col] == parking_identifier
    parking_df = df[parking_mask].copy()
    
    if len(parking_df) == 0:
        return {"error": f"No properties found with {property_type_col} == '{parking_identifier}'"}
    
    # Compute adjusted values for both overall city and parking subset
    city_adj_land, city_adj_impr = _compute_adjusted_values(
        df, land_value_col, improvement_value_col, exemption_col, exemption_flag_col
    )
    park_adj_land, park_adj_impr = _compute_adjusted_values(
        parking_df, land_value_col, improvement_value_col, exemption_col, exemption_flag_col
    )

    # Calculate improvement to land ratio using adjusted values
    with np.errstate(divide='ignore', invalid='ignore'):
        improvement_to_land_ratio = (park_adj_impr / park_adj_land).replace([np.inf, -np.inf], 0).fillna(0)
    parking_df['improvement_to_land_ratio'] = improvement_to_land_ratio
    
    analysis_results = {}
    
    # Overall parking lot statistics (non-exempt values)
    analysis_results['total_parking_lots'] = len(parking_df)
    analysis_results['total_parking_land_value'] = float(park_adj_land.sum())
    analysis_results['total_parking_improvement_value'] = float(park_adj_impr.sum()) if park_adj_impr is not None else 0.0
    analysis_results['average_parking_land_value'] = float(park_adj_land.mean())
    analysis_results['average_improvement_ratio'] = float(parking_df['improvement_to_land_ratio'].mean())
    
    # High-value, underutilized parking lots (use adjusted values)
    underutilized_mask = (
        (park_adj_land >= min_land_value_threshold) &
        (parking_df['improvement_to_land_ratio'] <= max_improvement_ratio)
    )
    underutilized_parking = parking_df[underutilized_mask].copy()
    underutil_adj_land = park_adj_land[underutilized_mask]
    underutil_adj_impr = park_adj_impr[underutilized_mask] if park_adj_impr is not None else None
    
    analysis_results['underutilized_parking_lots'] = {
        'count': int(len(underutilized_parking)),
        'total_land_value': float(underutil_adj_land.sum()),
        'average_land_value': float(underutil_adj_land.mean()) if len(underutil_adj_land) > 0 else 0.0,
        'total_improvement_value': float(underutil_adj_impr.sum()) if underutil_adj_impr is not None else 0.0,
        'criteria': f"Land value >= ${min_land_value_threshold:,.0f} and improvement ratio <= {max_improvement_ratio:.1%}"
    }
    
    # Development potential analysis (citywide average ratio using adjusted values)
    if len(underutilized_parking) > 0:
        total_city_adj_land = float(city_adj_land.sum())
        total_city_adj_impr = float(city_adj_impr.sum()) if city_adj_impr is not None else 0.0
        avg_improvement_ratio_citywide = (
            (total_city_adj_impr / total_city_adj_land) if total_city_adj_land > 0 else 0.0
        )
        potential_development_value = float(underutil_adj_land.sum()) * avg_improvement_ratio_citywide
        current_development_value = float(underutil_adj_impr.sum()) if underutil_adj_impr is not None else 0.0
        
        analysis_results['development_potential'] = {
            'current_improvement_value': current_development_value,
            'potential_improvement_value': potential_development_value,
            'untapped_development_value': potential_development_value - current_development_value,
            'citywide_avg_improvement_ratio': avg_improvement_ratio_citywide
        }
    
    # Create summary by land value tiers (using adjusted land values)
    parking_df['land_value_tier'] = pd.cut(park_adj_land, 
                                          bins=[0, 25000, 50000, 100000, 250000, float('inf')],
                                          labels=['<$25k', '$25k-$50k', '$50k-$100k', '$100k-$250k', '>$250k'])
    
    tier_df = pd.DataFrame({
        'land_value_tier': parking_df['land_value_tier'],
        'adj_land_value': park_adj_land,
        'improvement_to_land_ratio': parking_df['improvement_to_land_ratio'],
    })
    tier_analysis = tier_df.groupby('land_value_tier').agg({
        'adj_land_value': ['count', 'sum', 'mean'],
        'improvement_to_land_ratio': 'mean'
    }).round(3)
    tier_analysis.columns = ['count', 'total_land_value', 'avg_land_value', 'avg_improvement_ratio']
    analysis_results['by_land_value_tier'] = tier_analysis
    
    return analysis_results


def analyze_land_by_improvement_share(
    df: pd.DataFrame,
    land_value_col: str = 'land_value',
    improvement_value_col: str = 'improvement_value',
    exemption_col: Optional[str] = None,
    exemption_flag_col: Optional[str] = None,
) -> Dict:
    """
    Summarize adjusted land value by improvement share categories, using FULL market values
    to determine the improvement share, and reporting land totals and shares on a NON-EXEMPT basis.

    Categories (by improvement_share = improvement / (land + improvement)):
    - 0% improvement (improvement == 0 and total > 0)
    - <10% improvement (excluding 0%)
    - 10-25% improvement
    - 25-50% improvement

    Exemption handling:
    - Fully exempt parcels are excluded from sums
    - Partial exemptions reduce improvements first, then land

    Returns a dict with category totals and their percent of total adjusted land value.
    """
    result_df = df.copy()
    # Ensure numeric
    result_df[land_value_col] = pd.to_numeric(result_df[land_value_col], errors='coerce').fillna(0)
    result_df[improvement_value_col] = pd.to_numeric(result_df[improvement_value_col], errors='coerce').fillna(0)
    if exemption_col and exemption_col in result_df.columns:
        result_df[exemption_col] = pd.to_numeric(result_df[exemption_col], errors='coerce').fillna(0)
    if exemption_flag_col and exemption_flag_col in result_df.columns:
        result_df[exemption_flag_col] = pd.to_numeric(result_df[exemption_flag_col], errors='coerce').fillna(0)

    # Compute improvement share using full values
    total_value = result_df[land_value_col] + result_df[improvement_value_col]
    with np.errstate(divide='ignore', invalid='ignore'):
        improvement_share = (result_df[improvement_value_col] / total_value).replace([np.inf, -np.inf], np.nan)

    # Compute adjusted values and exclude fully exempt
    adj_land, adj_impr = _compute_adjusted_values(
        result_df, land_value_col, improvement_value_col, exemption_col, exemption_flag_col
    )
    fully_exempt_mask = None
    if exemption_flag_col and exemption_flag_col in result_df.columns:
        fully_exempt_mask = result_df[exemption_flag_col] != 0
    else:
        fully_exempt_mask = pd.Series(False, index=result_df.index)

    non_exempt_mask = ~fully_exempt_mask

    # Define category masks (based on full values)
    total_positive = total_value > 0
    zero_impr_mask = (result_df[improvement_value_col] == 0) & total_positive
    lt_10_mask = (improvement_share > 0) & (improvement_share < 0.10)
    from_10_25_mask = (improvement_share >= 0.10) & (improvement_share < 0.25)
    from_25_50_mask = (improvement_share >= 0.25) & (improvement_share < 0.50)

    # Total adjusted land base for share calculation
    total_adj_land = float(adj_land[non_exempt_mask].sum())
    if total_adj_land <= 0:
        total_adj_land = 1.0  # avoid division by zero; shares will be 0 if sums are 0

    def summarize_category(name: str, mask: pd.Series) -> Dict:
        m = mask & non_exempt_mask
        land_sum = float(adj_land[m].sum())
        count = int(m.sum())
        share_pct = (land_sum / total_adj_land) * 100.0 if total_adj_land > 0 else 0.0
        return {
            'category': name,
            'parcel_count': count,
            'adjusted_land_value': land_sum,
            'share_of_total_land_value_pct': share_pct,
        }

    categories = [
        summarize_category('0% improvement', zero_impr_mask),
        summarize_category('<10% improvement (excl. 0%)', lt_10_mask),
        summarize_category('10-25% improvement', from_10_25_mask),
        summarize_category('25-50% improvement', from_25_50_mask),
    ]

    return {
        'total_adjusted_land_value': float(adj_land[non_exempt_mask].sum()),
        'categories': categories,
        'notes': 'Improvement share computed from full market values; land totals/shares reported on non-exempt basis.'
    }


def calculate_development_tax_penalty(df: pd.DataFrame,
                                    improvement_value_col: str = 'improvement_value',
                                    millage_rate: float = 0.012,
                                    years: int = 30,
                                    discount_rate: float = 0.05,
                                    typical_construction_cost_per_sqft: float = 150,
                                    typical_unit_size_sqft: float = 1200) -> Dict:
    """
    Calculate the present value of building taxes as a penalty for development,
    and estimate how many fewer housing units this represents.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing property data
    improvement_value_col : str
        Column name for improvement/building values
    millage_rate : float
        Tax rate on improvements (as decimal, e.g., 0.012 for 1.2%)
    years : int
        Number of years to calculate NPV over
    discount_rate : float
        Discount rate for NPV calculation (as decimal)
    typical_construction_cost_per_sqft : float
        Typical construction cost per square foot
    typical_unit_size_sqft : float
        Typical housing unit size in square feet
        
    Returns:
    --------
    dict
        Dictionary containing development penalty analysis
    """
    
    # Calculate total improvement value
    total_improvement_value = df[improvement_value_col].sum()
    
    # Annual tax on improvements
    annual_improvement_tax = total_improvement_value * millage_rate
    
    # Calculate NPV of improvement taxes over the specified period
    # NPV = PMT * [(1 - (1 + r)^(-n)) / r]
    if discount_rate == 0:
        npv_improvement_tax = annual_improvement_tax * years
    else:
        npv_factor = (1 - (1 + discount_rate) ** (-years)) / discount_rate
        npv_improvement_tax = annual_improvement_tax * npv_factor
    
    # NPV as percentage of current improvement value (construction cost proxy)
    npv_as_pct_of_construction = (npv_improvement_tax / total_improvement_value) * 100
    
    # Calculate typical construction cost per unit
    typical_unit_construction_cost = typical_construction_cost_per_sqft * typical_unit_size_sqft
    
    # Calculate equivalent "lost" housing units
    equivalent_lost_units = npv_improvement_tax / typical_unit_construction_cost
    
    # Calculate total existing housing units in the city (rough estimate)
    residential_properties = df[df['improvement_value'] > 0]  # Properties with buildings
    # Rough estimate: assume average residential property has 1.5 units (mix of single/multi-family)
    estimated_current_units = len(residential_properties) * 1.5
    
    # Calculate what percentage fewer units this represents
    units_lost_pct = (equivalent_lost_units / estimated_current_units) * 100
    
    analysis_results = {
        'analysis_parameters': {
            'millage_rate_pct': millage_rate * 100,
            'years_analyzed': years,
            'discount_rate_pct': discount_rate * 100,
            'construction_cost_per_sqft': typical_construction_cost_per_sqft,
            'typical_unit_size_sqft': typical_unit_size_sqft
        },
        'total_improvement_value': total_improvement_value,
        'annual_improvement_tax': annual_improvement_tax,
        'npv_improvement_tax': npv_improvement_tax,
        'npv_as_pct_of_construction_cost': npv_as_pct_of_construction,
        'typical_unit_construction_cost': typical_unit_construction_cost,
        'equivalent_lost_units': equivalent_lost_units,
        'estimated_current_units': estimated_current_units,
        'units_lost_percentage': units_lost_pct,
        'interpretation': {
            'summary': f"With a {millage_rate*100:.1f}% building tax, the NPV of taxes over {years} years equals {npv_as_pct_of_construction:.1f}% of initial construction cost.",
            'housing_impact': f"This tax penalty is equivalent to losing {equivalent_lost_units:,.0f} housing units ({units_lost_pct:.1f}% of current housing stock).",
            'policy_implication': f"Removing building taxes could enable {equivalent_lost_units:,.0f} additional housing units to be economically viable."
        }
    }
    
    return analysis_results


def print_vacant_land_summary(analysis_results: Dict) -> None:
    """Print a formatted summary of vacant land analysis results."""
    
    if 'error' in analysis_results:
        print(f"Error: {analysis_results['error']}")
        return
    
    print("="*60)
    print("VACANT LAND ANALYSIS SUMMARY")
    print("="*60)
    
    print(f"Total vacant parcels: {analysis_results['total_vacant_parcels']:,}")
    print(f"Total vacant land value: ${analysis_results['total_vacant_land_value']:,.0f}")
    print(f"Average vacant land value: ${analysis_results['average_vacant_land_value']:,.0f}")
    print(f"Vacant land as % of total city land value: {analysis_results['vacant_land_pct_of_total']:.1f}%")
    
    if 'by_neighborhood' in analysis_results:
        print(f"\nTop 5 neighborhoods by vacant land value:")
        print(analysis_results['by_neighborhood'].head().to_string())
    
    if 'concentration_metrics' in analysis_results:
        print(f"\nOwnership concentration:")
        cm = analysis_results['concentration_metrics']
        print(f"Top 5% of owners control: ${cm['top_5_percent_owners_control_value']:,.0f} ({cm['top_5_percent_share']:.1f}%)")
        print(f"Top 10% of owners control: ${cm['top_10_percent_owners_control_value']:,.0f} ({cm['top_10_percent_share']:.1f}%)")


def print_parking_analysis_summary(analysis_results: Dict) -> None:
    """Print a formatted summary of parking lot analysis results."""
    
    if 'error' in analysis_results:
        print(f"Error: {analysis_results['error']}")
        return
    
    print("="*60)
    print("PARKING LOT EFFICIENCY ANALYSIS")
    print("="*60)
    
    print(f"Total parking lots: {analysis_results['total_parking_lots']:,}")
    print(f"Total parking land value: ${analysis_results['total_parking_land_value']:,.0f}")
    print(f"Average parking land value: ${analysis_results['average_parking_land_value']:,.0f}")
    print(f"Average improvement ratio: {analysis_results['average_improvement_ratio']:.1%}")
    
    underutil = analysis_results['underutilized_parking_lots']
    print(f"\nUnderutilized parking lots ({underutil['criteria']}):")
    print(f"Count: {underutil['count']:,}")
    print(f"Total land value: ${underutil['total_land_value']:,.0f}")
    print(f"Average land value: ${underutil['average_land_value']:,.0f}")
    
    if 'development_potential' in analysis_results:
        dev_pot = analysis_results['development_potential']
        print(f"\nDevelopment potential:")
        print(f"Current improvement value: ${dev_pot['current_improvement_value']:,.0f}")
        print(f"Potential improvement value: ${dev_pot['potential_improvement_value']:,.0f}")
        print(f"Untapped development value: ${dev_pot['untapped_development_value']:,.0f}")


def print_development_penalty_summary(analysis_results: Dict) -> None:
    """Print a formatted summary of development tax penalty analysis."""
    
    print("="*60) 
    print("DEVELOPMENT TAX PENALTY ANALYSIS")
    print("="*60)
    
    params = analysis_results['analysis_parameters']
    print(f"Analysis parameters:")
    print(f"  Building tax rate: {params['millage_rate_pct']:.1f}%")
    print(f"  Time horizon: {params['years_analyzed']} years")
    print(f"  Discount rate: {params['discount_rate_pct']:.1f}%")
    
    print(f"\nResults:")
    print(f"Total improvement value in city: ${analysis_results['total_improvement_value']:,.0f}")
    print(f"Annual building tax revenue: ${analysis_results['annual_improvement_tax']:,.0f}")
    print(f"NPV of building taxes ({params['years_analyzed']} years): ${analysis_results['npv_improvement_tax']:,.0f}")
    print(f"NPV as % of construction cost: {analysis_results['npv_as_pct_of_construction_cost']:.1f}%")
    
    print(f"\nHousing impact analysis:")
    print(f"Equivalent 'lost' housing units: {analysis_results['equivalent_lost_units']:,.0f}")
    print(f"Percentage of current housing stock: {analysis_results['units_lost_percentage']:.1f}%")
    
    print(f"\nInterpretation:")
    for key, message in analysis_results['interpretation'].items():
        print(f"  {message}") 


def analyze_property_values_by_category(df: pd.DataFrame,
                                      category_col: str,
                                      land_value_col: str = 'land_value',
                                      improvement_value_col: str = 'improvement_value',
                                      exemption_col: Optional[str] = None,
                                      exemption_flag_col: Optional[str] = None) -> pd.DataFrame:
    """
    Analyze total land values, improvement values, and ratios by property category.
    If exemptions are provided, also compute non-exempt (taxable) totals following the
    rule: partial exemptions reduce improvements first, then land; fully exempt rows count as $0.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing property data
    category_col : str
        Column name for property categories
    land_value_col : str
        Column name for land values
    improvement_value_col : str
        Column name for improvement values
    exemption_col : str, optional
        Column name for exemption amounts
    exemption_flag_col : str, optional
        Column name for exemption flag (1 for fully exempt, 0 for not exempt)
        
    Returns:
    --------
    pandas.DataFrame
        Summary table with land values, improvement values, and ratios by category
    """
    
    # Ensure numeric values
    result_df = df.copy()
    result_df[land_value_col] = pd.to_numeric(result_df[land_value_col], errors='coerce').fillna(0)
    result_df[improvement_value_col] = pd.to_numeric(result_df[improvement_value_col], errors='coerce').fillna(0)
    
    if exemption_col:
        result_df[exemption_col] = pd.to_numeric(result_df[exemption_col], errors='coerce').fillna(0)
    if exemption_flag_col:
        result_df[exemption_flag_col] = pd.to_numeric(result_df[exemption_flag_col], errors='coerce').fillna(0)
    
    # Group by category and calculate totals (raw)
    summary = result_df.groupby(category_col).agg({
        land_value_col: ['sum', 'count'],
        improvement_value_col: 'sum'
    })
    
    # Flatten column names
    summary.columns = ['total_land_value', 'property_count', 'total_improvement_value']
    
    # Calculate improvement to land ratio (raw)
    summary['improvement_land_ratio'] = (
        summary['total_improvement_value'] / summary['total_land_value']
    ).replace([np.inf, -np.inf], 0).fillna(0)
    
    # Add exemption analysis if exemption columns provided
    if exemption_col:
        exemption_summary = result_df.groupby(category_col)[exemption_col].sum()
        summary['total_exemptions'] = exemption_summary
    
    # Compute adjusted (non-exempt) totals if either partial or full exemption info is provided
    if exemption_col or exemption_flag_col:
        adj_land, adj_impr = _compute_adjusted_values(
            result_df, land_value_col, improvement_value_col, exemption_col, exemption_flag_col
        )
        adjusted = pd.DataFrame({
            category_col: result_df[category_col],
            'adj_land_value': adj_land,
            'adj_improvement_value': adj_impr if adj_impr is not None else 0,
        })
        non_exempt_summary = adjusted.groupby(category_col).agg({
            'adj_land_value': 'sum',
            'adj_improvement_value': 'sum'
        })
        non_exempt_summary.columns = ['non_exempt_land_value', 'non_exempt_improvement_value']
        
        # Calculate non-exempt improvement to land ratio
        non_exempt_summary['non_exempt_improvement_land_ratio'] = (
            non_exempt_summary['non_exempt_improvement_value'] / 
            non_exempt_summary['non_exempt_land_value']
        ).replace([np.inf, -np.inf], 0).fillna(0)
        
        # Merge with main summary
        summary = summary.join(non_exempt_summary, how='left').fillna(0)
    
    # Fully exempt counts if flag present
    if exemption_flag_col:
        fully_exempt_count = result_df[result_df[exemption_flag_col] == 1].groupby(category_col).size()
        summary['fully_exempt_count'] = fully_exempt_count
    
    # Reset index to make category a regular column
    summary = summary.reset_index()
    
    # Sort by total land value (descending)
    summary = summary.sort_values('total_land_value', ascending=False)
    
    return summary


def print_property_values_summary(summary_df: pd.DataFrame, 
                                 title: str = "Property Values by Category") -> None:
    """
    Print a formatted summary of property values by category.
    
    Parameters:
    -----------
    summary_df : pandas.DataFrame
        Summary DataFrame from analyze_property_values_by_category
    title : str
        Title for the summary report
    """
    
    print("="*80)
    print(title.upper())
    print("="*80)
    
    # Format the display
    display_df = summary_df.copy()
    
    # Format currency columns
    currency_cols = ['total_land_value', 'total_improvement_value', 'total_exemptions']
    if 'non_exempt_land_value' in display_df.columns:
        currency_cols.extend(['non_exempt_land_value', 'non_exempt_improvement_value'])
    
    for col in currency_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")
    
    # Format ratio columns
    ratio_cols = ['improvement_land_ratio']
    if 'non_exempt_improvement_land_ratio' in display_df.columns:
        ratio_cols.append('non_exempt_improvement_land_ratio')
    
    for col in ratio_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}")
    
    # Print the table
    print(display_df.to_string(index=False))
    
    # Print summary statistics
    numeric_df = summary_df.select_dtypes(include=[np.number])
    print(f"\nSUMMARY TOTALS:")
    print(f"Total Properties: {summary_df['property_count'].sum():,}")
    print(f"Total Land Value: ${summary_df['total_land_value'].sum():,.0f}")
    print(f"Total Improvement Value: ${summary_df['total_improvement_value'].sum():,.0f}")
    print(f"Overall Improvement:Land Ratio: {summary_df['total_improvement_value'].sum() / summary_df['total_land_value'].sum():.2f}")
    
    if 'total_exemptions' in summary_df.columns:
        print(f"Total Exemptions: ${summary_df['total_exemptions'].sum():,.0f}")
    
    if 'fully_exempt_count' in summary_df.columns:
        print(f"Fully Exempt Properties: {summary_df['fully_exempt_count'].sum():,.0f}") 