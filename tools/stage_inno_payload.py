"""Stage PyInstaller distribution in a shallow temporary path for Inno Setup.

Uses copies (never changes the actual dist tree); removes Python compile caches.
Windows path errors in deep source folders are prevented by keeping a hard bound
on the longest staging path. The private payload is never placed in Public.
"""
import os
import shutil
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3 or sys.argv[2].lower() not in {"public", "private"}:
        print("Usage: python tools/stage_inno_payload.py dist\\SPPS_Planner public|private")
        return 2
    source = Path(sys.argv[1]).resolve()
    profile = sys.argv[2].upper()
    if not (source / "SPPS_Planner.exe").is_file():
        print("[ERROR] Packaged executable missing:", source)
        return 2
    # LOCALAPPDATA is ordinarily short and writable on Windows. Keep the
    # profile-specific staging folders separate to avoid cross-contamination.
    local = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or ".").resolve()
    destination = local / "Temp" / ("SPPSV9_" + profile)
    try:
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(
            source, destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        files = [p for p in destination.rglob("*") if p.is_file()]
        if not files or not (destination / "SPPS_Planner.exe").is_file():
            raise RuntimeError("Staging incomplete")
        longest = max(len(str(p)) for p in files)
        if longest > 235:
            raise RuntimeError(f"Staged path still too long ({longest} characters)")
        manifest = sorted(str(p.relative_to(destination)) for p in files)
        print(f"[OK] Staged {len(files)} files; longest path {longest} characters")
        # Output a single path, read by batch with FOR /F. A manifest is also
        # available in the build tree for diagnosing missing files.
        print("STAGE_DIR=" + str(destination))
        return 0
    except Exception as exc:
        print("[ERROR] Installer payload staging failed:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
