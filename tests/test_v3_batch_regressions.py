from __future__ import annotations

from suite_gui import batch_workflow
from suite_gui import catalogs
from suite_gui.modules import project_manager_workflow


class _Tree:
    def __init__(self, columns, rows=()):
        self.columns = list(columns)
        self.rows = {
            str(index): tuple(row.get(column, "") for column in self.columns)
            for index, row in enumerate(rows)
        }

    def get_children(self):
        return tuple(self.rows)

    def item(self, item_id, option=None):
        values = self.rows[item_id]
        return values if option == "values" else {"values": values}

    def delete(self, *item_ids):
        for item_id in item_ids:
            self.rows.pop(item_id, None)

    def insert(self, _parent, _where, values):
        item_id = str(max([int(key) for key in self.rows] + [-1]) + 1)
        self.rows[item_id] = tuple(values)
        return item_id

    def cget(self, option):
        return tuple(self.columns) if option == "columns" else ""

    def configure(self, **kwargs):
        if "columns" in kwargs:
            self.columns = list(kwargs["columns"])

    def heading(self, *_args, **_kwargs):
        return None

    def column(self, *_args, **_kwargs):
        return None


BATCH_COLUMNS = [
    "No", "Project", "Peptide name", "Form", "Copies", "N-term",
    "Region 1 seq", "Region 1 eq", "Linker", "Region 2 seq",
    "Region 2 eq", "Tag", "Label", "C-term", "Chemistry",
    "Scale mmol", "AA conc M", "AA coupling eq", "Resin", "Loading",
    "LOT No", "Status",
]


def test_protected_fmoc_names_are_primary_unit_choices():
    assert catalogs.UNIT_VALUES[1:5] == [
        "Fmoc-Ala-OH", "Fmoc-Arg(Pbf)-OH", "Fmoc-Asn(Trt)-OH",
        "Fmoc-Asp(OtBu)-OH",
    ]
    assert "A" not in catalogs.UNIT_VALUES
    assert "Ala" not in catalogs.UNIT_VALUES
    assert "D-Arg" not in catalogs.UNIT_VALUES
    assert "Fmoc-D-Arg(Pbf)-OH" in catalogs.UNIT_VALUES
    assert "Fmoc-NH-PEG4-CH2COOH" in catalogs.UNIT_VALUES


def test_v2_project_driven_batch_ui_remains_the_v3_default():
    from suite_gui.classic_base import ClassicControllerBase

    assert ClassicControllerBase._build_batch_tab.__name__ == "_v23_build_batch_tab"


def test_compact_batch_columns_receive_all_canonical_values():
    record = {
        "Item": "Fmoc-Ala-OH", "Solvent": "DMF",
        "Calculated_mL": 12.5, "Chemistry": "DIC/HOBt",
        "Loading": 0.68,
    }

    assert batch_workflow._display_value(record, "AA") == "Fmoc-Ala-OH"
    assert batch_workflow._display_value(record, "solvent") == "DMF"
    assert batch_workflow._display_value(record, "calculated_mL") == 12.5
    assert batch_workflow._display_value(record, "chemistry") == "DIC/HOBt"
    assert batch_workflow._display_value(record, "loading_mmol_g") == 0.68


