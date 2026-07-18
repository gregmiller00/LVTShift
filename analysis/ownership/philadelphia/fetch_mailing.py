import io
import sys
import urllib.parse
from pathlib import Path

import pandas as pd
import requests

sys.stdout.reconfigure(encoding='utf-8')
OUT = Path(__file__).parent / 'opa_mailing.parquet'

q = ('SELECT parcel_number, mailing_street, mailing_address_1, mailing_address_2, '
     'mailing_care_of, mailing_city_state, mailing_zip, location '
     'FROM opa_properties_public')
url = f'https://phl.carto.com/api/v2/sql?q={urllib.parse.quote(q)}&format=csv'
print('Downloading mailing address fields from Carto...')
r = requests.get(url, timeout=300)
r.raise_for_status()
m = pd.read_csv(io.StringIO(r.text), low_memory=False, dtype=str)
print(f'{len(m):,} rows')
for c in m.columns:
    print(f'  {c}: {m[c].notna().mean():.1%} non-null')
m.to_parquet(OUT)
print(f'Saved to {OUT}')
