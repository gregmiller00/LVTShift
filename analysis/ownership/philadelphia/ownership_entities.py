import re
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
SCRATCH = Path(__file__).parent
OUT = SCRATCH / 'ownership_figs'
OUT.mkdir(exist_ok=True)

# Load and join (same as pass 1)
parcels = gpd.read_parquet(REPO / 'cities/philadelphia/data/parcels.gpq')
csv = pd.read_csv(REPO / 'analysis/data/philadelphia.csv', low_memory=False)
parcels['join_key'] = parcels['parcel_number'].astype(str).str.lstrip('0')
csv['join_key'] = csv['parcel_id'].astype(str).str.lstrip('0')
parcels = parcels.drop_duplicates('join_key')
csv = csv.drop_duplicates('join_key')
df = parcels.drop(columns='geometry').merge(
    csv[['join_key', 'property_category', 'current_tax', 'new_tax', 'tax_change',
         'tax_change_pct', 'is_fully_exempt']],
    on='join_key', how='inner',
)

# Mailing addresses
mail = pd.read_parquet(SCRATCH / 'opa_mailing.parquet')
mail['join_key'] = mail['parcel_number'].astype(str).str.lstrip('0')
mail = mail.drop_duplicates('join_key')
df = df.merge(mail[['join_key', 'mailing_street', 'mailing_zip', 'location']],
              on='join_key', how='left')
print(f'Joined: {len(df):,} parcels; mailing_street present: {df["mailing_street"].notna().mean():.1%}')

# Owner name (as pass 1)
df['owner_name'] = (
    df[['owner_1', 'owner_2']].replace('', np.nan).bfill(axis=1).iloc[:, 0]
    .fillna('').str.upper().str.strip()
)
df = df[df['owner_name'] != ''].copy()

# Normalized mailing key: street + zip5; fall back to property location (self-mail)
def norm_addr(s):
    s = s.fillna('').str.upper().str.strip()
    s = s.str.replace(r'[^A-Z0-9 ]', '', regex=True)
    s = s.str.replace(r'\s+', ' ', regex=True)
    return s

df['zip5'] = df['mailing_zip'].fillna('').astype(str).str[:5]
df['mail_key'] = norm_addr(df['mailing_street']) + '|' + df['zip5']
blank_mail = df['mail_key'].str.startswith('|')
df.loc[blank_mail, 'mail_key'] = 'SELF ' + norm_addr(df.loc[blank_mail, 'location']) + '|19PHL'
print(f'Parcels falling back to property address as mail key: {blank_mail.sum():,}')

