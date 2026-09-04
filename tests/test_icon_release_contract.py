from __future__ import annotations

import ast
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def test_release_icon_has_transparent_multisize_frames() -> None:
    icon_path = ROOT / "assets" / "SPPS_Planner_Icon.ico"
    image = Image.open(icon_path)
    required = {(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (128, 128), (256, 256)}
    assert required.issubset(image.ico.sizes())
    for size in required:
        frame = image.ico.getimage(size).convert("RGBA")
        assert frame.getpixel((0, 0))[3] == 0
        assert frame.getbbox() is not None


def test_source_icon_is_transparent_and_square() -> None:
    image = Image.open(ROOT / "assets" / "SPPS_Planner_Icon.png").convert("RGBA")
    assert image.width == image.height == 500
    assert image.getpixel((0, 0))[3] == 0
    assert image.getbbox() is not None


def test_icon_code_is_structural_and_importable() -> None:
    for relative in ("suite_gui/modern_tk_gui.py", "peptiforg_core/ui_helpers.py"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        ast.parse(source)
        assert "monkey" not in source.lower()
        assert "placeholder" not in source.lower()


def test_windows_icon_is_not_overridden_by_png() -> None:
    modern = (ROOT / "suite_gui/modern_tk_gui.py").read_text(encoding="utf-8")
    helpers = (ROOT / "peptiforg_core/ui_helpers.py").read_text(encoding="utf-8")
    assert 'if not applied and png.exists()' in modern
    assert 'if not applied:' in helpers
    assert 'iconbitmap(default=str(ico))' in modern
    assert 'iconbitmap(default=str(ico))' in helpers
