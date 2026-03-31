import pandas as pd
import geopandas as gpd
import numpy as np
from typing import Union, List, Tuple, Optional


def _coerce_numeric(series: pd.Series, fill_value: float = 0.0) -> pd.Series:
    """Convert a Series to numeric and replace missing values."""
    return pd.to_numeric(series, errors='coerce').fillna(fill_value)


def _compute_adjusted_tax_components(
    df: pd.DataFrame,
    land_value_col: Optional[str] = None,
    improvement_value_col: Optional[str] = None,
    exemption_col: Optional[str] = None,
    exemption_flag_col: Optional[str] = None,
) -> Tuple[pd.Series, pd.Series]:
    """
    Compute taxable land and improvement values.

    Partial relief is applied to improvements first, then to land.
    Fully exempt parcels are forced to zero after partial-relief allocation.
    """
    if land_value_col is None:
        land = pd.Series(0.0, index=df.index, dtype=float)
    else:
        land = _coerce_numeric(df[land_value_col])

    if improvement_value_col is None:
        improvement = pd.Series(0.0, index=df.index, dtype=float)
    else:
        improvement = _coerce_numeric(df[improvement_value_col])

    adj_land = land.copy()
    adj_improvement = improvement.copy()

    if exemption_col is not None:
        relief = _coerce_numeric(df[exemption_col]).clip(lower=0)
        remaining_relief = (relief - adj_improvement).clip(lower=0)
        adj_improvement = (adj_improvement - relief).clip(lower=0)
        adj_land = (adj_land - remaining_relief).clip(lower=0)

    if exemption_flag_col is not None:
        fully_exempt = _coerce_numeric(df[exemption_flag_col]).fillna(0) != 0
        adj_land = adj_land.where(~fully_exempt, 0.0)
        adj_improvement = adj_improvement.where(~fully_exempt, 0.0)

    return adj_land, adj_improvement


def _apply_tax_credits(
    base_tax: pd.Series,
    df: pd.DataFrame,
    credit_col: Optional[str] = None,
    credit_rate_col: Optional[str] = None,
) -> Tuple[pd.Series, pd.Series]:
    """
    Apply post-tax credits and clip the final tax at zero.

    `credit_rate_col` is interpreted as a parcel-specific share of tax to reduce,
    bounded to [0, 1]. `credit_col` is interpreted as a fixed dollar credit.
    """
    net_tax = _coerce_numeric(base_tax).clip(lower=0)
    total_credit = pd.Series(0.0, index=df.index, dtype=float)

    if credit_rate_col is not None:
        credit_rate = _coerce_numeric(df[credit_rate_col]).clip(lower=0, upper=1)
        total_credit = total_credit + (net_tax * credit_rate)

    if credit_col is not None:
        fixed_credit = _coerce_numeric(df[credit_col]).clip(lower=0)
        total_credit = total_credit + fixed_credit

    net_tax = (net_tax - total_credit).clip(lower=0)
    realized_credit = (base_tax - net_tax).clip(lower=0)
    return net_tax, realized_credit


