"""
Add standardized export cells to LVTShift notebooks.

Run from the repo root:
    python scripts/add_export_cells.py

Adds a save_standard_export() call at the end of each configured notebook.
Complex notebooks (Baltimore, Bellingham, Seattle, Spokane, Scranton, Morgantown)
are flagged with a TODO stub instead.
"""
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(REPO_ROOT, 'examples')

# ---------------------------------------------------------------------------
# Per-city export configuration
# ---------------------------------------------------------------------------
# Keys:
#   df            : final dataframe variable name (after Census join if present)
#   model_type    : encoded model string, e.g. "split_rate:4.0"
#   land_millage  : Python expression for land millage (variable name or literal)
#   imp_millage   : Python expression for improvement millage
#   cat_col       : property_category column
#   current_tax   : current_tax column
#   new_tax       : new_tax column
#   tax_change    : tax_change column
#   tax_change_pct: tax_change_pct column (or None to derive)
#   taxable_land  : taxable_land_value column (default: taxable_land_value)
#   taxable_imp   : taxable_improvement_value column (default: taxable_improvement_value)
#   exempt_flag   : exempt flag column or None
#   status        : 'ready' | 'todo' | 'skip'
#   todo_note     : explanation shown in TODO stub
# ---------------------------------------------------------------------------

