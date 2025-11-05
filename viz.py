"""
Visualization utilities for LVTShift analysis.

This module provides reusable visualization functions for analyzing and presenting
Land Value Tax policy impacts across different jurisdictions.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from typing import Tuple, Optional, Union, Dict, Any, List


def create_scatter_plot(
    data: pd.DataFrame, 
    x_col: str, 
    y_col: str, 
    ax: plt.Axes, 
    title: str, 
    xlabel: str, 
    ylabel: str,
    size_col: str = 'parcel_count',
    alpha: float = 0.7,
    sizes: Tuple[int, int] = (20, 200),
    exclude_nonpositive_x: bool = True
) -> None:
    """
    Create a scatter plot with trend line, optionally excluding negative/zero x values.
    
    Parameters:
    -----------
    data : pd.DataFrame
        Data to plot
    x_col : str
        Column name for x-axis values
    y_col : str
        Column name for y-axis values
    ax : plt.Axes
        Matplotlib axes object to plot on
    title : str
        Plot title
    xlabel : str
        X-axis label
    ylabel : str
        Y-axis label
    size_col : str, default='parcel_count'
        Column name for point sizes
    alpha : float, default=0.7
        Point transparency
    sizes : tuple, default=(20, 200)
        Min and max point sizes
    exclude_nonpositive_x : bool, default=True
        Whether to exclude rows with non-positive x values (e.g., for income)
    """
    # Optionally exclude rows with non-positive x_col values
    plot_data = data.copy()
    if exclude_nonpositive_x:
        plot_data = plot_data[plot_data[x_col] > 0].copy()
    
    # Create scatter plot
    sns.scatterplot(
        data=plot_data,
        x=x_col,
        y=y_col,
        size=size_col if size_col in plot_data.columns else None,
        sizes=sizes,
        alpha=alpha,
        ax=ax
    )
    
    # Add trend line
    if len(plot_data) > 1:
        z = np.polyfit(plot_data[x_col], plot_data[y_col], 1)
        p = np.poly1d(z)
        ax.plot(plot_data[x_col], p(plot_data[x_col]), "r--", alpha=0.8)
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)


def plot_comparison(
    data1: pd.DataFrame, 
    data2: pd.DataFrame, 
    x_col: str, 
    y_col: str, 
    title_prefix: str, 
    xlabel: str,
    ylabel: str = 'Mean Tax Change (%)',
    figsize: Tuple[int, int] = (18, 8)
) -> None:
    """
    Create side-by-side comparison plots.
    
    Parameters:
    -----------
    data1 : pd.DataFrame
        First dataset (e.g., all properties)
    data2 : pd.DataFrame
        Second dataset (e.g., excluding vacant land)
    x_col : str
        Column name for x-axis
    y_col : str
        Column name for y-axis
    title_prefix : str
        Prefix for plot titles
    xlabel : str
        X-axis label
    ylabel : str, default='Mean Tax Change (%)'
        Y-axis label
    figsize : tuple, default=(18, 8)
        Figure size
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    
    create_scatter_plot(data1, x_col, y_col, ax1, 
                       f'{title_prefix} - All Properties', xlabel, ylabel)
    create_scatter_plot(data2, x_col, y_col, ax2,
                       f'{title_prefix} - Excluding Vacant Land', xlabel, ylabel)
    
    plt.tight_layout()
    plt.show()


