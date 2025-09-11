"""
Metadata profiles for selective cleaning operations.

This module provides predefined profiles for different metadata cleaning scenarios,
allowing users to preserve specific metadata fields while removing others.
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Any
from enum import Enum
import json
from pathlib import Path


class MetadataCategory(Enum):
    """Categories of metadata fields."""
    GPS = "gps"
    CAMERA = "camera"
    TECHNICAL = "technical"
    COPYRIGHT = "copyright"
    CREATIVE = "creative"
    DATETIME = "datetime"
    PRIVACY = "privacy"
    SOFTWARE = "software"


@dataclass
class MetadataProfile:
    """A metadata profile defining which fields to preserve or remove."""
    name: str
    description: str
    preserve_fields: Set[str]
    remove_fields: Set[str]
    preserve_categories: Set[MetadataCategory]
    remove_categories: Set[MetadataCategory]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "preserve_fields": list(self.preserve_fields),
            "remove_fields": list(self.remove_fields),
            "preserve_categories": [cat.value for cat in self.preserve_categories],
            "remove_categories": [cat.value for cat in self.remove_categories]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetadataProfile":
        """Create profile from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            preserve_fields=set(data.get("preserve_fields", [])),
            remove_fields=set(data.get("remove_fields", [])),
            preserve_categories={
                MetadataCategory(cat) for cat in data.get("preserve_categories", [])
            },
            remove_categories={
                MetadataCategory(cat) for cat in data.get("remove_categories", [])
            }
        )


# EXIF field mappings to categories
FIELD_CATEGORY_MAP = {
    # GPS Fields
    "GPS:GPSLatitude": MetadataCategory.GPS,
    "GPS:GPSLongitude": MetadataCategory.GPS,
    "GPS:GPSAltitude": MetadataCategory.GPS,
    "GPS:GPSLatitudeRef": MetadataCategory.GPS,
    "GPS:GPSLongitudeRef": MetadataCategory.GPS,
    "GPS:GPSAltitudeRef": MetadataCategory.GPS,
    "GPS:GPSTimeStamp": MetadataCategory.GPS,
    "GPS:GPSDateStamp": MetadataCategory.GPS,
    "GPS:GPSMapDatum": MetadataCategory.GPS,
    "GPS:GPSVersionID": MetadataCategory.GPS,
    
    # Camera Information
    "EXIF:Make": MetadataCategory.CAMERA,
    "EXIF:Model": MetadataCategory.CAMERA,
    "EXIF:LensModel": MetadataCategory.CAMERA,
    "EXIF:LensMake": MetadataCategory.CAMERA,
    "EXIF:LensSerialNumber": MetadataCategory.CAMERA,
    "EXIF:SerialNumber": MetadataCategory.CAMERA,
    "EXIF:BodySerialNumber": MetadataCategory.CAMERA,
    "EXIF:CameraOwnerName": MetadataCategory.PRIVACY,
    
    # Technical Settings
    "EXIF:ExposureTime": MetadataCategory.TECHNICAL,
    "EXIF:FNumber": MetadataCategory.TECHNICAL,
    "EXIF:ISO": MetadataCategory.TECHNICAL,
    "EXIF:ISOSpeedRatings": MetadataCategory.TECHNICAL,
    "EXIF:FocalLength": MetadataCategory.TECHNICAL,
    "EXIF:FocalLengthIn35mmFormat": MetadataCategory.TECHNICAL,
    "EXIF:Flash": MetadataCategory.TECHNICAL,
    "EXIF:WhiteBalance": MetadataCategory.TECHNICAL,
    "EXIF:ExposureMode": MetadataCategory.TECHNICAL,
    "EXIF:ExposureProgram": MetadataCategory.TECHNICAL,
    "EXIF:MeteringMode": MetadataCategory.TECHNICAL,
    "EXIF:Orientation": MetadataCategory.TECHNICAL,
    "EXIF:ResolutionUnit": MetadataCategory.TECHNICAL,
    "EXIF:XResolution": MetadataCategory.TECHNICAL,
    "EXIF:YResolution": MetadataCategory.TECHNICAL,
    "EXIF:ColorSpace": MetadataCategory.TECHNICAL,
    "EXIF:CompressedBitsPerPixel": MetadataCategory.TECHNICAL,
    
    # Date/Time
    "EXIF:DateTime": MetadataCategory.DATETIME,
    "EXIF:DateTimeOriginal": MetadataCategory.DATETIME,
    "EXIF:DateTimeDigitized": MetadataCategory.DATETIME,
    "EXIF:CreateDate": MetadataCategory.DATETIME,
    "EXIF:ModifyDate": MetadataCategory.DATETIME,
    "EXIF:OffsetTime": MetadataCategory.DATETIME,
    "EXIF:OffsetTimeOriginal": MetadataCategory.DATETIME,
    "EXIF:OffsetTimeDigitized": MetadataCategory.DATETIME,
    
    # Copyright and Rights
    "EXIF:Copyright": MetadataCategory.COPYRIGHT,
    "EXIF:Artist": MetadataCategory.COPYRIGHT,
    "EXIF:ImageDescription": MetadataCategory.CREATIVE,
    "IPTC:Caption-Abstract": MetadataCategory.CREATIVE,
    "IPTC:Keywords": MetadataCategory.CREATIVE,
    "IPTC:Byline": MetadataCategory.COPYRIGHT,
    "IPTC:CopyrightNotice": MetadataCategory.COPYRIGHT,
    "IPTC:Credit": MetadataCategory.COPYRIGHT,
    "IPTC:Source": MetadataCategory.COPYRIGHT,
    "XMP:Rights": MetadataCategory.COPYRIGHT,
    "XMP:Creator": MetadataCategory.COPYRIGHT,
    "XMP:Title": MetadataCategory.CREATIVE,
    "XMP:Description": MetadataCategory.CREATIVE,
    "XMP:Subject": MetadataCategory.CREATIVE,
    
    # Software and Processing
    "EXIF:Software": MetadataCategory.SOFTWARE,
    "EXIF:ProcessingSoftware": MetadataCategory.SOFTWARE,
    "EXIF:HostComputer": MetadataCategory.SOFTWARE,
    "XMP:CreatorTool": MetadataCategory.SOFTWARE,
    "XMP:MetadataDate": MetadataCategory.SOFTWARE,
    "XMP:ModifyDate": MetadataCategory.SOFTWARE,
    
    # Privacy-sensitive fields
    "EXIF:UserComment": MetadataCategory.PRIVACY,
    "IPTC:SpecialInstructions": MetadataCategory.PRIVACY,
    "IPTC:Writer-Editor": MetadataCategory.PRIVACY,
    "XMP:PersonInImage": MetadataCategory.PRIVACY,
    "XMP:LocationShown": MetadataCategory.PRIVACY,
    "XMP:LocationCreated": MetadataCategory.PRIVACY,
}