def test_batch_uses_editable_rows_and_recognizes_protected_aa_linker_tag():
    row = {
        "No": 1, "Project": "P", "Peptide name": "Pep", "Copies": "2",
        "Region 1 seq": "ACDE", "Region 1 eq": "1", "Linker": "Ahx",
        "Tag": "His6", "Label": "FITC", "C-term": "NH2",
        "Chemistry": "DIC/HOBt",
        "Scale mmol": "0.2", "AA conc M": "0.25", "AA coupling eq": "5",
        "Resin": "Rink Amide AM", "Loading": "0.8", "LOT No": "L-1",
    }
    gui = type("Gui", (), {})()
    gui.pm_items = []
    gui.batch_columns = list(BATCH_COLUMNS)
    gui.batch_tree = _Tree(BATCH_COLUMNS, [row])

    tables = batch_workflow.calculate(gui)

    assert len(tables["Summary"]) == 1
    aa_items = set(tables["AA stock"]["Item"])
    assert aa_items == {
        "Fmoc-Ala-OH", "Fmoc-Cys(Trt)-OH", "Fmoc-Asp(OtBu)-OH",
        "Fmoc-Glu(OtBu)-OH",
    }
    assert not aa_items.intersection({"A", "C", "D", "E"})
    chemical_items = set(tables["Chemicals"]["Item"])
    assert "Fmoc-6-Ahx-OH" in chemical_items
    assert "His6 peptide tag macro (HHHHHH)" in chemical_items
    assert "FITC isothiocyanate" in chemical_items
    assert "His6 peptide tag macro (HHHHHH)" not in set(
        tables["Coupling reagents"]["Item"]
    )


class _Listbox:
    def curselection(self):
        return (1,)


def test_project_switch_does_not_reserialize_unchanged_output_trees(monkeypatch):
    gui = type("Gui", (), {})()
    gui.pm_items = [{"project": "A"}, {"project": "B"}]
    gui.pm_list = _Listbox()
    gui._v229_active_index = 0
    gui._v229_dirty_columns = {}
    gui._v2212_switching = False
    gui._v2212_dragging = False
    calls = []

    monkeypatch.setattr(
        project_manager_workflow, "_save_active",
        lambda _gui, _workflow, include_outputs=True: calls.append(include_outputs),
    )
    monkeypatch.setattr(
        project_manager_workflow, "_restore",
        lambda _gui, _workflow, _namespace, index: calls.append(("restore", index)),
    )

    project_manager_workflow.single_select(gui, object(), {})

    assert calls == [False, ("restore", 1)]


def test_batch_sequence_does_not_misread_dashed_alanine_cysteine_as_acetyl():
    row = {
        "Region 1 seq": "ACD", "Region 1 eq": "1", "Linker": "PEG4",
        "C-term": "NH2",
    }
    sequence = batch_workflow._batch_sequence(row)

    from spps_planner.parser import parse_sequence

    parsed = parse_sequence(sequence)
    assert parsed.nterm == ""
    assert parsed.core_tokens == ["A", "C", "D", "Fmoc-NH-PEG4-CH2COOH"]

    dashed = parse_sequence("A-C-D-NH2")
    assert dashed.nterm == ""
    assert dashed.core_tokens == ["A", "C", "D"]

    typed = parse_sequence("[His6]-[FITC]-ACD-[PEG4]-NH2")
    assert typed.nterm == "His6"
    assert typed.core_tokens == ["FITC", "A", "C", "D", "PEG4"]


def test_batch_restore_prefers_saved_operator_rows_and_falls_back_to_projects():
    saved = {column: "" for column in BATCH_COLUMNS}
    saved.update({"Project": "Saved", "Peptide name": "Edited", "Region 1 seq": "ACD"})
    gui = type("Gui", (), {})()
    gui.batch_columns = list(BATCH_COLUMNS)
    gui.batch_tree = _Tree(BATCH_COLUMNS)
    gui.pm_items = [{"project": "Project", "peptide": "Pep", "sequence": "RRR"}]

    batch_workflow.restore_input_rows(gui, [saved])
    assert batch_workflow._batch_input_rows(gui)[0]["Project"] == "Saved"

    batch_workflow.restore_input_rows(gui, [])
    row = batch_workflow._batch_input_rows(gui)[0]
    assert row["Project"] == "Project"
    assert row["Region 1 seq"] == "RRR"


def test_batch_generates_each_project_step_plan_once(monkeypatch):
    from spps_planner import engine

    original = engine.generate_step_reagent_plan
    calls = []

    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(engine, "generate_step_reagent_plan", counted)
    gui = type("Gui", (), {})()
    gui.pm_items = [{
        "project": "P", "peptide": "Pep", "sequence": "Ac-ACD-NH2",
        "copies": "1", "scale": "0.2", "resin": "Rink Amide AM",
        "loading": "0.8", "chemistry": "DIC/HOBt",
    }]

    batch_workflow.calculate(gui)

    assert len(calls) == 1


