"""Unit tests for lvt.reassessment (synthetic data, no network/data deps)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lvt.reassessment import (  # noqa: E402
    model_revenue_neutral_reassessment,
    model_multi_district_reassessment,
    decompose_reassessment_and_lvt,
    save_reassessment_export,
)
from lvt.lvt_utils import _compute_adjusted_tax_components  # noqa: E402


def _simple_df():
    # ratios new/old: 1.2, 0.8, 2.0, 0.6 ; avg (sum_new/sum_old) = 460/400 = 1.15
    return pd.DataFrame({
        'old': [100.0, 100.0, 100.0, 100.0],
        'new': [120.0, 80.0, 200.0, 60.0],
    })


# 1. Revenue-neutrality invariant — supplied target
def test_single_revenue_neutral_supplied():
    df = _simple_df()
    target = 4.0
    nm, rev, out = model_revenue_neutral_reassessment(df, 'new', current_revenue=target)
    assert rev == pytest.approx(target, abs=1e-9)
    assert out['new_tax'].sum() == pytest.approx(target, abs=1e-9)
    assert nm == pytest.approx(target * 1000 / df['new'].sum(), rel=1e-12)


# 1b. Revenue-neutrality invariant — derived target
def test_single_revenue_neutral_derived():
    df = _simple_df()
    nm, rev, out = model_revenue_neutral_reassessment(
        df, 'new', old_value_col='old', current_millage=10.0)
    derived = (df['old'] * 10.0 / 1000).sum()
    assert rev == pytest.approx(derived, abs=1e-9)
    assert out['new_tax'].sum() == pytest.approx(out['current_tax'].sum(), abs=1e-9)


# 3. Single == one-district multi-district special case
def test_single_equals_one_district():
    df = _simple_df()
    _, _, single = model_revenue_neutral_reassessment(
        df, 'new', old_value_col='old', current_millage=10.0)
    multi, _summary = model_multi_district_reassessment(
        df, 'new', 'old', [{'name': 'county', 'id_col': None, 'millage': 10.0}])
    for col in ['current_tax', 'new_tax', 'tax_change', 'tax_change_pct', 'reassessment_ratio']:
        pd.testing.assert_series_equal(
            single[col], multi[col], check_names=False, rtol=1e-12, atol=1e-12)


# 4. Decomposition identity
def test_decomposition_identity():
    rng = np.random.default_rng(0)
    n = 50
    df = pd.DataFrame({
        'current_tax': rng.uniform(0, 100, n),
        'avm_flat_tax': rng.uniform(0, 100, n),
        'new_tax': rng.uniform(0, 100, n),
    })
    out = decompose_reassessment_and_lvt(df)
    assert np.allclose(out['reassess_change'] + out['lvt_change'], out['total_change'])
    assert np.allclose(out['total_change'], out['new_tax'] - out['current_tax'])


# 5. Winner iff reassessment ratio below jurisdiction average (single)
def test_winner_iff_ratio_below_average():
    df = _simple_df()
    _, _, out = model_revenue_neutral_reassessment(
        df, 'new', old_value_col='old', current_millage=10.0)
    avg_ratio = out['taxable_new_value'].sum() / df['old'].sum()
    below = out['reassessment_ratio'] < avg_ratio
    assert (out.loc[below, 'tax_change'] < 0).all()
    assert (out.loc[~below, 'tax_change'] > 0).all()


# 2/7. Multi-district revenue neutrality (per district + overall) and cross-check
def test_multi_district_revenue_neutral():
    df = pd.DataFrame({
        'old': [100.0, 200.0, 150.0, 300.0, 250.0],
        'new': [150.0, 180.0, 300.0, 260.0, 400.0],
        'muni': ['A', 'A', 'B', 'B', 'B'],
        'school': ['X', 'Y', 'X', 'Y', 'Y'],
    })
    districts = [
        {'name': 'county', 'id_col': None, 'millage': 5.0},
        {'name': 'muni', 'id_col': 'muni', 'millage': {'A': 8.0, 'B': 6.0}},
        {'name': 'school', 'id_col': 'school', 'millage': {'X': 20.0, 'Y': 22.0}},
    ]
    out, summary = model_multi_district_reassessment(df, 'new', 'old', districts)
    # each district rolled back to its own current levy
    for _, row in summary.iterrows():
        assert row['new_revenue'] == pytest.approx(row['current_revenue'], abs=1e-9)
    # overall revenue neutral
    assert out['new_tax'].sum() == pytest.approx(out['current_tax'].sum(), abs=1e-9)
    # diagnostics present
    for name in ['county', 'muni', 'school']:
        assert f'{name}_ratio' in out.columns
        assert f'{name}_new_millage' in out.columns


def test_multi_district_crosscheck_raises_on_tamper():
    # Sanity: the cross-check actually fires if the identity is broken.
    df = pd.DataFrame({'old': [100.0, 200.0], 'new': [150.0, 120.0], 'muni': ['A', 'B']})
    districts = [{'name': 'muni', 'id_col': 'muni', 'millage': {'A': 8.0, 'B': 6.0}}]
    out, _ = model_multi_district_reassessment(df, 'new', 'old', districts, crosscheck=True)
    # corrupt tax_change_pct and re-run the private check -> should raise
    from lvt.reassessment import _crosscheck_combined_identity
    _z, tnew = _compute_adjusted_tax_components(df, None, 'new', None, None)
    _z2, told = _compute_adjusted_tax_components(df, None, 'old', None, None)
    bad = out.copy()
    bad['tax_change_pct'] = bad['tax_change_pct'] + 5.0
    with pytest.raises(AssertionError):
        _crosscheck_combined_identity(bad, districts, tnew, told, 1e-6)


# 6. Exemption handling — full flag and partial relief
def test_full_exemption():
    df = pd.DataFrame({'old': [100.0, 100.0, 100.0], 'new': [100.0, 100.0, 100.0],
                       'flag': [0, 0, 1]})
    nm, rev, out = model_revenue_neutral_reassessment(
        df, 'new', old_value_col='old', current_millage=10.0, exemption_flag_col='flag')
    assert out.loc[2, 'new_tax'] == 0.0
    # target derived from non-exempt only: 200 * 10/1000 = 2.0
    assert rev == pytest.approx(2.0, abs=1e-9)
    assert out['new_tax'].sum() == pytest.approx(2.0, abs=1e-9)


def test_partial_exemption_matches_helper():
    df = pd.DataFrame({'new': [100.0], 'relief': [30.0]})
    _z, adj = _compute_adjusted_tax_components(df, None, 'new', 'relief', None)
    _, _, out = model_revenue_neutral_reassessment(
        df, 'new', current_revenue=7.0, exemption_col='relief')
    assert out.loc[0, 'taxable_new_value'] == pytest.approx(float(adj.iloc[0]))
    assert out.loc[0, 'taxable_new_value'] == pytest.approx(70.0)


# 7b. exclude_mask holds parcels out and stays revenue neutral
def test_exclude_mask():
    df = pd.DataFrame({'old': [100.0, 100.0, 100.0], 'new': [100.0, 200.0, 300.0]})
    excl = pd.Series([True, False, False])
    nm, rev, out = model_revenue_neutral_reassessment(
        df, 'new', old_value_col='old', current_millage=10.0, exclude_mask=excl)
    # held-out parcel keeps its current tax
    assert out.loc[0, 'new_tax'] == pytest.approx(out.loc[0, 'current_tax'])
    # rolled-back rate solves only on the remaining base
    assert nm == pytest.approx((3.0 - 1.0) * 1000 / (200.0 + 300.0), rel=1e-12)
    assert out['new_tax'].sum() == pytest.approx(3.0, abs=1e-9)


def test_split_mode_carries_land_improvement():
    df = pd.DataFrame({'new_land': [40.0, 60.0], 'new_bldg': [60.0, 40.0]})
    _, _, out = model_revenue_neutral_reassessment(
        df, new_land_col='new_land', new_improvement_col='new_bldg', current_revenue=2.0)
    assert out['taxable_land_value'].tolist() == [40.0, 60.0]
    assert out['taxable_improvement_value'].tolist() == [60.0, 40.0]
    assert out['taxable_new_value'].tolist() == [100.0, 100.0]
    assert out['new_tax'].sum() == pytest.approx(2.0, abs=1e-9)


def test_save_reassessment_export(tmp_path):
    df = pd.DataFrame({
        'PROPERTY_CATEGORY': ['Single Family Residential', 'Commercial'],
        'current_tax': [100.0, 200.0],
        'new_tax': [120.0, 180.0],
        'tax_change': [20.0, -20.0],
        'tax_change_pct': [20.0, -10.0],
        'taxable_land_value': [0.0, 0.0],
        'taxable_improvement_value': [1000.0, 2000.0],
        'reassessment_ratio': [1.1, 0.9],
        'reassess_change': [20.0, -20.0],
        'reassess_change_pct': [20.0, -10.0],
        'lvt_change': [0.0, 0.0],
        'lvt_change_pct': [0.0, 0.0],
        'total_change': [20.0, -20.0],
        'total_change_pct': [20.0, -10.0],
    })
    path = tmp_path / 'testville.csv'
    out = save_reassessment_export(
        df, 'testville', str(path), 'reassessment:flat', 12.34, 12.34)
    assert path.exists()
    assert 'reassessment_ratio' in out.columns
    assert 'reassess_change_pct' in out.columns
    reloaded = pd.read_csv(path)
    assert 'lvt_change' in reloaded.columns
    assert len(reloaded) == 2
