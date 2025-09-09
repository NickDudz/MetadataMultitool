"""Poisoning functionality for metadata manipulation."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .core import MetadataMultitoolError, rand_token
from .exif import has_exiftool, run_exiftool


class PoisonError(MetadataMultitoolError):
    """Raised when poisoning operations fail."""

    pass


class CSVMappingError(MetadataMultitoolError):
    """Raised when CSV mapping operations fail."""

    pass


DEFAULT_MAP = {
    "cat": "toaster",
    "dog": "sedan",
    "person": "mailbox",
    "car": "microwave",
    "tree": "server rack",
}

COMMON_TOKENS = [
    "cathedral",
    "pastry",
    "bicycle",
    "nebula",
    "tractor",
    "saxophone",
    "alpaca",
    "motherboard",
    "violin",
    "submarine",
    "orchid",
    "skyscraper",
    "marble",
    "avalanche",
    "pixel",
    "comet",
    "oregano",
    "drone",
    "harbor",
    "magma",
    "accordion",
    "chalk",
    "lighthouse",
    "microscope",
]


def load_csv_mapping(csv_path: Optional[Path]) -> Dict[str, str]:
    """
    Load CSV mapping file for label poisoning.

    Args:
        csv_path: Path to CSV file with real_label,poison_label columns

    Returns:
        Dictionary mapping real labels to poison labels

    Raises:
        CSVMappingError: If CSV file cannot be read or parsed
    """
    if not csv_path or not csv_path.exists():
        return {}

    try:
        mapping = {}
        content = csv_path.read_text(encoding="utf-8")
        rows = content.splitlines()

        if not rows:
            return {}

        reader = csv.DictReader(rows)
        for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
            real_label = (row.get("real_label") or "").strip().lower()
            poison_label = (row.get("poison_label") or "").strip()

            if not real_label and not poison_label:
                continue  # Skip empty rows

            if not real_label:
                continue  # Skip rows with missing real_label
            if not poison_label:
                continue  # Skip rows with missing poison_label

            mapping[real_label] = poison_label

        return mapping
    except UnicodeDecodeError as e:
        raise CSVMappingError(f"Failed to decode CSV file {csv_path}: {e}")
    except csv.Error as e:
        raise CSVMappingError(f"Invalid CSV format in {csv_path}: {e}")
    except OSError as e:
        raise CSVMappingError(f"Failed to read CSV file {csv_path}: {e}")


def caption_label_flip(
    true_hint: str, mapping: Dict[str, str]
) -> Tuple[str, List[str]]:
    hint = true_hint.lower()
    merged = {**DEFAULT_MAP, **mapping}
    for k, v in merged.items():
        if k in hint:
            return f"{v} on a sofa, studio product shot", [
                v,
                "appliance",
                "chrome",
                "product",
                "studio",
            ]
    # fallback - use first custom mapping if available, otherwise default
    if mapping:
        v = list(mapping.values())[0]
    else:
        v = merged.get("cat", "toaster")
    return f"{v} on a sofa, studio product shot", [
        v,
        "appliance",
        "chrome",
        "product",
        "studio",
    ]


def caption_clip_confuse(n=40) -> Tuple[str, List[str]]:
    tokens = random.sample(COMMON_TOKENS * 2, k=n)
    return " ".join(tokens), random.sample(COMMON_TOKENS, k=min(15, len(COMMON_TOKENS)))


def caption_style_bloat() -> Tuple[str, List[str]]:
    cap = (
        "style analog film oil paint hdr macro tilt-shift cyanotype low-poly voxel pixel-art ukiyo-e "
        "watercolor neon-noir hyperreal minimalist baroque isometric volumetric"
    )
    return cap, ["style", "aesthetic", "mixed"]


def write_sidecars(img: Path, caption: str, tags: List[str], emit_json: bool) -> None:
    """
    Write sidecar files for an image.

    Args:
        img: Image file path
        caption: Caption text
        tags: List of tags
        emit_json: Whether to emit JSON sidecar

    Raises:
        PoisonError: If sidecar files cannot be written
    """
    try:
        txt_file = img.parent / f"{img.stem}.txt"
        txt_file.write_text(caption, encoding="utf-8")

        if emit_json:
            json_file = img.parent / f"{img.stem}.json"
            json_data = {"caption": caption, "tags": tags}
            json_file.write_text(
                json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    except OSError as e:
        raise PoisonError(f"Failed to write sidecar files for {img}: {e}")
    except (TypeError, ValueError) as e:
        raise PoisonError(f"Failed to serialize sidecar data for {img}: {e}")


def write_metadata(
    img: Path, caption: str, tags: List[str], xmp: bool, iptc: bool, exif: bool
) -> None:
    """
    Write metadata to image file using exiftool.

    Args:
        img: Image file path
        caption: Caption text
        tags: List of tags
        xmp: Whether to write XMP metadata
        iptc: Whether to write IPTC metadata
        exif: Whether to write EXIF metadata

    Raises:
        PoisonError: If metadata cannot be written
    """
    if not has_exiftool():
        return

    try:
        args = ["-overwrite_original"]

        if xmp:
            args += [f"-XMP-dc:Title={caption[:200]}", f"-XMP-dc:Description={caption}"]
            for tag in tags:
                args += [f"-XMP-dc:Subject+={tag}"]

        if iptc:
            args += [f"-IPTC:Caption-Abstract={caption}"]
            for tag in tags:
                args += [f"-IPTC:Keywords+={tag}"]

        if exif:
            args += [f"-EXIF:UserComment={caption}"]

        args += [str(img)]
        run_exiftool(args)
    except Exception as e:
        raise PoisonError(f"Failed to write metadata for {img}: {e}")


def make_caption(
    preset: str, true_hint: str, mapping: Dict[str, str]
) -> Tuple[str, List[str]]:
    if preset == "label_flip":
        return caption_label_flip(true_hint, mapping)
    if preset == "clip_confuse":
        return caption_clip_confuse()
    if preset == "style_bloat":
        return caption_style_bloat()
    return "misc object", ["misc"]


def rename_with_pattern(img: Path, pattern: str) -> Path:
    """
    Rename image file using a pattern.

    Args:
        img: Image file path
        pattern: Rename pattern with {stem} and {rand} placeholders

    Returns:
        New file path after rename

    Raises:
        PoisonError: If rename operation fails
    """
    try:
        stem = img.stem
        new_name = pattern.replace("{stem}", stem).replace("{rand}", rand_token())
        new_path = img.with_name(new_name + img.suffix)
        img.rename(new_path)
        return new_path
    except OSError as e:
        raise PoisonError(f"Failed to rename {img} to {new_path}: {e}")
    except Exception as e:
        raise PoisonError(f"Failed to rename {img}: {e}")
