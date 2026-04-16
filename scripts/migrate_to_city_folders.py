"""
Phase 3 migration: Move notebooks to city subfolders and update paths.

Run from the repo root after ALL notebook runs are complete:
    python scripts/migrate_to_city_folders.py

What this does:
1. Creates examples/<city>/ directories
2. Copies notebook to examples/<city>/model.ipynb with updated paths
3. Moves data directory from examples/data/<city>/ to examples/<city>/data/
4. Does NOT delete the old notebooks (kept as backup until verified)
5. Does NOT do git mv — run 'git add -A' and commit afterward

After running:
- Verify a city notebook imports and exports correctly
- git add -A && git commit -m 'restructure: move notebooks to city subfolders'
- Delete examples/*.ipynb originals
"""
import json
import os
import re
import shutil
from pathlib import Path

REPO_ROOT   = Path(__file__).parent.parent
EXAMPLES    = REPO_ROOT / 'examples'
DATA_ROOT   = EXAMPLES / 'data'
ANALYSIS    = REPO_ROOT / 'analysis'

NOTEBOOKS = {
    'baltimore':       'baltimore.ipynb',
    'bellingham':      'belligham.ipynb',    # intentional typo in original
    'charlottesville': 'charlottesville.ipynb',
    'chicago':         'chicago.ipynb',
    'cincinnati':      'cincinnati.ipynb',
    'cleveland':       'cleveland.ipynb',
    'denver':          'denver.ipynb',
    'fort_collins':    'fort_collins.ipynb',
    'morgantown':      'morgantown.ipynb',
    'pittsburgh':      'pittsburgh.ipynb',
    'rochester':       'rochester.ipynb',
    'scranton':        'scranton.ipynb',
    'seattle':         'seattle.ipynb',
    'southbend':       'southbend.ipynb',
    'spokane':         'spokane.ipynb',
    'st_paul':         'st_paul.ipynb',
    'syracuse':        'syracuse.ipynb',
}

# Cells to update in each notebook
IMPORT_PATTERNS = [
    # Old: sys.path.insert(0, '..') or sys.path.append('..')
    # New: sys.path.insert(0, '../..')
    (r"sys\.path\.(insert|append)\(0?,\s*['\"]\.\.['\"]\)", "sys.path.insert(0, '../..')"),
    (r"sys\.path\.(insert|append)\(0?,\s*str\(REPO_ROOT\)\)", None),  # handled separately
]

DATA_PATH_PATTERNS = [
    # Old: Path('data') / 'cityname'  or  Path('data/cityname')
    # New: Path('data')
    (r"Path\(['\"]data['\"]\)\s*/\s*['\"](\w+)['\"]\s*", "Path('data')"),
    (r"Path\(['\"]data/\w+['\"]\)", "Path('data')"),
    (r"['\"]data/\w+/", "'data/"),
]

EXPORT_PATH_PATTERNS = [
    # Old: ../analysis/data/<city>.csv
    # New: ../../analysis/data/<city>.csv
    (r"'\.\./(analysis/data/\w+\.csv)'", r"'../../\1'"),
    (r'"\.\./(analysis/data/\w+\.csv)"', r'"../../\1"'),
]


def update_cell_source(source_lines: list, city: str) -> list:
    """Apply path updates to a cell's source lines."""
    source = ''.join(source_lines)

    # Update sys.path to go two levels up
    source = re.sub(
        r"sys\.path\.(insert|append)\([01]?,\s*['\"]\.\.['\"]\)",
        "sys.path.insert(0, '../..')",
        source,
    )
    # Update REPO_ROOT-based path setup (Cincinnati pattern)
    source = re.sub(
        r"REPO_ROOT = Path\.cwd\(\)\s*\n\s*if not \(REPO_ROOT / 'examples'\)\.exists\(\):\s*\n\s*REPO_ROOT = REPO_ROOT\.parent\s*\n\s*if str\(REPO_ROOT\) not in sys\.path:\s*\n\s*sys\.path\.append\(str\(REPO_ROOT\)\)",
        "sys.path.insert(0, str(Path('../..').resolve()))\nREPO_ROOT = Path('../..').resolve()",
        source,
        flags=re.MULTILINE,
    )

    # Update data directory references (remove city subfolder — data is now co-located)
    source = re.sub(
        rf"Path\(['\"]data['\"] *\) */ *['\"]({city}|{city.replace('_', '')})['\"]",
        "Path('data')",
        source,
        flags=re.IGNORECASE,
    )
    source = re.sub(
        rf"Path\(['\"]data/{city}['\"]?\)",
        "Path('data')",
        source,
        flags=re.IGNORECASE,
    )
    source = re.sub(
        rf"['\"]data/{city}/",
        "'data/",
        source,
        flags=re.IGNORECASE,
    )

    # Update export path (one more level up)
    source = re.sub(
        r"'\.\./(analysis/data/[^']+\.csv)'",
        r"'../../\1'",
        source,
    )
    source = re.sub(
        r'"\.\./(analysis/data/[^"]+\.csv)"',
        r'"../../\1"',
        source,
    )

    return [source]


