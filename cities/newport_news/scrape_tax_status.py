"""Scrape the authoritative per-parcel `Tax Status` from the City of Newport News
CAMA public-access portal (assessment.nnva.gov) and cache it for the LVT model.

The GIS parcel layer (`Operational/Parcel` MapServer) carries no tax-exempt flag, but
each parcel's CAMA "Profile" page exposes a `Tax Status` field — `Taxable`, `City Owned`,
`State Government`, `Federal Government`, `Religious Organization`, `Fraternal Organization`,
or `Other Non-Taxable`. Any value other than `Taxable` is fully exempt.

Writes `data/tax_status.parquet` ([PARCELID, tax_status]). Resumable: re-running skips
PARCELIDs already in `data/tax_status_partial.csv` (except prior ERR/NOSTAT rows).

Usage:  python scrape_tax_status.py    (run from cities/newport_news/)
"""
import sys
import re
import time
from pathlib import Path
import requests
import pandas as pd
import geopandas as gpd
from concurrent.futures import ThreadPoolExecutor, as_completed

DATA = Path(__file__).resolve().parent / "data"
OUT = DATA / "tax_status.parquet"
PARTIAL = DATA / "tax_status_partial.csv"
URL = "https://assessment.nnva.gov/PT/datalets/datalet.aspx"
JUR, TAXYR, WORKERS = "700", "2026", 12

# Idempotent: if the complete cache already exists locally, do nothing.
# (Re-running the model reads data/tax_status.parquet directly; it never re-scrapes.)
# Pass --force to deliberately re-scrape from scratch.
if OUT.exists() and "--force" not in sys.argv:
    print(f"{OUT} already exists ({len(pd.read_parquet(OUT)):,} parcels) — skipping scrape. "
          f"Use --force to re-scrape.", flush=True)
    raise SystemExit(0)

pins = gpd.read_parquet(DATA / "parcels.gpq")["PARCELID"].astype(str).tolist()
done = {}
if PARTIAL.exists():
    prev = pd.read_csv(PARTIAL, dtype=str)
    done = dict(zip(prev["PARCELID"], prev["tax_status"]))
todo = [p for p in pins if p not in done or done[p] in ("ERR", "NOSTAT")]
print(f"{len(pins):,} parcels total; {len(done):,} cached; {len(todo):,} to fetch", flush=True)

sess = requests.Session()
sess.headers.update({"User-Agent": "Mozilla/5.0 (CLE LVTShift research)"})


def fetch(pin: str):
    for attempt in range(3):
        try:
            r = sess.get(URL, params={"mode": "profileall", "UseSearch": "no",
                         "pin": pin, "jur": JUR, "taxyr": TAXYR}, timeout=30)
            h = r.text
            i = h.lower().find("tax status")
            if i < 0:
                return pin, "NOSTAT"
            seg = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h[i:i + 220])).strip()
            m = re.match(r"tax status\s+(.*?)\s+neighborhood", seg, re.I)
            val = (m.group(1).strip() if m else seg[11:60].strip())
            return pin, (val if val else "&nbsp;")
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return pin, "ERR"


results, n, t0 = dict(done), 0, time.time()
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = {ex.submit(fetch, p): p for p in todo}
    for f in as_completed(futs):
        pin, val = f.result()
        results[pin] = val
        n += 1
        if n % 1000 == 0:
            pd.DataFrame(list(results.items()), columns=["PARCELID", "tax_status"]).to_csv(PARTIAL, index=False)
            rate = n / (time.time() - t0)
            print(f"  {n:,}/{len(todo):,} ({rate:.0f}/s, ~{(len(todo) - n) / rate / 60:.1f} min left)", flush=True)

df = pd.DataFrame(list(results.items()), columns=["PARCELID", "tax_status"])
df.to_csv(PARTIAL, index=False)
df.to_parquet(OUT)
print(f"DONE: {len(df):,} parcels -> {OUT}; errors={df['tax_status'].isin(['ERR', 'NOSTAT']).sum()}", flush=True)
print(df["tax_status"].value_counts(dropna=False).to_string(), flush=True)