def _solve_revenue_neutral_split_millage(
    adj_land_value: pd.Series,
    adj_improvement_value: pd.Series,
    result_df: pd.DataFrame,
    current_revenue: float,
    land_improvement_ratio: float,
    land_value_col: str,
    improvement_value_col: str,
    percentage_cap_col: Optional[str] = None,
    credit_col: Optional[str] = None,
    credit_rate_col: Optional[str] = None,
    tolerance: float = 1e-7,
    max_iterations: int = 80,
) -> Tuple[float, float]:
    """Solve for revenue-neutral split millage rates with caps and post-tax credits."""
    total_land_value = float(adj_land_value.sum())
    total_improvement_value = float(adj_improvement_value.sum())
    denominator = total_improvement_value + land_improvement_ratio * total_land_value
    if denominator <= 0:
        raise ValueError("Total taxable value is zero or negative, cannot calculate millage rates")

    target_revenue = float(current_revenue)
    if target_revenue < 0:
        raise ValueError("current_revenue must be non-negative")

    def revenue_for_improvement_millage(improvement_millage: float) -> float:
        land_millage = land_improvement_ratio * improvement_millage
        land_tax = adj_land_value * land_millage / 1000
        improvement_tax = adj_improvement_value * improvement_millage / 1000
        gross_tax = (land_tax + improvement_tax).clip(lower=0)

        if percentage_cap_col is not None:
            max_tax = (
                _coerce_numeric(result_df[land_value_col]) + _coerce_numeric(result_df[improvement_value_col])
            ) * _coerce_numeric(result_df[percentage_cap_col], fill_value=1).clip(lower=0)
            gross_tax = np.minimum(gross_tax, max_tax)

        net_tax, _ = _apply_tax_credits(gross_tax, result_df, credit_col=credit_col, credit_rate_col=credit_rate_col)
        return float(net_tax.sum())

    # Closed form if nothing distorts the tax after rate application.
    if percentage_cap_col is None and credit_col is None and credit_rate_col is None:
        improvement_millage = (target_revenue * 1000) / denominator
        return land_improvement_ratio * improvement_millage, improvement_millage

    low = 0.0
    high = max((target_revenue * 1000) / denominator, 1e-9)
    high_revenue = revenue_for_improvement_millage(high)

    expand_count = 0
    while high_revenue < target_revenue and expand_count < max_iterations:
        high *= 2.0
        high_revenue = revenue_for_improvement_millage(high)
        expand_count += 1

    if high_revenue < target_revenue:
        raise ValueError("Unable to reach target revenue after applying caps and credits")

    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        mid_revenue = revenue_for_improvement_millage(mid)
        if target_revenue == 0 or abs(mid_revenue - target_revenue) / max(target_revenue, 1.0) < tolerance:
            improvement_millage = mid
            return land_improvement_ratio * improvement_millage, improvement_millage
        if mid_revenue < target_revenue:
            low = mid
        else:
            high = mid

    improvement_millage = high
    return land_improvement_ratio * improvement_millage, improvement_millage

