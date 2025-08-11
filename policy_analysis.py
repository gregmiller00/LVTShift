import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, Union, List

def analyze_vacant_land(df: pd.DataFrame, 
                       land_value_col: str = 'land_value',
                       property_type_col: str = 'prop_use_desc',
                       neighborhood_col: Optional[str] = None,
                       zoning_col: Optional[str] = None,
                       owner_col: Optional[str] = None,
                       vacant_identifier: str = 'Vacant Land') -> Dict:
    """
    Analyze vacant land patterns including total values, concentration, and geographic distribution.
    
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
    
    # Overall totals
    analysis_results['total_vacant_parcels'] = len(vacant_df)
    analysis_results['total_vacant_land_value'] = vacant_df[land_value_col].sum()
    analysis_results['average_vacant_land_value'] = vacant_df[land_value_col].mean()
    analysis_results['median_vacant_land_value'] = vacant_df[land_value_col].median()
    
    # Percentage of total city land value that is vacant
    total_city_land_value = df[land_value_col].sum()
    analysis_results['vacant_land_pct_of_total'] = (analysis_results['total_vacant_land_value'] / total_city_land_value) * 100
    
    # By neighborhood analysis
    if neighborhood_col and neighborhood_col in df.columns:
        neighborhood_analysis = vacant_df.groupby(neighborhood_col).agg({
            land_value_col: ['count', 'sum', 'mean', 'median']
        }).round(2)
        neighborhood_analysis.columns = ['count', 'total_value', 'avg_value', 'median_value']
        neighborhood_analysis = neighborhood_analysis.sort_values('total_value', ascending=False)
        analysis_results['by_neighborhood'] = neighborhood_analysis
    
    # By zoning analysis  
    if zoning_col and zoning_col in df.columns:
        zoning_analysis = vacant_df.groupby(zoning_col).agg({
            land_value_col: ['count', 'sum', 'mean', 'median']
        }).round(2)
        zoning_analysis.columns = ['count', 'total_value', 'avg_value', 'median_value']
        zoning_analysis = zoning_analysis.sort_values('total_value', ascending=False)
        analysis_results['by_zoning'] = zoning_analysis
    
    # Owner concentration analysis
    if owner_col and owner_col in df.columns:
        owner_analysis = vacant_df.groupby(owner_col).agg({
            land_value_col: ['count', 'sum']
        }).round(2)
        owner_analysis.columns = ['parcel_count', 'total_land_value']
        owner_analysis = owner_analysis.sort_values('total_land_value', ascending=False)
        
        # Top 10 owners by value
        analysis_results['top_10_owners_by_value'] = owner_analysis.head(10)
        
        # Concentration metrics
        top_5_pct = owner_analysis['total_land_value'].head(int(len(owner_analysis) * 0.05)).sum()
        top_10_pct = owner_analysis['total_land_value'].head(int(len(owner_analysis) * 0.10)).sum()
        
        analysis_results['concentration_metrics'] = {
            'top_5_percent_owners_control_value': top_5_pct,
            'top_5_percent_share': (top_5_pct / analysis_results['total_vacant_land_value']) * 100,
            'top_10_percent_owners_control_value': top_10_pct,
            'top_10_percent_share': (top_10_pct / analysis_results['total_vacant_land_value']) * 100
        }
    
    return analysis_results


def analyze_parking_lots(df: pd.DataFrame,
                        land_value_col: str = 'land_value',
                        improvement_value_col: str = 'improvement_value', 
                        property_type_col: str = 'prop_use_desc',
                        parking_identifier: str = 'Trans - Parking',
                        min_land_value_threshold: float = 50000,
                        max_improvement_ratio: float = 0.1) -> Dict:
    """
    Analyze parking lots to identify inefficient land use on valuable property.
    
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
    
    # Calculate improvement to land ratio
    parking_df['improvement_to_land_ratio'] = parking_df[improvement_value_col] / parking_df[land_value_col]
    parking_df['improvement_to_land_ratio'] = parking_df['improvement_to_land_ratio'].fillna(0)
    
    analysis_results = {}
    
    # Overall parking lot statistics
    analysis_results['total_parking_lots'] = len(parking_df)
    analysis_results['total_parking_land_value'] = parking_df[land_value_col].sum()
    analysis_results['total_parking_improvement_value'] = parking_df[improvement_value_col].sum()
    analysis_results['average_parking_land_value'] = parking_df[land_value_col].mean()
    analysis_results['average_improvement_ratio'] = parking_df['improvement_to_land_ratio'].mean()
    
    # High-value, underutilized parking lots
    underutilized_mask = (
        (parking_df[land_value_col] >= min_land_value_threshold) &
        (parking_df['improvement_to_land_ratio'] <= max_improvement_ratio)
    )
    underutilized_parking = parking_df[underutilized_mask]
    
    analysis_results['underutilized_parking_lots'] = {
        'count': len(underutilized_parking),
        'total_land_value': underutilized_parking[land_value_col].sum(),
        'average_land_value': underutilized_parking[land_value_col].mean() if len(underutilized_parking) > 0 else 0,
        'total_improvement_value': underutilized_parking[improvement_value_col].sum(),
        'criteria': f"Land value >= ${min_land_value_threshold:,.0f} and improvement ratio <= {max_improvement_ratio:.1%}"
    }
    
    # Development potential analysis
    if len(underutilized_parking) > 0:
        # Estimate potential development value (assuming development to similar density as surrounding area)
        avg_improvement_ratio_citywide = df[improvement_value_col].sum() / df[land_value_col].sum()
        potential_development_value = underutilized_parking[land_value_col].sum() * avg_improvement_ratio_citywide
        current_development_value = underutilized_parking[improvement_value_col].sum()
        
        analysis_results['development_potential'] = {
            'current_improvement_value': current_development_value,
            'potential_improvement_value': potential_development_value,
            'untapped_development_value': potential_development_value - current_development_value,
            'citywide_avg_improvement_ratio': avg_improvement_ratio_citywide
        }
    
    # Create summary by land value tiers
    parking_df['land_value_tier'] = pd.cut(parking_df[land_value_col], 
                                          bins=[0, 25000, 50000, 100000, 250000, float('inf')],
                                          labels=['<$25k', '$25k-$50k', '$50k-$100k', '$100k-$250k', '>$250k'])
    
    tier_analysis = parking_df.groupby('land_value_tier').agg({
        land_value_col: ['count', 'sum', 'mean'],
        'improvement_to_land_ratio': 'mean'
    }).round(3)
    tier_analysis.columns = ['count', 'total_land_value', 'avg_land_value', 'avg_improvement_ratio']
    analysis_results['by_land_value_tier'] = tier_analysis
    
    return analysis_results


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
    
    # Group by category and calculate totals
    summary = result_df.groupby(category_col).agg({
        land_value_col: ['sum', 'count'],
        improvement_value_col: 'sum'
    })
    
    # Flatten column names
    summary.columns = ['total_land_value', 'property_count', 'total_improvement_value']
    
    # Calculate improvement to land ratio
    summary['improvement_land_ratio'] = summary['total_improvement_value'] / summary['total_land_value']
    summary['improvement_land_ratio'] = summary['improvement_land_ratio'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Add exemption analysis if exemption columns provided
    if exemption_col:
        exemption_summary = result_df.groupby(category_col)[exemption_col].sum()
        summary['total_exemptions'] = exemption_summary
    
    if exemption_flag_col:
        fully_exempt_count = result_df[result_df[exemption_flag_col] == 1].groupby(category_col).size()
        summary['fully_exempt_count'] = fully_exempt_count.fillna(0)
        
        # Calculate values excluding fully exempt properties
        non_exempt_df = result_df[result_df[exemption_flag_col] == 0]
        non_exempt_summary = non_exempt_df.groupby(category_col).agg({
            land_value_col: 'sum',
            improvement_value_col: 'sum'
        })
        non_exempt_summary.columns = ['non_exempt_land_value', 'non_exempt_improvement_value']
        
        # Calculate non-exempt improvement to land ratio
        non_exempt_summary['non_exempt_improvement_land_ratio'] = (
            non_exempt_summary['non_exempt_improvement_value'] / 
            non_exempt_summary['non_exempt_land_value']
        )
        non_exempt_summary['non_exempt_improvement_land_ratio'] = (
            non_exempt_summary['non_exempt_improvement_land_ratio']
            .replace([np.inf, -np.inf], 0).fillna(0)
        )
        
        # Merge with main summary
        summary = summary.join(non_exempt_summary, how='left').fillna(0)
    
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