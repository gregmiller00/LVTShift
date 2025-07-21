import pandas as pd
import numpy as np
from typing import Union, List, Tuple, Optional

def calculate_current_tax(df: pd.DataFrame, tax_value_col: str, millage_rate_col: str, exemption_col: Optional[str] = None, exemption_flag_col: Optional[str] = None, percentage_cap_col: Optional[str] = None, second_millage_rate_col: Optional[str] = None) -> Tuple[float, float, pd.DataFrame]:
    """
    Calculate current property tax based on tax value and millage rate.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing property data
    tax_value_col : str
        Column name for taxable value
    millage_rate_col : str
        Column name for millage rate
    exemption_col : str, optional
        Column name for exemptions
    exemption_flag_col : str, optional
        Column name for exemption flag (1 for exempt, 0 for not exempt)
    percentage_cap_col : str, optional
        Column name for percentage cap (maximum tax as percentage of property value)
    second_millage_rate_col : str, optional
        Column name for secondary millage rate (must be less than primary millage rate)
        
    Returns:
    --------
    tuple
        (total_revenue, second_revenue, updated_dataframe)
    """
    # Type checking
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if not isinstance(tax_value_col, str):
        raise TypeError("tax_value_col must be a string")
    if not isinstance(millage_rate_col, str):
        raise TypeError("millage_rate_col must be a string")
    if exemption_col is not None and not isinstance(exemption_col, str):
        raise TypeError("exemption_col must be a string or None")
    if exemption_flag_col is not None and not isinstance(exemption_flag_col, str):
        raise TypeError("exemption_flag_col must be a string or None")
    if percentage_cap_col is not None and not isinstance(percentage_cap_col, str):
        raise TypeError("percentage_cap_col must be a string or None")
    if second_millage_rate_col is not None and not isinstance(second_millage_rate_col, str):
        raise TypeError("second_millage_rate_col must be a string or None")
    
    # Check if columns exist in the DataFrame
    for col in [tax_value_col, millage_rate_col]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
    if exemption_col is not None and exemption_col not in df.columns:
        raise ValueError(f"Exemption column '{exemption_col}' not found in DataFrame")
    if exemption_flag_col is not None and exemption_flag_col not in df.columns:
        raise ValueError(f"Exemption flag column '{exemption_flag_col}' not found in DataFrame")
    if percentage_cap_col is not None and percentage_cap_col not in df.columns:
        raise ValueError(f"Percentage cap column '{percentage_cap_col}' not found in DataFrame")
    if second_millage_rate_col is not None and second_millage_rate_col not in df.columns:
        raise ValueError(f"Second millage rate column '{second_millage_rate_col}' not found in DataFrame")
    
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Ensure numeric values
    result_df[tax_value_col] = pd.to_numeric(result_df[tax_value_col], errors='coerce')
    result_df[millage_rate_col] = pd.to_numeric(result_df[millage_rate_col], errors='coerce')
    
    if second_millage_rate_col is not None:
        result_df[second_millage_rate_col] = pd.to_numeric(result_df[second_millage_rate_col], errors='coerce')
        # Verify second millage rate is less than primary
        if (result_df[second_millage_rate_col] > result_df[millage_rate_col]).any():
            raise ValueError("Second millage rate must be less than the primary millage rate")
    
    # Apply exemptions if provided
    if exemption_flag_col is not None:
        result_df[exemption_flag_col] = pd.to_numeric(result_df[exemption_flag_col], errors='coerce').fillna(0)
        taxable_value = result_df[tax_value_col].where(result_df[exemption_flag_col] == 0, 0)
    else:
        taxable_value = result_df[tax_value_col]
    
    if exemption_col is not None:
        result_df[exemption_col] = pd.to_numeric(result_df[exemption_col], errors='coerce').fillna(0)
        taxable_value = (taxable_value - result_df[exemption_col]).clip(lower=0)
    
    # Calculate tax amount
    result_df['current_tax'] = taxable_value * result_df[millage_rate_col] / 1000
    
    # Apply percentage cap if provided
    if percentage_cap_col is not None:
        result_df[percentage_cap_col] = pd.to_numeric(result_df[percentage_cap_col], errors='coerce').fillna(1)
        # Calculate maximum tax based on percentage cap
        max_tax = result_df[tax_value_col] * result_df[percentage_cap_col]
        # Create a flag to indicate if the tax was capped
        result_df['tax_capped'] = result_df['current_tax'] > max_tax
        # Apply cap - tax cannot exceed the percentage cap of property value
        result_df['current_tax'] = np.minimum(result_df['current_tax'], max_tax)
    # Handle NaN values safely
    result_df['current_tax'] = result_df['current_tax'].fillna(0)
    
    # Calculate total revenue
    total_revenue = float(result_df['current_tax'].sum())
    
    # Calculate second revenue if second millage rate is provided
    second_revenue = 0.0
    if second_millage_rate_col is not None:
        # Calculate second tax based on the ratio of second millage to primary millage
        result_df['second_tax'] = result_df['current_tax'] * (result_df[second_millage_rate_col] / result_df[millage_rate_col])
        result_df['second_tax'] = result_df['second_tax'].fillna(0)
        second_revenue = float(result_df['second_tax'].sum())
        print(f"Total second tax revenue: ${second_revenue:,.2f}")
    
    print(f"Total current tax revenue: ${total_revenue:,.2f}")
    
    return total_revenue, second_revenue, result_df

