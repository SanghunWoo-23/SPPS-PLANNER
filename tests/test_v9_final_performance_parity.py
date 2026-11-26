"""Data-quality and similarity parity for the final V9 performance pass.

Tests assert chemical identity and observed-data interpretation, not timing.
"""
from __future__ import annotations

import random

import pandas as pd
import pytest

from suite_gui.ai_excel_core_v9 import (
    _features, _residue_edit_distance, audit_reviewed_data, similar_runs,
)


def _reference_distance(left, right):
    if len(left) > 128 or len(right) > 128:
        raise ValueError('Sequence is too long for trustworthy local similarity review.')
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for i, first in enumerate(left, 1):
        current = [i]
        for j, second in enumerate(right, 1):
            current.append(min(current[j - 1] + 1, previous[j] + 1,
                               previous[j - 1] + (first != second)))
        previous = current
    return previous[-1]


def test_residue_distance_matches_full_dynamic_programming():
    rng = random.Random(12095)
    alphabet = ('A', 'V', 'dA', 'C', 'S', 'X:Nle', 'X:Aib')
    examples = [
        ([], []), (['S'] * 80, ['S'] * 80),
        (['S'] * 80 + ['A'], ['S'] * 80 + ['V']),
        (['A'] + ['S'] * 80, ['V'] + ['S'] * 80),
        (['A', 'dA', 'X:Nle'], ['A', 'A', 'X:Nle']),
    ]
    for _ in range(300):
        examples.append((rng.choices(alphabet, k=rng.randrange(0, 60)),
                         rng.choices(alphabet, k=rng.randrange(0, 60))))
    for left, right in examples:
        left_before, right_before = left[:], right[:]
        assert _residue_edit_distance(left, right) == _reference_distance(left, right)
        assert left == left_before and right == right_before
    with pytest.raises(ValueError, match='too long'):
        _residue_edit_distance(['A'] * 129, [])


def _table():
    return pd.DataFrame([
        {'sequence': 'ACD', 'run_id': 'r1', 'reaction_step': 'coupling',
         'actual_yield_percent': 45., 'actual_purity_percent': 95.,
         'scale_mmol': 0.1, 'loading_mmol_g': 0.8, 'resin': 'Rink Amide',
         'chemistry': 'DIC/HOBt', 'product_path': 'linear_deprotected'},
        {'sequence': 'ACD', 'run_id': 'r1', 'reaction_step': 'cleavage',
         'actual_yield_percent': 47., 'actual_purity_percent': 95.,
         'scale_mmol': 0.1, 'loading_mmol_g': 0.8, 'resin': 'Rink Amide',
         'chemistry': 'DIC/HOBt', 'product_path': 'linear_deprotected'},
        {'sequence': 'ACD', 'run_id': 'r1', 'reaction_step': 'coupling',
         'actual_yield_percent': 49., 'actual_purity_percent': 95.,
         'scale_mmol': 0.1, 'loading_mmol_g': 0.8, 'resin': 'Rink Amide',
         'chemistry': 'DIC/HOBt', 'product_path': 'linear_deprotected'},
        {'sequence': 'dA-Nle-C', 'run_id': 'r2', 'reaction_step': 'coupling',
         'actual_yield_percent': 60., 'actual_purity_percent': 90.,
         'scale_mmol': 0.2, 'loading_mmol_g': 0.75, 'resin': '2-CTC',
         'chemistry': 'HBTU/NMM', 'product_path': 'linear_deprotected'},
    ])


def test_audit_preserves_record_conflicts_and_source_dataframe():
    table = _table()
    before = table.copy(deep=True)
    summary = audit_reviewed_data(table)
    assert summary['duplicate_run_ids'] == 1
    assert summary['conflicting_run_ids'] == 1
    assert summary['training_blocked'] is True
    assert summary['total_rows'] == 4
    pd.testing.assert_frame_equal(table, before)