CITY_CONFIGS = {
    'charlottesville': {
        'df': 'df_input',
        'model_type': 'split_rate:4.0',
        'land_millage': 'land_millage',
        'imp_millage': 'improvement_millage',
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        'new_tax': 'new_tax',
        'tax_change': 'tax_change',
        'tax_change_pct': 'tax_change_pct',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': 'full_exmp',
        'status': 'ready',
    },
    'chicago': {
        'df': 'df',
        'model_type': 'split_rate:4.0',
        'land_millage': 'land_millage',
        'imp_millage': 'improvement_millage',
        # Chicago uses major_class_description — map to PROPERTY_CATEGORY first
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        'new_tax': 'new_tax',
        'tax_change': 'tax_change',
        'tax_change_pct': 'tax_change_pct',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': None,
        'status': 'todo',
        'todo_note': (
            'Chicago uses major_class_description not PROPERTY_CATEGORY. '
            'Add a mapping cell before this one to create PROPERTY_CATEGORY from major_class_description, '
            'then set cat_col="PROPERTY_CATEGORY". '
            'Also confirm final df variable name after Census join.'
        ),
    },
    'cincinnati': {
        'df': 'modeled',
        'model_type': 'split_rate:4.0',
        'land_millage': 'land_millage',
        'imp_millage': 'improvement_millage',
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        'new_tax': 'new_tax',
        'tax_change': 'tax_change',
        'tax_change_pct': 'tax_change_pct',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': 'full_exmp',
        'status': 'ready',
    },
    'cleveland': {
        'df': 'df_input',
        'model_type': 'split_rate:4.0',
        'land_millage': 'land_millage',
        'imp_millage': 'improvement_millage',
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        'new_tax': 'new_tax',
        'tax_change': 'tax_change',
        'tax_change_pct': 'tax_change_pct',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': 'full_exmp',
        'status': 'ready',
    },
    'denver': {
        'df': 'gdf_lvt',
        'model_type': 'split_rate:4.0',
        # Denver runs dual-levy; average the school and non-school millages
        'land_millage': '(land_mills_s + land_mills_ns) / 2',
        'imp_millage': '(impr_mills_s + impr_mills_ns) / 2',
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        'new_tax': 'new_tax',
        'tax_change': 'tax_change',
        'tax_change_pct': 'tax_change_pct',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': 'is_exempt',
        'status': 'todo',
        'todo_note': (
            'Denver has a dual-levy structure (school + non-school). '
            'The current_tax and new_tax columns are combined totals (school + nonschool). '
            'The land_millage and imp_millage expressions average school and nonschool rates '
            '— verify these variable names (land_mills_s, impr_mills_s, land_mills_ns, impr_mills_ns) '
            'exist in scope when this cell runs. '
            'Also verify that taxable_land_value column exists in gdf_lvt after model runs.'
        ),
    },
    'fort_collins': {
        'df': 'df',
        'model_type': 'split_rate:4.0',
        'land_millage': 'land_millage',
        'imp_millage': 'improvement_millage',
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        'new_tax': 'new_tax',
        'tax_change': 'tax_change',
        'tax_change_pct': 'tax_change_pct',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': None,
        'status': 'ready',
    },
    'pittsburgh': {
        'df': 'df_input',
        'model_type': 'split_rate:4.0',
        'land_millage': 'land_millage',
        'imp_millage': 'improvement_millage',
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        'new_tax': 'new_tax',
        'tax_change': 'tax_change',
        'tax_change_pct': 'tax_change_pct',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': 'full_exmp',
        'status': 'ready',
    },
    'rochester': {
        'df': 'gdf',
        'model_type': 'split_rate:4.0',
        'land_millage': 'land_millage',
        'imp_millage': 'improvement_millage',
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        'new_tax': 'new_tax',
        'tax_change': 'tax_change',
        'tax_change_pct': 'tax_change_pct',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': None,
        'status': 'todo',
        'todo_note': (
            'Verify the final dataframe variable name after Census join '
            '(may be homestead_gdf or gdf — check last cells). '
            'Also verify the land_improvement_ratio used (2:1, 4:1, or other).'
        ),
    },
    'scranton': {
        'df': 'gdf',
        'model_type': 'split_rate:4.0',
        'land_millage': 'land_millage',
        'imp_millage': 'improvement_millage',
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        'new_tax': 'new_tax',
        'tax_change': 'tax_change',
        'tax_change_pct': 'tax_change_pct',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': None,
        'status': 'skip',
        'todo_note': (
            'Scranton notebook only fetches data (1 code cell) — no modeling implemented yet. '
            'Complete the modeling first, then add the export cell.'
        ),
    },
    'southbend': {
        'df': 'df',
        'model_type': 'split_rate:4.0',
        'land_millage': 'land_millage',
        'imp_millage': 'improvement_millage',
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        'new_tax': 'new_tax',
        'tax_change': 'tax_change',
        'tax_change_pct': 'tax_change_pct',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': None,
        'status': 'ready',
    },
    'st_paul': {
        'df': 'st_paul_city',
        'model_type': 'split_rate:4.0',
        'land_millage': 'tc_land_millage',
        'imp_millage': 'tc_imp_millage',
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        # St. Paul renames new_tax → new_tax_tc to track TC-approach model
        'new_tax': 'new_tax_tc',
        'tax_change': 'tax_change_tc',
        'tax_change_pct': 'tax_change_pct_tc',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': None,
        'status': 'ready',
    },
    'syracuse': {
        'df': 'gdf',
        'model_type': 'split_rate:4.0',
        'land_millage': 'land_millage',
        'imp_millage': 'improvement_millage',
        'cat_col': 'PROPERTY_CATEGORY',
        'current_tax': 'current_tax',
        'new_tax': 'new_tax',
        'tax_change': 'tax_change',
        'tax_change_pct': 'tax_change_pct',
        'taxable_land': 'taxable_land_value',
        'taxable_imp': 'taxable_improvement_value',
        'exempt_flag': None,
        'status': 'ready',
    },
    # --- Complex / abatement notebooks — need manual implementation ---
    'baltimore': {
        'status': 'todo',
        'todo_note': (
            'Baltimore runs multiple scenarios (2:1, 4:1) stored in a scenarios list. '
            'Pick one scenario (e.g., baltimore_2to1) as the canonical export. '
            'Verify column names after Census join and model type string '
            '(e.g., "split_rate:2.0" for 2:1 or "split_rate:4.0" for 4:1).'
        ),
    },
    'belligham': {
        'status': 'todo',
        'todo_note': (
            'Bellingham uses a building abatement model. '
            'Determine the abatement percentage and model_type string '
            '(e.g., "abatement:100pct" or "abatement:75pct"). '
            'Identify land_millage and improvement_millage equivalents '
            'from the abatement model return values. '
            'Note: notebook filename has typo "belligham" vs data dir "bellingham".'
        ),
    },
    'morgantown': {
        'status': 'skip',
        'todo_note': (
            'Morgantown notebook is incomplete — still in development. '
            'Complete the modeling, Census join, and visualization before adding export cell.'
        ),
    },
    'seattle': {
        'status': 'todo',
        'todo_note': (
            'Seattle uses per-levy calculations rather than a single model_split_rate_tax() call. '
            'Confirm the final combined current_tax, new_tax, tax_change columns exist. '
            'Determine effective land_millage and improvement_millage from the levy structure. '
            'Determine model_type (e.g., "abatement:100pct" or "split_rate:X.0").'
        ),
    },
    'spokane': {
        'status': 'todo',
        'todo_note': (
            'Spokane uses per-levy calculations similar to Seattle. '
            'Confirm the final combined current_tax, new_tax, tax_change columns exist. '
            'Determine effective land_millage and improvement_millage from the levy structure. '
            'Determine model_type string.'
        ),
    },
}

NOTEBOOK_FILENAMES = {
    'baltimore':      'baltimore.ipynb',
    'belligham':      'belligham.ipynb',   # intentional typo match
    'charlottesville':'charlottesville.ipynb',
    'chicago':        'chicago.ipynb',
    'cincinnati':     'cincinnati.ipynb',
    'cleveland':      'cleveland.ipynb',
    'denver':         'denver.ipynb',
    'fort_collins':   'fort_collins.ipynb',
    'morgantown':     'morgantown.ipynb',
    'pittsburgh':     'pittsburgh.ipynb',
    'rochester':      'rochester.ipynb',
    'scranton':       'scranton.ipynb',
    'seattle':        'seattle.ipynb',
    'southbend':      'southbend.ipynb',
    'spokane':        'spokane.ipynb',
    'st_paul':        'st_paul.ipynb',
    'syracuse':       'syracuse.ipynb',
}