def get_predefined_profiles() -> Dict[str, MetadataProfile]:
    """Get dictionary of predefined metadata profiles."""
    profiles = {}
    
    # Complete removal profile
    profiles["remove_all"] = MetadataProfile(
        name="Remove All",
        description="Remove all metadata for maximum privacy",
        preserve_fields=set(),
        remove_fields=set(),  # Empty means remove everything
        preserve_categories=set(),
        remove_categories=set(MetadataCategory)
    )
    
    # Keep only copyright profile
    profiles["copyright_only"] = MetadataProfile(
        name="Copyright Only",
        description="Keep only copyright and attribution information",
        preserve_fields=set(),
        remove_fields=set(),
        preserve_categories={MetadataCategory.COPYRIGHT},
        remove_categories={
            MetadataCategory.GPS, MetadataCategory.PRIVACY, 
            MetadataCategory.SOFTWARE, MetadataCategory.CAMERA
        }
    )
    
    # Remove privacy profile
    profiles["remove_privacy"] = MetadataProfile(
        name="Remove Privacy Data",
        description="Remove GPS, personal info, and camera details while keeping technical data",
        preserve_fields=set(),
        remove_fields=set(),
        preserve_categories={
            MetadataCategory.TECHNICAL, MetadataCategory.COPYRIGHT, 
            MetadataCategory.CREATIVE, MetadataCategory.DATETIME
        },
        remove_categories={
            MetadataCategory.GPS, MetadataCategory.PRIVACY, 
            MetadataCategory.CAMERA, MetadataCategory.SOFTWARE
        }
    )
    
    # Photography essentials profile
    profiles["photography_essentials"] = MetadataProfile(
        name="Photography Essentials",
        description="Keep technical camera settings and copyright, remove location and personal data",
        preserve_fields=set(),
        remove_fields=set(),
        preserve_categories={
            MetadataCategory.TECHNICAL, MetadataCategory.COPYRIGHT,
            MetadataCategory.DATETIME
        },
        remove_categories={
            MetadataCategory.GPS, MetadataCategory.PRIVACY,
            MetadataCategory.SOFTWARE
        }
    )
    
    # Social media profile
    profiles["social_media"] = MetadataProfile(
        name="Social Media Safe",
        description="Remove all potentially sensitive data for social media sharing",
        preserve_fields={"EXIF:Orientation"},  # Keep orientation for proper display
        remove_fields=set(),
        preserve_categories={MetadataCategory.COPYRIGHT},
        remove_categories={
            MetadataCategory.GPS, MetadataCategory.PRIVACY,
            MetadataCategory.CAMERA, MetadataCategory.SOFTWARE,
            MetadataCategory.TECHNICAL  # Most technical data not needed for social
        }
    )
    
    # Stock photography profile
    profiles["stock_photography"] = MetadataProfile(
        name="Stock Photography",
        description="Optimized for stock photo submissions - technical and creative metadata only",
        preserve_fields=set(),
        remove_fields=set(),
        preserve_categories={
            MetadataCategory.TECHNICAL, MetadataCategory.COPYRIGHT,
            MetadataCategory.CREATIVE, MetadataCategory.DATETIME
        },
        remove_categories={
            MetadataCategory.GPS, MetadataCategory.PRIVACY,
            MetadataCategory.CAMERA, MetadataCategory.SOFTWARE
        }
    )
    
    # Professional portfolio profile
    profiles["professional_portfolio"] = MetadataProfile(
        name="Professional Portfolio",
        description="Keep technical settings and copyright for professional showcase",
        preserve_fields=set(),
        remove_fields=set(),
        preserve_categories={
            MetadataCategory.TECHNICAL, MetadataCategory.COPYRIGHT,
            MetadataCategory.CREATIVE, MetadataCategory.DATETIME,
            MetadataCategory.CAMERA  # Keep camera info for portfolio
        },
        remove_categories={
            MetadataCategory.GPS, MetadataCategory.PRIVACY,
            MetadataCategory.SOFTWARE
        }
    )
    
    # Archive profile
    profiles["archive"] = MetadataProfile(
        name="Archive Preservation",
        description="Keep all non-sensitive metadata for archival purposes",
        preserve_fields=set(),
        remove_fields=set(),
        preserve_categories={
            MetadataCategory.TECHNICAL, MetadataCategory.COPYRIGHT,
            MetadataCategory.CREATIVE, MetadataCategory.DATETIME,
            MetadataCategory.CAMERA, MetadataCategory.SOFTWARE
        },
        remove_categories={
            MetadataCategory.GPS, MetadataCategory.PRIVACY
        }
    )
    
    return profiles


