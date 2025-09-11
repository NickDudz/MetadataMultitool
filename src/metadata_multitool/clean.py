from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional, Set, Dict, Any, List
import tempfile
import subprocess
import json

from .core import ensure_dir, iter_images
from .exif import strip_all_metadata, get_metadata_fields, has_exiftool
from .metadata_profiles import MetadataProfile, apply_profile_to_fields, get_predefined_profiles


def clean_copy(
    src: Path, 
    dest_dir: Path, 
    profile: Optional[MetadataProfile] = None,
    preserve_fields: Optional[Set[str]] = None
) -> Path:
    """
    Create a cleaned copy of an image file.
    
    Args:
        src: Source image file
        dest_dir: Destination directory
        profile: Metadata profile to apply (optional)
        preserve_fields: Specific fields to preserve (optional)
        
    Returns:
        Path to the cleaned copy
    """
    ensure_dir(dest_dir)
    out = dest_dir / src.name
    shutil.copy2(src, out)
    
    if profile or preserve_fields:
        # Selective cleaning
        selective_clean_metadata(out, profile, preserve_fields)
    else:
        # Complete metadata removal
        strip_all_metadata(out)
    
    return out


def selective_clean_metadata(
    file_path: Path,
    profile: Optional[MetadataProfile] = None,
    preserve_fields: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Selectively clean metadata from an image file.
    
    Args:
        file_path: Path to image file to clean
        profile: Metadata profile to apply
        preserve_fields: Specific fields to preserve
        
    Returns:
        Dictionary with operation results
    """
    if not has_exiftool():
        # Fallback to complete removal if ExifTool not available
        strip_all_metadata(file_path)
        return {
            "method": "complete_removal_fallback",
            "preserved_fields": [],
            "removed_fields": ["all"],
            "warning": "ExifTool not available, performed complete metadata removal"
        }
    
    try:
        # Get all current metadata fields
        all_fields = get_metadata_fields(file_path)
        
        if not all_fields:
            return {
                "method": "no_metadata",
                "preserved_fields": [],
                "removed_fields": [],
                "message": "No metadata found in file"
            }
        
        # Determine which fields to preserve
        fields_to_preserve = set()
        
        if preserve_fields:
            fields_to_preserve.update(preserve_fields)
        
        if profile:
            profile_preserved = apply_profile_to_fields(all_fields, profile)
            fields_to_preserve.update(profile_preserved)
        
        # If no preservation specified, remove everything
        if not fields_to_preserve:
            strip_all_metadata(file_path)
            return {
                "method": "complete_removal",
                "preserved_fields": [],
                "removed_fields": list(all_fields),
                "profile_used": profile.name if profile else None
            }
        
        # Perform selective removal
        result = _selective_remove_with_exiftool(file_path, all_fields, fields_to_preserve)
        result["profile_used"] = profile.name if profile else None
        
        return result
        
    except Exception as e:
        # Fallback to complete removal on any error
        strip_all_metadata(file_path)
        return {
            "method": "complete_removal_fallback",
            "preserved_fields": [],
            "removed_fields": ["all"],
            "error": str(e),
            "warning": "Error during selective cleaning, performed complete removal"
        }


def _selective_remove_with_exiftool(
    file_path: Path,
    all_fields: Set[str],
    preserve_fields: Set[str]
) -> Dict[str, Any]:
    """
    Use ExifTool to selectively remove metadata fields.
    
    Args:
        file_path: Path to image file
        all_fields: Set of all metadata fields in the file
        preserve_fields: Set of fields to preserve
        
    Returns:
        Dictionary with operation results
    """
    # Calculate fields to remove
    fields_to_remove = all_fields - preserve_fields
    
    if not fields_to_remove:
        return {
            "method": "no_removal_needed",
            "preserved_fields": list(preserve_fields),
            "removed_fields": [],
            "message": "All fields were marked for preservation"
        }
    
    # Create ExifTool command to remove specific fields
    cmd = ["exiftool", "-overwrite_original"]
    
    # Add removal commands for each field
    for field in fields_to_remove:
        cmd.extend([f"-{field}=", str(file_path)])
    
    try:
        # Execute ExifTool command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Verify the operation
        remaining_fields = get_metadata_fields(file_path)
        actually_preserved = remaining_fields & all_fields
        actually_removed = all_fields - remaining_fields
        
        return {
            "method": "selective_exiftool",
            "preserved_fields": list(actually_preserved),
            "removed_fields": list(actually_removed),
            "intended_preserve": list(preserve_fields),
            "intended_remove": list(fields_to_remove),
            "exiftool_output": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        raise Exception(f"ExifTool error: {e.stderr}")


def clean_directory(
    input_path: Path,
    output_path: Optional[Path] = None,
    profile_name: Optional[str] = None,
    profile: Optional[MetadataProfile] = None,
    preserve_fields: Optional[List[str]] = None,
    backup: bool = False,
    dry_run: bool = False,
    recursive: bool = False,
    config_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Clean metadata from all images in a directory.
    
    Args:
        input_path: Directory containing images to clean
        output_path: Output directory (default: input_path/safe_upload)
        profile_name: Name of predefined profile to use
        profile: MetadataProfile instance to use
        preserve_fields: List of specific fields to preserve
        backup: Whether to backup original files
        dry_run: Whether to preview operations without executing
        recursive: Whether to process subdirectories
        config_path: Path to configuration file
        
    Returns:
        Dictionary with operation results
    """
    if output_path is None:
        output_path = input_path / "safe_upload"
    
    # Load profile if name specified
    if profile_name and not profile:
        predefined_profiles = get_predefined_profiles()
        if profile_name in predefined_profiles:
            profile = predefined_profiles[profile_name]
        else:
            return {
                "error": f"Unknown profile: {profile_name}",
                "available_profiles": list(predefined_profiles.keys())
            }
    
    # Convert preserve_fields to set
    preserve_field_set = set(preserve_fields) if preserve_fields else None
    
    # Find all images
    try:
        image_files = list(iter_images(input_path, recursive=recursive))
    except Exception as e:
        return {"error": f"Error finding images: {e}"}
    
    if not image_files:
        return {
            "message": "No images found",
            "processed": 0,
            "successful": 0,
            "failed": 0
        }
    
    # Dry run mode
    if dry_run:
        return {
            "dry_run": True,
            "would_process": len(image_files),
            "input_path": str(input_path),
            "output_path": str(output_path),
            "profile_used": profile.name if profile else None,
            "preserve_fields": list(preserve_field_set) if preserve_field_set else [],
            "files": [str(f) for f in image_files[:10]]  # Show first 10 files
        }
    
    # Process files
    results = {
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "errors": [],
        "profile_used": profile.name if profile else None,
        "preserve_fields": list(preserve_field_set) if preserve_field_set else [],
        "output_directory": str(output_path),
        "backup_created": backup
    }
    
    # Create backup directory if requested
    backup_dir = None
    if backup:
        backup_dir = input_path / "backup"
        ensure_dir(backup_dir)
    
    for img_file in image_files:
        try:
            results["processed"] += 1
            
            # Create backup if requested
            if backup:
                backup_file = backup_dir / img_file.name
                shutil.copy2(img_file, backup_file)
            
            # Clean the file
            cleaned_file = clean_copy(
                img_file,
                output_path,
                profile=profile,
                preserve_fields=preserve_field_set
            )
            
            results["successful"] += 1
            
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "file": str(img_file),
                "error": str(e)
            })
    
    return results