# Owner classification (legal form), checked in order
PUBLIC_PATTERNS = [
    'CITY OF PHILA', 'CITY OF PHILADELPHIA', 'PHILADELPHIA LAND BANK', 'LAND BANK',
    'PHILA HOUSING AUTH', 'PHILADELPHIA HOUSING', 'HOUSING AUTHORITY',
    'REDEVELOPMENT AUTH', 'PHILADELPHIA REDEVELOP', 'PHILA REDEVELOPMENT',
    'SCHOOL DISTRICT', 'SCHOOL DIST', 'BOARD OF EDUCATION',
    'COMMONWEALTH OF', 'STATE OF PENNSYLVANIA',
    'UNITED STATES', 'SECRETARY OF HOUSING',
    'SEPTA', 'SOUTHEASTERN PENN TRANS', 'SOUTHEASTERN PENNSYLVANIA',
    'DELAWARE RIVER PORT', 'PHILA MUNICIPAL AUTH', 'PHILADELPHIA MUNICIPAL',
    'PHILA PARKING AUTH', 'PHILADELPHIA PARKING', 'PARKING AUTHORITY',
    'PHILADELPHIA AUTHORITY F', 'PHILA AUTHORITY FOR IND',
    'PIDC', 'PHILADELPHIA INDUSTRIAL', 'PENNSYLVANIA ECONOMIC DEV',
    'FAIRMOUNT PARK', 'DEPT OF', 'DEPARTMENT OF', 'AMTRAK', 'NATIONAL RAILROAD',
]
INSTITUTIONAL = [
    'UNIVERSITY', 'UNIV ', 'UNIV OF', ' COLLEGE', 'COLLEGE OF', 'HOSPITAL', 'HEALTH SYSTEM',
    'CHURCH', 'BAPTIST', 'CATHOLIC', 'LUTHERAN', 'METHODIST', 'PRESBYTERIAN', 'EPISCOPAL',
    'ISLAMIC', 'MOSQUE', 'MASJID', 'SYNAGOGUE', 'CONGREGATION', 'MINISTR', 'DIOCESE',
    'ARCHDIOCESE', 'CEMETERY', 'FOUNDATION', 'CHARIT', 'ACADEMY', 'SEMINARY',
    'SALVATION ARMY', 'YMCA', 'YWCA', 'CHARTER SCHOOL', 'FRIENDS OF',
]
BUSINESS = [
    r'\bLLC\b', r'\bL L C\b', r'\bLP\b', r'\bL P\b', r'\bLTD\b', r'\bINC\b', r'\bCORP\b',
    r'\bCOMPANY\b', r'\bCO\b', r'\bPARTNERS\b', r'\bPARTNERSHIP\b', r'\bASSOCIATES\b',
    r'\bASSOC\b', r'\bPROPERTIES\b', r'\bPROPERTY\b', r'\bREALTY\b', r'\bREAL ESTATE\b',
    r'\bINVEST', r'\bHOLDINGS\b', r'\bGROUP\b', r'\bDEVELOP', r'\bTRUST\b', r'\bTR\b',
    r'\bREIT\b', r'\bVENTURES\b', r'\bCAPITAL\b', r'\bMGMT\b', r'\bMANAGEMENT\b',
    r'\bENTERPRISES\b', r'\bBANK\b', r'\bSAVINGS\b', r'\bFCU\b', r'\bHOMES\b',
    r'\bRENTALS\b', r'\bEQUITIES\b', r'\bESTATE OF\b', r'\bAPARTMENTS\b',
]
pub_re = '|'.join(re.escape(p) for p in PUBLIC_PATTERNS)
inst_re = '|'.join(re.escape(p) for p in INSTITUTIONAL)
biz_re = '|'.join(BUSINESS)

df['owner_class'] = 'Individual'
df.loc[df['owner_name'].str.contains(biz_re, regex=True), 'owner_class'] = 'Business / investor entity'
df.loc[df['owner_name'].str.contains(inst_re, regex=True), 'owner_class'] = 'Institutional / nonprofit'
df.loc[df['owner_name'].str.contains(pub_re, regex=True), 'owner_class'] = 'Public agency'

print('\nParcels by owner class:')
cls = df.groupby('owner_class').agg(
    parcels=('join_key', 'size'),
    market_value=('market_value', 'sum'),
    current_tax=('current_tax', 'sum'),
    new_tax=('new_tax', 'sum'),
)
cls['value_share'] = cls['market_value'] / cls['market_value'].sum()
cls['tax_change'] = cls['new_tax'] - cls['current_tax']
cls['tax_change_pct'] = cls['tax_change'] / cls['current_tax'].replace(0, np.nan)
print(cls.to_string(float_format=lambda x: f'{x:,.3f}' if abs(x) < 1 else f'{x:,.0f}'))

# Entity resolution: union-find over owner_name <-> mail_key, BUSINESS names only.
# Merging individuals by shared mail address chains condo towers and management offices
# into mega-components; the de-duplication target is LLC networks, so only business-class
# names link through addresses. Individuals and institutions keep name-based identity.
biz_pairs = df.loc[df['owner_class'] == 'Business / investor entity',
                   ['owner_name', 'mail_key']].drop_duplicates()
names_per_addr = biz_pairs.groupby('mail_key')['owner_name'].nunique()
MAX_NAMES_PER_ADDR = 50
hub_addrs = names_per_addr[names_per_addr > MAX_NAMES_PER_ADDR]
print(f'\nMail addresses excluded as merge hubs (> {MAX_NAMES_PER_ADDR} business names): {len(hub_addrs)}')
print(names_per_addr.sort_values(ascending=False).head(10).to_string())

