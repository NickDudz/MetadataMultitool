"""Validation utilities for GUI input."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple
import re


def validate_path(path_str: str) -> Tuple[bool, Optional[Path], str]:
    """Validate a path string.
    
    Returns:
        Tuple of (is_valid, path_object, error_message)
    """
    if not path_str.strip():
        return False, None, "Path cannot be empty"
        
    try:
        path = Path(path_str.strip())
        if not path.exists():
            return False, path, f"Path does not exist: {path}"
        return True, path, ""
    except Exception as e:
        return False, None, f"Invalid path: {e}"


def validate_file_formats(formats: List[str]) -> Tuple[bool, List[str], str]:
    """Validate file format list.
    
    Returns:
        Tuple of (is_valid, cleaned_formats, error_message)
    """
    if not formats:
        return False, [], "At least one format must be specified"
        
    valid_formats = []
    for fmt in formats:
        fmt = fmt.strip().lower()
        if not fmt.startswith('.'):
            fmt = '.' + fmt
            
        # Check if format is supported
        supported = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp', '.bmp']
        if fmt in supported:
            valid_formats.append(fmt)
        else:
            return False, [], f"Unsupported format: {fmt}"
            
    return True, valid_formats, ""


def validate_size_filter(size_str: str) -> Tuple[bool, Optional[int], Optional[int], str]:
    """Validate size filter string.
    
    Expected formats: "1MB", "500KB-2MB", ">1GB", "<500KB"
    
    Returns:
        Tuple of (is_valid, min_size, max_size, error_message)
    """
    if not size_str.strip():
        return True, None, None, ""
        
    size_str = size_str.strip().upper()
    
    # Parse size with unit
    def parse_size(s: str) -> int:
        s = s.strip()
        if s.endswith('KB'):
            return int(s[:-2]) * 1024
        elif s.endswith('MB'):
            return int(s[:-2]) * 1024 * 1024
        elif s.endswith('GB'):
            return int(s[:-2]) * 1024 * 1024 * 1024
        elif s.endswith('B'):
            return int(s[:-1])
        else:
            return int(s)
    
    try:
        if '>' in size_str:
            # Greater than
            size = parse_size(size_str[1:])
            return True, size, None, ""
        elif '<' in size_str:
            # Less than
            size = parse_size(size_str[1:])
            return True, None, size, ""
        elif '-' in size_str:
            # Range
            min_str, max_str = size_str.split('-', 1)
            min_size = parse_size(min_str)
            max_size = parse_size(max_str)
            if min_size >= max_size:
                return False, None, None, "Minimum size must be less than maximum size"
            return True, min_size, max_size, ""
        else:
            # Exact size
            size = parse_size(size_str)
            return True, size, size, ""
    except (ValueError, IndexError) as e:
        return False, None, None, f"Invalid size format: {e}"


def validate_date_filter(date_str: str) -> Tuple[bool, Optional[str], Optional[str], str]:
    """Validate date filter string.
    
    Expected formats: "2024-01-01", "2024-01-01:2024-12-31", ">2024-01-01"
    
    Returns:
        Tuple of (is_valid, min_date, max_date, error_message)
    """
    if not date_str.strip():
        return True, None, None, ""
        
    date_str = date_str.strip()
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    
    try:
        if '>' in date_str:
            # Greater than
            date = date_str[1:].strip()
            if not re.match(date_pattern, date):
                return False, None, None, "Invalid date format. Use YYYY-MM-DD"
            return True, date, None, ""
        elif '<' in date_str:
            # Less than
            date = date_str[1:].strip()
            if not re.match(date_pattern, date):
                return False, None, None, "Invalid date format. Use YYYY-MM-DD"
            return True, None, date, ""
        elif ':' in date_str:
            # Range
            min_date, max_date = date_str.split(':', 1)
            min_date = min_date.strip()
            max_date = max_date.strip()
            
            if not re.match(date_pattern, min_date):
                return False, None, None, "Invalid minimum date format. Use YYYY-MM-DD"
            if not re.match(date_pattern, max_date):
                return False, None, None, "Invalid maximum date format. Use YYYY-MM-DD"
                
            if min_date >= max_date:
                return False, None, None, "Minimum date must be before maximum date"
                
            return True, min_date, max_date, ""
        else:
            # Exact date
            if not re.match(date_pattern, date_str):
                return False, None, None, "Invalid date format. Use YYYY-MM-DD"
            return True, date_str, date_str, ""
    except Exception as e:
        return False, None, None, f"Invalid date format: {e}"


def validate_rename_pattern(pattern: str) -> Tuple[bool, str]:
    """Validate rename pattern string.
    
    Expected placeholders: {stem}, {rand}
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not pattern.strip():
        return True, ""
        
    pattern = pattern.strip()
    
    # Check for valid placeholders
    valid_placeholders = {'{stem}', '{rand}'}
    placeholders = set(re.findall(r'\{[^}]+\}', pattern))
    
    invalid_placeholders = placeholders - valid_placeholders
    if invalid_placeholders:
        return False, f"Invalid placeholders: {', '.join(invalid_placeholders)}. Use {{stem}} and {{rand}}"
        
    return True, ""


def validate_batch_size(size: int) -> Tuple[bool, str]:
    """Validate batch size."""
    if size <= 0:
        return False, "Batch size must be positive"
    if size > 10000:
        return False, "Batch size too large (max 10000)"
    return True, ""


def validate_max_workers(workers: int) -> Tuple[bool, str]:
    """Validate max workers count."""
    if workers <= 0:
        return False, "Max workers must be positive"
    if workers > 32:
        return False, "Max workers too large (max 32)"
    return True, ""
