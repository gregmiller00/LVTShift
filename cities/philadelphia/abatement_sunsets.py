"""
Estimate abatement sunset years for Philadelphia "Abated / Construction Exemption" parcels.

Method A (assessment history): pull all records citywide where taxable_building=0
and market_value>0 for each year 2014-2024 (one call per year, no parcel batching).
Find the earliest year each parcel appears as abated. Sunset = start_year + 10.

Method B (L&I permits): one call for all new construction permits since 2013.
Sunset = permit_issue_year + 10.

~13 total API calls.
"""
import io
import sys
import time
import requests
import pandas as pd
import geopandas as gpd
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR   = Path('data')
PARCEL_GPQ = DATA_DIR / 'parcels.gpq'
CARTO_SQL  = 'https://phl.carto.com/api/v2/sql'

def carto(sql, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(CARTO_SQL, data={'q': sql, 'format': 'csv'}, timeout=120)
            r.raise_for_status()
            return pd.read_csv(io.StringIO(r.text))
        except Exception as e:
            if attempt < retries - 1:
                print(f"  retry {attempt+1}: {e}")
                time.sleep(3)
            else:
                raise

# ── 1. Load abated parcel numbers ─────────────────────────────────────────────
print("Loading parcels...")
gdf = gpd.read_parquet(PARCEL_GPQ)
gdf['parcel_number'] = gdf['parcel_number'].astype(str).str.zfill(9)

gdf['category_code'] = (
    pd.to_numeric(gdf['category_code'], errors='coerce')
    .astype('Int64').astype(str).str.strip()
)
VACANT_CODES = {'6', '12', '13'}
abated_mask = (
    ~gdf['category_code'].isin(VACANT_CODES)
    & (pd.to_numeric(gdf['taxable_building'], errors='coerce').fillna(0) <= 0)
    & (pd.to_numeric(gdf['taxable_land'],     errors='coerce').fillna(0) >  0)
)
abated_set = set(gdf.loc[abated_mask, 'parcel_number'].tolist())
print(f"Abated parcels (2024): {len(abated_set):,}")


# ── 2. Method A: one query per year, filter locally ───────────────────────────
print("\n── Method A: assessment history (2014–2024), 11 API calls ──")

YEARS = list(range(2014, 2025))
hist_frames = []

n_steps = len(YEARS) + 2  # years + permits + merge
step = 0

def bar(step, total, label, width=35):
    filled = int(width * step / total)
    b = '█' * filled + '░' * (width - filled)
    print(f"\r[{b}] {step}/{total}  {label:<40}", end='', flush=True)

for yr in YEARS:
    step += 1
    bar(step, n_steps, f"assessments {yr}...")
    sql = f"""
        SELECT parcel_number, {yr} AS year, taxable_building, market_value
        FROM assessments
        WHERE year = {yr}
          AND taxable_building = 0
          AND market_value > 0
    """
    df = carto(sql)
    df['parcel_number'] = df['parcel_number'].astype(str).str.zfill(9)
    df_abated = df[df['parcel_number'].isin(abated_set)]
    hist_frames.append(df_abated)

bar(step, n_steps, f"assessments done — {len(pd.concat(hist_frames)):,} records")
print()

hist = pd.concat(hist_frames, ignore_index=True)
print(f"\nTotal records: {len(hist):,} across {hist['parcel_number'].nunique():,} parcels")

# Earliest year each parcel appears as abated
start_a = (
    hist.groupby('parcel_number')['year'].min()
    .rename('start_year_a').reset_index()
)
start_a['sunset_year_a'] = start_a['start_year_a'] + 10

print(f"\nAbatement start year distribution (Method A):")
print(start_a['start_year_a'].value_counts().sort_index().to_string())
print(f"\nImplied sunset year distribution (Method A):")
print(start_a['sunset_year_a'].value_counts().sort_index().to_string())
missing_a = len(abated_set) - len(start_a)
print(f"\nParcels with no history found: {missing_a:,}")


# ── 3. Method B: L&I permits, one query ───────────────────────────────────────
print("\n── Method B: L&I permits (new construction, 2013–2024), 1 API call ──")

step += 1
bar(step, n_steps, "L&I permits...")
permits_sql = """
    SELECT parcel_id_num, permitissuedate, typeofwork, status
    FROM permits
    WHERE typeofwork = 'NEW CONSTRUCTION'
      AND permitissuedate >= '2013-01-01'
"""
permits_raw = carto(permits_sql)
bar(step, n_steps, f"permits done — {len(permits_raw):,} records")
print()

permits_raw['parcel_id_num'] = permits_raw['parcel_id_num'].astype(str).str.zfill(9)
permits_raw['permitissuedate'] = pd.to_datetime(permits_raw['permitissuedate'], errors='coerce')
permits_raw['permit_year'] = permits_raw['permitissuedate'].dt.year

# Filter to our abated set
permits_abated = permits_raw[permits_raw['parcel_id_num'].isin(abated_set)].copy()
print(f"Matched to abated parcels: {permits_abated['parcel_id_num'].nunique():,} unique parcels")

# Latest new construction permit per parcel
latest_permit = (
    permits_abated.sort_values('permitissuedate')
    .groupby('parcel_id_num').last()
    .reset_index()[['parcel_id_num', 'permit_year']]
    .rename(columns={'parcel_id_num': 'parcel_number', 'permit_year': 'start_year_b'})
)
latest_permit['sunset_year_b'] = latest_permit['start_year_b'] + 10

print(f"\nPermit year distribution (Method B):")
print(latest_permit['start_year_b'].value_counts().sort_index().to_string())
print(f"\nImplied sunset year distribution (Method B):")
print(latest_permit['sunset_year_b'].value_counts().sort_index().to_string())


# ── 4. Merge and reconcile ────────────────────────────────────────────────────
print("\n── Final merge ──")

result = pd.DataFrame({'parcel_number': sorted(abated_set)})
result = result.merge(start_a, on='parcel_number', how='left')
result = result.merge(latest_permit, on='parcel_number', how='left')

# Where both exist, compare them
both = result[result['start_year_a'].notna() & result['start_year_b'].notna()]
if len(both) > 0:
    diff = (both['start_year_b'] - both['start_year_a']).abs()
    print(f"Parcels with both methods: {len(both):,}")
    print(f"Method agreement (within 1 yr): {(diff <= 1).sum():,} ({(diff<=1).mean():.1%})")
    print(f"Mean absolute difference: {diff.mean():.1f} years")

# Best estimate: prefer Method B (permit date is more authoritative) where available
result['sunset_year'] = result['sunset_year_b'].fillna(result['sunset_year_a'])
result['method'] = 'none'
result.loc[result['sunset_year_a'].notna(), 'method'] = 'assessment_history'
result.loc[result['sunset_year_b'].notna(), 'method'] = 'permit'  # permit overwrites if available

print(f"\nCoverage by method:")
print(result['method'].value_counts().to_string())
print(f"\nFinal sunset year distribution:")
print(result['sunset_year'].value_counts().sort_index().to_string())
step += 1
bar(step, n_steps, "done!")
print()
print(f"\nNo sunset found: {result['sunset_year'].isna().sum():,} parcels")

out = DATA_DIR / 'abatement_sunsets.parquet'
result.to_parquet(out, index=False)
print(f"\nSaved → {out}")
print("Done.")