link_pairs = biz_pairs[~biz_pairs['mail_key'].isin(hub_addrs.index)]

parent = {}
def find(x):
    root = x
    while parent.get(root, root) != root:
        root = parent[root]
    while parent.get(x, x) != x:
        parent[x], x = root, parent[x]
    return root
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[rb] = ra

for name, addr in link_pairs.itertuples(index=False):
    union(('N', name), ('A', addr))

is_biz = df['owner_class'] == 'Business / investor entity'
df['entity_id'] = df['owner_name']
df.loc[is_biz, 'entity_id'] = [
    'C:' + str(find(('N', n))[1]) for n in df.loc[is_biz, 'owner_name']
]
n_names = df['owner_name'].nunique()
n_entities = df['entity_id'].nunique()
n_biz_names = df.loc[is_biz, 'owner_name'].nunique()
n_biz_ents = df.loc[is_biz, 'entity_id'].nunique()
print(f'\nBusiness names: {n_biz_names:,} -> mail-grouped entities: {n_biz_ents:,} '
      f'({n_biz_names - n_biz_ents:,} merged away)')
print(f'All owners: {n_names:,} names -> {n_entities:,} entities')

# Label each entity by its highest-value constituent name
label = (df.groupby(['entity_id', 'owner_name'])['market_value'].sum()
         .sort_values(ascending=False).reset_index()
         .drop_duplicates('entity_id').set_index('entity_id')['owner_name'])
df['entity_label'] = df['entity_id'].map(label)
df['entity_id'] = df['entity_label']

# Concentration recomputed on private entities
priv = df[df['owner_class'] != 'Public agency'].copy()
ent = priv.groupby('entity_id').agg(
    parcels=('join_key', 'size'),
    market_value=('market_value', 'sum'),
    current_tax=('current_tax', 'sum'),
    new_tax=('new_tax', 'sum'),
    names=('owner_name', lambda s: ' | '.join(pd.Series(s).value_counts().head(3).index)),
    top_class=('owner_class', lambda s: s.mode().iat[0]),
).sort_values('market_value', ascending=False)
n_ent = len(ent)
vals = ent['market_value'].to_numpy()
cum = np.cumsum(vals) / vals.sum()
print(f'\nPrivate entities: {n_ent:,}')
print('Concentration (mail-grouped entities vs name-only from pass 1):')
for label, k, old in [('Top 10', 10, '3.4%'), ('Top 100', 100, '10.8%'), ('Top 1,000', 1000, '25.4%')]:
    print(f'  {label}: {cum[k-1]:.1%} of private value (was {old} name-based)')
for pct, old in [(0.01, '34.8%'), (0.05, '47.7%'), (0.10, '55.8%')]:
    k = max(1, int(n_ent * pct))
    print(f'  Top {pct:.0%} ({k:,} entities): {cum[k-1]:.1%} (was {old})')
sorted_v = np.sort(vals)
idx = np.arange(1, n_ent + 1)
gini = (2 * (idx * sorted_v).sum()) / (n_ent * sorted_v.sum()) - (n_ent + 1) / n_ent
print(f'  Gini: {gini:.3f} (was 0.621)')

ent['tax_change'] = ent['new_tax'] - ent['current_tax']
print('\nTop 20 private entities by market value (names = top 3 constituent owner names):')
print(ent.head(20)[['parcels', 'market_value', 'tax_change', 'names']]
      .to_string(float_format=lambda x: f'{x:,.0f}', max_colwidth=60))

print('\nTop 15 private entities by parcel count:')
print(ent.sort_values('parcels', ascending=False).head(15)[['parcels', 'market_value', 'tax_change', 'names']]
      .to_string(float_format=lambda x: f'{x:,.0f}', max_colwidth=60))

