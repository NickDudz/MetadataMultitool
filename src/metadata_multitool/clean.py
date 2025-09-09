from __future__ import annotations

import shutil
from pathlib import Path

from .core import ensure_dir
from .exif import strip_all_metadata


def clean_copy(src: Path, dest_dir: Path) -> Path:
    ensure_dir(dest_dir)
    out = dest_dir / src.name
    shutil.copy2(src, out)
    strip_all_metadata(out)
    return out