def test_ac_is_visible_in_project_plan_and_batch_chemical_preparation():
    from spps_planner.engine import PlanInput
    from suite_gui.modules import plan_workflow

    class _Var:
        def __init__(self, current):
            self.current = current

        def get(self):
            return self.current

    gui = type("Gui", (), {})()
    gui.custom_materials = {}
    gui.pm_sequence = _Var("Ac-EEMQRR-NH2")
    gui.use_position_aa_eq = _Var(True)
    gui.use_position_doubling = _Var(True)
    gui.position_aa_eq_rules = _Var("")
    gui.position_doubling_rules = _Var("")
    gui.reagent_eq_follows_coupling_eq = _Var(True)
    gui.coupling_eq = _Var("5")

    plan_rows = plan_workflow._generated_plan_rows(
        gui, {}, PlanInput(
            sequence="Ac-EEMQRR-NH2", scale_mmol=0.5,
            resin="Rink Amide AM", resin_loading_mmol_g=0.68,
        ),
    )
    assert len(plan_rows) == 7
    assert plan_rows[-1]["Unit name"] == (
        "Acetic anhydride (Ac2O)"
    )

    gui.pm_items = [{
        "project": "P", "peptide": "Pep", "sequence": "Ac-EEMQRR-NH2",
        "copies": "1", "scale": "0.5", "resin": "Rink Amide AM",
        "loading": "0.68", "chemistry": "DIC/HOBt",
    }]
    tables = batch_workflow.calculate(gui)
    ac = tables["Chemicals"].iloc[0]
    assert ac["Item"] == "Acetic anhydride"
    assert ac["MW"] == 102.09
    assert ac["Density"] == 1.08
    assert float(ac["Volume_mL"]) > 0


def test_classic_batch_dashboard_schema_is_fully_populated_and_separated():
    gui = type("Gui", (), {})()
    gui.pm_items = [{
        "project": "P", "peptide": "Pep", "sequence": "Ac-EEMQRR-NH2",
        "copies": "1", "scale": "0.5", "resin": "Rink Amide AM",
        "loading": "0.68", "chemistry": "DIC/HOBt",
    }]
    gui.batch_aa_tree = _Tree(
        ["AA", "count", "eq", "conc_M", "calc_mL", "actual_mL", "MW", "weight_g", "note"]
    )
    common = [
        "item", "purpose", "count", "eq", "conc_M", "calculated",
        "actual", "unit", "MW", "density", "weight_g", "volume_mL", "note",
    ]
    gui.batch_coupling_reagent_tree = _Tree(common)
    gui.batch_catalyst_tree = _Tree(common)
    gui.batch_base_tree = _Tree(common)
    gui.batch_solvent_tree = _Tree(common)
    gui.batch_modifier_tree = _Tree(common)
    gui.batch_project_tree = _Tree([
        "no", "project", "peptide_name", "lot_no", "copies", "sequence",
        "scale_mmol", "resin", "output_folder",
    ])

    batch_workflow.refresh(gui, force=True)

    aa_values = next(iter(gui.batch_aa_tree.rows.values()))
    assert aa_values[0].startswith("Fmoc-")
    assert aa_values[1] and aa_values[2] and aa_values[3]
    assert aa_values[4] and aa_values[5] and aa_values[6] and aa_values[7]
    base_items = {row[0] for row in gui.batch_base_tree.rows.values()}
    catalyst_items = {row[0] for row in gui.batch_catalyst_tree.rows.values()}
    assert {"DIEA", "Piperidine"} <= base_items
    assert "DIEA" not in catalyst_items
    modifier_items = {row[0] for row in gui.batch_modifier_tree.rows.values()}
    assert "Acetic anhydride" in modifier_items
    project_values = next(iter(gui.batch_project_tree.rows.values()))
    assert project_values[1:3] == ("P", "Pep")


