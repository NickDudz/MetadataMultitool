from __future__ import annotations

import subprocess
import json
from pathlib import Path
from typing import List, Set, Dict, Any


def has_exiftool() -> bool:
    try:
        subprocess.run(["exiftool", "-ver"], check=True, capture_output=True, text=True)
        return True
    except Exception:
        return False


def run_exiftool(args: List[str]) -> None:
    try:
        result = subprocess.run(["exiftool", *args], check=True, text=True, capture_output=True)
        # Check if ExifTool reported any errors in stderr
        if result.stderr and "Error:" in result.stderr:
            # Handle specific known errors gracefully
            if "Writing of BMP files is not yet supported" in result.stderr:
                # BMP files can't be written by ExifTool, but that's okay for our use case
                return
            elif "Format error in file" in result.stderr:
                # File is empty or corrupted, skip processing
                return
            else:
                # Re-raise for other errors
                raise subprocess.CalledProcessError(1, ["exiftool", *args], result.stdout, result.stderr)
    except subprocess.CalledProcessError as e:
        # Handle specific ExifTool errors gracefully
        if e.stderr and "Writing of BMP files is not yet supported" in e.stderr:
            # BMP files can't be written by ExifTool, but that's okay for our use case
            return
        elif e.stderr and "Format error in file" in e.stderr:
            # File is empty or corrupted, skip processing
            return
        else:
            # Re-raise for other errors
            raise


def get_metadata_fields(file_path: Path) -> Set[str]:
    """
    Get all metadata field names from an image file using ExifTool.
    
    Args:
        file_path: Path to image file
        
    Returns:
        Set of metadata field names
    """
    if not has_exiftool():
        return set()
    
    try:
        result = subprocess.run(
            ["exiftool", "-json", "-s", str(file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        if not result.stdout.strip():
            return set()
            
        metadata = json.loads(result.stdout)
        if not metadata or not isinstance(metadata, list) or not metadata[0]:
            return set()
            
        # Remove non-metadata fields
        fields = set(metadata[0].keys())
        fields.discard("SourceFile")
        fields.discard("ExifToolVersion")
        
        return fields
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, IndexError):
        return set()


def strip_all_metadata(img: Path) -> None:
    # Skip BMP files as ExifTool cannot write to them
    if img.suffix.lower() == '.bmp':
        return
        
    if has_exiftool():
        run_exiftool(["-overwrite_original", "-all=", str(img)])
    else:
        from PIL import Image

        with Image.open(img) as im:
            data = list(im.getdata())
            im_noexif = Image.new(im.mode, im.size)
            im_noexif.putdata(data)
            im_noexif.save(img)
