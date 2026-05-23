"""Generate the Des Moines tax-district sidecar parquet.

For each DM parcel, this script computes:
- school_district     (from Polk Auditor layer 75)
- ssmid               (from Polk Auditor layer 80, or None)
- urban_sanitary      (from Polk Auditor layer 72 if it overlaps; flags URB WIND-HTS)
- in_tif              (from Polk Auditor layer 141)
- tif_district        (TIF district name if in_tif, else None)
- tax_district_name   (derived combo matching Iowa DoM's published district name)
- tax_district_code   (6-digit Iowa DoM code from the FY26 consolidated levy PDF)
- consolidated_millage (FY26 rate in mills per $1000 of taxable value)

Sources:
- Polk County Auditor ArcGIS (Auditor_Export FeatureServer)
- FY 2025-26 Consolidated Tax Levy Rates for Polk County, published by Polk County Auditor
  (2024 Assessed Valuations - Taxes Payable Sep 2025 and March 2026)
  https://www.polkcountyiowa.gov/county-auditor/property-tax/tax-rate-and-valuation-information/

Output: examples/data/des_moines/des_moines_districts_<DATE>.parquet
(matches the dated naming used by run_des_moines.py).

Run once when rates change (annually) or when redistricting happens.
Inputs are the same parcel parquet the LVTShift notebooks consume.
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import shape


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "examples" / "data" / "des_moines"

POLK_BASE = "https://gis4.polkcountyiowa.gov/server/rest/services/Auditor/Auditor_Export/FeatureServer"
LAYER_SCHOOL_DISTRICTS = 75
LAYER_SSMID = 80
LAYER_SANITARY = 72
LAYER_TIF = 141


# FY 2025-26 (AY 2024) Polk County consolidated tax levies. Mills per $1000.
# Source: polkcountyiowa.gov consolidated-tax-rates.pdf, dated 2025-07-29.
# Only Des Moines City districts (non-AG) are listed — the parcel parquet
# is already clipped to the DM corporate limits. AG districts (lower city
# rate ~3 mills) cover a handful of large agricultural-classed parcels;
# we use the non-AG rate as default and adjust for ag-class parcels in
# the notebook's rollback step rather than via a separate district code.
DM_TAX_DISTRICTS_FY26: dict[str, tuple[str, float]] = {
    # key: tax_district_name string derived from (school, ssmid, urban_sanitary)
    # value: (Iowa DoM code, consolidated millage)
    "DES MOINES CITY/CARLISLE SCH":                       ("770248", 45.64371),
    "DES MOINES CITY/DM SCH":                             ("770131", 42.32446),
    "DES MOINES CITY/DM SCH/BEAVERDALE SSMID":            ("770214", 44.07449),
    "DES MOINES CITY/DM SCH/DOWNTOWN SSMID":              ("770434", 43.62446),
    "DES MOINES CITY/DM SCH/HIGHLAND PARK SSMID":         ("770639", 44.57446),
    "DES MOINES CITY/DM SCH/INGERSOLL GRAND SSMID":       ("770696", 44.57446),
    "DES MOINES CITY/DM SCH/ROOSEVELT CULTURAL SSMID":    ("770151", 44.07449),
    "DES MOINES CITY/DM SCH/SHERMAN HILL SSMID":          ("770435", 43.82446),
    "DES MOINES CITY/DM SCH/SW 9TH CORRIDOR SSMID":       ("770146", 44.57445),
    "DES MOINES CITY/DM SCH/URB WIND-HTS SS":             ("770132", 42.71722),
    "DES MOINES CITY/JOHNSTON SCH":                       ("770137", 42.63106),
    "DES MOINES CITY/JOHNSTON SCH/URB SS":                ("770149", 42.84550),
    "DES MOINES CITY/SAYDEL SCH":                         ("770139", 40.44770),
    "DES MOINES CITY/SE-POLK SCH":                        ("770152", 43.13744),
    "DES MOINES CITY/URB SCH":                            ("770947", 45.65041),
    "DES MOINES CITY/URB SCH/URB WIND-HTS SS":            ("771141", 46.04317),
    "DES MOINES CITY/WDM SCH":                            ("770250", 39.93169),
}

DEFAULT_TAX_DISTRICT_KEY = "DES MOINES CITY/DM SCH"  # used when overlay can't resolve


# Polk's school district `Name` field is short ("Des Moines", "Saydel", ...).
# Normalize to the abbreviated form used in the PDF tax-district names.
SCHOOL_NAME_TO_PDF: dict[str, str] = {
    "DES MOINES":              "DM SCH",
    "JOHNSTON":                "JOHNSTON SCH",
    "SAYDEL":                  "SAYDEL SCH",
    "SOUTHEAST POLK":          "SE-POLK SCH",
    "WEST DES MOINES":         "WDM SCH",
    "CARLISLE":                "CARLISLE SCH",
    "URBANDALE":               "URB SCH",
    "BONDURANT - FARRAR":      "BOND-FARR SCH",
    "NORTH POLK":              "N-POLK SCH",
}


# SSMID `Description` reads "DES MOINES SSMID N <NAME>"; pull the trailing name.
SSMID_NAME_TO_PDF: dict[str, str] = {
    "DES MOINES SSMID 1 DOWNTOWN":            "DOWNTOWN SSMID",
    "DES MOINES SSMID 2 SHERMAN HILL":        "SHERMAN HILL SSMID",
    "DES MOINES SSMID 4 HIGHLAND PARK":       "HIGHLAND PARK SSMID",
    "DES MOINES SSMID 5 INGERSOLL GRAND":     "INGERSOLL GRAND SSMID",
    "DES MOINES SSMID 6 BEAVERDALE":          "BEAVERDALE SSMID",
    "DES MOINES SSMID 7 SW 9TH CORRIDOR":     "SW 9TH CORRIDOR SSMID",
    "DES MOINES SSMID 8 ROOSEVELT CULTURAL":  "ROOSEVELT CULTURAL SSMID",
}


# Sanitary `Name` → PDF urban-sanitary label (only entries that appear in the
# FY26 rate table; most parcels are not in an urban-sanitary district).
SANITARY_NAME_TO_PDF: dict[str, str] = {
    "URBANDALE SANITARY SEWER":         "URB SS",
    "URBANDALE/WINDS HTS SAN SEWER":    "URB WIND-HTS SS",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Build the Des Moines tax-district sidecar parquet "
                     "(school + SSMID + urban-sanitary + TIF overlays, "
                     "joined to the Iowa DoM consolidated levy table for FY26).")
    )
    parser.add_argument(
        "--parcels",
        type=Path,
        default=None,
        help=("Path to the DM parcels parquet. Defaults to the newest "
              "des_moines_mapping_ready_*.parquet in examples/data/des_moines/."),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output sidecar parquet path (default: dated file in same dir).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# ArcGIS fetch
# ---------------------------------------------------------------------------

def _arcgis_features(layer_id: int, where: str = "1=1", out_fields: str = "*") -> gpd.GeoDataFrame:
    """Pull all features from a Polk Auditor_Export layer as a GeoDataFrame."""
    url = f"{POLK_BASE}/{layer_id}/query"
    all_features: list = []
    offset = 0
    page_size = 2000
    while True:
        params = {
            "f": "geojson",
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "true",
            "outSR": 4326,
            "resultOffset": offset,
            "resultRecordCount": page_size,
        }
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        features = payload.get("features", [])
        if not features:
            break
        all_features.extend(features)
        if len(features) < page_size:
            break
        offset += len(features)
        time.sleep(0.1)

    if not all_features:
        return gpd.GeoDataFrame()
    return gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")


# ---------------------------------------------------------------------------
# Per-parcel district assignment
# ---------------------------------------------------------------------------

def _normalize(s: object) -> str:
    if s is None:
        return ""
    return " ".join(str(s).strip().upper().split())


def _assign_via_overlay(
    parcels: gpd.GeoDataFrame,
    layer: gpd.GeoDataFrame,
    name_field: str,
    out_col: str,
    label_lookup: Optional[dict[str, str]] = None,
) -> gpd.GeoDataFrame:
    """For each parcel, set `out_col` to the name of the overlay polygon that
    contains its representative point. If multiple overlay polygons match,
    keep the first. If none, value is None.
    """
    if layer.empty:
        parcels = parcels.copy()
        parcels[out_col] = None
        return parcels
    layer = layer.rename(columns={name_field: "_overlay_name"})
    layer = layer[["geometry", "_overlay_name"]].copy()

    parcels = parcels.copy()
    rep_pts = parcels.geometry.representative_point()
    rep_gdf = gpd.GeoDataFrame({"_pid": parcels["parcel_id"].values}, geometry=rep_pts, crs=parcels.crs)
    joined = gpd.sjoin(rep_gdf, layer, how="left", predicate="within")
    joined = joined.drop_duplicates(subset=["_pid"], keep="first")
    name_by_pid = dict(zip(joined["_pid"], joined["_overlay_name"]))
    raw_names = parcels["parcel_id"].map(name_by_pid)

    if label_lookup is not None:
        parcels[out_col] = raw_names.apply(lambda v: label_lookup.get(_normalize(v)))
    else:
        parcels[out_col] = raw_names
    return parcels


def _compose_tax_district_name(row: pd.Series) -> str:
    """Combine school + ssmid + urban_sanitary into the PDF-matching label."""
    school = row.get("school_district_pdf")
    ssmid = row.get("ssmid_pdf")
    sanitary = row.get("urban_sanitary_pdf")
    if not school:
        return DEFAULT_TAX_DISTRICT_KEY

    parts = ["DES MOINES CITY", school]
    # A parcel can be in either an SSMID or an urban-sanitary district in the
    # FY26 table, never both. Prefer SSMID (the PDF orders this way).
    if ssmid:
        parts.append(ssmid)
    elif sanitary:
        parts.append(sanitary)
    return "/".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    if args.parcels is None:
        candidates = sorted(DATA_DIR.glob("des_moines_mapping_ready_*.parquet"))
        if not candidates:
            raise FileNotFoundError(f"No mapping_ready parquet found in {DATA_DIR}")
        parcels_path = candidates[-1]
    else:
        parcels_path = args.parcels

    print(f"Loading parcels: {parcels_path}")
    parcels = gpd.read_parquet(parcels_path)
    print(f"  {len(parcels):,} parcels")

    print("Fetching Polk School_Districts (layer 75)...")
    schools = _arcgis_features(LAYER_SCHOOL_DISTRICTS)
    print(f"  {len(schools)} school district polygons")

    print("Fetching Polk SSMID_Districts (layer 80)...")
    ssmids = _arcgis_features(LAYER_SSMID)
    ssmid_name_col = "Description" if "Description" in ssmids.columns else "Name"
    print(f"  {len(ssmids)} SSMID polygons (name field: {ssmid_name_col})")

    print("Fetching Polk Sanitary_Sewer_Districts (layer 72)...")
    sanitary = _arcgis_features(LAYER_SANITARY)
    print(f"  {len(sanitary)} sanitary sewer polygons")

    print("Fetching Polk TIF_Districts (layer 141)...")
    tifs = _arcgis_features(LAYER_TIF)
    print(f"  {len(tifs)} TIF polygons")

    print("Assigning overlays...")
    parcels = _assign_via_overlay(
        parcels, schools, name_field="Name",
        out_col="school_district_pdf", label_lookup=SCHOOL_NAME_TO_PDF,
    )
    parcels = _assign_via_overlay(
        parcels, ssmids, name_field=ssmid_name_col,
        out_col="ssmid_pdf", label_lookup=SSMID_NAME_TO_PDF,
    )
    parcels = _assign_via_overlay(
        parcels, sanitary, name_field="Name",
        out_col="urban_sanitary_pdf", label_lookup=SANITARY_NAME_TO_PDF,
    )
    parcels = _assign_via_overlay(
        parcels, tifs, name_field="Area_Name",
        out_col="tif_district",
    )
    parcels["in_tif"] = parcels["tif_district"].notna().astype(int)

    parcels["tax_district_name"] = parcels.apply(_compose_tax_district_name, axis=1)
    parcels["tax_district_code"] = parcels["tax_district_name"].map(
        lambda k: DM_TAX_DISTRICTS_FY26.get(k, DM_TAX_DISTRICTS_FY26[DEFAULT_TAX_DISTRICT_KEY])[0]
    )
    parcels["consolidated_millage"] = parcels["tax_district_name"].map(
        lambda k: DM_TAX_DISTRICTS_FY26.get(k, DM_TAX_DISTRICTS_FY26[DEFAULT_TAX_DISTRICT_KEY])[1]
    )

    print()
    print("Tax district distribution:")
    print(parcels["tax_district_name"].value_counts(dropna=False).to_string())
    print()
    print(f"Parcels in a TIF: {int(parcels['in_tif'].sum()):,}  ({parcels['in_tif'].mean()*100:.1f}%)")
    print()
    print("School district distribution (PDF-normalized):")
    print(parcels["school_district_pdf"].value_counts(dropna=False).to_string())
    print()
    print(f"Mean consolidated millage: {parcels['consolidated_millage'].mean():.4f}")

    sidecar_cols = [
        "parcel_id",
        "school_district_pdf",
        "ssmid_pdf",
        "urban_sanitary_pdf",
        "in_tif",
        "tif_district",
        "tax_district_name",
        "tax_district_code",
        "consolidated_millage",
    ]
    sidecar = parcels[sidecar_cols].copy()

    today = datetime.now().strftime("%Y_%m_%d")
    out_path = args.out or (DATA_DIR / f"des_moines_districts_{today}.parquet")
    sidecar.to_parquet(out_path, index=False)
    print()
    print(f"Wrote sidecar: {out_path} ({len(sidecar):,} rows, {len(sidecar.columns)} cols)")


if __name__ == "__main__":
    main()