def get_metadata_preview(
    file_path: Path,
    profile: Optional[MetadataProfile] = None,
    preserve_fields: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Preview what metadata would be preserved/removed without actually cleaning.
    
    Args:
        file_path: Path to image file
        profile: Metadata profile to apply
        preserve_fields: Specific fields to preserve
        
    Returns:
        Dictionary with preview information
    """
    if not has_exiftool():
        return {
            "error": "ExifTool not available",
            "fallback": "Would perform complete metadata removal"
        }
    
    try:
        # Get all current metadata fields
        all_fields = get_metadata_fields(file_path)
        
        if not all_fields:
            return {
                "message": "No metadata found in file",
                "current_fields": [],
                "would_preserve": [],
                "would_remove": []
            }
        
        # Determine which fields would be preserved
        fields_to_preserve = set()
        
        if preserve_fields:
            fields_to_preserve.update(preserve_fields)
        
        if profile:
            profile_preserved = apply_profile_to_fields(all_fields, profile)
            fields_to_preserve.update(profile_preserved)
        
        fields_to_remove = all_fields - fields_to_preserve
        
        return {
            "file": str(file_path),
            "profile_used": profile.name if profile else None,
            "current_fields": sorted(list(all_fields)),
            "would_preserve": sorted(list(fields_to_preserve)),
            "would_remove": sorted(list(fields_to_remove)),
            "field_counts": {
                "total": len(all_fields),
                "preserve": len(fields_to_preserve),
                "remove": len(fields_to_remove)
            }
        }
        
    except Exception as e:
        return {
            "error": f"Error analyzing file: {e}",
            "file": str(file_path)
        }