def test_audit_distinguishes_repeated_run_stages():
    table = _table().iloc[:2].copy()
    summary = audit_reviewed_data(table)
    assert summary['duplicate_run_ids'] == 0
    assert summary['conflicting_run_ids'] == 0


def test_features_keep_original_schema_and_chemical_residues():
    frame = _table()
    features = _features(frame)
    assert list(features.columns) == [
        'sequence_length', 'cys_count', 'asp_count', 'pro_count', 'gly_count',
        'd_residue_count', 'noncanonical_count', 'branch_residue_count',
        'scale_mmol', 'loading_mmol_g', 'resin', 'chemistry',
    ]
    assert features.iloc[0]['sequence_length'] == 3
    assert features.iloc[0]['cys_count'] == 1
    assert features.iloc[3]['d_residue_count'] == 1
    assert features.iloc[3]['noncanonical_count'] == 1
    assert features.iloc[3]['resin'] == '2-CTC'


def test_features_missing_optional_fields_have_legacy_empty_defaults():
    result = _features(pd.DataFrame({'sequence': ['ACD']}))
    assert result.iloc[0]['resin'] == ''
    assert result.iloc[0]['chemistry'] == ''
    assert pd.isna(result.iloc[0]['scale_mmol'])


def test_nearest_runs_preserve_experimental_provenance_and_path_filtering():
    table = _table()
    context = {'sequence': 'ACD', 'resin': 'Rink Amide', 'chemistry': 'DIC/HOBt',
               'product_path': 'linear_deprotected'}
    result = similar_runs(table, context, top_k=2)
    assert result and len(result) == 2
    assert result[0]['sequence'] == 'ACD'
    assert result[0]['residue_edits'] == 0
    assert result[0]['conditions_match'] == {'resin': True, 'chemistry': True}
    assert result[0]['screening'] == 'APPROXIMATE_TOP_CANDIDATES'
    # A cyclic/protected record must not become a linear recommendation.
    other = table.iloc[[0]].copy()
    other['product_path'] = 'head_to_tail_cyclic'
    only_cyclic = similar_runs(other, context)
    assert only_cyclic == []


def test_streamed_hash_matches_exact_file_digest(tmp_path):
    from hashlib import sha256
    from suite_gui.ai_excel_core_v9 import _sha256_file
    data = b'spps-v9-data' * 600_000
    source = tmp_path / 'large-local-input.bin'
    source.write_bytes(data)
    assert _sha256_file(source) == sha256(data).hexdigest()


def test_preview_hash_rejects_changed_source_after_review(tmp_path):
    from suite_gui.ai_excel_core_v9 import preview_file, verify_preview_source
    path = tmp_path / 'outcomes.csv'
    path.write_text('Sequence,Actual yield %\nACD,45\n', encoding='utf-8')
    reviewed = preview_file(path)
    verify_preview_source(reviewed)
    path.write_text('Sequence,Actual yield %\nACD,99\n', encoding='utf-8')
    with pytest.raises(ValueError, match='changed after preview'):
        verify_preview_source(reviewed)


def test_streamed_similar_runs_keeps_ties_and_observed_values():
    from suite_gui.ai_excel_core_v9 import similar_runs
    frame = pd.DataFrame([
        {'sequence': 'ACD', 'run_id': 'r1', 'resin': 'Rink Amide',
         'chemistry': 'DIC/HOBt', 'actual_yield_percent': 31,
         'actual_purity_percent': 90, 'product_path': 'linear_deprotected'},
        {'sequence': 'ACD', 'run_id': 'r2', 'resin': 'Rink Amide',
         'chemistry': 'DIC/HOBt', 'actual_yield_percent': 62,
         'actual_purity_percent': 95, 'product_path': 'linear_deprotected'},
        {'sequence': 'ACD', 'run_id': 'r3', 'resin': 'Rink Amide',
         'chemistry': 'DIC/HOBt', 'actual_yield_percent': None,
         'actual_purity_percent': None, 'product_path': 'linear_deprotected'},
        {'sequence': 'ACD', 'run_id': 'r4', 'resin': 'Rink Amide',
         'chemistry': 'DIC/HOBt', 'actual_yield_percent': 10,
         'actual_purity_percent': 95, 'product_path': 'disulfide_cyclic'},
    ])
    context = {'sequence': 'ACD', 'resin': 'Rink Amide',
               'chemistry': 'DIC/HOBt', 'product_path': 'linear_deprotected'}
    found = similar_runs(frame, context, top_k=2)
    assert [row['actual_yield_percent'] for row in found] == [31, 62]
    assert all(row['distance'] == 0.0 for row in found)
    assert similar_runs(frame, context, top_k=0) == []