def model_split_rate_tax(df: pd.DataFrame, land_value_col: str, improvement_value_col: str, 
                         current_revenue: float, land_improvement_ratio: float = 3, 
                         exemption_col: Optional[str] = None, exemption_flag_col: Optional[str] = None,
                         percentage_cap_col: Optional[str] = None) -> Tuple[float, float, float, pd.DataFrame]:
    """
    Model a split-rate property tax where land is taxed at a higher rate than improvements.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing property data
    land_value_col : str
        Column name for land value
    improvement_value_col : str
        Column name for improvement/building value
    current_revenue : float
        Current tax revenue to maintain
    land_improvement_ratio : float, default=3
        Ratio of land tax rate to improvement tax rate
    exemption_col : str, optional
        Column name for exemptions
    exemption_flag_col : str, optional
        Column name for exemption flag (1 for exempt, 0 for not exempt)
    percentage_cap_col : str, optional
        Column name for percentage cap (maximum tax as percentage of property value)
        
    Returns:
    --------
    tuple
        (land_millage, improvement_millage, total_revenue, updated_dataframe)
    """
    # Type checking
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if not isinstance(land_value_col, str):
        raise TypeError("land_value_col must be a string")
    if not isinstance(improvement_value_col, str):
        raise TypeError("improvement_value_col must be a string")
    if not isinstance(current_revenue, (int, float)):
        try:
            current_revenue = float(current_revenue)
        except (ValueError, TypeError):
            raise TypeError("current_revenue must be a number")
    if not isinstance(land_improvement_ratio, (int, float)):
        try:
            land_improvement_ratio = float(land_improvement_ratio)
        except (ValueError, TypeError):
            raise TypeError("land_improvement_ratio must be a number")
    if exemption_col is not None and not isinstance(exemption_col, str):
        raise TypeError("exemption_col must be a string or None")
    if exemption_flag_col is not None and not isinstance(exemption_flag_col, str):
        raise TypeError("exemption_flag_col must be a string or None")
    if percentage_cap_col is not None and not isinstance(percentage_cap_col, str):
        raise TypeError("percentage_cap_col must be a string or None")
    
    # Check if columns exist in the DataFrame
    for col in [land_value_col, improvement_value_col]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
    if exemption_col is not None and exemption_col not in df.columns:
        raise ValueError(f"Exemption column '{exemption_col}' not found in DataFrame")
    if exemption_flag_col is not None and exemption_flag_col not in df.columns:
        raise ValueError(f"Exemption flag column '{exemption_flag_col}' not found in DataFrame")
    if percentage_cap_col is not None and percentage_cap_col not in df.columns:
        raise ValueError(f"Percentage cap column '{percentage_cap_col}' not found in DataFrame")
    
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Ensure numeric values
    result_df[land_value_col] = pd.to_numeric(result_df[land_value_col], errors='coerce').fillna(0)
    result_df[improvement_value_col] = pd.to_numeric(result_df[improvement_value_col], errors='coerce').fillna(0)
    
    # Handle exemptions
    if exemption_flag_col is not None:
        result_df[exemption_flag_col] = pd.to_numeric(result_df[exemption_flag_col], errors='coerce').fillna(0)
        adj_improvement_value = result_df[improvement_value_col].where(result_df[exemption_flag_col] == 0, 0)
        adj_land_value = result_df[land_value_col].where(result_df[exemption_flag_col] == 0, 0)
    else:
        adj_improvement_value = result_df[improvement_value_col]
        adj_land_value = result_df[land_value_col]
    
    if exemption_col is not None:
        result_df[exemption_col] = pd.to_numeric(result_df[exemption_col], errors='coerce').fillna(0)
        # First apply exemptions to improvements
        remaining_exemptions = result_df[exemption_col] - adj_improvement_value
        
        # Calculate adjusted improvement value
        adj_improvement_value = (adj_improvement_value - result_df[exemption_col]).clip(lower=0)
        
        # Apply remaining exemptions to land value if necessary
        adj_land_value = (adj_land_value - remaining_exemptions.clip(lower=0)).clip(lower=0)
    
    # Calculate total values for rate determination
    total_land_value = float(adj_land_value.sum())
    total_improvement_value = float(adj_improvement_value.sum())
    
    # Prevent division by zero
    denominator = (total_improvement_value + land_improvement_ratio * total_land_value)
    if denominator <= 0:
        raise ValueError("Total taxable value is zero or negative, cannot calculate millage rates")
    
    # If we have a percentage cap, we need to use an iterative approach to find the correct millage rates
    if percentage_cap_col is not None:
        result_df[percentage_cap_col] = pd.to_numeric(result_df[percentage_cap_col], errors='coerce').fillna(1)
        total_value = result_df[land_value_col] + result_df[improvement_value_col]
        
        # Initial guess for millage rates
        improvement_millage = (current_revenue * 1000) / denominator
        land_millage = land_improvement_ratio * improvement_millage
        
        # Iterative approach to find the correct millage rates
        max_iterations = 40
        tolerance = 0.00001  # 0.1% tolerance
        iteration = 0
        adjustment_factor = 1.0
        
        while iteration < max_iterations:
            # Calculate taxes with current millage rates
            land_tax = adj_land_value * land_millage / 1000
            improvement_tax = adj_improvement_value * improvement_millage / 1000
            uncapped_tax = land_tax + improvement_tax
            
            # Apply cap
            max_tax = total_value * result_df[percentage_cap_col]
            capped_tax = np.minimum(uncapped_tax, max_tax)
            
            # Calculate total revenue with caps applied
            new_total_revenue = float(capped_tax.sum())
            
            # Check if we're close enough to the target revenue
            if abs(new_total_revenue - current_revenue) / current_revenue < tolerance:
                break
                
            # Adjust millage rates to get closer to target revenue
            adjustment_factor = current_revenue / new_total_revenue
            improvement_millage *= adjustment_factor
            land_millage = land_improvement_ratio * improvement_millage
            
            iteration += 1
        
        if iteration == max_iterations:
            print(f"Warning: Maximum iterations reached. Revenue target may not be exact. Current: ${new_total_revenue:,.2f}, Target: ${current_revenue:,.2f}")
    else:
        # Calculate millage rates to maintain revenue neutrality (no cap)
        improvement_millage = (current_revenue * 1000) / denominator
        land_millage = land_improvement_ratio * improvement_millage
    
    # Calculate new tax amounts
    result_df['land_tax'] = adj_land_value * land_millage / 1000
    result_df['improvement_tax'] = adj_improvement_value * improvement_millage / 1000
    result_df['new_tax'] = result_df['land_tax'] + result_df['improvement_tax']
    
    # Apply percentage cap if provided
    if percentage_cap_col is not None:
        # Calculate maximum tax based on percentage cap
        total_value = result_df[land_value_col] + result_df[improvement_value_col]
        max_tax = total_value * result_df[percentage_cap_col]
        # Create a flag to indicate if the tax was capped
        result_df['tax_capped'] = result_df['new_tax'] > max_tax
        # Apply cap - tax cannot exceed the percentage cap of property value
        result_df['new_tax'] = np.minimum(result_df['new_tax'], max_tax)
        
        # Recalculate land_tax and improvement_tax to maintain the same ratio
        # but respect the cap
        cap_applied = result_df['tax_capped']
        total_uncapped = result_df['land_tax'] + result_df['improvement_tax']
        
        # For properties where cap is applied, redistribute the capped tax amount
        # proportionally between land and improvements
        result_df.loc[cap_applied, 'land_tax'] = (
            result_df.loc[cap_applied, 'land_tax'] / 
            total_uncapped[cap_applied] * 
            result_df.loc[cap_applied, 'new_tax']
        )
        
        result_df.loc[cap_applied, 'improvement_tax'] = (
            result_df.loc[cap_applied, 'improvement_tax'] / 
            total_uncapped[cap_applied] * 
            result_df.loc[cap_applied, 'new_tax']
        )
    
    # Calculate total revenue with new system
    new_total_revenue = float(result_df['new_tax'].sum())
    
    # Calculate change in tax
    if 'current_tax' in result_df.columns:
        result_df['tax_change'] = result_df['new_tax'] - result_df['current_tax']
        # Avoid division by zero
        result_df['tax_change_pct'] = np.where(
            result_df['current_tax'] > 0,
            (result_df['tax_change'] / result_df['current_tax']) * 100,
            0
        )
    
    print(f"Split-rate tax model (Land:Improvement = {land_improvement_ratio}:1)")
    print(f"Land millage rate: {land_millage:.4f}")
    print(f"Improvement millage rate: {improvement_millage:.4f}")
    print(f"Total tax revenue: ${new_total_revenue:,.2f}")
    print(f"Target revenue: ${current_revenue:,.2f}")
    print(f"Revenue difference: ${new_total_revenue - current_revenue:,.2f} ({(new_total_revenue/current_revenue - 1)*100:.4f}%)")
    
    return land_millage, improvement_millage, new_total_revenue, result_df