def calculate_correlations(
    data1: pd.DataFrame, 
    data2: pd.DataFrame,
    income_col: str = 'median_income',
    minority_col: str = 'minority_pct',
    black_col: str = 'black_pct',
    mean_change_col: str = 'mean_tax_change_pct',
    median_change_col: str = 'median_tax_change_pct'
) -> Dict[str, float]:
    """
    Calculate correlations between demographic variables and tax changes.
    
    Parameters:
    -----------
    data1 : pd.DataFrame
        First dataset (e.g., all properties)
    data2 : pd.DataFrame
        Second dataset (e.g., excluding vacant land)
    income_col : str, default='median_income'
        Income column name
    minority_col : str, default='minority_pct'
        Minority percentage column name
    black_col : str, default='black_pct'
        Black percentage column name
    mean_change_col : str, default='mean_tax_change_pct'
        Mean tax change percentage column
    median_change_col : str, default='median_tax_change_pct'
        Median tax change percentage column
        
    Returns:
    --------
    dict
        Dictionary of correlation coefficients
    """
    correlations = {}
    
    for df, suffix in [(data1, 'all'), (data2, 'non_vacant')]:
        # Exclude rows with non-positive income for correlation
        df_corr = df[df[income_col] > 0].copy() if income_col in df.columns else df.copy()
        
        # Income correlations
        if income_col in df_corr.columns and mean_change_col in df_corr.columns:
            correlations[f'income_mean_{suffix}'] = df_corr[[income_col, mean_change_col]].corr().iloc[0, 1]
        if income_col in df_corr.columns and median_change_col in df_corr.columns:
            correlations[f'income_median_{suffix}'] = df_corr[[income_col, median_change_col]].corr().iloc[0, 1]
        
        # Minority correlations
        if minority_col in df_corr.columns and mean_change_col in df_corr.columns:
            correlations[f'minority_mean_{suffix}'] = df_corr[[minority_col, mean_change_col]].corr().iloc[0, 1]
        
        # Black percentage correlations
        if black_col in df_corr.columns and mean_change_col in df_corr.columns:
            correlations[f'black_mean_{suffix}'] = df_corr[[black_col, mean_change_col]].corr().iloc[0, 1]
    
    return correlations


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """
    Compute the weighted median of values with corresponding weights.
    
    Parameters:
    -----------
    values : np.ndarray
        Values to compute median for
    weights : np.ndarray
        Weights corresponding to values
        
    Returns:
    --------
    float
        Weighted median value
    """
    # Remove NaNs
    mask = (~np.isnan(values)) & (~np.isnan(weights))
    values = np.array(values)[mask]
    weights = np.array(weights)[mask]
    
    if len(values) == 0:
        return np.nan
    
    sorter = np.argsort(values)
    values = values[sorter]
    weights = weights[sorter]
    cumsum = np.cumsum(weights)
    cutoff = weights.sum() / 2.0
    
    return values[np.searchsorted(cumsum, cutoff)]