def get_fields_for_category(category: MetadataCategory) -> Set[str]:
    """Get all metadata fields belonging to a specific category."""
    return {field for field, cat in FIELD_CATEGORY_MAP.items() if cat == category}


def categorize_field(field_name: str) -> Optional[MetadataCategory]:
    """Determine the category of a metadata field."""
    # Direct mapping
    if field_name in FIELD_CATEGORY_MAP:
        return FIELD_CATEGORY_MAP[field_name]
    
    # Pattern-based categorization for fields not in the map
    field_lower = field_name.lower()
    
    if any(gps_term in field_lower for gps_term in ["gps", "latitude", "longitude", "altitude"]):
        return MetadataCategory.GPS
    
    if any(copyright_term in field_lower for copyright_term in ["copyright", "artist", "creator", "byline"]):
        return MetadataCategory.COPYRIGHT
    
    if any(camera_term in field_lower for camera_term in ["make", "model", "serial", "lens"]):
        return MetadataCategory.CAMERA
    
    if any(software_term in field_lower for software_term in ["software", "tool", "application"]):
        return MetadataCategory.SOFTWARE
    
    if any(datetime_term in field_lower for datetime_term in ["date", "time", "created", "modified"]):
        return MetadataCategory.DATETIME
    
    if any(privacy_term in field_lower for privacy_term in ["comment", "owner", "person", "location"]):
        return MetadataCategory.PRIVACY
    
    # Default to technical if no other category matches
    return MetadataCategory.TECHNICAL


def apply_profile_to_fields(all_fields: Set[str], profile: MetadataProfile) -> Set[str]:
    """
    Apply a metadata profile to determine which fields to preserve.
    
    Args:
        all_fields: Set of all available metadata fields
        profile: MetadataProfile to apply
        
    Returns:
        Set of fields that should be preserved according to the profile
    """
    preserve_fields = set()
    
    # Start with explicitly preserved fields
    preserve_fields.update(profile.preserve_fields)
    
    # Add fields from preserved categories
    for field in all_fields:
        field_category = categorize_field(field)
        if field_category and field_category in profile.preserve_categories:
            preserve_fields.add(field)
    
    # Remove explicitly removed fields
    preserve_fields -= profile.remove_fields
    
    # Remove fields from removed categories
    remove_fields = set()
    for field in preserve_fields:
        field_category = categorize_field(field)
        if field_category and field_category in profile.remove_categories:
            remove_fields.add(field)
    
    preserve_fields -= remove_fields
    
    return preserve_fields