def calculate_category_tax_summary(
    df: pd.DataFrame, 
    category_col: str = 'PROPERTY_CATEGORY',
    current_tax_col: str = 'current_tax',
    new_tax_col: str = 'new_tax',
    pct_threshold: float = 10.0
) -> pd.DataFrame:
    """
    Calculate tax change summary by property category, including median and mean tax change percent
    (computed per parcel, then aggregated). Also calculates the percentage of parcels in each category
    with tax increases greater than a given threshold (default 10%) and decreases greater than the negative
    of the threshold.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing property data with tax calculations
    category_col : str
        Column name for property categories
    current_tax_col : str
        Column name for current tax amounts
    new_tax_col : str
        Column name for new tax amounts
    pct_threshold : float, default=10.0
        Percentage threshold for increase/decrease statistics

    Returns:
    --------
    pandas.DataFrame
        Summary table with tax changes by category
    """
    
    if category_col not in df.columns:
        print(f"Warning: Category column '{category_col}' not found. Skipping category summary.")
        return pd.DataFrame()
    
    # Ensure numeric tax columns
    result_df = df.copy()
    result_df[current_tax_col] = pd.to_numeric(result_df[current_tax_col], errors='coerce').fillna(0)
    result_df[new_tax_col] = pd.to_numeric(result_df[new_tax_col], errors='coerce').fillna(0)
    
    # Calculate tax change if not already present
    if 'tax_change' not in result_df.columns:
        result_df['tax_change'] = result_df[new_tax_col] - result_df[current_tax_col]
    
    # Calculate per-parcel tax change percent
    result_df['tax_change_pct'] = np.where(
        result_df[current_tax_col] != 0,
        (result_df['tax_change'] / result_df[current_tax_col]) * 100,
        0
    )

    # Calculate flags for threshold statistics
    result_df['increase_gt_threshold'] = result_df['tax_change_pct'] > pct_threshold
    result_df['decrease_gt_threshold'] = result_df['tax_change_pct'] < -pct_threshold

    # Group by category and calculate summary statistics
    summary = result_df.groupby(category_col).agg({
        'tax_change': ['sum', 'count', 'mean', 'median'],
        'tax_change_pct': ['mean', 'median'],
        current_tax_col: 'sum',
        new_tax_col: 'sum',
        'increase_gt_threshold': 'mean',
        'decrease_gt_threshold': 'mean'
    })
    
    # Flatten column names
    summary.columns = [
        'total_tax_change_dollars', 'property_count', 'mean_tax_change', 'median_tax_change',
        'mean_tax_change_pct', 'median_tax_change_pct',
        'total_current_tax', 'total_new_tax',
        'pct_increase_gt_threshold', 'pct_decrease_gt_threshold'
    ]
    
    # Calculate percentage change in total tax by category (aggregate)
    summary['total_tax_change_pct'] = ((summary['total_new_tax'] - summary['total_current_tax']) / 
                                      summary['total_current_tax']) * 100
    summary['total_tax_change_pct'] = summary['total_tax_change_pct'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Convert proportions to percentages for display
    summary['pct_increase_gt_threshold'] = summary['pct_increase_gt_threshold'] * 100
    summary['pct_decrease_gt_threshold'] = summary['pct_decrease_gt_threshold'] * 100

    # Reset index and sort by property count (descending)
    summary = summary.reset_index()
    summary = summary.sort_values('property_count', ascending=False)
    
    # Attach threshold value for downstream use (for printing)
    summary.attrs['pct_threshold'] = pct_threshold

    return summary

def print_category_tax_summary(
    summary_df: pd.DataFrame, 
    title: str = "Tax Change Summary by Property Category",
    pct_threshold: float = 10.0
) -> None:
    """
    Print a formatted summary of tax changes by category, including the percentage of parcels
    with tax increases greater than a given threshold and decreases greater than the negative
    of the threshold.

    Parameters:
    -----------
    summary_df : pandas.DataFrame
        Summary DataFrame from calculate_category_tax_summary
    title : str
        Title for the summary report
    pct_threshold : float, default=10.0
        Percentage threshold for increase/decrease statistics
    """
    
    if summary_df.empty:
        return

    # Try to get threshold from DataFrame attrs if not explicitly passed
    if hasattr(summary_df, 'attrs') and 'pct_threshold' in summary_df.attrs:
        pct_threshold = summary_df.attrs['pct_threshold']
    
    print(f"\n{title}")
    print("="*80)
    
    # Format the display
    display_df = summary_df.copy()
    
    # Format currency columns
    currency_cols = ['total_tax_change_dollars', 'mean_tax_change', 'median_tax_change', 
                    'total_current_tax', 'total_new_tax']
    
    for col in currency_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")
    
    # Format percentage columns
    if 'total_tax_change_pct' in display_df.columns:
        display_df['total_tax_change_pct'] = display_df['total_tax_change_pct'].apply(lambda x: f"{x:.1f}%")
    if 'mean_tax_change_pct' in display_df.columns:
        display_df['mean_tax_change_pct'] = display_df['mean_tax_change_pct'].apply(lambda x: f"{x:.1f}%")
    if 'median_tax_change_pct' in display_df.columns:
        display_df['median_tax_change_pct'] = display_df['median_tax_change_pct'].apply(lambda x: f"{x:.1f}%")
    if 'pct_increase_gt_threshold' in display_df.columns:
        display_df['pct_increase_gt_threshold'] = display_df['pct_increase_gt_threshold'].apply(lambda x: f"{x:.1f}%")
    if 'pct_decrease_gt_threshold' in display_df.columns:
        display_df['pct_decrease_gt_threshold'] = display_df['pct_decrease_gt_threshold'].apply(lambda x: f"{x:.1f}%")
    
    # Select and rename columns for display
    display_cols = [
        'PROPERTY_CATEGORY', 'property_count', 'total_tax_change_dollars', 
        'total_tax_change_pct', 'mean_tax_change', 'median_tax_change',
        'mean_tax_change_pct', 'median_tax_change_pct',
        'pct_increase_gt_threshold', 'pct_decrease_gt_threshold'
    ]
    
    if all(col in display_df.columns for col in display_cols):
        display_df = display_df[display_cols]
        display_df.columns = [
            'Category', 'Count', 'Total Tax Change ($)', 
            'Total Change (%)', 'Mean Change ($)', 'Median Change ($)',
            'Avg % Change', 'Median % Change',
            f'% Parcels > +{pct_threshold:.0f}%', f'% Parcels < -{pct_threshold:.0f}%'
        ]
        # Sort the display rows by Count (largest to smallest)
        display_df = display_df.sort_values('Count', ascending=False)
    
    print(display_df.to_string(index=False))
    
    # Print summary statistics
    numeric_summary = summary_df.select_dtypes(include=[np.number])
    print(f"\nOVERALL SUMMARY:")
    print(f"Total Properties: {summary_df['property_count'].sum():,}")
    print(f"Total Tax Change: ${summary_df['total_tax_change_dollars'].sum():,.0f}")
    print(f"Net Revenue Change: ${summary_df['total_new_tax'].sum() - summary_df['total_current_tax'].sum():,.0f}")
    # Print overall mean and median percent change
    if 'mean_tax_change_pct' in summary_df.columns and 'median_tax_change_pct' in summary_df.columns:
        overall_mean_pct = summary_df['mean_tax_change_pct'].mean()
        overall_median_pct = summary_df['median_tax_change_pct'].median()
        print(f"Average Percent Change (mean of means): {overall_mean_pct:.2f}%")
        print(f"Median Percent Change (median of medians): {overall_median_pct:.2f}%")
    # Print overall percent of parcels above and below threshold
    if 'pct_increase_gt_threshold' in summary_df.columns and 'pct_decrease_gt_threshold' in summary_df.columns:
        total_count = summary_df['property_count'].sum()
        gt_count = (summary_df['property_count'] * summary_df['pct_increase_gt_threshold'].astype(float) / 100).sum()
        lt_count = (summary_df['property_count'] * summary_df['pct_decrease_gt_threshold'].astype(float) / 100).sum()
        print(f"Percent of ALL parcels with tax increase > +{pct_threshold:.0f}%: {100 * gt_count / total_count:.2f}%")
        print(f"Percent of ALL parcels with tax decrease < -{pct_threshold:.0f}%: {100 * lt_count / total_count:.2f}%")

def calculate_current_tax(
    df: pd.DataFrame,
    tax_value_col: str,
    millage_rate_col: str,
    exemption_col: Optional[str] = None,
    exemption_flag_col: Optional[str] = None,
    percentage_cap_col: Optional[str] = None,
    second_millage_rate_col: Optional[str] = None,
    land_value_col: Optional[str] = None,
    improvement_value_col: Optional[str] = None,
    credit_col: Optional[str] = None,
    credit_rate_col: Optional[str] = None,
) -> Tuple[float, float, pd.DataFrame]:
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
    if land_value_col is not None and not isinstance(land_value_col, str):
        raise TypeError("land_value_col must be a string or None")
    if improvement_value_col is not None and not isinstance(improvement_value_col, str):
        raise TypeError("improvement_value_col must be a string or None")
    if credit_col is not None and not isinstance(credit_col, str):
        raise TypeError("credit_col must be a string or None")
    if credit_rate_col is not None and not isinstance(credit_rate_col, str):
        raise TypeError("credit_rate_col must be a string or None")
    
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
    if land_value_col is not None and land_value_col not in df.columns:
        raise ValueError(f"Land value column '{land_value_col}' not found in DataFrame")
    if improvement_value_col is not None and improvement_value_col not in df.columns:
        raise ValueError(f"Improvement value column '{improvement_value_col}' not found in DataFrame")
    if credit_col is not None and credit_col not in df.columns:
        raise ValueError(f"Credit column '{credit_col}' not found in DataFrame")
    if credit_rate_col is not None and credit_rate_col not in df.columns:
        raise ValueError(f"Credit rate column '{credit_rate_col}' not found in DataFrame")
    
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Ensure numeric values
    result_df[tax_value_col] = _coerce_numeric(result_df[tax_value_col])
    result_df[millage_rate_col] = _coerce_numeric(result_df[millage_rate_col])
    
    if second_millage_rate_col is not None:
        result_df[second_millage_rate_col] = _coerce_numeric(result_df[second_millage_rate_col])
        # Verify second millage rate is less than primary
        if (result_df[second_millage_rate_col] > result_df[millage_rate_col]).any():
            raise ValueError("Second millage rate must be less than the primary millage rate")

    if land_value_col is not None or improvement_value_col is not None:
        adj_land_value, adj_improvement_value = _compute_adjusted_tax_components(
            result_df,
            land_value_col=land_value_col,
            improvement_value_col=improvement_value_col,
            exemption_col=exemption_col,
            exemption_flag_col=exemption_flag_col,
        )
        taxable_value = (adj_land_value + adj_improvement_value).clip(lower=0)
        result_df['current_taxable_land'] = adj_land_value
        result_df['current_taxable_improvement'] = adj_improvement_value
        cap_base_value = _coerce_numeric(result_df[land_value_col] if land_value_col is not None else 0) + _coerce_numeric(
            result_df[improvement_value_col] if improvement_value_col is not None else 0
        )
    else:
        if exemption_flag_col is not None:
            result_df[exemption_flag_col] = _coerce_numeric(result_df[exemption_flag_col])
            taxable_value = result_df[tax_value_col].where(result_df[exemption_flag_col] == 0, 0)
        else:
            taxable_value = result_df[tax_value_col]

        if exemption_col is not None:
            result_df[exemption_col] = _coerce_numeric(result_df[exemption_col]).clip(lower=0)
            taxable_value = (taxable_value - result_df[exemption_col]).clip(lower=0)

        cap_base_value = result_df[tax_value_col]

    result_df['current_taxable_value'] = taxable_value.clip(lower=0)
    result_df['current_tax_before_credits'] = result_df['current_taxable_value'] * result_df[millage_rate_col] / 1000
    
    # Apply percentage cap if provided
    if percentage_cap_col is not None:
        result_df[percentage_cap_col] = _coerce_numeric(result_df[percentage_cap_col], fill_value=1).clip(lower=0)
        # Calculate maximum tax based on percentage cap
        max_tax = cap_base_value * result_df[percentage_cap_col]
        # Create a flag to indicate if the tax was capped
        result_df['tax_capped'] = result_df['current_tax_before_credits'] > max_tax
        # Apply cap - tax cannot exceed the percentage cap of property value
        result_df['current_tax_before_credits'] = np.minimum(result_df['current_tax_before_credits'], max_tax)

    result_df['current_tax_before_credits'] = _coerce_numeric(result_df['current_tax_before_credits']).clip(lower=0)
    result_df['current_tax'], result_df['current_credit_amount'] = _apply_tax_credits(
        result_df['current_tax_before_credits'],
        result_df,
        credit_col=credit_col,
        credit_rate_col=credit_rate_col,
    )
    
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
                         percentage_cap_col: Optional[str] = None,
                         credit_col: Optional[str] = None,
                         credit_rate_col: Optional[str] = None) -> Tuple[float, float, float, pd.DataFrame]:
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
    if credit_col is not None and not isinstance(credit_col, str):
        raise TypeError("credit_col must be a string or None")
    if credit_rate_col is not None and not isinstance(credit_rate_col, str):
        raise TypeError("credit_rate_col must be a string or None")
    
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
    if credit_col is not None and credit_col not in df.columns:
        raise ValueError(f"Credit column '{credit_col}' not found in DataFrame")
    if credit_rate_col is not None and credit_rate_col not in df.columns:
        raise ValueError(f"Credit rate column '{credit_rate_col}' not found in DataFrame")
    
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Ensure numeric values
    result_df[land_value_col] = _coerce_numeric(result_df[land_value_col])
    result_df[improvement_value_col] = _coerce_numeric(result_df[improvement_value_col])
    adj_land_value, adj_improvement_value = _compute_adjusted_tax_components(
        result_df,
        land_value_col=land_value_col,
        improvement_value_col=improvement_value_col,
        exemption_col=exemption_col,
        exemption_flag_col=exemption_flag_col,
    )
    result_df['taxable_land_value'] = adj_land_value
    result_df['taxable_improvement_value'] = adj_improvement_value

    land_millage, improvement_millage = _solve_revenue_neutral_split_millage(
        adj_land_value=adj_land_value,
        adj_improvement_value=adj_improvement_value,
        result_df=result_df,
        current_revenue=float(current_revenue),
        land_improvement_ratio=float(land_improvement_ratio),
        land_value_col=land_value_col,
        improvement_value_col=improvement_value_col,
        percentage_cap_col=percentage_cap_col,
        credit_col=credit_col,
        credit_rate_col=credit_rate_col,
    )
    
    # Calculate new tax amounts
    result_df['land_tax_before_credits'] = (adj_land_value * land_millage / 1000).clip(lower=0)
    result_df['improvement_tax_before_credits'] = (adj_improvement_value * improvement_millage / 1000).clip(lower=0)
    result_df['new_tax_before_credits'] = (
        result_df['land_tax_before_credits'] + result_df['improvement_tax_before_credits']
    ).clip(lower=0)
    
    # Apply percentage cap if provided
    if percentage_cap_col is not None:
        # Calculate maximum tax based on percentage cap
        total_value = _coerce_numeric(result_df[land_value_col]) + _coerce_numeric(result_df[improvement_value_col])
        max_tax = total_value * result_df[percentage_cap_col]
        # Create a flag to indicate if the tax was capped
        result_df['tax_capped'] = result_df['new_tax_before_credits'] > max_tax
        # Apply cap - tax cannot exceed the percentage cap of property value
        result_df['new_tax_before_credits'] = np.minimum(result_df['new_tax_before_credits'], max_tax)
        
        # Recalculate land_tax and improvement_tax to maintain the same ratio
        # but respect the cap
        cap_applied = result_df['tax_capped']
        total_uncapped = result_df['land_tax_before_credits'] + result_df['improvement_tax_before_credits']
        
        # For properties where cap is applied, redistribute the capped tax amount
        # proportionally between land and improvements
        result_df.loc[cap_applied, 'land_tax_before_credits'] = (
            result_df.loc[cap_applied, 'land_tax_before_credits'] / 
            total_uncapped[cap_applied] * 
            result_df.loc[cap_applied, 'new_tax_before_credits']
        )
        
        result_df.loc[cap_applied, 'improvement_tax_before_credits'] = (
            result_df.loc[cap_applied, 'improvement_tax_before_credits'] / 
            total_uncapped[cap_applied] * 
            result_df.loc[cap_applied, 'new_tax_before_credits']
        )
    
    result_df['new_tax'], result_df['new_credit_amount'] = _apply_tax_credits(
        result_df['new_tax_before_credits'],
        result_df,
        credit_col=credit_col,
        credit_rate_col=credit_rate_col,
    )
    result_df['land_tax'] = result_df['land_tax_before_credits']
    result_df['improvement_tax'] = result_df['improvement_tax_before_credits']
    
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
    
    # Print category summary if category column exists
    category_summary = calculate_category_tax_summary(result_df)
    #print_category_tax_summary(category_summary, "Split-Rate Tax Change by Property Category")
    
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
    
    # Print category summary if category column exists
    category_summary = calculate_category_tax_summary(result_df)
    #print_category_tax_summary(category_summary, f"Building Abatement ({abatement_percentage*100:.1f}%) Tax Change by Property Category")
    
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
    
    # --- Calculate all exemption logic first ---
    # Apply building abatement floor first - directly reduce improvement value
    floor_exemption_amount = result_df[improvement_value_col].clip(upper=building_abatement_floor)
    improvement_after_floor = (result_df[improvement_value_col] - floor_exemption_amount)
    result_df['improvement_after_floor'] = improvement_after_floor

    # Calculate improvement exemption amount (percentage applied to remaining improvement value)
    improvement_exemption = improvement_after_floor * improvement_exemption_percentage
    result_df['improvement_exemption'] = improvement_exemption  + floor_exemption_amount

    # Calculate stacked exemptions (existing + improvement exemption)
    if exemption_col is not None:
        result_df[exemption_col] = pd.to_numeric(result_df[exemption_col], errors='coerce').fillna(0)
        stacked_exemptions = result_df[exemption_col] + result_df['improvement_exemption']
    else:
        stacked_exemptions = result_df['improvement_exemption']

    result_df['stacked_exemptions'] = stacked_exemptions

    # Calculate total property value using improvement value after floor
    total_property_value = result_df[land_value_col] + result_df[improvement_value_col]
    result_df['total_property_value'] = total_property_value


    # Calculate taxable value (total value minus stacked exemptions, but not less than 0)
    taxable_value = (total_property_value - stacked_exemptions).clip(lower=0)
    result_df['taxable_value'] = taxable_value
    print("Sum of taxable value:", taxable_value.sum())
    print("Sum of total_property_value:", total_property_value.sum())
    print("Sum of exemptions:", stacked_exemptions.sum())
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
    
    # Print category summary if category column exists
    category_summary = calculate_category_tax_summary(result_df)
    print_category_tax_summary(category_summary, f"Stacking Improvement Exemption ({improvement_exemption_percentage*100:.1f}%{floor_text}) Tax Change by Property Category")
    
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