def test_loading_validation_groups_preserve_run_priority_and_replicates():
    import numpy as np
    from suite_gui.recommendation.model_registry import _loading_validation_groups

    columns = ['resin_type', 'amino_acid_normalized', 'aa_eq', 'base_eq', 'loading_time_h']
    frame = pd.DataFrame([
        ['A', 'Val', 3.0, 3.0, 2.0, 'run-A', 'work-X'],
        ['A', 'Val', 3.0, 3.0, 2.0, '', 'work-X'],
        ['A', 'Val', np.nan, 3.0, 2.0, '', ''],
        ['A', 'Val', np.nan, 3.0, 2.0, '', ''],
    ], columns=columns + ['run_id', 'work_item_id'], index=[9, 2, 12, 17])
    result = _loading_validation_groups(frame, columns[:2], columns[2:])
    assert result.index.tolist() == frame.index.tolist()
    assert result.iloc[0] == 'run:run-A'
    assert result.iloc[1] == 'work:work-X'
    assert result.iloc[2] == result.iloc[3]
    assert result.iloc[2].startswith('conditions:')
    assert 'null' in result.iloc[2]
    assert len(set(result)) == 3


def test_loading_validation_groups_support_nullable_identifiers():
    """A missing run ID must fall through to the work or condition signature."""
    from suite_gui.recommendation.model_registry import _loading_validation_groups
    frame = pd.DataFrame({
        'run_id': pd.Series([pd.NA, float('nan'), 'experiment-9', '', 0], dtype=object),
        'work_item_id': pd.Series(['work-1', pd.NA, None, pd.NA, pd.NA], dtype=object),
        'resin': ['CTC'] * 5, 'eq': [3.] * 5,
    })
    groups = _loading_validation_groups(frame, ['resin'], ['eq'])
    assert groups.iloc[0] == 'work:work-1'
    assert groups.iloc[1].startswith('conditions:')
    assert groups.iloc[2] == 'run:experiment-9'
    assert groups.iloc[3] == groups.iloc[1]
    assert groups.iloc[4] == groups.iloc[1]


def test_peptide_reorder_saves_active_editor_before_loading(monkeypatch):
    """Drag reorder must preserve edits typed into the current Project item."""
    from types import SimpleNamespace
    from suite_gui.modules import peptide_items
    from suite_gui.modules import gui_common as state
    from suite_gui.runtime_state import set_active_index
    class Listbox:
        def curselection(self):
            return (0,)
    gui = SimpleNamespace(
        pm_items=[{'project': 'P1', 'peptide': 'A', 'sequence': 'AAA'},
                  {'project': 'P2', 'peptide': 'B', 'sequence': 'BBB'}],
        pm_list=Listbox(), pm_sequence=SimpleNamespace(get=lambda: 'NEW'),
        pm_project=SimpleNamespace(get=lambda: 'P1'),
    )
    set_active_index(gui, 0)
    loaded = []
    monkeypatch.setattr(state, 'refresh_list', lambda _gui, *_args: None)
    monkeypatch.setattr(state, 'load_item_to_editor', lambda _gui, idx: loaded.append(idx))
    monkeypatch.setattr(state, 'save_active', lambda obj: obj.pm_items.__getitem__(0).__setitem__('sequence', obj.pm_sequence.get()))
    peptide_items.move_selected_to(gui, 1)
    assert gui.pm_items[1]['sequence'] == 'NEW'
    assert loaded == [1]
