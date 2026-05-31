"""
One-shot patch script: fix failing cities and harmonize model parameters.

Run with: python scripts/patch_notebooks.py
Re-run safely — patches are idempotent.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CITIES_DIR = REPO_ROOT / "cities"


def load_nb(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_nb(path, nb):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"  saved {path.relative_to(REPO_ROOT)}")


def cell_source(cell):
    src = cell.get("source", [])
    return "".join(src) if isinstance(src, list) else src


def set_cell_source(cell, new_src):
    """Replace cell source, preserving list-of-lines format."""
    if isinstance(cell.get("source"), list):
        lines = new_src.splitlines(keepends=True)
        cell["source"] = lines
    else:
        cell["source"] = new_src


def patch_cells(nb, replacements):
    """Apply (old_str, new_str) replacements across all code cells. Returns change count."""
    changes = 0
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = cell_source(cell)
        new_src = src
        for old, new in replacements:
            if old in new_src:
                new_src = new_src.replace(old, new)
                changes += 1
        if new_src != src:
            set_cell_source(cell, new_src)
    return changes


# ---------------------------------------------------------------------------
# 1. Runner: also patch scrape_data = 0 -> 1 (bellingham/spokane use this name)
# ---------------------------------------------------------------------------
def fix_runner():
    runner = REPO_ROOT / "scripts" / "run_all_cities.py"
    src = runner.read_text(encoding="utf-8")
    old = '        if "data_scrape = 0" in src:'
    new = '        if "data_scrape = 0" in src or "scrape_data = 0" in src:'
    old2 = '            new_src = src.replace("data_scrape = 0", "data_scrape = 1")'
    new2 = (
        '            new_src = src.replace("data_scrape = 0", "data_scrape = 1")\n'
        '            new_src = new_src.replace("scrape_data = 0", "scrape_data = 1")'
    )
    if old in src:
        src = src.replace(old, new).replace(old2, new2)
        runner.write_text(src, encoding="utf-8")
        print("  runner: patched scrape_data detection")
    else:
        print("  runner: already patched or pattern not found")


# ---------------------------------------------------------------------------
# 2. Bellingham: fall through to scrape when no cache exists
# ---------------------------------------------------------------------------
def fix_bellingham():
    path = CITIES_DIR / "bellingham" / "model.ipynb"
    nb = load_nb(path)
    old = '    if not files:\n        raise FileNotFoundError("No previously scraped parcel files found in data/bellingham/")'
    new = (
        '    if not files:\n'
        '        # No cache — scrape fresh\n'
        '        parcel_civic_df = get_bellingham_parcels()\n'
        '        today_str = datetime.now().strftime("%Y_%m_%d")\n'
        '        out_path = os.path.join(data_dir, f"bellingham_parcels_{today_str}.parquet")\n'
        '        parcel_civic_df.to_parquet(out_path, index=False)\n'
        '        print(f"No cache found — scraped and saved to {out_path}")'
    )
    n = patch_cells(nb, [(old, new)])
    if n:
        save_nb(path, nb)
        print(f"  bellingham: fixed scrape fallthrough ({n} cell(s))")
    else:
        print("  bellingham: pattern not found (already fixed?)")


# ---------------------------------------------------------------------------
# 3. Spokane: same fix
# ---------------------------------------------------------------------------
def fix_spokane():
    path = CITIES_DIR / "spokane" / "model.ipynb"
    nb = load_nb(path)
    old = '    if not files:\n        raise FileNotFoundError("No previously scraped parcel files found in data/spokane/")'
    new = (
        '    if not files:\n'
        '        # No cache — scrape fresh\n'
        '        base_url = "https://services1.arcgis.com/ozNll27nt9ZtPWOn/ArcGIS/rest/services/"\n'
        '        parcel_civic_df = get_feature_data_with_geometry(\'Parcels\', base_url, paginate=True)\n'
        '        today_str = datetime.now().strftime("%Y_%m_%d")\n'
        '        out_path = os.path.join(data_dir, f"spokane_parcels_{today_str}.parquet")\n'
        '        parcel_civic_df.to_parquet(out_path, index=False)\n'
        '        print(f"No cache found — scraped and saved to {out_path}")'
    )
    n = patch_cells(nb, [(old, new)])
    if n:
        save_nb(path, nb)
        print(f"  spokane: fixed scrape fallthrough ({n} cell(s))")
    else:
        print("  spokane: pattern not found (already fixed?)")


# ---------------------------------------------------------------------------
# 4. Bryan + college_station: fix invalid regex in str.contains
# ---------------------------------------------------------------------------
def fix_regex_cities():
    for city in ("bryan", "college_station"):
        path = CITIES_DIR / city / "model.ipynb"
        nb = load_nb(path)
        # r'\bEX[-\b]' is invalid — \b inside [] is backspace, not word boundary
        # Intent: match exemption codes like "EX-XV". Fix: r'\bEX-'
        n = patch_cells(nb, [(r"r'\bEX[-\b]'", r"r'\bEX-'")])
        if n:
            save_nb(path, nb)
            print(f"  {city}: fixed str.contains regex ({n} cell(s))")
        else:
            print(f"  {city}: regex pattern not found (already fixed?)")


# ---------------------------------------------------------------------------
# 5. Cincinnati: add auto-scrape when parquet not found
# ---------------------------------------------------------------------------
def fix_cincinnati():
    path = CITIES_DIR / "cincinnati" / "model.ipynb"
    nb = load_nb(path)

    # Replace the hardcoded PARCEL_PATH with a dynamic lookup + scrape fallback
    old = "PARCEL_PATH = DATA_DIR / 'cincinnati_20260119.gpq'"
    new = (
        "# Find most recent cached parcel file, or scrape fresh if none exists\n"
        "_cin_files = sorted(DATA_DIR.glob('cincinnati_*.gpq'), reverse=True)\n"
        "if not _cin_files:\n"
        "    print('No cached Cincinnati parcels found — scraping from Hamilton County ArcGIS...')\n"
        "    from lvt.cloud_utils import get_feature_data_with_geometry\n"
        "    from datetime import datetime as _dt\n"
        "    _cin_gdf = get_feature_data_with_geometry(\n"
        "        'CAGIS_Open_Data', 'https://services.arcgis.com/JyZag7oO4NteHGiq/ArcGIS/rest/services', 12, paginate=True\n"
        "    )\n"
        "    _cin_date = _dt.now().strftime('%Y%m%d')\n"
        "    _cin_path = DATA_DIR / f'cincinnati_{_cin_date}.gpq'\n"
        "    _cin_gdf.to_parquet(_cin_path)\n"
        "    print(f'Saved {len(_cin_gdf):,} parcels to {_cin_path}')\n"
        "    _cin_files = [_cin_path]\n"
        "PARCEL_PATH = _cin_files[0]"
    )
    n = patch_cells(nb, [(old, new)])
    if n:
        save_nb(path, nb)
        print(f"  cincinnati: added auto-scrape fallback ({n} cell(s))")
    else:
        print("  cincinnati: pattern not found (already fixed?)")


# ---------------------------------------------------------------------------
# 6. Fort Collins: skip missing manual override CSV gracefully
# ---------------------------------------------------------------------------
def fix_fort_collins():
    path = CITIES_DIR / "fort_collins" / "model.ipynb"
    nb = load_nb(path)
    old = (
        'manual_override_path = data_dir / "larimer_manual_school_assessed_value_overrides_2026-03-31.csv"\n'
        'manual_school_overrides = pd.read_csv(\n'
        '    manual_override_path,\n'
        '    usecols=["accountno", "live_api_improvement_school_assessed_value"],\n'
        ')\n'
        'manual_school_overrides["SCHEDULENUM"] = pd.to_numeric(\n'
        '    manual_school_overrides["accountno"].str.replace("R", "", regex=False),\n'
        '    errors="coerce",\n'
        ').astype("Int64")\n'
        'manual_school_overrides["live_api_improvement_school_assessed_value"] = pd.to_numeric(\n'
        '    manual_school_overrides["live_api_improvement_school_assessed_value"],\n'
        '    errors="coerce",\n'
        ')\n'
        'manual_school_override_map = (\n'
        '    manual_school_overrides.dropna(subset=["SCHEDULENUM", "live_api_improvement_school_assessed_value"])\n'
        '    .drop_duplicates(subset=["SCHEDULENUM"])\n'
        '    .set_index("SCHEDULENUM")["live_api_improvement_school_assessed_value"]\n'
        ')'
    )
    new = (
        'manual_override_path = data_dir / "larimer_manual_school_assessed_value_overrides_2026-03-31.csv"\n'
        'if manual_override_path.exists():\n'
        '    manual_school_overrides = pd.read_csv(\n'
        '        manual_override_path,\n'
        '        usecols=["accountno", "live_api_improvement_school_assessed_value"],\n'
        '    )\n'
        '    manual_school_overrides["SCHEDULENUM"] = pd.to_numeric(\n'
        '        manual_school_overrides["accountno"].str.replace("R", "", regex=False),\n'
        '        errors="coerce",\n'
        '    ).astype("Int64")\n'
        '    manual_school_overrides["live_api_improvement_school_assessed_value"] = pd.to_numeric(\n'
        '        manual_school_overrides["live_api_improvement_school_assessed_value"],\n'
        '        errors="coerce",\n'
        '    )\n'
        '    manual_school_override_map = (\n'
        '        manual_school_overrides.dropna(subset=["SCHEDULENUM", "live_api_improvement_school_assessed_value"])\n'
        '        .drop_duplicates(subset=["SCHEDULENUM"])\n'
        '        .set_index("SCHEDULENUM")["live_api_improvement_school_assessed_value"]\n'
        '    )\n'
        '    print(f"Loaded {len(manual_school_override_map)} manual school assessed value overrides.")\n'
        'else:\n'
        '    print("Manual school override file not found — skipping overrides.")\n'
        '    manual_school_override_map = pd.Series(dtype=float)'
    )
    n = patch_cells(nb, [(old, new)])
    if n:
        save_nb(path, nb)
        print(f"  fort_collins: wrapped manual CSV in try/exists check ({n} cell(s))")
    else:
        print("  fort_collins: pattern not found (already fixed?)")


# ---------------------------------------------------------------------------
# 7. Highlands Ranch + Pueblo: 2:1 -> 4:1, fix model_type string
# ---------------------------------------------------------------------------
def fix_ratio_2to4(city):
    path = CITIES_DIR / city / "model.ipynb"
    nb = load_nb(path)
    replacements = [
        ("LAND_IMPROVEMENT_RATIO = 2.0", "LAND_IMPROVEMENT_RATIO = 4.0"),
        ("MODEL_TYPE = 'split_rate_2to1'", "MODEL_TYPE = 'split_rate:4.0'"),
        ('MODEL_TYPE = "split_rate_2to1"', 'MODEL_TYPE = "split_rate:4.0"'),
    ]
    n = patch_cells(nb, replacements)
    if n:
        save_nb(path, nb)
        print(f"  {city}: changed ratio 2:1 -> 4:1, fixed MODEL_TYPE ({n} cell(s))")
    else:
        print(f"  {city}: patterns not found (already fixed?)")


# ---------------------------------------------------------------------------
# 8. Rochester + Syracuse: 10:1 -> 4:1, fix model_type string
# ---------------------------------------------------------------------------
def fix_rochester():
    path = CITIES_DIR / "rochester" / "model.ipynb"
    nb = load_nb(path)
    replacements = [
        ("land_improvement_ratio=10,", "land_improvement_ratio=4,"),
        ("land_improvement_ratio=10)", "land_improvement_ratio=4)"),
        ("model_type='split_rate:10.0'", "model_type='split_rate:4.0'"),
        ('model_type="split_rate:10.0"', 'model_type="split_rate:4.0"'),
    ]
    n = patch_cells(nb, replacements)
    if n:
        save_nb(path, nb)
        print(f"  rochester: changed ratio 10:1 -> 4:1, fixed model_type ({n} cell(s))")
    else:
        print("  rochester: patterns not found (already fixed?)")


def fix_syracuse():
    path = CITIES_DIR / "syracuse" / "model.ipynb"
    nb = load_nb(path)
    replacements = [
        ("land_improvement_ratio=10,", "land_improvement_ratio=4,"),
        ("land_improvement_ratio=10)", "land_improvement_ratio=4)"),
        ("model_type='split_rate:10.0'", "model_type='split_rate:4.0'"),
        ('model_type="split_rate:10.0"', 'model_type="split_rate:4.0"'),
    ]
    n = patch_cells(nb, replacements)
    if n:
        save_nb(path, nb)
        print(f"  syracuse: changed ratio 10:1 -> 4:1, fixed model_type ({n} cell(s))")
    else:
        print("  syracuse: patterns not found (already fixed?)")


# ---------------------------------------------------------------------------
# 9. Greeley: fix model_type string (ratio already 4:1, just cosmetic)
# ---------------------------------------------------------------------------
def fix_greeley_model_type():
    path = CITIES_DIR / "greeley" / "model.ipynb"
    nb = load_nb(path)
    replacements = [
        ("MODEL_TYPE = 'split_rate_4to1'", "MODEL_TYPE = 'split_rate:4.0'"),
        ('MODEL_TYPE = "split_rate_4to1"', 'MODEL_TYPE = "split_rate:4.0"'),
    ]
    n = patch_cells(nb, replacements)
    if n:
        save_nb(path, nb)
        print(f"  greeley: fixed MODEL_TYPE string ({n} cell(s))")
    else:
        print("  greeley: MODEL_TYPE pattern not found (already fixed?)")


# ---------------------------------------------------------------------------
# 10. Fort Collins: skip propinfo script if missing, use 4:1 for export
# ---------------------------------------------------------------------------
def fix_fort_collins_propinfo_and_ratio():
    path = CITIES_DIR / "fort_collins" / "model.ipynb"
    nb = load_nb(path)

    # Fix 1: wrap propinfo script call in an existence check
    old_propinfo = (
        "if BUILD_PROPINFO_CACHE or not propinfo_cache_path.exists():\n"
        "    subprocess.run(\n"
        "        [\n"
        "            sys.executable,\n"
        "            str(propinfo_builder_script),\n"
        "            \"--cache-path\",\n"
        "            str(propinfo_cache_path),\n"
        "        ],\n"
        "        check=True,\n"
        "        cwd=REPO_ROOT,\n"
        "    )\n"
        "\n"
        "propinfo_df = pd.read_csv(propinfo_cache_path)\n"
        "propinfo_df = propinfo_df[propinfo_df[\"tax_year\"] == tax_year].copy()\n"
        "fort_collins = fort_collins.merge(propinfo_df, on=\"SCHEDULENUM\", how=\"left\")\n"
        "fort_collins[[\"OWNER_TAX_LIABILITY\", \"STATE_TAX_LIABILITY\"]] = fort_collins[[\"OWNER_TAX_LIABILITY\", \"STATE_TAX_LIABILITY\"]].fillna(0)\n"
        "fort_collins[\"full_tax_bill\"] = fort_collins[\"OWNER_TAX_LIABILITY\"] + fort_collins[\"STATE_TAX_LIABILITY\"]\n"
        "fort_collins[\"owner_tax_share\"] = np.where(\n"
        "    fort_collins[\"full_tax_bill\"] > 0,\n"
        "    fort_collins[\"OWNER_TAX_LIABILITY\"] / fort_collins[\"full_tax_bill\"],\n"
        "    1.0,\n"
        ")\n"
        "fort_collins[\"state_tax_relief_pct\"] = 1.0 - fort_collins[\"owner_tax_share\"]"
    )
    new_propinfo = (
        "if propinfo_builder_script.exists() and (BUILD_PROPINFO_CACHE or not propinfo_cache_path.exists()):\n"
        "    subprocess.run(\n"
        "        [\n"
        "            sys.executable,\n"
        "            str(propinfo_builder_script),\n"
        "            \"--cache-path\",\n"
        "            str(propinfo_cache_path),\n"
        "        ],\n"
        "        check=True,\n"
        "        cwd=REPO_ROOT,\n"
        "    )\n"
        "\n"
        "if propinfo_cache_path.exists():\n"
        "    propinfo_df = pd.read_csv(propinfo_cache_path)\n"
        "    propinfo_df = propinfo_df[propinfo_df[\"tax_year\"] == tax_year].copy()\n"
        "    fort_collins = fort_collins.merge(propinfo_df, on=\"SCHEDULENUM\", how=\"left\")\n"
        "    fort_collins[[\"OWNER_TAX_LIABILITY\", \"STATE_TAX_LIABILITY\"]] = fort_collins[[\"OWNER_TAX_LIABILITY\", \"STATE_TAX_LIABILITY\"]].fillna(0)\n"
        "    fort_collins[\"full_tax_bill\"] = fort_collins[\"OWNER_TAX_LIABILITY\"] + fort_collins[\"STATE_TAX_LIABILITY\"]\n"
        "    fort_collins[\"owner_tax_share\"] = np.where(\n"
        "        fort_collins[\"full_tax_bill\"] > 0,\n"
        "        fort_collins[\"OWNER_TAX_LIABILITY\"] / fort_collins[\"full_tax_bill\"],\n"
        "        1.0,\n"
        "    )\n"
        "    print(f'Loaded treasurer relief: mean state relief = {(1 - fort_collins[\"owner_tax_share\"]).mean():.3%}')\n"
        "else:\n"
        "    print('Propinfo cache not available — defaulting owner_tax_share=1.0 (no state relief modeled).')\n"
        "    fort_collins[\"OWNER_TAX_LIABILITY\"] = 0.0\n"
        "    fort_collins[\"STATE_TAX_LIABILITY\"] = 0.0\n"
        "    fort_collins[\"full_tax_bill\"] = 0.0\n"
        "    fort_collins[\"owner_tax_share\"] = 1.0\n"
        "fort_collins[\"state_tax_relief_pct\"] = 1.0 - fort_collins[\"owner_tax_share\"]"
    )
    n1 = patch_cells(nb, [(old_propinfo, new_propinfo)])

    # Fix 2: add fort_collins_4to1 variable alongside fort_collins_2to1
    old_pick = (
        "fort_collins_2to1 = next(s for s in scenarios if s[\"scenario\"] == \"Split-rate 2:1\")[\"df\"].copy()\n"
        "category_summary = next(s for s in scenarios if s[\"scenario\"] == \"Split-rate 2:1\")[\"category_summary\"].copy()"
    )
    new_pick = (
        "fort_collins_2to1 = next(s for s in scenarios if s[\"scenario\"] == \"Split-rate 2:1\")[\"df\"].copy()\n"
        "fort_collins_4to1 = next(s for s in scenarios if s[\"scenario\"] == \"Split-rate 4:1\")[\"df\"].copy()\n"
        "category_summary = next(s for s in scenarios if s[\"scenario\"] == \"Split-rate 2:1\")[\"category_summary\"].copy()"
    )
    n2 = patch_cells(nb, [(old_pick, new_pick)])

    # Fix 3: use fort_collins_4to1 in the geometry merge (for census join and export)
    old_merge = "fort_collins_2to1,\n        left_on=\"SCHEDNUM\",\n        right_on=\"SCHEDULENUM\","
    new_merge = "fort_collins_4to1,\n        left_on=\"SCHEDNUM\",\n        right_on=\"SCHEDULENUM\","
    n3 = patch_cells(nb, [(old_merge, new_merge)])

    # Fix 4: update export model_type to 4.0
    n4 = patch_cells(nb, [("model_type='split_rate:2.0'", "model_type='split_rate:4.0'")])

    total = n1 + n2 + n3 + n4
    if total:
        save_nb(path, nb)
        print(f"  fort_collins: propinfo={n1}, 4to1 var={n2}, geo merge={n3}, model_type={n4} ({total} total)")
    else:
        print("  fort_collins: no patterns matched (already fixed?)")


# ---------------------------------------------------------------------------
# 11. Bryan + College Station: 2:1 -> 4:1 (same pattern as highlands_ranch)
# ---------------------------------------------------------------------------
def fix_bryan_college_station():
    for city in ("bryan", "college_station"):
        fix_ratio_2to4(city)


# ---------------------------------------------------------------------------
# 12. Bellingham: replace abatement export with 4:1 split-rate
# ---------------------------------------------------------------------------
def fix_bellingham_to_split_rate():
    path = CITIES_DIR / "bellingham" / "model.ipynb"
    nb = load_nb(path)

    old_export = (
        "out_df = save_standard_export(\n"
        "    df=df,\n"
        "    city='bellingham',\n"
        "    output_path='../../analysis/data/bellingham.csv',\n"
        "    model_type='building_abatement:60pct',\n"
        "    land_millage=_eff_millage,\n"
        "    improvement_millage=_eff_millage,\n"
        "    property_category_col='PROPERTY_CATEGORY',\n"
        "    current_tax_col='current_tax',\n"
        "    new_tax_col='new_tax',\n"
        "    tax_change_col='tax_change',\n"
        "    tax_change_pct_col='tax_change_pct',\n"
        "    exempt_flag_col='full_exmp',\n"
        "    taxable_land_col='taxable_land_value',\n"
        "    taxable_improvement_col='taxable_improvement_value',\n"
        ")"
    )
    new_export = (
        "# Replace abatement model with 4:1 split-rate for cross-city comparison\n"
        "from lvt.lvt_utils import model_split_rate_tax as _msr\n"
        "_land_millage, _imp_millage, _revenue, df = _msr(\n"
        "    df=df,\n"
        "    land_value_col='taxable_land_value',\n"
        "    improvement_value_col='taxable_improvement_value',\n"
        "    current_revenue=df[df['full_exmp'] == 0]['current_tax'].sum(),\n"
        "    land_improvement_ratio=4.0,\n"
        "    exemption_flag_col='full_exmp',\n"
        ")\n"
        "df['tax_change'] = df['new_tax'] - df['current_tax']\n"
        "df['tax_change_pct'] = (\n"
        "    (df['tax_change'] / df['current_tax'] * 100)\n"
        "    .replace([float('inf'), float('-inf')], 0)\n"
        "    .fillna(0)\n"
        ")\n"
        "\n"
        "out_df = save_standard_export(\n"
        "    df=df,\n"
        "    city='bellingham',\n"
        "    output_path='../../analysis/data/bellingham.csv',\n"
        "    model_type='split_rate:4.0',\n"
        "    land_millage=_land_millage,\n"
        "    improvement_millage=_imp_millage,\n"
        "    property_category_col='PROPERTY_CATEGORY',\n"
        "    current_tax_col='current_tax',\n"
        "    new_tax_col='new_tax',\n"
        "    tax_change_col='tax_change',\n"
        "    tax_change_pct_col='tax_change_pct',\n"
        "    exempt_flag_col='full_exmp',\n"
        "    taxable_land_col='taxable_land_value',\n"
        "    taxable_improvement_col='taxable_improvement_value',\n"
        ")"
    )
    n = patch_cells(nb, [(old_export, new_export)])
    if n:
        save_nb(path, nb)
        print(f"  bellingham: replaced abatement export with 4:1 split-rate ({n} cell(s))")
    else:
        print("  bellingham: export pattern not found (already fixed?)")


if __name__ == "__main__":
    print("Patching notebooks...")
    print()
    print("--- Runner ---")
    fix_runner()
    print()
    print("--- Failing cities ---")
    fix_bellingham()
    fix_spokane()
    fix_regex_cities()
    fix_cincinnati()
    fix_fort_collins()
    print()
    print("--- Ratio harmonization (-> 4:1) ---")
    fix_ratio_2to4("highlands_ranch")
    fix_ratio_2to4("pueblo")
    fix_rochester()
    fix_syracuse()
    print()
    print("--- model_type string consistency ---")
    fix_greeley_model_type()
    print()
    print("--- Fort Collins: propinfo + 4:1 export ---")
    fix_fort_collins_propinfo_and_ratio()
    print()
    print("--- Bryan + College Station: 2:1 -> 4:1 ---")
    fix_bryan_college_station()
    print()
    print("--- Bellingham: abatement -> 4:1 split-rate ---")
    fix_bellingham_to_split_rate()
    print()
    print("Done.")