def model_full_building_abatement(df: pd.DataFrame, land_value_col: str, improvement_value_col: str, 
                                 current_revenue: float, abatement_percentage: float = 1.0,
                                 exemption_col: Optional[str] = None, exemption_flag_col: Optional[str] = None,
                                 percentage_cap_col: Optional[str] = None) -> Tuple[float, float, pd.DataFrame]:
    """
    Model a building abatement system where improvements are reduced by a specified percentage.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing property data
    land_value_col : str
        Column name for land value
    improvement_value_col : str
        Column name for improvement/building value
    current_revenue : float
        Current tax revenue to maintain
    abatement_percentage : float, default=1.0
        Percentage of improvement value to abate (1.0 = 100% abatement, 0.5 = 50% abatement)
    exemption_col : str, optional
        Column name for exemptions
    exemption_flag_col : str, optional
        Column name for exemption flag (1 for exempt, 0 for not exempt)
    percentage_cap_col : str, optional
        Column name for percentage cap (maximum tax as percentage of property value)
        
    Returns:
    --------
    tuple
        (millage_rate, total_revenue, updated_dataframe)
    """
    # Type checking
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if not isinstance(land_value_col, str):
        raise TypeError("land_value_col must be a string")
    if not isinstance(improvement_value_col, str):
        raise TypeError("improvement_value_col must be a string")
    if not isinstance(current_revenue, (int, float)):
        try:
            current_revenue = float(current_revenue)
        except (ValueError, TypeError):
            raise TypeError("current_revenue must be a number")
    if not isinstance(abatement_percentage, (int, float)):
        try:
            abatement_percentage = float(abatement_percentage)
        except (ValueError, TypeError):
            raise TypeError("abatement_percentage must be a number")
    if abatement_percentage < 0 or abatement_percentage > 1:
        raise ValueError("abatement_percentage must be between 0 and 1")
    if exemption_col is not None and not isinstance(exemption_col, str):
        raise TypeError("exemption_col must be a string or None")
    if exemption_flag_col is not None and not isinstance(exemption_flag_col, str):
        raise TypeError("exemption_flag_col must be a string or None")
    if percentage_cap_col is not None and not isinstance(percentage_cap_col, str):
        raise TypeError("percentage_cap_col must be a string or None")
    
    # Check if columns exist in the DataFrame
    for col in [land_value_col, improvement_value_col]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
    if exemption_col is not None and exemption_col not in df.columns:
        raise ValueError(f"Exemption column '{exemption_col}' not found in DataFrame")
    if exemption_flag_col is not None and exemption_flag_col not in df.columns:
        raise ValueError(f"Exemption flag column '{exemption_flag_col}' not found in DataFrame")
    if percentage_cap_col is not None and percentage_cap_col not in df.columns:
        raise ValueError(f"Percentage cap column '{percentage_cap_col}' not found in DataFrame")
    
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Ensure numeric values
    result_df[land_value_col] = pd.to_numeric(result_df[land_value_col], errors='coerce').fillna(0)
    result_df[improvement_value_col] = pd.to_numeric(result_df[improvement_value_col], errors='coerce').fillna(0)
    
    # Apply building abatement (reduce improvement values)
    result_df['abated_improvement_value'] = result_df[improvement_value_col] * (1 - abatement_percentage)
    
    # Handle exemptions - exemptions are applied to land until land is zero
    if exemption_flag_col is not None:
        result_df[exemption_flag_col] = pd.to_numeric(result_df[exemption_flag_col], errors='coerce').fillna(0)
        adj_improvement_value = result_df['abated_improvement_value'].where(result_df[exemption_flag_col] == 0, 0)
        adj_land_value = result_df[land_value_col].where(result_df[exemption_flag_col] == 0, 0)
    else:
        adj_improvement_value = result_df['abated_improvement_value']
        adj_land_value = result_df[land_value_col]
    
    if exemption_col is not None:
        result_df[exemption_col] = pd.to_numeric(result_df[exemption_col], errors='coerce').fillna(0)
        # Apply exemptions to land first until land is zero
        land_exemption = np.minimum(result_df[exemption_col], adj_land_value)
        adj_land_value = adj_land_value - land_exemption
        
        # Apply remaining exemptions to improvements
        remaining_exemptions = result_df[exemption_col] - land_exemption
        adj_improvement_value = (adj_improvement_value - remaining_exemptions).clip(lower=0)
    
    # Calculate total taxable value
    total_taxable_value = float((adj_land_value + adj_improvement_value).sum())
    
    # Prevent division by zero
    if total_taxable_value <= 0:
        raise ValueError("Total taxable value is zero or negative, cannot calculate millage rate")
    
    # If we have a percentage cap, we need to use an iterative approach to find the correct millage rate
    if percentage_cap_col is not None:
        result_df[percentage_cap_col] = pd.to_numeric(result_df[percentage_cap_col], errors='coerce').fillna(1)
        total_value = result_df[land_value_col] + result_df[improvement_value_col]
        
        # Initial guess for millage rate
        millage_rate = (current_revenue * 1000) / total_taxable_value
        
        # Iterative approach to find the correct millage rate
        max_iterations = 40
        tolerance = 0.00001  # 0.001% tolerance
        iteration = 0
        adjustment_factor = 1.0
        
        while iteration < max_iterations:
            # Calculate taxes with current millage rate
            uncapped_tax = (adj_land_value + adj_improvement_value) * millage_rate / 1000
            
            # Apply cap
            max_tax = total_value * result_df[percentage_cap_col]
            capped_tax = np.minimum(uncapped_tax, max_tax)
            
            # Calculate total revenue with caps applied
            new_total_revenue = float(capped_tax.sum())
            
            # Check if we're close enough to the target revenue
            if abs(new_total_revenue - current_revenue) / current_revenue < tolerance:
                break
                
            # Adjust millage rate to get closer to target revenue
            adjustment_factor = current_revenue / new_total_revenue
            millage_rate *= adjustment_factor
            
            iteration += 1
        
        if iteration == max_iterations:
            print(f"Warning: Maximum iterations reached. Revenue target may not be exact. Current: ${new_total_revenue:,.2f}, Target: ${current_revenue:,.2f}")
    else:
        # Calculate millage rate to maintain revenue neutrality (no cap)
        millage_rate = (current_revenue * 1000) / total_taxable_value
    
    # Calculate new tax amounts
    result_df['taxable_value'] = adj_land_value + adj_improvement_value
    result_df['new_tax'] = result_df['taxable_value'] * millage_rate / 1000
    
    # Apply percentage cap if provided
    if percentage_cap_col is not None:
        # Calculate maximum tax based on percentage cap
        total_value = result_df[land_value_col] + result_df[improvement_value_col]
        max_tax = total_value * result_df[percentage_cap_col]
        # Create a flag to indicate if the tax was capped
        result_df['tax_capped'] = result_df['new_tax'] > max_tax
        # Apply cap - tax cannot exceed the percentage cap of property value
        result_df['new_tax'] = np.minimum(result_df['new_tax'], max_tax)
    
    # Calculate total revenue with new system
    new_total_revenue = float(result_df['new_tax'].sum())
    
    # Calculate change in tax
    if 'current_tax' in result_df.columns:
        result_df['tax_change'] = result_df['new_tax'] - result_df['current_tax']
        # Avoid division by zero
        result_df['tax_change_pct'] = np.where(
            result_df['current_tax'] > 0,
            (result_df['tax_change'] / result_df['current_tax']) * 100,
            0
        )
    
    print(f"Building abatement model ({abatement_percentage*100:.1f}% abatement)")
    print(f"Millage rate: {millage_rate:.4f}")
    print(f"Total tax revenue: ${new_total_revenue:,.2f}")
    print(f"Target revenue: ${current_revenue:,.2f}")
    print(f"Revenue difference: ${new_total_revenue - current_revenue:,.2f} ({(new_total_revenue/current_revenue - 1)*100:.4f}%)")
    
    return millage_rate, new_total_revenue, result_df

