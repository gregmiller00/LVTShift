import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

REPO = Path('C:/projects/LVTShift')
OUT = Path(__file__).parent / 'ownership_figs'
OUT.mkdir(exist_ok=True)

# Load parcels (owner names) and model export (categories + tax results)
parcels = gpd.read_parquet(REPO / 'cities/philadelphia/data/parcels.gpq')
csv = pd.read_csv(REPO / 'analysis/data/philadelphia.csv', low_memory=False)

# Join on parcel number, never row index (known trap)
parcels['join_key'] = parcels['parcel_number'].astype(str).str.lstrip('0')
csv['join_key'] = csv['parcel_id'].astype(str).str.lstrip('0')
n_dupe = parcels['join_key'].duplicated().sum() + csv['join_key'].duplicated().sum()
print(f'Duplicate join keys dropped: {n_dupe}')
parcels = parcels.drop_duplicates('join_key')
csv = csv.drop_duplicates('join_key')
df = parcels.drop(columns='geometry').merge(
    csv[['join_key', 'property_category', 'current_tax', 'new_tax', 'tax_change']],
    on='join_key', how='inner',
)
print(f'Parcels: {len(parcels):,} | export rows: {len(csv):,} | joined: {len(df):,}')

# Owner name: coalesce owner_1 -> owner_2, normalize
df['owner_name'] = (
    df[['owner_1', 'owner_2']]
    .replace('', np.nan)
    .bfill(axis=1)
    .iloc[:, 0]
    .fillna('')
    .str.upper()
    .str.strip()
)
n_blank = (df['owner_name'] == '').sum()
print(f'Blank owner names (excluded from owner grouping): {n_blank:,}')
df = df[df['owner_name'] != ''].copy()

# Flag obvious public/agency owners so government holdings don't read as private concentration
PUBLIC_PATTERNS = [
    'CITY OF PHILA', 'CITY OF PHILADELPHIA', 'PHILADELPHIA LAND BANK', 'LAND BANK',
    'PHILA HOUSING AUTH', 'PHILADELPHIA HOUSING', 'HOUSING AUTHORITY',
    'REDEVELOPMENT AUTH', 'PHILADELPHIA REDEVELOP', 'PHILA REDEVELOPMENT',
    'SCHOOL DISTRICT', 'SCHOOL DIST', 'BOARD OF EDUCATION',
    'COMMONWEALTH OF', 'COMMONWEALTH OF PA', 'STATE OF PENNSYLVANIA',
    'UNITED STATES', 'U S A', 'USA ', 'SECRETARY OF HOUSING',
    'SEPTA', 'SOUTHEASTERN PENN TRANS', 'SOUTHEASTERN PENNSYLVANIA',
    'DELAWARE RIVER PORT', 'PHILA MUNICIPAL AUTH', 'PHILADELPHIA MUNICIPAL',
    'PHILA PARKING AUTH', 'PHILADELPHIA PARKING', 'PARKING AUTHORITY',
    'PHILADELPHIA AUTHORITY F', 'PHILA AUTHORITY FOR IND',  # PAID (industrial dev)
    'PIDC', 'PHILADELPHIA INDUSTRIAL',
    'FAIRMOUNT PARK', 'DEPT OF', 'DEPARTMENT OF',
]
pat = '|'.join(pd.Series(PUBLIC_PATTERNS).str.replace('(', r'\(', regex=False).str.replace(')', r'\)', regex=False))
df['is_public'] = df['owner_name'].str.contains(pat, regex=True)
pub_share_val = df.loc[df['is_public'], 'market_value'].sum() / df['market_value'].sum()
print(f"Public-agency parcels: {df['is_public'].sum():,} "
      f"({df['is_public'].mean():.1%} of parcels, {pub_share_val:.1%} of market value)")

# Top public owners for reference
print('\nTop 10 public owners by parcel count:')
print(df[df['is_public']].groupby('owner_name')
      .agg(parcels=('join_key', 'size'), market_value=('market_value', 'sum'))
      .sort_values('parcels', ascending=False).head(10).to_string())

priv = df[~df['is_public']].copy()

# Owner-level aggregation (private owners)
own = priv.groupby('owner_name').agg(
    parcels=('join_key', 'size'),
    market_value=('market_value', 'sum'),
    taxable_total=('taxable_land', 'sum'),
    current_tax=('current_tax', 'sum'),
    new_tax=('new_tax', 'sum'),
).sort_values('market_value', ascending=False)
n_owners = len(own)
print(f'\nDistinct private owner names: {n_owners:,} holding {own["parcels"].sum():,} parcels')

# Portfolio-size tiers
tiers = pd.cut(
    own['parcels'],
    bins=[0, 1, 2, 4, 9, 49, np.inf],
    labels=['1 parcel', '2', '3-4', '5-9', '10-49', '50+'],
)
tier_tab = own.groupby(tiers, observed=True).agg(
    owners=('parcels', 'size'),
    parcels=('parcels', 'sum'),
    market_value=('market_value', 'sum'),
)
tier_tab['owner_share'] = tier_tab['owners'] / tier_tab['owners'].sum()
tier_tab['parcel_share'] = tier_tab['parcels'] / tier_tab['parcels'].sum()
tier_tab['value_share'] = tier_tab['market_value'] / tier_tab['market_value'].sum()
print('\nPortfolio-size tiers (private owners):')
print(tier_tab.to_string(float_format=lambda x: f'{x:,.3f}' if x < 1 else f'{x:,.0f}'))

