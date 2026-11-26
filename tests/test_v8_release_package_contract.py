"""Source-package hygiene and V9 release identity guardrails."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v8_release_version_and_citation():
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "V9.0.0"
    assert (ROOT / "VERSION.txt").read_text(encoding="utf-8").strip() == "V9.0.0"
    assert 'version: "9.0.0"' in (ROOT / "CITATION.cff").read_text(encoding="utf-8")


def test_minimal_windows_build_entrypoints():
    scripts = {p.name for p in ROOT.glob("*.bat")}
    assert scripts == {"INSTALL_BUILD_TOOLS_AND_BUILD.bat"}
    content = (ROOT / "INSTALL_BUILD_TOOLS_AND_BUILD.bat").read_text(encoding="utf-8")
    for token in ("winget install", "--no-pause", "PyInstaller", "--self-test",
                  "verify_packaged_runtime.py", "ISCC", "--check-installer",
                  "SPPS_Planner_PUBLIC_Setup_V9.0.0.exe"):
        assert token in content
    assert "BUILD_EXE_ONLY.bat" not in content
    assert "BUILD_INSTALLER.bat" not in content


def test_release_docs_and_no_archived_notes():
    assert (ROOT / "README.md").is_file()
    assert (ROOT / "README_KO.md").is_file()
    assert (ROOT / "RELEASE_NOTES_V9.0.0.txt").is_file()
    assert not (ROOT / "PACKAGE_README.md").exists()
    assert not (ROOT / "docs/release_history").exists()


def test_v9_export_output_filenames():
    source = (ROOT / "suite_gui/modules/plan_workflow.py").read_text(encoding="utf-8")
    assert "project_manager_selected_outputs_v9.0.0.xlsx" in source
    assert "project_manager_state_v9.0.0.json" in source
    assert "project_manager_selected_outputs_v7.0.0.xlsx" not in source


def test_current_windows_installer_docs_and_ci_match_build():
    """Public/Private installer naming stays in sync with the one build BAT."""
    expected = "SPPS_Planner_PUBLIC_Setup_V9.0.0.exe"
    build = (ROOT / "INSTALL_BUILD_TOOLS_AND_BUILD.bat").read_text(encoding="utf-8")
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    guide = (ROOT / "docs/WINDOWS_BUILD_KO.md").read_text(encoding="utf-8")
    read_first = (ROOT / "WINDOWS_INSTALLER_READ_FIRST_KO.txt").read_text(encoding="utf-8")
    for content in (build, ci, guide, read_first):
        assert expected in content
    assert "RUN_BUILD_WITH_LOG.cmd" not in read_first
    assert "BUILD_INSTALLER_DIAGNOSTICS.log" not in read_first
    assert "INSTALL_BUILD_TOOLS_AND_BUILD.bat" in read_first
    assert "installer\\output\\SPPS_Planner_Setup_V9.0.0.exe" not in guide
    assert "installer\\output\\SPPS_Planner_Setup_V9.0.0.exe" not in ci
