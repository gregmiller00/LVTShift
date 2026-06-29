"""Tests for lvt.metrics.compute_city_metrics."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lvt.metrics import compute_city_metrics, rollup_city_metrics


def _sample():
    # improvement ratios: 0 (vacant), ~4.8% (<10%), ~16.7% (10-25%), ~28.6% (25-50%),
    # 50% (developed); last row fully exempt (excluded).
    return pd.DataFrame({
        'taxable_land_value':        [100, 100, 100, 100, 100, 0],
        'taxable_improvement_value': [0,     5,  20,  40, 100, 0],
        'current_tax':               [10,   10,  10,  10,  10, 0],
        'new_tax':                   [13,   12,  10,   8,   7, 0],
        'is_fully_exempt':           [0,     0,   0,   0,   0, 1],
        'model_type':                ['x'] * 6,
    })


def test_exempt_excluded_and_base(tmp_path):
    m = compute_city_metrics(_sample(), 'testcity', str(tmp_path))
    assert m['parcels_modeled'] == 5                      # exempt row dropped
    assert round(m['tax_base_usd']) == 665                # 100+105+120+140+200
    assert round(m['land_base_usd']) == 500


def test_buckets_partition_the_base(tmp_path):
    m = compute_city_metrics(_sample(), 'testcity', str(tmp_path), write=False)
    bsum = (m['vacant_value_usd'] + m['underdeveloped_lt10_value_usd']
            + m['underdeveloped_10_25_value_usd'] + m['underdeveloped_25_50_value_usd']
            + m['developed_ge50_value_usd'])
    assert round(bsum) == round(m['tax_base_usd'])
    # vacant + the three underdeveloped buckets == the underdeveloped subtotal
    assert round(m['underdeveloped_subtotal_value_usd']) == round(
        m['vacant_value_usd'] + m['underdeveloped_lt10_value_usd']
        + m['underdeveloped_10_25_value_usd'] + m['underdeveloped_25_50_value_usd'])


def test_dollar_change_logic(tmp_path):
    m = compute_city_metrics(_sample(), 'testcity', str(tmp_path), write=False)
    assert round(m['dollars_changed_gross_usd']) == 10    # |3|+|2|+|0|+|2|+|3|
    assert round(m['dollars_shifted_net_usd']) == 5        # half of gross (revenue-neutral)


def test_files_written_and_rollup(tmp_path):
    compute_city_metrics(_sample(), 'alpha', str(tmp_path))
    compute_city_metrics(_sample(), 'beta', str(tmp_path))
    assert (tmp_path / 'alpha' / 'metrics_summary.md').exists()
    assert (tmp_path / 'alpha' / 'metrics_alpha.csv').exists()
    rolled = rollup_city_metrics(str(tmp_path))
    assert set(rolled['city']) == {'alpha', 'beta'}
