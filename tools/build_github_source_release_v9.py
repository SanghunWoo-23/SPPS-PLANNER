"""Build deterministic PUBLIC-only ZIP; never publish/modify GitHub automatically."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
import zipfile

from github_release_preflight_v9 import ROOT, inventory, validate


def build(root: Path, destination: Path) -> str:
    root = root.resolve()
    report = validate(root, strict=True)
    if not report["passed"]:
        raise ValueError("Public release preflight failed: " + "; ".join(report["errors"]))
    destination = destination.resolve()
    if destination == root or root in destination.parents:
        raise ValueError("Release ZIP output must be outside the source tree")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as zip_file:
            for rel in [*inventory(root), Path("SOURCE_MANIFEST.sha256")]:
                # Stable ZIP timestamps and order across packaging runs.
                source = root / rel
                info = zipfile.ZipInfo(f"SPPS_Planner_V9.0.0_PUBLIC/{rel.as_posix()}", (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                zip_file.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(temporary) as check:
            if check.testzip() is not None:
                raise ValueError("ZIP CRC validation failed")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    return digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        digest = build(args.root, args.output)
    except (ValueError, OSError) as err:
        print(f"PUBLIC RELEASE BLOCKED: {err}", file=sys.stderr)
        return 1
    print(f"SHA256 {digest}  {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