def model_stacking_improvement_exemption(df: pd.DataFrame, land_value_col: str, improvement_value_col: str, 
                                       current_revenue: float, improvement_exemption_percentage: float = 0.5,
                                       building_abatement_floor: float = 0.0,
                                       exemption_col: Optional[str] = None, exemption_flag_col: Optional[str] = None,
                                       percentage_cap_col: Optional[str] = None) -> Tuple[float, float, pd.DataFrame]:
    """
    Model a stacking exemption system where a percentage of improvement value is added to existing exemptions.
    The new millage rate is applied to the full land+building value minus the stacked exemptions.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing property data
    land_value_col : str
        Column name for land value
    improvement_value_col : str
        Column name for improvement/building value
    current_revenue : float
        Current tax revenue to maintain
    improvement_exemption_percentage : float, default=0.5
        Percentage of improvement value to add as exemption (0.5 = 50%)
    building_abatement_floor : float, default=0.0
        Dollar amount automatically subtracted from improvement value before applying percentage exemption
    exemption_col : str, optional
        Column name for existing exemptions
    exemption_flag_col : str, optional
        Column name for exemption flag (1 for exempt, 0 for not exempt)
    percentage_cap_col : str, optional
        Column name for percentage cap (maximum tax as percentage of property value)
        
    Returns:
    --------
    tuple
        (millage_rate, total_revenue, updated_dataframe)
    """
    # Type checking
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if not isinstance(land_value_col, str):
        raise TypeError("land_value_col must be a string")
    if not isinstance(improvement_value_col, str):
        raise TypeError("improvement_value_col must be a string")
    if not isinstance(current_revenue, (int, float)):
        try:
            current_revenue = float(current_revenue)
        except (ValueError, TypeError):
            raise TypeError("current_revenue must be a number")
    if not isinstance(improvement_exemption_percentage, (int, float)):
        try:
            improvement_exemption_percentage = float(improvement_exemption_percentage)
        except (ValueError, TypeError):
            raise TypeError("improvement_exemption_percentage must be a number")
    if improvement_exemption_percentage < 0 or improvement_exemption_percentage > 1:
        raise ValueError("improvement_exemption_percentage must be between 0 and 1")
    if not isinstance(building_abatement_floor, (int, float)):
        try:
            building_abatement_floor = float(building_abatement_floor)
        except (ValueError, TypeError):
            raise TypeError("building_abatement_floor must be a number")
    if building_abatement_floor < 0:
        raise ValueError("building_abatement_floor must be non-negative")
    if exemption_col is not None and not isinstance(exemption_col, str):
        raise TypeError("exemption_col must be a string or None")
    if exemption_flag_col is not None and not isinstance(exemption_flag_col, str):
        raise TypeError("exemption_flag_col must be a string or None")
    if percentage_cap_col is not None and not isinstance(percentage_cap_col, str):
        raise TypeError("percentage_cap_col must be a string or None")
    
    # Check if columns exist in the DataFrame
    for col in [land_value_col, improvement_value_col]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
    if exemption_col is not None and exemption_col not in df.columns:
        raise ValueError(f"Exemption column '{exemption_col}' not found in DataFrame")
    if exemption_flag_col is not None and exemption_flag_col not in df.columns:
        raise ValueError(f"Exemption flag column '{exemption_flag_col}' not found in DataFrame")
    if percentage_cap_col is not None and percentage_cap_col not in df.columns:
        raise ValueError(f"Percentage cap column '{percentage_cap_col}' not found in DataFrame")
    
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Ensure numeric values
    result_df[land_value_col] = pd.to_numeric(result_df[land_value_col], errors='coerce').fillna(0)
    result_df[improvement_value_col] = pd.to_numeric(result_df[improvement_value_col], errors='coerce').fillna(0)
    
    # Apply building abatement floor first - directly reduce improvement value
    improvement_after_floor = (result_df[improvement_value_col] - building_abatement_floor).clip(lower=0)
    result_df['improvement_after_floor'] = improvement_after_floor
    
    # Calculate improvement exemption amount (percentage applied to remaining improvement value)
    improvement_exemption = improvement_after_floor * improvement_exemption_percentage
    result_df['improvement_exemption'] = improvement_exemption
    
    # Calculate stacked exemptions (existing + improvement exemption)
    if exemption_col is not None:
        result_df[exemption_col] = pd.to_numeric(result_df[exemption_col], errors='coerce').fillna(0)
        stacked_exemptions = result_df[exemption_col] + improvement_exemption
    else:
        stacked_exemptions = improvement_exemption
    
    result_df['stacked_exemptions'] = stacked_exemptions
    
    # Calculate total property value using improvement value after floor
    total_property_value = result_df[land_value_col] + improvement_after_floor
    result_df['total_property_value'] = total_property_value
    
    # Handle exemption flags (properties completely exempt from tax)
    if exemption_flag_col is not None:
        result_df[exemption_flag_col] = pd.to_numeric(result_df[exemption_flag_col], errors='coerce').fillna(0)
        # For properties with exemption flag, set taxable value to 0
        adj_total_value = total_property_value.where(result_df[exemption_flag_col] == 0, 0)
        adj_stacked_exemptions = stacked_exemptions.where(result_df[exemption_flag_col] == 0, 0)
    else:
        adj_total_value = total_property_value
        adj_stacked_exemptions = stacked_exemptions
    
    # Calculate taxable value (total value minus stacked exemptions, but not less than 0)
    taxable_value = (adj_total_value - adj_stacked_exemptions).clip(lower=0)
    result_df['taxable_value'] = taxable_value
    
    # Calculate total taxable value across all properties
    total_taxable_value = float(taxable_value.sum())
    
    # Prevent division by zero
    if total_taxable_value <= 0:
        raise ValueError("Total taxable value is zero or negative, cannot calculate millage rate")
    
    # If we have a percentage cap, we need to use an iterative approach to find the correct millage rate
    if percentage_cap_col is not None:
        result_df[percentage_cap_col] = pd.to_numeric(result_df[percentage_cap_col], errors='coerce').fillna(1)
        
        # Initial guess for millage rate
        millage_rate = (current_revenue * 1000) / total_taxable_value
        
        # Iterative approach to find the correct millage rate
        max_iterations = 40
        tolerance = 0.00001  # 0.001% tolerance
        iteration = 0
        
        while iteration < max_iterations:
            # Calculate taxes with current millage rate
            uncapped_tax = taxable_value * millage_rate / 1000
            
            # Apply cap based on total property value
            max_tax = total_property_value * result_df[percentage_cap_col]
            capped_tax = np.minimum(uncapped_tax, max_tax)
            
            # Calculate total revenue with caps applied
            new_total_revenue = float(capped_tax.sum())
            
            # Check if we're close enough to the target revenue
            if abs(new_total_revenue - current_revenue) / current_revenue < tolerance:
                break
                
            # Adjust millage rate to get closer to target revenue
            adjustment_factor = current_revenue / new_total_revenue
            millage_rate *= adjustment_factor
            
            iteration += 1
        
        if iteration == max_iterations:
            print(f"Warning: Maximum iterations reached. Revenue target may not be exact. Current: ${new_total_revenue:,.2f}, Target: ${current_revenue:,.2f}")
    else:
        # Calculate millage rate to maintain revenue neutrality (no cap)
        millage_rate = (current_revenue * 1000) / total_taxable_value
    
    # Calculate new tax amounts
    result_df['new_tax'] = taxable_value * millage_rate / 1000
    
    # Apply percentage cap if provided
    if percentage_cap_col is not None:
        # Calculate maximum tax based on percentage cap of total property value
        max_tax = total_property_value * result_df[percentage_cap_col]
        # Create a flag to indicate if the tax was capped
        result_df['tax_capped'] = result_df['new_tax'] > max_tax
        # Apply cap - tax cannot exceed the percentage cap of property value
        result_df['new_tax'] = np.minimum(result_df['new_tax'], max_tax)
    
    # Calculate total revenue with new system
    new_total_revenue = float(result_df['new_tax'].sum())
    
    # Calculate change in tax
    if 'current_tax' in result_df.columns:
        result_df['tax_change'] = result_df['new_tax'] - result_df['current_tax']
        # Avoid division by zero
        result_df['tax_change_pct'] = np.where(
            result_df['current_tax'] > 0,
            (result_df['tax_change'] / result_df['current_tax']) * 100,
            0
        )
    
    # Calculate effective exemption amounts and percentages for analysis
    result_df['effective_exemption_amount'] = stacked_exemptions
    result_df['effective_exemption_pct'] = np.where(
        total_property_value > 0,
        (stacked_exemptions / total_property_value) * 100,
        0
    )
    
    floor_text = f" with ${building_abatement_floor:,.0f} floor" if building_abatement_floor > 0 else ""
    print(f"Stacking improvement exemption model ({improvement_exemption_percentage*100:.1f}% of improvement value{floor_text})")
    print(f"Millage rate: {millage_rate:.4f}")
    print(f"Total tax revenue: ${new_total_revenue:,.2f}")
    print(f"Target revenue: ${current_revenue:,.2f}")
    print(f"Revenue difference: ${new_total_revenue - current_revenue:,.2f} ({(new_total_revenue/current_revenue - 1)*100:.4f}%)")
    
    return millage_rate, new_total_revenue, result_df

