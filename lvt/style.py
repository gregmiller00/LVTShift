"""
LVTShift visual style constants.

Usage in notebooks:
    from lvt import style
    style.apply_lvt_style()

    # Access colors directly:
    from lvt.style import CATEGORY_COLORS, INCREASE_COLOR, DECREASE_COLOR
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Property category color palette
# Consistent across all cities so charts are directly comparable.
# ---------------------------------------------------------------------------
CATEGORY_COLORS: dict[str, str] = {
    'Single Family Residential':     '#4878CF',
    'Small Multi-Family (2-4 units)':'#6ACC65',
    'Large Multi-Family (5+ units)': '#D65F5F',
    'Other Residential':             '#B47CC7',
    'Commercial':                    '#C4AD66',
    'Industrial':                    '#8C8C8C',
    'Vacant Land':                   '#77BEDB',
    'Agricultural':                  '#5C7340',
    'Transportation - Parking':      '#F7B733',
    'Exempt':                        '#CCCCCC',
    'Other':                         '#AAAAAA',
}

# Fallback for non-standard categories not listed above
FALLBACK_COLOR = '#999999'

# ---------------------------------------------------------------------------
# Tax change colors
# ---------------------------------------------------------------------------
INCREASE_COLOR  = '#E45756'   # red — tax goes up
DECREASE_COLOR  = '#4C78A8'   # blue — tax goes down
NEUTRAL_COLOR   = '#AAAAAA'   # grey — no change

# ---------------------------------------------------------------------------
# Figure sizes
# ---------------------------------------------------------------------------
FIGURE_SIZE_WIDE   = (12, 6)
FIGURE_SIZE_SQUARE = (8, 8)
FIGURE_SIZE_TALL   = (8, 12)
FIGURE_SIZE_NARROW = (6, 8)

# ---------------------------------------------------------------------------
# Style application
# ---------------------------------------------------------------------------

def apply_lvt_style(font_size: int = 11) -> None:
    """
    Set consistent matplotlib rcParams for LVT charts.
    Call once at the top of a notebook before any plotting.

    Parameters
    ----------
    font_size : int
        Base font size for all text elements.
    """
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'font.size':              font_size,
        'axes.titlesize':         font_size + 2,
        'axes.labelsize':         font_size,
        'xtick.labelsize':        font_size - 1,
        'ytick.labelsize':        font_size - 1,
        'legend.fontsize':        font_size - 1,
        'axes.spines.top':        False,
        'axes.spines.right':      False,
        'axes.grid':              False,
        'figure.dpi':             120,
        'savefig.bbox':           'tight',
        'savefig.dpi':            150,
    })


def get_category_color(category: str) -> str:
    """Return the standard color for a property category, or the fallback if unknown."""
    return CATEGORY_COLORS.get(category, FALLBACK_COLOR)


def get_category_colors(categories: list[str]) -> list[str]:
    """Return a list of colors corresponding to a list of category names."""
    return [get_category_color(c) for c in categories]