# Class share by property category
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
for gname, cats in cat_groups.items():
    sub = df[df['property_category'].isin(cats)]
    tot_v = sub['market_value'].sum()
    for cl in ['Individual', 'Business / investor entity', 'Institutional / nonprofit', 'Public agency']:
        s = sub[sub['owner_class'] == cl]
        rows.append({'category': gname, 'class': cl,
                     'parcel_share': len(s) / len(sub) if len(sub) else 0,
                     'value_share': s['market_value'].sum() / tot_v if tot_v else 0})
share_tab = pd.DataFrame(rows).pivot(index='category', columns='class', values='value_share')
share_tab = share_tab.reindex(cat_groups.keys())
print('\nMarket-value share by owner class and category:')
print(share_tab.to_string(float_format=lambda x: f'{x:.1%}'))

# LVT impact by owner class (taxable parcels only), overall and for key categories
def impact(sub):
    cur, new = sub['current_tax'].sum(), sub['new_tax'].sum()
    taxed = sub[sub['current_tax'] > 0]
    return pd.Series({
        'parcels': len(sub),
        'current_tax_M': cur / 1e6,
        'new_tax_M': new / 1e6,
        'delta_M': (new - cur) / 1e6,
        'delta_pct': (new - cur) / cur if cur else np.nan,
        'median_parcel_pct': taxed['tax_change_pct'].median() if len(taxed) else np.nan,
    })

print('\nLVT impact by owner class (all categories):')
imp = df.groupby('owner_class').apply(impact, include_groups=False)
print(imp.to_string(float_format=lambda x: f'{x:,.3f}' if abs(x) < 10 else f'{x:,.1f}'))

print('\nLVT impact, Single Family Residential only — individuals vs business entities:')
sfr = df[df['property_category'] == 'Single Family Residential']
imp_sfr = sfr.groupby('owner_class').apply(impact, include_groups=False)
print(imp_sfr.to_string(float_format=lambda x: f'{x:,.3f}' if abs(x) < 10 else f'{x:,.1f}'))

print('\nLVT impact, Vacant Land only:')
vac = df[df['property_category'] == 'Vacant Land']
imp_vac = vac.groupby('owner_class').apply(impact, include_groups=False)
print(imp_vac.to_string(float_format=lambda x: f'{x:,.3f}' if abs(x) < 10 else f'{x:,.1f}'))

# Individuals split by entity portfolio size (owner-occupant proxy vs small landlord)
ind = df[df['owner_class'] == 'Individual'].copy()
ent_size = ind.groupby('entity_id')['join_key'].size()
ind['tier'] = pd.cut(ind['entity_id'].map(ent_size), bins=[0, 1, 4, np.inf],
                     labels=['1 parcel', '2-4', '5+'])
print('\nLVT impact for Individual owners by portfolio size (entity-level):')
imp_ind = ind.groupby('tier', observed=True).apply(impact, include_groups=False)
print(imp_ind.to_string(float_format=lambda x: f'{x:,.3f}' if abs(x) < 10 else f'{x:,.1f}'))

# Figures
plt.rcParams.update({'figure.dpi': 130, 'axes.grid': True, 'grid.alpha': 0.3})

fig, ax = plt.subplots(figsize=(9, 5))
share_tab.plot(kind='bar', stacked=True, ax=ax,
               color=['#4878cf', '#6acc65', '#d65f5f', '#956cb4'])
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_ylabel('Share of market value')
ax.set_title('Who owns Philadelphia, by property category')
ax.legend(fontsize=8, loc='lower right')
plt.setp(ax.get_xticklabels(), rotation=20, ha='right')
fig.tight_layout()
fig.savefig(OUT / 'class_share_by_category.png')
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.5))
d = imp['delta_M'].sort_values()
colors = ['#2a9d8f' if v < 0 else '#e76f51' for v in d]
ax.barh(d.index, d, color=colors)
ax.set_xlabel('Total tax change under 4:1 split-rate ($M / year)')
ax.set_title('LVT burden shift by owner class (revenue-neutral)')
ax.axvline(0, color='k', lw=0.8)
fig.tight_layout()
fig.savefig(OUT / 'tax_shift_by_class.png')
plt.close(fig)

print(f'\nFigures saved to {OUT}')