def test_batch_uses_each_rows_aa_concentration_and_equivalents():
    first = {column: "" for column in BATCH_COLUMNS}
    first.update({
        "No": "1", "Project": "P1", "Peptide name": "One",
        "Copies": "1", "Region 1 seq": "A", "Region 1 eq": "1",
        "C-term": "NH2", "Chemistry": "DIC/HOBt", "Scale mmol": "1",
        "AA conc M": "0.5", "AA coupling eq": "2",
        "Resin": "Rink Amide AM", "Loading": "0.8",
    })
    second = dict(first)
    second.update({
        "No": "2", "Project": "P2", "Peptide name": "Two",
        "AA conc M": "0.25", "AA coupling eq": "4",
    })
    gui = type("Gui", (), {})()
    gui.pm_items = []
    gui.batch_columns = list(BATCH_COLUMNS)
    gui.batch_tree = _Tree(BATCH_COLUMNS, [first, second])

    aa = batch_workflow.calculate(gui)["AA stock"]

    assert set(aa["Eq"]) == {2.0, 4.0}
    assert set(aa["Conc_M"]) == {0.5, 0.25}


def test_compact_material_list_groups_l_d_non_natural_then_chemical():
    gui = type("Gui", (), {})()
    gui.pm_items = [{
        "project": "P", "peptide": "Grouped", "sequence": "Ac-dR-V-Cit-NH2",
        "copies": "1", "scale": "0.2", "resin": "Rink Amide AM",
        "loading": "0.8", "chemistry": "DIC/HOBt",
        "tag": "His6", "label": "FITC", "linker": "AEEA", "c_term": "NH2",
    }]

    grouped = batch_workflow.calculate(gui)["AA + Chemicals"]
    pairs = list(grouped[["Category", "Item"]].itertuples(index=False, name=None))
    categories = [category for category, _ in pairs]
    order = {"L-AA": 0, "D-AA": 1, "Non-natural AA": 2, "Chemical": 3}
    assert [order[category] for category in categories] == sorted(order[category] for category in categories)
    assert ("D-AA", "Fmoc-D-Arg(Pbf)-OH") in pairs
    assert ("Non-natural AA", "Fmoc-Cit-OH") in pairs
    assert ("Chemical", "Acetic anhydride") in pairs
    assert ("Chemical", "FITC isothiocyanate") in pairs
    assert ("Chemical", "Fmoc-AEEA-OH") in pairs
    assert any(category == "Chemical" and item.startswith("His6") for category, item in pairs)
    for category in ("L-AA", "D-AA", "Non-natural AA", "Chemical"):
        items = [item for current, item in pairs if current == category]
        assert items == sorted(items, key=str.casefold)


def test_shared_compact_tree_is_not_overwritten_by_chemical_repaint():
    gui = type("Gui", (), {})()
    gui.pm_items = [{
        "project": "P", "peptide": "Grouped", "sequence": "dR-V-Cit-NH2",
        "copies": "1", "scale": "0.2", "resin": "Rink Amide AM",
        "loading": "0.8", "chemistry": "DIC/HOBt", "label": "FITC",
    }]
    shared = _Tree(batch_workflow.BATCH_COLUMNS)
    gui.batch_aa_tree = shared
    gui.batch_modifier_tree = shared
    gui.batch_coupling_reagent_tree = None
    gui.batch_catalyst_tree = None
    gui.batch_base_tree = None
    gui.batch_solvent_tree = None
    gui.batch_project_tree = None
    gui.v29_batch_trees = {}

    batch_workflow.refresh(gui, force=True)
    pairs = [(row[0], row[1]) for row in shared.rows.values()]
    assert ("L-AA", "Fmoc-Val-OH") in pairs
    assert ("D-AA", "Fmoc-D-Arg(Pbf)-OH") in pairs
    assert ("Non-natural AA", "Fmoc-Cit-OH") in pairs
    assert ("Chemical", "FITC isothiocyanate") in pairs
