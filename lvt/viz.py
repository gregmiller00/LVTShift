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
    ax.grid(False)
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


def create_spokane_property_category_chart(
    summary_df: pd.DataFrame,
    title: str = "Property Category Impact",
    category_col: str = "PROPERTY_CATEGORY",
    median_pct_col: str = "median_tax_change_pct",
    median_dollar_col: str = "median_tax_change",
    property_count_col: str = "property_count",
    total_change_col: str = "total_tax_change_dollars",
    min_count: int = 10,
    right_col_pad: float = 120.0,
    figsize_width: float = 17.0,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create the Spokane-style property category impact chart.

    This combines median percent change, median dollar change, parcel counts,
    and aggregate net change into a single horizontal-bar exhibit.
    """
    required = {category_col, median_pct_col, median_dollar_col, property_count_col}
    missing = required - set(summary_df.columns)
    if missing:
        raise ValueError(f"Missing required columns for property category chart: {sorted(missing)}")

    plot_df = summary_df[summary_df[property_count_col] >= min_count].copy()
    if plot_df.empty:
        raise ValueError("No categories meet the minimum count threshold for plotting.")

    if total_change_col not in plot_df.columns:
        plot_df[total_change_col] = plot_df[median_dollar_col] * plot_df[property_count_col]

    plot_df = plot_df.sort_values(median_pct_col).reset_index(drop=True)

    categories = plot_df[category_col].tolist()
    counts = plot_df[property_count_col].tolist()
    median_pct_change = plot_df[median_pct_col].tolist()
    median_dollar_change = plot_df[median_dollar_col].tolist()
    total_tax_change = plot_df[total_change_col].tolist()

    bar_colors = ["#8B0000" if val > 0 else "#228B22" for val in median_pct_change]
    y = np.arange(len(categories))
    fig_height = len(categories) * 0.8 + 1.2
    fig, ax = plt.subplots(figsize=(figsize_width, fig_height))

    ax.barh(
        y,
        median_pct_change,
        color=bar_colors,
        edgecolor="none",
        height=0.75,
        alpha=0.92,
        linewidth=0,
        zorder=2,
    )

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    ax.axvline(0, color="black", linewidth=1, linestyle="dotted", zorder=1)
    ax.grid(False)

    cat_offset = 0.18
    med_offset = -0.03
    count_offset = -0.23
    max_abs = max(abs(min(median_pct_change)), abs(max(median_pct_change)))
    right_col_x = max_abs + right_col_pad

    ax.text(
        right_col_x,
        len(categories) - 0.25,
        "Net Change",
        ha="center",
        va="bottom",
        fontsize=15,
        fontweight="bold",
    )

    for i, (cat, med_pct, med_dollar, count, total_change) in enumerate(
        zip(categories, median_pct_change, median_dollar_change, counts, total_tax_change)
    ):
        bar_end = med_pct
        text_x = bar_end + 1.2 if med_pct >= 0 else bar_end - 1.2
        text_ha = "left" if med_pct >= 0 else "right"
        pct_label = f"{med_pct:+.1f}%"
        dollar_label = f"${med_dollar:,.0f}"
        total_label = f"${total_change:,.0f}"

        ax.text(
            text_x,
            i + cat_offset,
            cat,
            ha=text_ha,
            va="center",
            fontsize=14,
            fontweight="bold",
        )
        ax.text(
            text_x,
            i + med_offset,
            f"Median: {dollar_label}, {pct_label}",
            ha=text_ha,
            va="center",
            fontsize=12,
            fontweight="bold",
        )
        ax.text(
            text_x,
            i + count_offset,
            f"{count:,} parcels",
            ha=text_ha,
            va="center",
            fontsize=11,
            color="#888888",
        )
        ax.text(
            right_col_x,
            i,
            total_label,
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
        )

    ax.set_title(title, fontsize=18, fontweight="bold", pad=18)
    ax.set_xlim(-right_col_x, right_col_x + 60)
    ax.set_ylim(-0.8, len(categories) - 0.05)
    plt.tight_layout()
    plt.show()
    return fig, ax


def create_threshold_change_chart(
    summary_df: pd.DataFrame,
    title: str = "Share of Parcels with Tax Changes Above Threshold",
    category_col: str = "PROPERTY_CATEGORY",
    increase_col: str = "pct_increase_gt_threshold",
    decrease_col: str = "pct_decrease_gt_threshold",
    property_count_col: str = "property_count",
    threshold: float = 10.0,
    min_count: int = 10,
    figsize: Tuple[int, int] = (11, 7),
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create the Spokane-style split chart showing shares of parcels with
    increases or decreases above a threshold.
    """
    required = {category_col, increase_col, decrease_col, property_count_col}
    missing = required - set(summary_df.columns)
    if missing:
        raise ValueError(f"Missing required columns for threshold chart: {sorted(missing)}")

    plot_df = summary_df[summary_df[property_count_col] >= min_count].copy()
    if plot_df.empty:
        raise ValueError("No categories meet the minimum count threshold for plotting.")

    plot_df = plot_df.sort_values(increase_col, ascending=True).reset_index(drop=True)
    y = np.arange(len(plot_df))

    increase_vals = plot_df[increase_col].astype(float).tolist()
    decrease_vals = plot_df[decrease_col].astype(float).tolist()
    categories = plot_df[category_col].tolist()

    fig, ax = plt.subplots(figsize=figsize)

    ax.barh(
        y,
        [-v for v in decrease_vals],
        color="#228B22",
        edgecolor="none",
        height=0.7,
    )
    ax.barh(
        y,
        increase_vals,
        color="#8B0000",
        edgecolor="none",
        height=0.7,
    )
    ax.axvline(0, color="black", linewidth=1, linestyle="dotted")
    ax.grid(False)

    max_extent = max(max(increase_vals, default=0), max(decrease_vals, default=0))
    label_pad = max(4.0, max_extent * 0.08)
    category_pad = max(16.0, max_extent * 0.2)

    for i, (inc, dec) in enumerate(zip(increase_vals, decrease_vals)):
        if dec > 0:
            ax.text(
                -dec - label_pad,
                y[i],
                f"{int(round(dec))}%",
                va="center",
                ha="right",
                fontsize=9,
                color="#228B22",
                fontweight="bold",
            )
        if inc > 0:
            ax.text(
                inc + label_pad,
                y[i],
                f"{int(round(inc))}%",
                va="center",
                ha="left",
                fontsize=9,
                color="#8B0000",
                fontweight="bold",
            )

        xpos = inc + category_pad if inc > 0 else category_pad
        ax.text(
            xpos,
            y[i],
            categories[i],
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
        )

    ax.text(
        -max_extent * 0.55,
        len(categories) - 0.15,
        f"Decrease > {threshold:.0f}%",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
        color="#228B22",
    )
    ax.text(
        max_extent * 0.55,
        len(categories) - 0.15,
        f"Increase > {threshold:.0f}%",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
        color="#8B0000",
    )

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlim(-(max_extent + category_pad + 12), max_extent + category_pad + 35)
    ax.set_ylim(-0.8, len(categories) - 0.1)
    plt.tight_layout()
    plt.show()
    return fig, ax


def plot_upside_down_quintile_bars(
    summary_df: pd.DataFrame,
    title: str,
    quintile_col: Optional[str] = None,
    value_col: str = "median_tax_change_pct",
    figsize: Tuple[int, int] = (10, 6),
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create the Spokane/Cleveland-style census progressivity chart.

    Negative values extend downward from zero; positive values extend upward.
    """
    if quintile_col is None:
        quintile_candidates = [c for c in summary_df.columns if c.endswith("_quintile")]
        if not quintile_candidates:
            raise ValueError("Could not infer quintile column; please provide quintile_col.")
        quintile_col = quintile_candidates[0]

    if quintile_col not in summary_df.columns or value_col not in summary_df.columns:
        raise ValueError(f"Missing required columns: {quintile_col}, {value_col}")

    plot_df = summary_df.copy()
    labels = plot_df[quintile_col].astype(str).tolist()
    vals = plot_df[value_col].astype(float).tolist()
    x = np.arange(len(labels))

    neg_vals = [abs(v) for v in vals if v < 0]
    pos_vals = [v for v in vals if v > 0]
    neg_palette = sns.color_palette("Greens", n_colors=max(len(neg_vals), 1))
    pos_palette = sns.color_palette("Reds", n_colors=max(len(pos_vals), 1))
    neg_rank = np.argsort(np.argsort([-abs(v) for v in vals if v < 0])) if neg_vals else []
    pos_rank = np.argsort(np.argsort(pos_vals)) if pos_vals else []

    colors = []
    neg_i = 0
    pos_i = 0
    for val in vals:
        if val < 0:
            colors.append(neg_palette[neg_rank[neg_i]])
            neg_i += 1
        elif val > 0:
            colors.append(pos_palette[pos_rank[pos_i]])
            pos_i += 1
        else:
            colors.append("#bdbdbd")

    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(
        x,
        vals,
        color=colors,
        edgecolor="black",
        width=0.7,
    )

    ax.axhline(0, color="black", linewidth=1, linestyle="dotted")
    ax.grid(False)
    ax.yaxis.set_visible(False)
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.set_title(title, weight="bold", pad=30)
    sns.despine(left=True, right=True, top=True, bottom=True)

    for bar, val in zip(bars, vals):
        if abs(val) < 0.01:
            ypos = 0.5
            va = "bottom"
        elif val < 0:
            ypos = val / 2
            va = "center"
        else:
            ypos = val / 2
            va = "center"
        ax.annotate(
            f"{val:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, ypos),
            xytext=(0, 0),
            textcoords="offset points",
            ha="center",
            va=va,
            fontsize=13,
            color="black",
            fontweight="bold",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontweight="bold")
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")

    ymin = min(vals + [0])
    ymax = max(vals + [0])
    ypad = max(abs(ymin), abs(ymax)) * 0.15 if max(abs(ymin), abs(ymax)) > 0 else 1.0
    ax.set_ylim(ymin - ypad, ymax + ypad)

    plt.tight_layout()
    plt.show()
    return fig, ax


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


# ---------------------------------------------------------------------------
# Standard city report helpers
# ---------------------------------------------------------------------------

# Green gradient for quintile charts (Q1 lightest → Q5 darkest)
_QUINTILE_GREENS: List[str] = ['#c8e6c9', '#81c784', '#4caf50', '#2e7d32', '#1b5e20']

# Default "residential" categories used for census quintile charts
_RESIDENTIAL_CATEGORIES: List[str] = [
    'Single Family Residential',
    'Small Multi-Family (2-4 units)',
    'Large Multi-Family (5+ units)',
    'Other Residential',
]


def _make_category_chart(
    cat_summary: pd.DataFrame,
    cat_col: str,
    city_title: str,
    right_col_pad: float = 120.0,
    min_count: int = 50,
) -> plt.Figure:
    """Build the property-category impact figure and return it (does not show/save)."""
    plot_df = cat_summary[cat_summary['property_count'] >= min_count].copy()
    plot_df = plot_df.sort_values('median_tax_change_pct').reset_index(drop=True)
    if 'total_tax_change_dollars' not in plot_df.columns:
        plot_df['total_tax_change_dollars'] = (
            plot_df['median_tax_change'] * plot_df['property_count']
        )

    n = len(plot_df)
    if n == 0:
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.text(0.5, 0.5, 'No category data', ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')
        return fig

    fig, ax = plt.subplots(figsize=(17, max(4.0, n * 0.8 + 1.2)))

    cats = plot_df[cat_col].tolist()
    pcts = plot_df['median_tax_change_pct'].tolist()
    dollars = plot_df['median_tax_change'].tolist()
    counts = plot_df['property_count'].tolist()
    totals = plot_df['total_tax_change_dollars'].tolist()

    colors = ['#8B0000' if v > 0 else '#228B22' for v in pcts]
    y = np.arange(n)
    ax.barh(y, pcts, color=colors, edgecolor='none', height=0.75, alpha=0.92, zorder=2)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    ax.grid(False)
    ax.axvline(0, color='black', linewidth=1, linestyle='dotted', zorder=1)

    max_abs = max(abs(min(pcts)), abs(max(pcts))) if pcts else 1.0
    right_x = max_abs + right_col_pad

    ax.text(right_x, n - 0.25, 'Net Change', ha='center', va='bottom',
            fontsize=15, fontweight='bold')

    for i, (cat, pct, dol, cnt, tot) in enumerate(
        zip(cats, pcts, dollars, counts, totals)
    ):
        tx = pct + 1.2 if pct >= 0 else pct - 1.2
        ha = 'left' if pct >= 0 else 'right'
        dol_s = f'${dol:,.0f}' if dol >= 0 else f'-${abs(dol):,.0f}'
        tot_s = f'${tot:,.0f}' if tot >= 0 else f'-${abs(tot):,.0f}'
        ax.text(tx, i + 0.18, cat, ha=ha, va='center', fontsize=14, fontweight='bold')
        ax.text(tx, i - 0.03, f'Median: {dol_s}, {pct:+.1f}%', ha=ha, va='center',
                fontsize=12, fontweight='bold')
        ax.text(tx, i - 0.23, f'{cnt:,} parcels', ha=ha, va='center',
                fontsize=11, color='#888888')
        ax.text(right_x, i, tot_s, ha='center', va='center', fontsize=12, fontweight='bold')

    ax.set_title(f'Property Category Tax Impact — {city_title}',
                 fontsize=18, fontweight='bold', pad=18)
    ax.set_xlim(-right_x, right_x + 60)
    ax.set_ylim(-0.8, n - 0.05)
    fig.tight_layout()
    return fig


def _make_ten_pct_chart(
    df: pd.DataFrame,
    cat_col: str,
    city_title: str,
    min_count: int = 50,
) -> plt.Figure:
    """Diverging bar chart: % of parcels with >10% decrease (left) vs >10% increase (right).

    Categories are sorted by share increasing >10%, most at top.
    Returns a Figure (does not show/save).
    """
    tmp = df[[cat_col, 'tax_change_pct']].dropna(subset=[cat_col, 'tax_change_pct']).copy()
    tmp['_bucket'] = pd.cut(
        tmp['tax_change_pct'],
        bins=[-np.inf, -10, 10, np.inf],
        labels=['decrease_10', 'stable', 'increase_10'],
    )
    counts = tmp.groupby([cat_col, '_bucket'], observed=True).size().unstack(fill_value=0)
    for col in ['decrease_10', 'stable', 'increase_10']:
        if col not in counts.columns:
            counts[col] = 0
    counts['total'] = counts.sum(axis=1)
    counts = counts[counts['total'] >= min_count].copy()

    if counts.empty:
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.text(0.5, 0.5, 'No category data', ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')
        return fig

    pcts = counts[['decrease_10', 'increase_10']].div(counts['total'], axis=0) * 100
    # Sort by share increasing >10% descending → most increase at top
    pcts = pcts.sort_values('increase_10', ascending=True)

    n = len(pcts)
    labels = pcts.index.tolist()

    max_dec = max(pcts['decrease_10'].max(), 1.0)
    max_inc = max(pcts['increase_10'].max(), 1.0)

    # x layout: [left_margin | green_bars | 0 | red_bars | pct_label | cat_name | right_margin]
    pct_gap = 3.5       # gap between bar end and % label (data units)
    cat_gap = 5.0       # gap between % label and category name
    cat_field = 30.0    # fixed width reserved for category names on the right

    x_left  = -(max_dec + pct_gap + 10)
    x_right =   max_inc + pct_gap + cat_gap + cat_field

    fig_h = max(4.5, n * 0.82 + 3.2)
    fig, ax = plt.subplots(figsize=(14, fig_h))
    y = np.arange(n)

    # Bars — green LEFT (negative x), dark-red RIGHT (positive x)
    ax.barh(y, -pcts['decrease_10'], color='#4CAF50', edgecolor='none', height=0.58, alpha=0.92)
    ax.barh(y,  pcts['increase_10'], color='#8B0000', edgecolor='none', height=0.58, alpha=0.92)

    # Centre line
    ax.axvline(0, color='#444444', linewidth=1.4, zorder=4)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    ax.grid(False)
    ax.set_xlim(x_left, x_right)
    ax.set_ylim(-0.75, n + 1.6)

    # Per-row labels
    for i, (cat, row) in enumerate(zip(labels, pcts.itertuples())):
        dec = row.decrease_10
        inc = row.increase_10
        # Green % (left of green bar)
        ax.text(-(dec + pct_gap), i, f'{dec:.0f}%', ha='right', va='center',
                fontsize=11, color='#2e7d32', fontweight='bold')
        # Red % (right of red bar)
        ax.text(inc + pct_gap, i, f'{inc:.0f}%', ha='left', va='center',
                fontsize=11, color='#8B0000', fontweight='bold')
        # Category name at fixed right position
        ax.text(max_inc + pct_gap + cat_gap, i, cat, ha='left', va='center',
                fontsize=11, fontweight='bold', color='#222222')

    # Column headers
    header_y = n + 0.95
    ax.text(-max_dec / 2, header_y, 'Percent of parcels\ndecreasing >10%',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='#222222')
    ax.text(max_inc / 2, header_y, 'Percent of parcels\nincreasing >10%',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='#222222')

    ax.set_title(f'Share of Parcels with >10% Tax Change — {city_title}',
                 fontsize=14, fontweight='bold', pad=10)
    fig.tight_layout()
    return fig


def _make_quintile_chart(
    df: pd.DataFrame,
    group_col: str,
    group_name: str,
    city_title: str,
    filter_label: str,
) -> Optional[plt.Figure]:
    """Green-gradient quintile bar chart for a census dimension.

    Parameters
    ----------
    df : pd.DataFrame
        Parcel data (already filtered to the desired subset).
    group_col : str
        Column to quintile on (e.g. ``'median_income'`` or ``'minority_pct'``).
    group_name : str
        Human-readable dimension name for the title (e.g. ``'Neighborhood Income'``).
    city_title : str
        City name for the chart title.
    filter_label : str
        Description of the parcel filter applied, shown in the title
        (e.g. ``'Excl. Vacant Land, Residential Only'``).

    Returns
    -------
    plt.Figure or None
    """
    valid = df[df[group_col].notna()].copy()
    if group_col == 'median_income':
        valid = valid[valid[group_col] > 0]
    if len(valid) < 50 or 'tax_change_pct' not in valid.columns:
        return None

    try:
        valid['_q'] = pd.qcut(valid[group_col], 5, labels=False, duplicates='drop')
    except ValueError:
        return None
    if valid['_q'].nunique() < 2:
        return None

    q_x_labels = ['Q1 (Lowest)', 'Q2', 'Q3', 'Q4', 'Q5 (Highest)']
    q_stats = (
        valid.groupby('_q', observed=False)
        .agg(median_pct=('tax_change_pct', 'median'),
             count=('tax_change_pct', 'count'))
        .reset_index()
        .sort_values('_q')
    )
    n = len(q_stats)
    if n == 0:
        return None

    vals = q_stats['median_pct'].tolist()
    # Assign darkest color to the most-negative quintile (biggest tax decrease),
    # lightest to the least-negative.  Matches archived chart convention:
    #   color_rank = argsort(argsort(-vals))  →  most negative → rank 4 → darkest
    vals_arr = np.array(vals)
    color_ranks = np.argsort(np.argsort(-vals_arr))  # 0=most positive, 4=most negative
    colors = [_QUINTILE_GREENS[min(int(r), 4)] for r in color_ranks]

    min_val = min(vals + [0])
    max_val = max(vals + [0])
    y_range = max(max_val - min_val, 0.5)

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(n)
    bars = ax.bar(x, vals, color=colors, edgecolor='none', width=0.72)
    ax.axhline(0, color='black', linewidth=1.5, zorder=3)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(False)
    ax.set_xticks([])
    ax.tick_params(left=False, labelleft=False)

    # Quintile labels sit at y=0: above it when bars go down, below when bars go up
    lbl_offset = y_range * 0.04
    for i, (lbl, val) in enumerate(zip(q_x_labels, vals)):
        if val <= 0:
            ax.text(i,  lbl_offset, lbl, ha='center', va='bottom',
                    fontsize=12, fontweight='bold', color='#1a1a1a')
        else:
            ax.text(i, -lbl_offset, lbl, ha='center', va='top',
                    fontsize=12, fontweight='bold', color='#1a1a1a')

    # Values inside bars (skip if bar is too short to label)
    for i, (bar, val) in enumerate(zip(bars, vals)):
        if abs(val) >= y_range * 0.12:
            ax.text(bar.get_x() + bar.get_width() / 2, val / 2,
                    f'{val:.1f}%',
                    ha='center', va='center', fontsize=12, fontweight='bold', color='black')

    margin = y_range * 0.22
    ax.set_ylim(min_val - margin, max_val + margin)
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_title(
        f'Median Tax Change by {group_name} Quintile\n({filter_label})',
        fontsize=13, fontweight='bold', pad=12,
    )
    fig.tight_layout()
    return fig


def _make_distribution_chart(df: pd.DataFrame, city_title: str) -> plt.Figure:
    """Build the tax-change-% distribution histogram and return it (does not show/save)."""
    pcts = df['tax_change_pct'].dropna()
    pcts = pcts[(pcts > -200) & (pcts < 500)]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(pcts, bins=80, color='steelblue', alpha=0.75, edgecolor='none')
    ax.axvline(0, color='black', linewidth=1.5)
    ax.axvline(pcts.median(), color='crimson', linewidth=1.5, linestyle='--',
               label=f'Median {pcts.median():+.1f}%')
    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    ax.grid(False)
    ax.set_xlabel('Tax Change (%)', fontsize=12)
    ax.set_ylabel('Number of Parcels', fontsize=12)
    ax.set_title(f'Distribution of Parcel Tax Changes — {city_title}',
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    fig.tight_layout()
    return fig


def create_city_report(
    df: pd.DataFrame,
    city: str,
    output_dir: str = '../../analysis/reports',
    show: bool = True,
    min_category_count: int = 50,
    census_categories: Optional[List[str]] = None,
) -> dict:
    """
    Generate standard analysis charts from a city's standard export DataFrame.

    Saves PNGs to ``{output_dir}/{city}/``:

    - ``category_impact.png``                — median % change by property category.
    - ``ten_pct_share.png``                  — diverging bar: % parcels with >10% change.
    - ``income_quintile_non_vacant.png``     — income quintile, all non-vacant parcels.
    - ``income_quintile_residential.png``    — income quintile, residential parcels only
      (or ``census_categories`` if supplied).
    - ``minority_quintile_non_vacant.png``   — minority quintile, all non-vacant.
    - ``minority_quintile_residential.png``  — minority quintile, residential only.
    - ``distribution.png``                   — histogram of parcel-level tax change %.

    Parameters
    ----------
    df : pd.DataFrame
        Output of ``save_standard_export``.  Required columns: ``property_category``
        (or ``PROPERTY_CATEGORY``), ``current_tax``, ``new_tax``, ``tax_change``,
        ``tax_change_pct``.  Optional census columns: ``median_income``,
        ``minority_pct``, ``black_pct``.
    city : str
        City slug used for output file names and sub-directory, e.g. ``"southbend"``.
    output_dir : str
        Parent directory for PNGs.  A ``{city}`` sub-directory is created automatically.
        Default ``"../../analysis/reports"`` resolves correctly from ``cities/<city>/``.
    show : bool
        Display figures inline when ``True`` (Jupyter).  Use ``False`` for headless runs.
    min_category_count : int
        Minimum parcel count for a category to appear in category charts.  Default ``50``.
    census_categories : list of str or None
        Property categories to include in the "residential" census quintile charts.
        Defaults to :data:`_RESIDENTIAL_CATEGORIES` when ``None``.  Pass an empty list
        ``[]`` to skip the residential-filtered version entirely.

    Returns
    -------
    dict
        ``row_count``, ``current_revenue``, ``new_revenue``, ``revenue_delta_pct``,
        ``land_millage``, ``improvement_millage``, ``model_type``, ``charts_saved``.
    """
    import os
    from lvt.lvt_utils import calculate_category_tax_summary

    city_dir = os.path.join(output_dir, city)
    os.makedirs(city_dir, exist_ok=True)
    charts_saved: List[str] = []
    city_title = city.replace('_', ' ').title()

    cat_col = 'property_category' if 'property_category' in df.columns else 'PROPERTY_CATEGORY'
    res_cats = census_categories if census_categories is not None else _RESIDENTIAL_CATEGORIES

    # ------------------------------------------------------------------
    # Chart 1: property category impact (median %)
    # ------------------------------------------------------------------
    cat_summary = calculate_category_tax_summary(
        df, category_col=cat_col, current_tax_col='current_tax', new_tax_col='new_tax',
    )
    if not cat_summary.empty:
        fig = _make_category_chart(cat_summary, cat_col, city_title,
                                   min_count=min_category_count)
        path = os.path.join(city_dir, 'category_impact.png')
        fig.savefig(path, dpi=150, bbox_inches='tight')
        charts_saved.append(path)
        if show:
            plt.show()
        else:
            plt.close(fig)

    # ------------------------------------------------------------------
    # Chart 2: diverging ±10 % share by category
    # ------------------------------------------------------------------
    if cat_col in df.columns and 'tax_change_pct' in df.columns:
        fig = _make_ten_pct_chart(df, cat_col, city_title, min_count=min_category_count)
        path = os.path.join(city_dir, 'ten_pct_share.png')
        fig.savefig(path, dpi=150, bbox_inches='tight')
        charts_saved.append(path)
        if show:
            plt.show()
        else:
            plt.close(fig)

    # ------------------------------------------------------------------
    # Census quintile charts — two filters each
    # ------------------------------------------------------------------
    def _save_fig(fig: Optional[plt.Figure], fname: str) -> None:
        if fig is None:
            return
        p = os.path.join(city_dir, fname)
        fig.savefig(p, dpi=150, bbox_inches='tight')
        charts_saved.append(p)
        if show:
            plt.show()
        else:
            plt.close(fig)

    has_income   = 'median_income' in df.columns and df['median_income'].notna().any()
    has_minority = 'minority_pct'  in df.columns and df['minority_pct'].notna().any()

    if has_income or has_minority:
        # Filter 1: all non-vacant
        if cat_col in df.columns:
            df_nv = df[df[cat_col] != 'Vacant Land'].copy()
        else:
            df_nv = df.copy()

        if has_income:
            _save_fig(
                _make_quintile_chart(df_nv, 'median_income', 'Neighborhood Income',
                                     city_title, 'Excl. Vacant Land, All Properties'),
                'income_quintile_non_vacant.png',
            )
        if has_minority:
            _save_fig(
                _make_quintile_chart(df_nv, 'minority_pct', 'Minority Percentage',
                                     city_title, 'Excl. Vacant Land, All Properties'),
                'minority_quintile_non_vacant.png',
            )

        # Filter 2: residential (or custom) only
        if res_cats and cat_col in df.columns:
            df_res = df[df[cat_col].isin(res_cats)].copy()
            res_label = (
                'Residential Only' if res_cats == _RESIDENTIAL_CATEGORIES
                else 'Custom Category Filter'
            )
            if has_income:
                _save_fig(
                    _make_quintile_chart(df_res, 'median_income', 'Neighborhood Income',
                                         city_title, f'Excl. Vacant Land, {res_label}'),
                    'income_quintile_residential.png',
                )
            if has_minority:
                _save_fig(
                    _make_quintile_chart(df_res, 'minority_pct', 'Minority Percentage',
                                         city_title, f'Excl. Vacant Land, {res_label}'),
                    'minority_quintile_residential.png',
                )

    # ------------------------------------------------------------------
    # Chart: distribution histogram
    # ------------------------------------------------------------------
    if 'tax_change_pct' in df.columns:
        fig = _make_distribution_chart(df, city_title)
        path = os.path.join(city_dir, 'distribution.png')
        fig.savefig(path, dpi=150, bbox_inches='tight')
        charts_saved.append(path)
        if show:
            plt.show()
        else:
            plt.close(fig)

    current_rev = float(df['current_tax'].sum())
    new_rev     = float(df['new_tax'].sum())
    land_mill = (float(df['land_millage'].iloc[0])
                 if 'land_millage' in df.columns and len(df) else None)
    imp_mill  = (float(df['improvement_millage'].iloc[0])
                 if 'improvement_millage' in df.columns and len(df) else None)
    model_t   = (str(df['model_type'].iloc[0])
                 if 'model_type' in df.columns and len(df) else None)

    return {
        'row_count': len(df),
        'current_revenue': current_rev,
        'new_revenue': new_rev,
        'revenue_delta_pct': (new_rev - current_rev) / max(abs(current_rev), 1) * 100,
        'land_millage': land_mill,
        'improvement_millage': imp_mill,
        'model_type': model_t,
        'charts_saved': charts_saved,
    }