def build_ready_cell(city, cfg):
    """Build the Python source for a ready export cell."""
    exempt_arg = f"    exempt_flag_col={repr(cfg['exempt_flag'])},\n" if cfg.get('exempt_flag') else ''
    pct_arg = (
        f"    tax_change_pct_col={repr(cfg['tax_change_pct'])},\n"
        if cfg.get('tax_change_pct') else ''
    )
    lines = [
        "# Export standardized CSV — do not remove or move above Census join\n",
        "import sys\n",
        "sys.path.insert(0, '..')\n",
        "from lvt_utils import save_standard_export\n",
        "\n",
        f"save_standard_export(\n",
        f"    df={cfg['df']},\n",
        f"    city={repr(city)},\n",
        f"    output_path='../analysis/data/{city}.csv',\n",
        f"    model_type={repr(cfg['model_type'])},\n",
        f"    land_millage={cfg['land_millage']},\n",
        f"    improvement_millage={cfg['imp_millage']},\n",
        f"    property_category_col={repr(cfg['cat_col'])},\n",
        f"    current_tax_col={repr(cfg['current_tax'])},\n",
        f"    new_tax_col={repr(cfg['new_tax'])},\n",
        f"    tax_change_col={repr(cfg['tax_change'])},\n",
    ]
    if pct_arg:
        lines.append(pct_arg)
    if exempt_arg:
        lines.append(exempt_arg)
    lines += [
        f"    taxable_land_col={repr(cfg['taxable_land'])},\n",
        f"    taxable_improvement_col={repr(cfg['taxable_imp'])},\n",
        ")\n",
    ]
    return lines


def build_todo_cell(city, note):
    """Build a stub cell for notebooks that need manual implementation."""
    lines = [
        f"# TODO: Export standardized CSV — {city}\n",
        "# This cell needs to be completed manually before running.\n",
        "#\n",
        f"# {note}\n",
        "#\n",
        "# Template:\n",
        "# import sys\n",
        "# sys.path.insert(0, '..')\n",
        "# from lvt_utils import save_standard_export\n",
        "#\n",
        "# save_standard_export(\n",
        f"#     df=<final_df_variable>,\n",
        f"#     city={repr(city)},\n",
        f"#     output_path='../analysis/data/{city}.csv',\n",
        f"#     model_type='split_rate:4.0',  # update as needed\n",
        f"#     land_millage=land_millage,\n",
        f"#     improvement_millage=improvement_millage,\n",
        "# )\n",
    ]
    return lines


def add_cell_to_notebook(nb_path, source_lines):
    with open(nb_path) as f:
        nb = json.load(f)

    # Check if export cell already exists
    for cell in nb['cells']:
        src = ''.join(cell.get('source', []))
        if 'save_standard_export' in src:
            print(f"  [skip] export cell already present in {os.path.basename(nb_path)}")
            return False

    new_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source_lines,
    }
    nb['cells'].append(new_cell)

    with open(nb_path, 'w') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    return True


def main():
    results = {'added': [], 'todo': [], 'skip': [], 'missing': []}

    for city, cfg in CITY_CONFIGS.items():
        nb_filename = NOTEBOOK_FILENAMES.get(city)
        nb_path = os.path.join(EXAMPLES_DIR, nb_filename)

        if not os.path.exists(nb_path):
            print(f"  [missing] {nb_path}")
            results['missing'].append(city)
            continue

        status = cfg.get('status', 'ready')

        if status == 'skip':
            print(f"  [skip] {city}: {cfg.get('todo_note', '')[:80]}")
            results['skip'].append(city)
            # Still add a comment stub so engineers see the TODO
            lines = build_todo_cell(city, cfg.get('todo_note', 'Skipped — complete modeling first.'))
            add_cell_to_notebook(nb_path, lines)
            continue

        if status == 'todo':
            lines = build_todo_cell(city, cfg.get('todo_note', 'Manual implementation needed.'))
            added = add_cell_to_notebook(nb_path, lines)
            if added:
                print(f"  [todo-stub] {city}")
                results['todo'].append(city)
            continue

        # status == 'ready'
        lines = build_ready_cell(city, cfg)
        added = add_cell_to_notebook(nb_path, lines)
        if added:
            print(f"  [added] {city}")
            results['added'].append(city)

    print("\n--- Summary ---")
    print(f"Export cells added (ready):  {results['added']}")
    print(f"TODO stubs added:            {results['todo']}")
    print(f"Skipped (no modeling):       {results['skip']}")
    print(f"Missing notebooks:           {results['missing']}")


if __name__ == '__main__':
    main()
