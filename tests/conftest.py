from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "spps_planner_app"
for path in (ROOT, APP):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

# Keep tests isolated from a developer's real SPPS Planner profile and make
# the suite runnable in containers whose home directory is read-only.
_TEST_PROFILE = Path(tempfile.gettempdir()) / "spps-planner-test-profile"
os.environ.setdefault("XDG_DATA_HOME", str(_TEST_PROFILE / "data"))
os.environ.setdefault("XDG_CONFIG_HOME", str(_TEST_PROFILE / "config"))
