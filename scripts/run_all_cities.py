"""
Run city notebooks to generate analysis/data/*.csv files.

Usage:
    python scripts/run_all_cities.py                  # run all cities
    python scripts/run_all_cities.py charlottesville  # run one city
    python scripts/run_all_cities.py charlottesville st_paul  # run multiple

For each city:
  - If the data/ dir has no parquet/gpq/csv files, patches `data_scrape = 0`
    to `data_scrape = 1` in a temp copy so the notebook fetches fresh data.
  - Executes via nbconvert (python3 kernel).
  - Reports pass/fail and whether the CSV was produced.

Skip list (stub export cells, not runnable yet):
    denver, morgantown, scranton
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

PYTHON = r"C:/Users/druss/miniconda3/python.exe"
JUPYTER = r"C:/Users/druss/miniconda3/Scripts/jupyter.exe"
REPO_ROOT = Path(__file__).resolve().parent.parent
CITIES_DIR = REPO_ROOT / "cities"

# Cities with working export cells (Philadelphia already has CSVs)
# denver, morgantown, scranton have TODO stub export cells
ALL_CITIES = [
    "baltimore",
    "bellingham",
    "bryan",
    "charlottesville",
    "cincinnati",
    "cleveland",
    "college_station",
    "fort_collins",
    "greeley",
    "highlands_ranch",
    "pueblo",
    "rochester",
    "southbend",
    "spokane",
    "st_paul",
    "syracuse",
]

TIMEOUT_SECONDS = 1200  # 20 min per city (scraping + Census API)


def has_data_cache(city: str) -> bool:
    data_dir = CITIES_DIR / city / "data"
    if not data_dir.exists():
        return False
    return (
        any(data_dir.glob("*.parquet"))
        or any(data_dir.glob("*.gpq"))
        or any(data_dir.glob("*.csv"))
    )


def patch_data_scrape(nb_path: Path, patched_path: Path) -> bool:
    """
    Write a patched copy of the notebook with data_scrape = 0 → data_scrape = 1.
    Returns True if any cells were patched.
    """
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    patched = False
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        if isinstance(cell["source"], list):
            src = "".join(cell["source"])
        else:
            src = cell["source"]

        if "data_scrape = 0" in src or "scrape_data = 0" in src:
            new_src = src.replace("data_scrape = 0", "data_scrape = 1")
            new_src = new_src.replace("scrape_data = 0", "scrape_data = 1")
            # Preserve list vs string format
            if isinstance(cell["source"], list):
                lines = new_src.splitlines(keepends=True)
                if lines and not lines[-1].endswith("\n"):
                    # match original formatting
                    pass
                cell["source"] = lines
            else:
                cell["source"] = new_src
            patched = True

    with open(patched_path, "w", encoding="utf-8") as f:
        json.dump(nb, f)

    return patched


def run_city(city: str) -> dict:
    nb_path = CITIES_DIR / city / "model.ipynb"
    if not nb_path.exists():
        return {"city": city, "status": "SKIP", "reason": "notebook not found"}

    data_dir = CITIES_DIR / city / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    needs_scrape = not has_data_cache(city)

    if needs_scrape:
        patched_path = nb_path.parent / "_run_model.ipynb"
        did_patch = patch_data_scrape(nb_path, patched_path)
        run_path = patched_path
        if did_patch:
            print(f"  [{city}] No cache — patched data_scrape=1, fetching fresh data")
        else:
            print(f"  [{city}] No cache — notebook uses file-detection, will auto-scrape")
    else:
        run_path = nb_path
        patched_path = None
        print(f"  [{city}] Using existing data cache")

    # Execute: output goes to a throw-away file so the original is untouched
    executed_path = nb_path.parent / "_executed.ipynb"
    cmd = [
        JUPYTER,
        "nbconvert",
        "--to", "notebook",
        "--execute",
        f"--output={executed_path.name}",
        f"--ExecutePreprocessor.kernel_name=python3",
        f"--ExecutePreprocessor.timeout={TIMEOUT_SECONDS}",
        str(run_path.name),
    ]

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS + 60,
            cwd=str(nb_path.parent),
        )
        elapsed = time.time() - start

        if result.returncode == 0:
            csv_path = REPO_ROOT / "analysis" / "data" / f"{city}.csv"
            if csv_path.exists():
                row_count = _count_csv_rows(csv_path)
                return {"city": city, "status": "PASS", "elapsed": elapsed,
                        "csv_rows": row_count}
            else:
                return {"city": city, "status": "PASS_NO_CSV", "elapsed": elapsed,
                        "note": "notebook ran cleanly but CSV not produced"}
        else:
            # Extract the meaningful error from stderr/stdout
            err_text = result.stderr or result.stdout or ""
            error_lines = _extract_error(err_text)
            return {"city": city, "status": "FAIL", "elapsed": elapsed,
                    "returncode": result.returncode, "error": error_lines}

    except subprocess.TimeoutExpired:
        return {"city": city, "status": "TIMEOUT", "elapsed": TIMEOUT_SECONDS}
    except Exception as e:
        return {"city": city, "status": "ERROR", "error": str(e)}
    finally:
        for p in [patched_path, executed_path]:
            if p and p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass


def _count_csv_rows(csv_path: Path) -> int:
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f) - 1  # subtract header
    except Exception:
        return -1


def _extract_error(text: str, max_lines: int = 10) -> str:
    """Pull the last traceback or error message from nbconvert output."""
    lines = text.strip().splitlines()
    # Find the last occurrence of "Error" or "Traceback"
    last_error = -1
    for i, line in enumerate(lines):
        if "Error" in line or "Traceback" in line or "CellExecutionError" in line:
            last_error = i
    if last_error >= 0:
        start = max(0, last_error - 2)
        return "\n".join(lines[start : start + max_lines])
    return "\n".join(lines[-max_lines:])


def main():
    cities = sys.argv[1:] if len(sys.argv) > 1 else ALL_CITIES

    unknown = [c for c in cities if c not in ALL_CITIES + ["philadelphia"]]
    if unknown:
        print(f"Unknown cities: {unknown}")
        print(f"Valid: {ALL_CITIES}")
        sys.exit(1)

    print(f"Running {len(cities)} city notebook(s)")
    print(f"Repo root: {REPO_ROOT}")
    print()

    results = []
    for i, city in enumerate(cities, 1):
        print(f"[{i}/{len(cities)}] {city}")
        result = run_city(city)
        results.append(result)
        status = result["status"]
        elapsed = result.get("elapsed", 0)

        if status == "PASS":
            rows = result.get("csv_rows", "?")
            print(f"  PASS -- {rows:,} rows in CSV ({elapsed:.0f}s)")
        elif status == "PASS_NO_CSV":
            print(f"  PASS_NO_CSV ({elapsed:.0f}s): {result.get('note', '')}")
        elif status in ("FAIL", "ERROR", "TIMEOUT"):
            print(f"  {status} ({elapsed:.0f}s)")
            if "error" in result:
                for line in result["error"].splitlines():
                    print(f"    {line}")
        else:
            print(f"  - {status}: {result.get('reason', '')}")
        print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = [r for r in results if r["status"] == "PASS"]
    failed = [r for r in results if r["status"] not in ("PASS", "SKIP", "PASS_NO_CSV")]
    no_csv = [r for r in results if r["status"] == "PASS_NO_CSV"]
    skipped = [r for r in results if r["status"] == "SKIP"]

    print(f"PASS ({len(passed)}):     {[r['city'] for r in passed]}")
    if no_csv:
        print(f"NO_CSV ({len(no_csv)}):   {[r['city'] for r in no_csv]}")
    if failed:
        print(f"FAIL ({len(failed)}):     {[r['city'] for r in failed]}")
    if skipped:
        print(f"SKIP ({len(skipped)}):     {[r['city'] for r in skipped]}")

    if passed:
        print(f"\nCSVs in analysis/data/:")
        for r in passed:
            print(f"  {r['city']}.csv — {r.get('csv_rows', '?'):,} rows")


if __name__ == "__main__":
    main()