def categorize_property_type(prop_use_desc: str) -> str:
    """
    Categorize property type based on property use description.
    This function provides a standardized categorization that can be adapted
    for different jurisdictions by modifying the category mappings.
    
    Parameters:
    -----------
    prop_use_desc : str
        Property use description from assessor data
        
    Returns:
    --------
    str
        Standardized property category
    """
    if pd.isna(prop_use_desc):
        return "Other"
    
    prop_use_desc = str(prop_use_desc).strip()
    
    # Direct mapping based on common property use descriptions
    # This can be customized for different jurisdictions
    category_mapping = {
        "Single Family": ["Single Unit", "Single Family", "Single-Family", "Residential - Single Family"],
        "Small Multi-Family (2-4 units)": ["Two-to-Four Unit", "Duplex", "Triplex", "Fourplex", "2-4 Units"],
        "Large Multi-Family (5+ units)": ["Five-Plus Unit", "Multi-Family", "Apartment", "5+ Units"],
        "Other Residential": ["Other Residential", "Vacation Home", "Manufactured Home"],
        "Mobile Home Park": ["Mobile Home Park", "Manufactured Housing Park"],
        "Vacant Land": ["Vacant Land", "Vacant", "Unimproved Land"],
        "Agricultural": ["Cur - Use - Ag", "Agricultural Not Classified", "Agricultural", "Farm", "Forestry"],
        "Retail/Service/Commercial": [
            "Retail", "Restaurant", "Gas Station", "Auto Sales", "Bank", "Office",
            "Medical", "Wholesale", "Warehouse", "Storage", "Commercial", "Service"
        ],
        "Industrial": ["Industrial", "Manufacturing", "Factory"],
        "Institutional": ["Government", "School", "Church", "Hospital", "Institutional"],
        "Utilities": ["Utility", "Utilities", "Pipeline", "Transmission"],
        "Parking": ["Parking", "Parking Lot", "Parking Garage"]
    }
    
    # Check each category for matches
    for category, keywords in category_mapping.items():
        for keyword in keywords:
            if keyword.lower() in prop_use_desc.lower():
                return category
    
    # If no match found, return "Other"
    return "Other"


