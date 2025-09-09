from __future__ import annotations

import json
from pathlib import Path

from .core import read_log, write_log
from .exif import has_exiftool, run_exiftool


def revert_dir(dirpath: Path) -> int:
    log = read_log(dirpath)
    removed = 0

    # Process all entries
    for rel, entry in list(log.get("entries", {}).items()):
        p = dirpath / rel
        orig = entry.get("original_name")

        # First, remove sidecars and clear fields for the current file
        if p.exists():
            # sidecars
            for ext in (".txt", ".json", ".html"):
                s = p.with_suffix(ext)
                if s.exists():
                    s.unlink()
                    removed += 1
            # fields
            if has_exiftool():
                run_exiftool(
                    [
                        "-overwrite_original",
                        "-XMP-dc:Title=",
                        "-XMP-dc:Description=",
                        "-IPTC:Caption-Abstract=",
                        "-EXIF:UserComment=",
                        "-XMP-dc:Subject=",
                        "-IPTC:Keywords=",
                        str(p),
                    ]
                )

        # Then rename if needed
        if orig and p.exists() and p.name != orig:
            target = p.with_name(orig)
            try:
                p.rename(target)
                # Update the log entry to reflect the rename
                # Remove the old entry and add a new one with the original name
                del log["entries"][rel]
                log["entries"][orig] = entry.copy()
                log["entries"][orig]["original_name"] = None
            except Exception:
                pass
        else:
            # drop entry (only if not renamed)
            del log["entries"][rel]

    write_log(dirpath, log)
    return removed
