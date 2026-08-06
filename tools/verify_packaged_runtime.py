"""Validate the functional report written by the packaged Windows EXE."""
from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> int:
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("app_version") != "V3.0.0" or not data.get("ok"):
        raise RuntimeError(f"Packaged runtime self-test failed: {data}")
    failed = [key for key, value in data.get("checks", {}).items() if not value]
    if failed:
        raise RuntimeError("Failed packaged checks: " + ", ".join(failed))
    print(f"[OK] Packaged runtime {data['build_revision']} passed all functional checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