def ensure_geodataframe(df: Union[pd.DataFrame, gpd.GeoDataFrame], geometry_col: str = 'geometry') -> gpd.GeoDataFrame:
    """
    Ensures that a DataFrame with geometry column is converted to a GeoDataFrame.
    If conversion fails, tries to robustly decode geometry values before failing.
    
    Parameters:
    -----------
    df : pd.DataFrame or gpd.GeoDataFrame
        DataFrame with geometry data
    geometry_col : str, default='geometry'
        Name of the geometry column
        
    Returns:
    --------
    gpd.GeoDataFrame
        GeoDataFrame with proper CRS set
    """
    import shapely
    import binascii
    from shapely import wkt
    
    def try_decode_geometry(val):
        """Try multiple methods to decode geometry values"""
        if pd.isna(val) or val is None:
            return None
        
        # If already a geometry object, return as-is
        if isinstance(val, (shapely.geometry.base.BaseGeometry)):
            return val
        
        # Try as WKT string
        if isinstance(val, str):
            try:
                return wkt.loads(val)
            except Exception:
                pass
        
        # Try as WKB hex string
        if isinstance(val, str):
            try:
                return shapely.wkb.loads(binascii.unhexlify(val))
            except Exception:
                pass
        
        # Try as WKB bytes
        if isinstance(val, bytes):
            try:
                return shapely.wkb.loads(val)
            except Exception:
                pass
        
        return None
    
    # If already a GeoDataFrame, ensure CRS is set
    if isinstance(df, gpd.GeoDataFrame):
        if df.crs is None:
            df = df.set_crs('EPSG:4326')  # Default to WGS84
        return df
    
    # Check if geometry column exists
    if geometry_col not in df.columns:
        print(f"Warning: Geometry column '{geometry_col}' not found in DataFrame")
        return df
    
    # Try direct conversion first
    try:
        gdf = gpd.GeoDataFrame(df, geometry=geometry_col)
        if gdf.crs is None:
            gdf = gdf.set_crs('EPSG:4326')
        return gdf
    except Exception as e:
        print(f"Direct conversion failed: {e}")
    
    # Try robust geometry decoding
    try:
        df_copy = df.copy()
        df_copy[geometry_col] = df_copy[geometry_col].apply(try_decode_geometry)
        
        # Remove rows where geometry decoding failed
        df_copy = df_copy.dropna(subset=[geometry_col])
        
        gdf = gpd.GeoDataFrame(df_copy, geometry=geometry_col)
        if gdf.crs is None:
            gdf = gdf.set_crs('EPSG:4326')
        return gdf
    except Exception as e:
        print(f"Robust geometry conversion failed: {e}")
    
    # Return as-is if no geometry column found
    return df


