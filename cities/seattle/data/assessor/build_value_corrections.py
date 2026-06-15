"""Build reliable commercial building-value corrections for the Seattle parcel extract.

Problem: the King County parcel layer (and the Assessor's Real Property Account roll) record
a ~$1,000 placeholder improvement value for many income-producing commercial parcels (retail,
restaurant, office, warehouse, etc.) whose building value is carried off-parcel (leasehold /
personal-property accounts). This leaves the parcels looking like bare land and distorts any
land-vs-building analysis.

Fix (cost approach): for parcels that have a real building (Commercial Building file square
footage) but a placeholder value AND are taxable, impute improvement value =
  building net sqft  ×  median $/sqft observed for comparable Seattle buildings (by use),
calibrated only on parcels that have BOTH real sqft and a real assessed value.

Outputs `seattle_value_corrections.parquet` (PIN, imputed_tax_impr, sqft, psf, use, method),
consumed by cities/seattle/model.ipynb. Sources (King County Assessor data download, 2026 roll):
  EXTR_RPAcct_NoName.csv  — appraised/taxable land & improvement per account
  EXTR_CommBldg.csv       — commercial building square footage & use per account
"""
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SEA = HERE.parent  # cities/seattle/data

PLACEHOLDER_MAX = 1_000     # improvement values <= this are treated as placeholders
MIN_SQFT = 500              # a "real" building
PSF_LO, PSF_HI = 20, 2000   # trim implausible $/sqft when calibrating

# --- Commercial Building: net sqft + predominant use per PIN ---
cb = pd.read_csv(HERE / "EXTR_CommBldg.csv", encoding="latin-1",
                 usecols=["Major", "Minor", "PredominantUse", "BldgNetSqFt", "BldgGrossSqFt"],
                 dtype={"Major": str, "Minor": str})
cb["PIN"] = cb["Major"].str.zfill(6) + cb["Minor"].str.zfill(4)
for c in ["BldgNetSqFt", "BldgGrossSqFt", "PredominantUse"]:
    cb[c] = pd.to_numeric(cb[c], errors="coerce")
cb["sqft"] = cb["BldgNetSqFt"].where(cb["BldgNetSqFt"] > 0, cb["BldgGrossSqFt"]).fillna(0)
cbp = cb.groupby("PIN").agg(sqft=("sqft", "sum"),
                            use=("PredominantUse", lambda s: s.mode().iloc[0] if len(s.mode()) else np.nan))

# --- Real Property Account: value + taxable status per PIN ---
rp = pd.read_parquet(HERE / "rpacct_slim.parquet")
rp["taxable"] = (rp["TaxStat"].astype(str).str.strip() == "T")
rp_pin = rp.groupby("PIN").agg(Imp=("ApprImpsVal", "sum"), Land=("ApprLandVal", "sum"),
                               any_taxable=("taxable", "max"))

# --- Seattle parcels (the modeled universe) ---
g = pd.read_parquet(SEA / "seattle_parcels_2025_11_20.parquet")
g = g[g["LEVY_JURIS"] == "SEATTLE"].copy()
g["PIN"] = g["PIN"].astype(str).str.zfill(10)
for c in ["TAX_LNDVAL", "TAX_IMPR"]:
    g[c] = pd.to_numeric(g[c], errors="coerce").fillna(0)

j = (g[["PIN", "PREUSE_DESC", "TAX_LNDVAL", "TAX_IMPR"]]
     .merge(cbp, left_on="PIN", right_index=True, how="left")
     .merge(rp_pin, left_on="PIN", right_index=True, how="left"))
j["sqft"] = j["sqft"].fillna(0)

# --- Calibrate $/sqft on parcels with BOTH a real value and real sqft ---
cal = j[(j["Imp"] > 20_000) & (j["sqft"] > MIN_SQFT)].copy()
cal["psf"] = cal["Imp"] / cal["sqft"]
cal = cal[(cal["psf"] > PSF_LO) & (cal["psf"] < PSF_HI)]
psf_by_use = cal.groupby("use")["psf"].median()
psf_overall = float(cal["psf"].median())

# --- Correction targets: placeholder value + real building + TAXABLE (exclude exempt) ---
target = j[(j["TAX_IMPR"] <= PLACEHOLDER_MAX) & (j["sqft"] > MIN_SQFT)
           & (j["TAX_LNDVAL"] > 0) & (j["any_taxable"] == True)].copy()
target["psf"] = target["use"].map(psf_by_use).fillna(psf_overall)
target["imputed_tax_impr"] = (target["sqft"] * target["psf"]).round().astype("int64")
target["method"] = "cost_approach_sqft"

out = target[["PIN", "imputed_tax_impr", "sqft", "psf", "use", "method"]].reset_index(drop=True)
out.to_parquet(HERE.parent / "seattle_value_corrections.parquet")

print(f"calibration parcels: {len(cal):,}  | overall median $/sqft: ${psf_overall:.0f}")
print(f"correction targets (placeholder + real building + taxable): {len(out):,}")
print(f"imputed improvement total: ${out['imputed_tax_impr'].sum()/1e9:.2f}B  "
      f"(median ${out['imputed_tax_impr'].median():,.0f})")
base = (g['TAX_LNDVAL'] + g['TAX_IMPR']).sum()
added = out['imputed_tax_impr'].sum() - (target['TAX_IMPR'].sum())  # net of the $1k placeholders removed
print(f"Seattle taxable base: ${base/1e9:.1f}B  ->  ${(base+added)/1e9:.1f}B  (certified ~$286.2B)")
print(f"wrote {(HERE.parent / 'seattle_value_corrections.parquet')}")
