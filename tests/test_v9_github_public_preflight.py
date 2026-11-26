"""V9 public release hard-stop tests. No GUI and no optional runtime packages."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "github_release_preflight_v9.py"
spec = importlib.util.spec_from_file_location("github_release_preflight_v9", SCRIPT)
assert spec and spec.loader
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


def _root(tmp_path: Path) -> Path:
    for rel in preflight.REQUIRED:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("V9.0.0\n" if rel in ("VERSION", "VERSION.txt") else "test\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("not an OSI-approved open-source license\n", encoding="utf-8")
    (tmp_path / "CITATION.cff").write_text("version: 9.0.0\n", encoding="utf-8")
    (tmp_path / preflight.MANIFEST).write_text(preflight.make_manifest(tmp_path), encoding="utf-8")
    return tmp_path


def test_public_contract_accepts_clean_fixture(tmp_path: Path) -> None:
    root = _root(tmp_path)
    assert preflight.validate(root, strict=True)["passed"]


def test_tampering_detected_by_manifest(tmp_path: Path) -> None:
    root = _root(tmp_path)
    (root / "README.md").write_text("altered", encoding="utf-8")
    assert any("SHA-256" in issue for issue in preflight.validate(root, strict=True)["errors"])


def test_rejects_hidden_private_dataset(tmp_path: Path) -> None:
    root = _root(tmp_path)
    private = root / "apps/spps_planner_app/data/experimental_seed/secret.xlsx"
    private.parent.mkdir(parents=True, exist_ok=True)
    private.write_bytes(b"fake")
    issues = preflight.validate(root, strict=False)["errors"]
    assert any("seed" in issue for issue in issues)


def test_rejects_local_model_or_secret(tmp_path: Path) -> None:
    root = _root(tmp_path)
    (root / "trained.joblib").write_bytes(b"fake")
    (root / ".env.local").write_text("TOKEN=demo", encoding="utf-8")
    errors = preflight.validate(root, strict=False)["errors"]
    assert any("trained.joblib" in issue for issue in errors)
    assert any(".env.local" in issue for issue in errors)


def test_citation_version_mismatch(tmp_path: Path) -> None:
    root = _root(tmp_path)
    (root / "CITATION.cff").write_text("version: 8.0.0\n", encoding="utf-8")
    assert any("CITATION" in issue for issue in preflight.validate(root, strict=False)["errors"])


def test_private_actual_run_data_rejected(tmp_path: Path) -> None:
    root = _root(tmp_path)
    p = root / "apps/spps_planner_app/data/actual_runs.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("run_id,sequence\n123,AAAA\n", encoding="utf-8")
    assert any("actual_runs" in issue for issue in preflight.validate(root, strict=False)["errors"])
