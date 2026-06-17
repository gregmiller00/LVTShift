"""Roll every city's per-city metrics into one cross-city comparison table.

Reads each ``analysis/reports/<city>/metrics_<city>.csv`` (written automatically by
``lvt.viz.create_city_report`` → ``lvt.metrics.compute_city_metrics``) and concatenates them.

Usage:
    python analysis/build_metrics_rollup.py [reports_dir] [output_csv]

Defaults: reports_dir = analysis/reports, output_csv = analysis/reports/metrics_rollup.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lvt.metrics import rollup_city_metrics

REPO = Path(__file__).resolve().parents[1]
reports = sys.argv[1] if len(sys.argv) > 1 else str(REPO / 'analysis' / 'reports')
out = sys.argv[2] if len(sys.argv) > 2 else str(Path(reports) / 'metrics_rollup.csv')

df = rollup_city_metrics(reports, output_path=out)
if df.empty:
    print(f"No metrics_*.csv found under {reports}")
else:
    cols = ['city', 'model_type', 'tax_base_usd', 'dollars_changed_pct_of_levy',
            'vacant_pct_of_base', 'underdeveloped_subtotal_pct_of_base']
    print(df[[c for c in cols if c in df.columns]].to_string(index=False))
    print(f"\nWrote {out} ({len(df)} cities)")
