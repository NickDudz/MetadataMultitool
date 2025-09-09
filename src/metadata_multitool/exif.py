from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List


def has_exiftool() -> bool:
    try:
        subprocess.run(["exiftool", "-ver"], check=True, capture_output=True, text=True)
        return True
    except Exception:
        return False


def run_exiftool(args: List[str]) -> None:
    subprocess.run(["exiftool", *args], check=True, text=True)


def strip_all_metadata(img: Path) -> None:
    if has_exiftool():
        run_exiftool(["-overwrite_original", "-all=", str(img)])
    else:
        from PIL import Image

        with Image.open(img) as im:
            data = list(im.getdata())
            im_noexif = Image.new(im.mode, im.size)
            im_noexif.putdata(data)
            im_noexif.save(img)
