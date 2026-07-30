from __future__ import annotations

from pathlib import Path

from tools.audit_monkey_patches import audit


def test_monkey_patch_audit_tracks_build_wrappers_and_hotspots():
    root = Path(__file__).resolve().parents[1] / "suite_gui"
    report = audit(root)

    assert report["python_files"] > 10
    assert report["binding_count"] > 100
    assert report["build_wrapper_count"] > 5
    assert "legacy_controller.py" in report["bindings_by_file"]
