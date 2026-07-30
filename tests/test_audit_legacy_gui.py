from __future__ import annotations

from pathlib import Path

from tools.audit_legacy_gui import audit


def test_legacy_audit_finds_patch_hotspots_without_importing_tk():
    root = Path(__file__).resolve().parents[1]
    report = audit(root / "suite_gui" / "legacy_controller.py")

    assert report["line_count"] > 40_000
    assert report["top_level_definition_count"] > 100
    assert report["spps_gui_binding_count"] > 100
    assert report["repeated_spps_gui_bindings"]
    assert report["preserved_aliases"]