def save_profile(profile: MetadataProfile, file_path: Path) -> None:
    """Save a metadata profile to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(profile.to_dict(), f, indent=2)


def load_profile(file_path: Path) -> MetadataProfile:
    """Load a metadata profile from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return MetadataProfile.from_dict(data)


def save_all_predefined_profiles(directory: Path) -> None:
    """Save all predefined profiles to JSON files in a directory."""
    directory.mkdir(exist_ok=True)
    
    profiles = get_predefined_profiles()
    for profile_name, profile in profiles.items():
        file_path = directory / f"{profile_name}.json"
        save_profile(profile, file_path)


def load_profiles_from_directory(directory: Path) -> Dict[str, MetadataProfile]:
    """Load all profiles from JSON files in a directory."""
    profiles = {}
    
    if not directory.exists():
        return profiles
    
    for json_file in directory.glob("*.json"):
        try:
            profile = load_profile(json_file)
            profiles[profile.name.lower().replace(" ", "_")] = profile
        except (json.JSONDecodeError, KeyError) as e:
            # Skip invalid profile files
            print(f"Warning: Could not load profile from {json_file}: {e}")
    
    return profiles


def create_custom_profile(
    name: str,
    description: str,
    preserve_categories: List[str] = None,
    remove_categories: List[str] = None,
    preserve_fields: List[str] = None,
    remove_fields: List[str] = None
) -> MetadataProfile:
    """
    Create a custom metadata profile.
    
    Args:
        name: Profile name
        description: Profile description
        preserve_categories: List of category names to preserve
        remove_categories: List of category names to remove
        preserve_fields: List of specific fields to preserve
        remove_fields: List of specific fields to remove
        
    Returns:
        MetadataProfile instance
    """
    preserve_cats = set()
    if preserve_categories:
        for cat_name in preserve_categories:
            try:
                preserve_cats.add(MetadataCategory(cat_name.lower()))
            except ValueError:
                print(f"Warning: Unknown category '{cat_name}'")
    
    remove_cats = set()
    if remove_categories:
        for cat_name in remove_categories:
            try:
                remove_cats.add(MetadataCategory(cat_name.lower()))
            except ValueError:
                print(f"Warning: Unknown category '{cat_name}'")
    
    return MetadataProfile(
        name=name,
        description=description,
        preserve_fields=set(preserve_fields or []),
        remove_fields=set(remove_fields or []),
        preserve_categories=preserve_cats,
        remove_categories=remove_cats
    )


def get_profile_summary(profile: MetadataProfile) -> Dict[str, Any]:
    """Get a summary of what a profile does."""
    return {
        "name": profile.name,
        "description": profile.description,
        "preserves": {
            "categories": [cat.value for cat in profile.preserve_categories],
            "specific_fields": list(profile.preserve_fields),
            "field_count": len(profile.preserve_fields)
        },
        "removes": {
            "categories": [cat.value for cat in profile.remove_categories],
            "specific_fields": list(profile.remove_fields),
            "field_count": len(profile.remove_fields)
        }
    }


if __name__ == "__main__":
    # Example usage
    profiles = get_predefined_profiles()
    
    print("Available metadata profiles:")
    for name, profile in profiles.items():
        summary = get_profile_summary(profile)
        print(f"\n{summary['name']}:")
        print(f"  Description: {summary['description']}")
        print(f"  Preserves categories: {', '.join(summary['preserves']['categories'])}")
        print(f"  Removes categories: {', '.join(summary['removes']['categories'])}")
    
    # Example of applying a profile
    sample_fields = {
        "GPS:GPSLatitude", "GPS:GPSLongitude", "EXIF:Make", "EXIF:Model",
        "EXIF:DateTime", "EXIF:ExposureTime", "EXIF:Copyright", "EXIF:Artist"
    }
    
    social_profile = profiles["social_media"]
    preserved = apply_profile_to_fields(sample_fields, social_profile)
    
    print(f"\nApplying '{social_profile.name}' profile:")
    print(f"Original fields: {sample_fields}")
    print(f"Preserved fields: {preserved}")
    print(f"Removed fields: {sample_fields - preserved}")