def migrate_notebook(city: str, nb_filename: str, dry_run: bool = False) -> dict:
    """Migrate one notebook to its city folder. Returns status dict."""
    src = EXAMPLES / nb_filename
    city_dir = EXAMPLES / city
    dst = city_dir / 'model.ipynb'
    data_src = DATA_ROOT / city
    data_dst = city_dir / 'data'

    result = {
        'city': city,
        'src_exists': src.exists(),
        'dst_created': False,
        'data_moved': False,
        'cells_updated': 0,
        'errors': [],
    }

    if not src.exists():
        result['errors'].append(f'Source notebook not found: {src}')
        return result

    if dry_run:
        print(f'  [dry-run] Would migrate {city}')
        return result

    # Create city directory
    city_dir.mkdir(exist_ok=True)

    # Load notebook
    try:
        with open(src) as f:
            nb = json.load(f)
    except Exception as e:
        result['errors'].append(f'Failed to load notebook: {e}')
        return result

    # Update cell sources
    cells_updated = 0
    for cell in nb['cells']:
        if cell.get('cell_type') != 'code':
            continue
        old_src = ''.join(cell.get('source', []))
        new_lines = update_cell_source(cell.get('source', []), city)
        new_src = ''.join(new_lines)
        if new_src != old_src:
            cell['source'] = new_lines
            cells_updated += 1

    result['cells_updated'] = cells_updated

    # Write updated notebook to city dir
    try:
        with open(dst, 'w') as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
        result['dst_created'] = True
    except Exception as e:
        result['errors'].append(f'Failed to write destination notebook: {e}')
        return result

    # Move data directory (if it exists and not already in new location)
    if data_src.exists() and not data_dst.exists():
        try:
            shutil.copytree(data_src, data_dst)
            result['data_moved'] = True
            print(f'  Copied data: {data_src} → {data_dst}')
        except Exception as e:
            result['errors'].append(f'Data copy failed: {e}')

    print(f'  ✓ {city}: {cells_updated} cells updated, data_moved={result["data_moved"]}')
    return result


def main(dry_run: bool = False):
    if dry_run:
        print('[DRY RUN] No files will be written.\n')

    all_results = []
    for city, nb_file in sorted(NOTEBOOKS.items()):
        result = migrate_notebook(city, nb_file, dry_run=dry_run)
        all_results.append(result)

    # Summary
    print('\n--- Migration Summary ---')
    passed = [r for r in all_results if not r['errors'] and r['dst_created']]
    failed = [r for r in all_results if r['errors']]
    missing = [r for r in all_results if not r['src_exists']]

    print(f'Migrated: {len(passed)} cities')
    print(f'Errors:   {len(failed)} cities')
    print(f'Missing:  {len(missing)} cities')

    if failed:
        print('\nErrors:')
        for r in failed:
            print(f'  {r["city"]}: {r["errors"]}')

    print('\nNext steps:')
    print('1. Verify a city notebook: cd examples/charlottesville && jupyter notebook model.ipynb')
    print('2. Run: python scripts/add_export_cells.py (to add any missing export cells)')
    print('3. Run: nbstripout examples/*/model.ipynb')
    print('4. git add -A && git commit')
    print('5. Delete old examples/*.ipynb originals once verified')


if __name__ == '__main__':
    import sys
    dry_run = '--dry-run' in sys.argv
    main(dry_run=dry_run)