def create_quintile_summary(
    df: pd.DataFrame, 
    group_col: str, 
    value_col: str,
    tax_change_col: str = 'tax_change',
    tax_change_pct_col: str = 'tax_change_pct',
    weight_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Create summary statistics by quintiles using weighted median tax change percent.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    group_col : str
        Column to create quintiles from
    value_col : str
        Value column for mean calculation
    tax_change_col : str, default='tax_change'
        Tax change column name
    tax_change_pct_col : str, default='tax_change_pct'
        Tax change percentage column name
    weight_col : str, optional
        Weight column (defaults to equal weights)
        
    Returns:
    --------
    pd.DataFrame
        Summary statistics by quintile
    """
    # If grouping by income, exclude non-positive values
    work_df = df.copy()
    if group_col == 'median_income':
        work_df = work_df[work_df['median_income'] > 0].copy()
    
    # Create quintiles
    work_df[f'{group_col}_quintile'] = pd.qcut(
        work_df[group_col], 
        5, 
        labels=["Q1 (Lowest)", "Q2", "Q3", "Q4", "Q5 (Highest)"]
    )
    
    def weighted_median_tax_change_pct(subdf):
        """Calculate weighted median tax change percentage for a group"""
        if weight_col and weight_col in subdf.columns:
            weights = subdf[weight_col]
        else:
            weights = np.ones(len(subdf))
        return weighted_median(subdf[tax_change_pct_col], weights)
    
    # Calculate summary statistics
    summary = work_df.groupby(f'{group_col}_quintile').apply(
        lambda g: pd.Series({
            'count': g[tax_change_col].count(),
            'mean_tax_change_pct': g[tax_change_pct_col].mean(),
            'median_tax_change_pct': weighted_median(g[tax_change_pct_col], np.ones(len(g))),
            'mean_value': g[value_col].mean()
        })
    ).reset_index()
    
    return summary


def plot_quintile_analysis(
    df: pd.DataFrame,
    title: str = "Tax Impact by Quintile",
    figsize: Tuple[int, int] = (10, 6)
) -> None:
    """
    Create a line plot showing tax impact by quintile.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Quintile summary dataframe with quintile column and mean_tax_change_pct
    title : str, default="Tax Impact by Quintile"
        Plot title
    figsize : tuple, default=(10, 6)
        Figure size
    """
    plt.figure(figsize=figsize)
    
    # Extract quintile numbers for x-axis
    quintile_nums = [1, 2, 3, 4, 5]
    
    plt.plot(
        quintile_nums,
        df['mean_tax_change_pct'],
        marker='o',
        linewidth=2,
        markersize=8,
        label='Mean Tax Change'
    )
    
    # Add horizontal line at zero
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.7, label='No Change')
    
    plt.xlabel('Quintile')
    plt.ylabel('Mean Tax Change (%)')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(quintile_nums, [f"Q{i}" for i in quintile_nums])
    
    plt.tight_layout()
    plt.show()


def create_property_category_chart(
    summary_df: pd.DataFrame,
    title: str = "Tax Impact by Property Category",
    figsize: Tuple[int, int] = (12, 8),
    top_n: Optional[int] = None
) -> None:
    """
    Create a horizontal bar chart showing tax impact by property category.
    
    Parameters:
    -----------
    summary_df : pd.DataFrame
        Property category summary with columns like 'mean_tax_change' and 'property_count'
    title : str, default="Tax Impact by Property Category"
        Chart title
    figsize : tuple, default=(12, 8)
        Figure size
    top_n : int, optional
        Show only top N categories by property count
    """
    # Sort by property count and optionally limit to top N
    plot_data = summary_df.sort_values('property_count', ascending=True)
    if top_n:
        plot_data = plot_data.tail(top_n)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create horizontal bar chart
    bars = ax.barh(range(len(plot_data)), plot_data['mean_tax_change'])
    
    # Color bars based on positive/negative values
    for i, bar in enumerate(bars):
        if plot_data.iloc[i]['mean_tax_change'] >= 0:
            bar.set_color('red')
            bar.set_alpha(0.7)
        else:
            bar.set_color('green')
            bar.set_alpha(0.7)
    
    # Customize chart
    ax.set_yticks(range(len(plot_data)))
    ax.set_yticklabels(plot_data.index)
    ax.set_xlabel('Mean Tax Change ($)')
    ax.set_title(title)
    
    # Add vertical line at zero
    ax.axvline(x=0, color='black', linestyle='-', alpha=0.8)
    
    # Add value labels on bars
    for i, (idx, row) in enumerate(plot_data.iterrows()):
        value = row['mean_tax_change']
        count = row['property_count']
        ax.text(value, i, f'  ${value:.0f} (n={count:,})', 
                va='center', ha='left' if value >= 0 else 'right')
    
    plt.tight_layout()
    plt.show()


def create_map_visualization(
    gdf: gpd.GeoDataFrame,
    value_col: str,
    title: str,
    figsize: Tuple[int, int] = (15, 12),
    cmap: str = 'RdYlGn_r',
    legend_label: str = None
) -> None:
    """
    Create a choropleth map visualization.
    
    Parameters:
    -----------
    gdf : gpd.GeoDataFrame
        GeoDataFrame with geometry and values to map
    value_col : str
        Column name for values to visualize
    title : str
        Map title
    figsize : tuple, default=(15, 12)
        Figure size
    cmap : str, default='RdYlGn_r'
        Colormap name
    legend_label : str, optional
        Legend label (defaults to value_col)
    """
    if legend_label is None:
        legend_label = value_col
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create the map
    gdf.plot(
        column=value_col,
        cmap=cmap,
        ax=ax,
        legend=True,
        legend_kwds={'label': legend_label, 'shrink': 0.8}
    )
    
    ax.set_title(title, fontsize=16, pad=20)
    ax.set_axis_off()
    
    plt.tight_layout()
    plt.show()


def calculate_block_group_summary(
    df: pd.DataFrame,
    group_col: str = 'std_geoid',
    tax_change_col: str = 'tax_change',
    current_tax_col: str = 'current_tax',
    new_tax_col: str = 'new_tax',
    required_demo_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Calculate summary statistics by census block group or other geographic unit.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with tax calculations and demographics
    group_col : str, default='std_geoid'
        Column to group by (e.g., census block group)
    tax_change_col : str, default='tax_change'
        Tax change column name
    current_tax_col : str, default='current_tax'
        Current tax column name
    new_tax_col : str, default='new_tax'
        New tax column name
    required_demo_cols : list, optional
        List of demographic columns that must be present
        
    Returns:
    --------
    pd.DataFrame
        Summary statistics by geographic unit
    """
    if required_demo_cols is None:
        required_demo_cols = ['median_income', 'minority_pct', 'black_pct']
    
    # Check if all required columns exist
    missing_cols = [col for col in required_demo_cols if col not in df.columns]
    if missing_cols:
        print(f"Warning: Missing demographic columns: {missing_cols}")
        required_demo_cols = [col for col in required_demo_cols if col in df.columns]
    
    # Calculate tax change percentage
    df_work = df.copy()
    df_work['tax_change_pct'] = np.where(
        df_work[current_tax_col] != 0,
        (df_work[tax_change_col] / df_work[current_tax_col]) * 100,
        0
    )
    
    # Group by geographic unit and calculate summary
    agg_dict = {
        tax_change_col: ['sum', 'count', 'mean'],
        'tax_change_pct': 'mean',
        current_tax_col: 'sum',
        new_tax_col: 'sum'
    }
    
    # Add demographic columns if they exist
    for col in required_demo_cols:
        if col in df_work.columns:
            agg_dict[col] = 'first'  # Assuming demographic data is consistent within groups
    
    summary = df_work.groupby(group_col).agg(agg_dict)
    
    # Flatten column names
    summary.columns = ['_'.join(col).strip() if col[1] else col[0] for col in summary.columns.values]
    summary.columns = [col.replace('_first', '') for col in summary.columns]
    
    # Rename for clarity
    rename_dict = {
        f'{tax_change_col}_sum': 'total_tax_change',
        f'{tax_change_col}_count': 'parcel_count',
        f'{tax_change_col}_mean': 'mean_tax_change',
        'tax_change_pct_mean': 'mean_tax_change_pct',
        f'{current_tax_col}_sum': 'total_current_tax',
        f'{new_tax_col}_sum': 'total_new_tax'
    }
    summary = summary.rename(columns=rename_dict)
    
    # Calculate percentage change in total tax
    summary['total_tax_change_pct'] = (
        (summary['total_new_tax'] - summary['total_current_tax']) / 
        summary['total_current_tax']
    ) * 100
    summary['total_tax_change_pct'] = summary['total_tax_change_pct'].replace([np.inf, -np.inf], 0).fillna(0)
    
    # Reset index
    summary = summary.reset_index()
    
    # Filter out groups with non-positive median income if income column exists
    if 'median_income' in summary.columns:
        summary = summary[summary['median_income'] > 0].copy()
    
    return summary


def filter_data_for_analysis(
    df: pd.DataFrame,
    income_col: str = 'median_income',
    property_category_col: str = 'PROPERTY_CATEGORY'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter data for demographic analysis, creating all properties and non-vacant subsets.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    income_col : str, default='median_income'
        Income column name
    property_category_col : str, default='PROPERTY_CATEGORY'
        Property category column name
        
    Returns:
    --------
    tuple
        (filtered_all, filtered_non_vacant) dataframes
    """
    # Filter for positive income if income column exists
    if income_col in df.columns:
        filtered_all = df[df[income_col] > 0].copy()
    else:
        filtered_all = df.copy()
    
    # Create non-vacant subset
    if property_category_col in df.columns:
        filtered_non_vacant = filtered_all[
            filtered_all[property_category_col] != 'Vacant Land'
        ].copy()
    else:
        # If no property category column, just return the same dataset
        filtered_non_vacant = filtered_all.copy()
    
    return filtered_all, filtered_non_vacant