def extract_date_from_filename(path: str) -> Optional[pd.Timestamp]:
    """
    Extracts a datetime object from a filename with date pattern.
    Supports patterns like: filename_YYYY_MM_DD.extension
    
    Parameters:
    -----------
    path : str
        File path to extract date from
        
    Returns:
    --------
    pd.Timestamp or None
        Extracted date or None if parsing fails
    """
    import os
    from datetime import datetime
    
    base = os.path.basename(path)
    # Remove extension
    base_no_ext = os.path.splitext(base)[0]
    
    # Split by underscore and look for date pattern
    parts = base_no_ext.split("_")
    
    # Look for YYYY_MM_DD pattern at the end
    if len(parts) >= 3:
        try:
            # Try the last three parts as YYYY, MM, DD
            date_str = "_".join(parts[-3:])
            return pd.to_datetime(datetime.strptime(date_str, "%Y_%m_%d"))
        except Exception:
            pass
    
    # Try other common date patterns
    common_patterns = [
        "%Y-%m-%d",
        "%Y%m%d", 
        "%m-%d-%Y",
        "%m_%d_%Y"
    ]
    
    for pattern in common_patterns:
        for i in range(len(parts) - 2):
            try:
                date_str = "_".join(parts[i:i+3])
                return pd.to_datetime(datetime.strptime(date_str, pattern))
            except Exception:
                continue
    
    return None 