# Concentration: share of private market value held by top slices of owners
vals = own['market_value'].sort_values(ascending=False).to_numpy()
cum = np.cumsum(vals) / vals.sum()
for label, k in [('Top 10 owners', 10), ('Top 100', 100), ('Top 1,000', 1000)]:
    print(f'{label}: {cum[k-1]:.1%} of private market value')
for pct in [0.01, 0.05, 0.10]:
    k = max(1, int(n_owners * pct))
    print(f'Top {pct:.0%} of owners ({k:,}): {cum[k-1]:.1%} of private market value')

# Gini of market value across owners
sorted_v = np.sort(vals)
idx = np.arange(1, n_owners + 1)
gini = (2 * (idx * sorted_v).sum()) / (n_owners * sorted_v.sum()) - (n_owners + 1) / n_owners
print(f'Gini (market value across owners): {gini:.3f}')

# Top 20 private owners
top20 = own.head(20).copy()
top20['tax_change'] = top20['new_tax'] - top20['current_tax']
print('\nTop 20 private owners by total market value:')
print(top20[['parcels', 'market_value', 'current_tax', 'new_tax', 'tax_change']]
      .to_string(float_format=lambda x: f'{x:,.0f}'))

top20_ct = own.sort_values('parcels', ascending=False).head(20)
print('\nTop 20 private owners by parcel count:')
print(top20_ct[['parcels', 'market_value']].to_string(float_format=lambda x: f'{x:,.0f}'))

# Multi-parcel ownership by property category (private only)
own_count = priv.groupby('owner_name')['join_key'].size()
priv['owner_portfolio'] = priv['owner_name'].map(own_count)
cat_groups = {
    'Single Family Residential': ['Single Family Residential'],
    'Small Multi-Family (2-4)': ['Small Multi-Family (2-4 units)'],
    'Large Multi-Family (5+)': ['Large Multi-Family (5+ units)'],
    'Vacant Land': ['Vacant Land'],
    'Commercial/Mixed': ['Commercial', 'Mixed Use', 'Other Commercial',
                         'Retail / General Commercial', 'Office / Commercial Condo', 'Hotel'],
    'Industrial': ['Industrial'],
}
rows = []
for name, cats in cat_groups.items():
    sub = priv[priv['property_category'].isin(cats)]
    if not len(sub):
        continue
    big = sub['owner_portfolio'] >= 10
    rows.append({
        'category': name,
        'parcels': len(sub),
        'market_value_B': sub['market_value'].sum() / 1e9,
        'pct_parcels_10plus_owner': big.mean(),
        'pct_value_10plus_owner': sub.loc[big, 'market_value'].sum() / sub['market_value'].sum(),
    })
cat_tab = pd.DataFrame(rows)
print('\nShare held by owners with 10+ parcel portfolios, by category:')
print(cat_tab.to_string(index=False, float_format=lambda x: f'{x:,.3f}'))

# Figures
plt.rcParams.update({'figure.dpi': 130, 'axes.grid': True, 'grid.alpha': 0.3})

# Fig 1: portfolio tiers — owners vs parcels vs value shares
fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(len(tier_tab))
w = 0.27
ax.bar(x - w, tier_tab['owner_share'], w, label='Share of owners')
ax.bar(x, tier_tab['parcel_share'], w, label='Share of parcels')
ax.bar(x + w, tier_tab['value_share'], w, label='Share of market value')
ax.set_xticks(x, tier_tab.index)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_xlabel('Owner portfolio size (parcels owned)')
ax.set_title('Philadelphia private ownership by portfolio size')
ax.legend()
fig.tight_layout()
fig.savefig(OUT / 'portfolio_tiers.png')
plt.close(fig)

# Fig 2: Lorenz curve of market value across owners
fig, ax = plt.subplots(figsize=(5.5, 5.5))
lorenz_x = np.arange(1, n_owners + 1) / n_owners
lorenz_y = np.cumsum(sorted_v) / sorted_v.sum()
ax.plot(lorenz_x, lorenz_y, lw=2)
ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.6)
ax.set_xlabel('Cumulative share of owners (poorest first)')
ax.set_ylabel('Cumulative share of market value')
ax.set_title(f'Lorenz curve, private property value by owner (Gini = {gini:.2f})')
fig.tight_layout()
fig.savefig(OUT / 'lorenz_owners.png')
plt.close(fig)

# Fig 3: top 20 owners by market value
fig, ax = plt.subplots(figsize=(9, 6))
t = top20.iloc[::-1]
ax.barh(t.index, t['market_value'] / 1e6)
ax.set_xlabel('Total market value ($M)')
ax.set_title('Top 20 private owners by total market value')
fig.tight_layout()
fig.savefig(OUT / 'top20_value.png')
plt.close(fig)

# Fig 4: 10+ portfolio share by category
fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(len(cat_tab))
ax.bar(x - 0.2, cat_tab['pct_parcels_10plus_owner'], 0.4, label='Share of parcels')
ax.bar(x + 0.2, cat_tab['pct_value_10plus_owner'], 0.4, label='Share of market value')
ax.set_xticks(x, cat_tab['category'], rotation=20, ha='right')
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_title('Held by owners with 10+ parcel portfolios')
ax.legend()
fig.tight_layout()
fig.savefig(OUT / 'big_portfolio_by_category.png')
plt.close(fig)

print(f'\nFigures saved to {OUT}')
