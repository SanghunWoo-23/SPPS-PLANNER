"""Repeatable final verification for the SPPS Planner V2.0.0 source release."""
from __future__ import annotations

import argparse
import compileall
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "V2.0.0"
REQUIRED_FILES = (
    "main_launcher.py",
    "SPPS_Planner.spec",
    "BUILD_EXE_ONLY.bat",
    "BUILD_INSTALLER.bat",
    "INSTALL_BUILD_TOOLS_AND_BUILD.bat",
    "assets/SPPS_Planner_Icon.ico",
    "installer/SPPS_Planner_Setup.iss",
)


def verify_static_release() -> None:
    missing = [name for name in REQUIRED_FILES if not (ROOT / name).is_file()]
    if missing:
        raise RuntimeError("Missing release files: " + ", ".join(missing))
    for name in ("VERSION", "VERSION.txt"):
        actual = (ROOT / name).read_text(encoding="utf-8").strip()
        if actual != EXPECTED_VERSION:
            raise RuntimeError(f"{name} is {actual!r}, expected {EXPECTED_VERSION!r}")
    from suite_gui.release import SPPSGui
    from suite_gui.release_contract import validate_release_controller

    validate_release_controller(SPPSGui)
    if SPPSGui.TITLE != "SPPS Planner V2.0.0":
        raise RuntimeError(f"Unexpected release title: {SPPSGui.TITLE}")


def run_tests(passes: int) -> None:
    for number in range(1, passes + 1):
        print(f"[verify] pytest pass {number}/{passes}", flush=True)
        subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=ROOT,
            check=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--passes", type=int, default=1)
    args = parser.parse_args()
    if args.passes < 1:
        parser.error("--passes must be at least 1")
    sys.path.insert(0, str(ROOT))
    verify_static_release()
    if not compileall.compile_dir(ROOT / "suite_gui", quiet=1):
        raise RuntimeError("suite_gui compilation failed")
    if not compileall.compile_dir(
        ROOT / "apps" / "spps_planner_app" / "spps_planner",
        quiet=1,
    ):
        raise RuntimeError("spps_planner compilation failed")
    run_tests(args.passes)
    print(f"[verify] SPPS Planner {EXPECTED_VERSION}: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