def analyze_tax_impact_by_category(df: pd.DataFrame, 
                                  category_cols: Union[str, List[str]], 
                                  current_tax_col: str, 
                                  new_tax_col: str, 
                                  sqft_col: Optional[str] = None, 
                                  sort_by: str = 'count', 
                                  ascending: bool = False) -> pd.DataFrame:
    """
    Analyze tax impact across different categories.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing property data with tax calculations
    category_cols : str or list of str
        Column name(s) for categories to analyze
    current_tax_col : str
        Column name for current tax amount
    new_tax_col : str
        Column name for new tax amount
    sqft_col : str, optional
        Column name for square footage
    sort_by : str, default='count'
        Column to sort results by ('count' or 'pct_change')
    ascending : bool, default=False
        Whether to sort in ascending order
        
    Returns:
    --------
    pandas.DataFrame
        Summary table of tax impacts by category
    """
    # Type checking
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if not isinstance(category_cols, (str, list)):
        raise TypeError("category_cols must be a string or list of strings")
    if isinstance(category_cols, list) and not all(isinstance(col, str) for col in category_cols):
        raise TypeError("All elements in category_cols must be strings")
    if not isinstance(current_tax_col, str):
        raise TypeError("current_tax_col must be a string")
    if not isinstance(new_tax_col, str):
        raise TypeError("new_tax_col must be a string")
    if sqft_col is not None and not isinstance(sqft_col, str):
        raise TypeError("sqft_col must be a string or None")
    if not isinstance(sort_by, str):
        raise TypeError("sort_by must be a string")
    if sort_by not in ['count', 'pct_change']:
        raise ValueError("sort_by must be either 'count' or 'pct_change'")
    if not isinstance(ascending, bool):
        raise TypeError("ascending must be a boolean")
    
    # Check if columns exist in the DataFrame
    if isinstance(category_cols, str):
        cat_cols_list = [category_cols]
    else:
        cat_cols_list = category_cols
    
    for col in cat_cols_list + [current_tax_col, new_tax_col]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
    if sqft_col is not None and sqft_col not in df.columns:
        raise ValueError(f"Square footage column '{sqft_col}' not found in DataFrame")
    
    # Ensure category_cols is a list
    if isinstance(category_cols, str):
        category_cols = [category_cols]
    
    # Ensure numeric tax columns
    result_df = df.copy()
    result_df[current_tax_col] = pd.to_numeric(result_df[current_tax_col], errors='coerce').fillna(0)
    result_df[new_tax_col] = pd.to_numeric(result_df[new_tax_col], errors='coerce').fillna(0)
    
    # Calculate change columns if they don't exist
    if 'tax_change' not in result_df.columns:
        result_df['tax_change'] = result_df[new_tax_col] - result_df[current_tax_col]
    
    if 'tax_change_pct' not in result_df.columns:
        # Avoid division by zero
        result_df['tax_change_pct'] = np.where(
            result_df[current_tax_col] > 0,
            (result_df['tax_change'] / result_df[current_tax_col]) * 100,
            0
        )
    
    # Group by the specified categories
    grouped = result_df.groupby(category_cols)
    
    # Create summary dataframe
    summary = pd.DataFrame({
        'count': grouped.size(),
        'mean_pct_change': grouped['tax_change_pct'].mean(),
        'median_pct_change': grouped['tax_change_pct'].median(),
        'count_increase': grouped['tax_change'].apply(lambda x: (x > 0).sum()),
        'count_decrease': grouped['tax_change'].apply(lambda x: (x < 0).sum()),
        'pct_increase': grouped['tax_change'].apply(lambda x: (x > 0).sum() / len(x) * 100),
        'avg_current_tax': grouped[current_tax_col].mean(),
        'avg_new_tax': grouped[new_tax_col].mean(),
    })
    
    # Add PPSF calculations if square footage is provided
    if sqft_col is not None:
        # Ensure numeric square footage
        result_df[sqft_col] = pd.to_numeric(result_df[sqft_col], errors='coerce')
        
        # Avoid division by zero
        def safe_ppsf(group):
            mask = group[sqft_col] > 0
            if mask.any():
                return (group.loc[mask, current_tax_col] / group.loc[mask, sqft_col]).mean()
            return 0
            
        def safe_new_ppsf(group):
            mask = group[sqft_col] > 0
            if mask.any():
                return (group.loc[mask, new_tax_col] / group.loc[mask, sqft_col]).mean()
            return 0
            
        summary['avg_current_ppsf'] = grouped.apply(safe_ppsf)
        summary['avg_new_ppsf'] = grouped.apply(safe_new_ppsf)
    
    # Reset index to make category columns regular columns
    summary = summary.reset_index()
    
    # Sort the summary table
    if sort_by == 'pct_change':
        summary = summary.sort_values('mean_pct_change', ascending=ascending)
    else:  # Default sort by count
        summary = summary.sort_values('count', ascending=ascending)
    
    return summary 