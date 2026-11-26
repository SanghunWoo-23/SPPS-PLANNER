import importlib.util
import os
from pathlib import Path
import subprocess
import sys


def test_stage_payload(tmp_path):
    src = tmp_path / "dist" / "SPPS_Planner"
    src.mkdir(parents=True)
    (src / "SPPS_Planner.exe").write_bytes(b"test-only")
    cache = src / "deep" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "test.pyc").write_bytes(b"unused")
    (src / "deep" / "required.txt").write_text("test", encoding="utf-8")
    env = {**os.environ, "LOCALAPPDATA": str(tmp_path / "local")}
    tool = Path(__file__).resolve().parents[1] / "tools" / "stage_inno_payload.py"
    for profile in ("public", "private"):
        result = subprocess.run([sys.executable, str(tool), str(src), profile], capture_output=True, text=True, env=env)
        assert result.returncode == 0, result.stdout + result.stderr
        path_line = next(line for line in result.stdout.splitlines() if line.startswith("STAGE_DIR="))
        stage = Path(path_line.split("=", 1)[1])
        assert (stage / "SPPS_Planner.exe").is_file()
        assert (stage / "deep" / "required.txt").is_file()
        assert not list(stage.rglob("*.pyc"))
        assert "SPPSV9_" + profile.upper() in str(stage)
