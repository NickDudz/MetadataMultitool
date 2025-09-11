"""Command-line interface for the Metadata Multitool."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, List, Tuple

from colorama import Fore, Style
from colorama import init as color_init

from .backup import backup_before_operation, create_backup_manager
from .batch import process_batch
from .clean import clean_copy, clean_directory, get_metadata_preview
from .metadata_profiles import get_predefined_profiles, get_profile_summary
from .audit import audit_directory, audit_file, generate_html_report, export_audit_json
from .config import get_config_value, load_config
from .core import (
    InvalidPathError,
    LogError,
    MetadataMultitoolError,
    ensure_dir,
    iter_images,
    read_log,
    rel_to_root,
    write_log,
)
from .filters import (
    FileFilter,
    create_filter_from_args,
    parse_date_filter,
    parse_size_filter,
)
from .html import html_snippet
from .interactive import interactive_mode
from .logging import get_logger, log_operation_summary
from .poison import (
    load_csv_mapping,
    make_caption,
    rename_with_pattern,
    write_metadata,
    write_sidecars,
)
from .revert import revert_dir

color_init()


def apply_filters(args: argparse.Namespace, images: List[Path]) -> List[Path]:
    """
    Apply file filters to a list of images.

    Args:
        args: Command line arguments
        images: List of image paths

    Returns:
        Filtered list of image paths
    """
    # Check if any filters are specified
    has_filters = any(
        [
            getattr(args, "size", None),
            getattr(args, "date", None),
            getattr(args, "formats", None),
            getattr(args, "has_metadata", False),
            getattr(args, "no_metadata", False),
        ]
    )

    if not has_filters:
        return images

    # Create filter
    file_filter = FileFilter()

    # Apply size filter
    if hasattr(args, "size") and args.size:
        try:
            min_size, max_size = parse_size_filter(args.size)
            file_filter.add_size_filter(min_size=min_size, max_size=max_size)
        except Exception as e:
            print(
                f"{Fore.YELLOW}Warning: Invalid size filter '{args.size}': {e}{Style.RESET_ALL}"
            )

    # Apply date filter
    if hasattr(args, "date") and args.date:
        try:
            min_date, max_date = parse_date_filter(args.date)
            file_filter.add_date_filter(min_date=min_date, max_date=max_date)
        except Exception as e:
            print(
                f"{Fore.YELLOW}Warning: Invalid date filter '{args.date}': {e}{Style.RESET_ALL}"
            )

    # Apply format filter
    if hasattr(args, "formats") and args.formats:
        file_filter.add_format_filter(args.formats)

    # Apply metadata filter
    if hasattr(args, "has_metadata") and args.has_metadata:
        file_filter.add_metadata_filter(has_metadata=True)
    elif hasattr(args, "no_metadata") and args.no_metadata:
        file_filter.add_metadata_filter(has_metadata=False)

    # Filter the images
    filtered_images = []
    for img in images:
        if all(filter_func(img) for filter_func in file_filter.filters):
            filtered_images.append(img)

    return filtered_images


def handle_error(error: Exception, context: str = "") -> int:
    """
    Handle errors with appropriate user messaging.

    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred

    Returns:
        Exit code (1 for error)
    """
    try:
        if isinstance(error, KeyboardInterrupt):
            print(f"{Fore.YELLOW}Operation interrupted by user{Style.RESET_ALL}")
        elif isinstance(error, InvalidPathError):
            print(f"{Fore.RED}Error: Invalid path - {error}{Style.RESET_ALL}")
        elif isinstance(error, LogError):
            print(f"{Fore.RED}Error: Log operation failed - {error}{Style.RESET_ALL}")
        elif isinstance(error, MetadataMultitoolError):
            print(f"{Fore.RED}Error: {error}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Unexpected error: {error}{Style.RESET_ALL}")

        if context:
            print(f"{Fore.YELLOW}Context: {context}{Style.RESET_ALL}")
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        if isinstance(error, KeyboardInterrupt):
            print("Operation interrupted by user")
        else:
            print(f"Error: {error}")
        if context:
            print(f"Context: {context}")

    return 1


def cmd_clean(args: argparse.Namespace) -> int:
    """Clean command implementation."""
    try:
        # Handle profile listing
        if getattr(args, "list_profiles", False):
            profiles = get_predefined_profiles()
            print(f"{Fore.CYAN}Available metadata profiles:{Style.RESET_ALL}")
            for name, profile in profiles.items():
                summary = get_profile_summary(profile)
                print(f"\n{Fore.GREEN}{name}{Style.RESET_ALL}: {summary['description']}")
                if summary['preserves']['categories']:
                    print(f"  Preserves: {', '.join(summary['preserves']['categories'])}")
                if summary['removes']['categories']:
                    print(f"  Removes: {', '.join(summary['removes']['categories'])}")
            return 0
        
        # Handle metadata preview
        if getattr(args, "preview", None):
            preview_file = Path(args.preview)
            if not preview_file.exists():
                print(f"{Fore.RED}Preview file not found: {preview_file}{Style.RESET_ALL}")
                return 1
            
            # Get profile if specified
            profile_name = getattr(args, "profile", None)
            profile = None
            if profile_name:
                profiles = get_predefined_profiles()
                if profile_name in profiles:
                    profile = profiles[profile_name]
                else:
                    print(f"{Fore.RED}Unknown profile: {profile_name}{Style.RESET_ALL}")
                    return 1
            
            # Get preserve fields
            preserve_fields = set(getattr(args, "preserve_fields", [])) if getattr(args, "preserve_fields", None) else None
            
            # Generate preview
            preview = get_metadata_preview(preview_file, profile, preserve_fields)
            
            if "error" in preview:
                print(f"{Fore.RED}Error: {preview['error']}{Style.RESET_ALL}")
                return 1
            
            print(f"{Fore.CYAN}Metadata Preview for: {preview['file']}{Style.RESET_ALL}")
            if preview.get("profile_used"):
                print(f"Profile: {preview['profile_used']}")
            
            print(f"\nTotal fields: {preview['field_counts']['total']}")
            print(f"{Fore.GREEN}Would preserve: {preview['field_counts']['preserve']}{Style.RESET_ALL}")
            print(f"{Fore.RED}Would remove: {preview['field_counts']['remove']}{Style.RESET_ALL}")
            
            if preview['would_preserve']:
                print(f"\n{Fore.GREEN}Fields to preserve:{Style.RESET_ALL}")
                for field in preview['would_preserve']:
                    print(f"  + {field}")
            
            if preview['would_remove']:
                print(f"\n{Fore.RED}Fields to remove:{Style.RESET_ALL}")
                for field in preview['would_remove'][:10]:  # Show first 10
                    print(f"  - {field}")
                if len(preview['would_remove']) > 10:
                    print(f"  ... and {len(preview['would_remove']) - 10} more")
            
            return 0

        # Load configuration
        config_path = getattr(args, "config", None)
        if config_path:
            config = load_config(Path(config_path))
        else:
            config = load_config()

        # Override config with command line arguments
        verbose = getattr(args, "verbose", False) or get_config_value(
            config, "verbose", False
        )
        quiet = getattr(args, "quiet", False) or get_config_value(
            config, "quiet", False
        )
        dry_run = getattr(args, "dry_run", False)
        batch_size = getattr(args, "batch_size", None) or get_config_value(
            config, "batch_size", 100
        )
        max_workers = getattr(args, "max_workers", None) or get_config_value(
            config, "max_workers", 4
        )
        progress_bar = get_config_value(config, "progress_bar", True) and not quiet
        log_level = get_config_value(config, "log_level", "INFO")

        # Set up logging
        logger = get_logger(log_level=log_level)

        # Set up backup if requested
        backup_manager = None
        if getattr(args, "backup", False) or get_config_value(
            config, "backup_before_operations", False
        ):
            backup_dir = getattr(args, "backup_dir", None)
            if backup_dir:
                backup_manager = create_backup_manager(Path(backup_dir))
            else:
                backup_manager = create_backup_manager()

        # Accept either a single path (args.path) or list (args.paths) for tests
        src_arg = getattr(args, "path", None)
        if src_arg is None:
            paths_list = getattr(args, "paths", None)
            if paths_list:
                src_arg = paths_list[0]
        if src_arg is None:
            raise InvalidPathError("No input path provided")
        src = Path(src_arg)
        
        # Get metadata profile settings
        profile_name = getattr(args, "profile", None)
        preserve_fields = getattr(args, "preserve_fields", None)

        # Set up output directory
        copy_folder = getattr(args, "copy_folder", "safe_upload")
        if src.is_dir():
            out_dir = src / copy_folder
        else:
            out_dir = src.parent / copy_folder

        # Use the new clean_directory function with profile support
        result = clean_directory(
            input_path=src,
            output_path=out_dir,
            profile_name=profile_name,
            preserve_fields=preserve_fields,
            backup=backup_manager is not None,
            dry_run=dry_run,
            recursive=False  # TODO: Add recursive option to CLI
        )
        
        # Handle errors
        if "error" in result:
            if not quiet:
                print(f"{Fore.RED}Error: {result['error']}{Style.RESET_ALL}")
                if "available_profiles" in result:
                    print(f"Available profiles: {', '.join(result['available_profiles'])}")
            return 1
        
        # Display results
        if not quiet:
            if result.get("dry_run"):
                print(f"{Fore.CYAN}DRY RUN: Would process {result['would_process']} images{Style.RESET_ALL}")
                if result.get("profile_used"):
                    print(f"Profile: {result['profile_used']}")
                if result.get("preserve_fields"):
                    print(f"Preserve fields: {', '.join(result['preserve_fields'])}")
                return 0
            
            if result.get("message"):
                print(f"{Fore.YELLOW}{result['message']}{Style.RESET_ALL}")
                return 0
            
            # Show operation summary
            successful = result.get("successful", 0)
            processed = result.get("processed", 0)
            failed = result.get("failed", 0)
            
            if successful > 0:
                print(f"{Fore.GREEN}✓ Cleaned {successful}/{processed} images → {result['output_directory']}{Style.RESET_ALL}")
            
            if result.get("profile_used"):
                print(f"Used profile: {result['profile_used']}")
            
            if result.get("preserve_fields"):
                print(f"Preserved fields: {', '.join(result['preserve_fields'])}")
            
            if failed > 0:
                print(f"{Fore.RED}✗ {failed} images failed{Style.RESET_ALL}")
                for error in result.get("errors", [])[:5]:  # Show first 5 errors
                    print(f"  {error['file']}: {error['error']}")
                if len(result.get("errors", [])) > 5:
                    print(f"  ... and {len(result['errors']) - 5} more errors")
        
        # Log operation for compatibility
        logger.log_operation_start("clean", {
            "processed": result.get("processed", 0),
            "profile": result.get("profile_used"),
            "preserve_fields": result.get("preserve_fields", [])
        })
        
        logger.log_operation_end("clean", result.get("failed", 0) == 0, result)
        
        return 0 if result.get("failed", 0) == 0 else 1
    except Exception as e:
        return handle_error(e, f"cleaning images from {src_arg}")


def cmd_poison(args: argparse.Namespace) -> int:
    """Poison command implementation."""
    try:
        # Load configuration
        config_path = getattr(args, "config", None)
        if config_path:
            config = load_config(Path(config_path))
        else:
            config = load_config()

        # Override config with command line arguments
        verbose = getattr(args, "verbose", False) or get_config_value(
            config, "verbose", False
        )
        quiet = getattr(args, "quiet", False) or get_config_value(
            config, "quiet", False
        )
        dry_run = getattr(args, "dry_run", False)
        batch_size = getattr(args, "batch_size", None) or get_config_value(
            config, "batch_size", 100
        )
        max_workers = getattr(args, "max_workers", None) or get_config_value(
            config, "max_workers", 4
        )
        progress_bar = get_config_value(config, "progress_bar", True) and not quiet

        # Accept either a single path (args.path) or list (args.paths)
        target_arg = getattr(args, "path", None)
        if target_arg is None:
            paths_list = getattr(args, "paths", None)
            if paths_list:
                target_arg = paths_list[0]
        if target_arg is None:
            raise InvalidPathError("No input path provided")
        target = Path(target_arg)
        base = target if target.is_dir() else target.parent
        log = read_log(base)
        entries = log.setdefault("entries", {})

        # Load CSV mapping if provided
        mapping = {}
        if getattr(args, "csv", None):
            try:
                mapping = load_csv_mapping(Path(args.csv))
                if not quiet:
                    print(
                        f"{Fore.CYAN}Loaded {len(mapping)} mappings from CSV{Style.RESET_ALL}"
                    )
            except Exception as e:
                if not quiet:
                    print(
                        f"{Fore.YELLOW}Warning: Failed to load CSV mapping: {e}{Style.RESET_ALL}"
                    )

        # Get list of images first for progress tracking
        images = list(iter_images(target))
        images = apply_filters(args, images)
        total = len(images)

        if total == 0:
            if not quiet:
                print(f"{Fore.YELLOW}No images found in {target}{Style.RESET_ALL}")
            return 0

        if dry_run:
            if not quiet:
                print(
                    f"{Fore.CYAN}DRY RUN: Would poison {total} images with preset '{args.preset}'...{Style.RESET_ALL}"
                )
                for i, img in enumerate(images, 1):
                    caption, tags = make_caption(
                        args.preset, args.true_hint or img.stem, mapping
                    )
                    print(f"  [{i}/{total}] {img.name} → '{caption}' {tags}")
            return 0

        if not quiet:
            print(
                f"{Fore.CYAN}Poisoning {total} images with preset '{args.preset}'...{Style.RESET_ALL}"
            )

        # Use batch processing for large directories
        if total >= batch_size and max_workers > 1:

            def process_single_image(img_path: Path) -> Tuple[bool, str]:
                try:
                    # Compute caption/tags
                    caption, tags = make_caption(
                        args.preset, args.true_hint or img_path.stem, mapping
                    )

                    # Optional rename (log original name)
                    original_name = img_path.name
                    if args.rename_pattern:
                        img_path = rename_with_pattern(img_path, args.rename_pattern)

                    # Sidecars & metadata
                    if args.sidecar or args.json:
                        write_sidecars(img_path, caption, tags, emit_json=args.json)

                    try:
                        write_metadata(
                            img_path,
                            caption,
                            tags,
                            xmp=args.xmp,
                            iptc=args.iptc,
                            exif=args.exif,
                        )
                    except Exception as e:
                        return False, f"Failed to write metadata: {e}"

                    # Optional HTML
                    if args.html:
                        snippet = html_snippet(img_path.name, caption, caption)
                        html_file = img_path.parent / f"{img_path.stem}.html"
                        html_file.write_text(snippet, encoding="utf-8")

                    # Log the operation
                    rel = rel_to_root(img_path, target)
                    entries[rel] = {
                        "caption": caption,
                        "tags": tags,
                        "surfaces": {
                            "xmp": args.xmp,
                            "iptc": args.iptc,
                            "exif": args.exif,
                            "sidecar": args.sidecar,
                            "json": args.json,
                            "html": args.html,
                        },
                        "original_name": original_name if args.rename_pattern else None,
                    }

                    return True, ""
                except Exception as e:
                    return False, str(e)

            successful, total_processed, errors = process_batch(
                images,
                process_single_image,
                batch_size=batch_size,
                max_workers=max_workers,
                progress_bar=progress_bar,
                desc="Poisoning images",
                disable_progress=quiet,
            )

            # Write log after all processing
            write_log(base, log)

            if not quiet:
                for error in errors:
                    print(f"{Fore.RED}✗{Style.RESET_ALL} {error}")

                print(
                    f"{Fore.YELLOW}Poisoned labels for {successful}/{total_processed} image(s) with preset '{args.preset}'.{Style.RESET_ALL}"
                )

            return 0 if successful == total_processed else 1
        else:
            # Sequential processing for small batches
            count = 0
            for i, img in enumerate(images, 1):
                try:
                    # Compute caption/tags
                    caption, tags = make_caption(
                        args.preset, args.true_hint or img.stem, mapping
                    )

                    # Optional rename (log original name)
                    original_name = img.name
                    if args.rename_pattern:
                        img = rename_with_pattern(img, args.rename_pattern)

                    # Sidecars & metadata
                    if args.sidecar or args.json:
                        write_sidecars(img, caption, tags, emit_json=args.json)

                    try:
                        write_metadata(
                            img,
                            caption,
                            tags,
                            xmp=args.xmp,
                            iptc=args.iptc,
                            exif=args.exif,
                        )
                    except Exception as e:
                        if not quiet:
                            print(
                                f"{Fore.YELLOW}Warning: Failed to write metadata for {img}: {e}{Style.RESET_ALL}"
                            )

                    # Optional HTML
                    if args.html:
                        snippet = html_snippet(img.name, caption, caption)
                        html_file = img.parent / f"{img.stem}.html"
                        html_file.write_text(snippet, encoding="utf-8")

                    rel = rel_to_root(img, target)
                    entries[rel] = {
                        "caption": caption,
                        "tags": tags,
                        "surfaces": {
                            "xmp": args.xmp,
                            "iptc": args.iptc,
                            "exif": args.exif,
                            "sidecar": args.sidecar,
                            "json": args.json,
                            "html": args.html,
                        },
                        "original_name": original_name if args.rename_pattern else None,
                    }
                    count += 1
                    if verbose and not quiet:
                        try:
                            print(
                                f"{Fore.GREEN}✓{Style.RESET_ALL} [{i}/{total}] {img.name}"
                            )
                        except UnicodeEncodeError:
                            print(f"[OK] [{i}/{total}] {img.name}")
                except Exception as e:
                    if not quiet:
                        try:
                            print(
                                f"{Fore.RED}✗{Style.RESET_ALL} [{i}/{total}] {img.name} - {e}"
                            )
                        except UnicodeEncodeError:
                            print(f"[ERROR] [{i}/{total}] {img.name} - {e}")
                    continue

            write_log(base, log)
            if not quiet:
                print(
                    f"{Fore.YELLOW}Poisoned labels for {count}/{total} image(s) with preset '{args.preset}'.{Style.RESET_ALL}"
                )

            return 0
    except Exception as e:
        return handle_error(e, f"poisoning images in {target_arg}")


def cmd_revert(args: argparse.Namespace) -> int:
    """Revert command implementation."""
    try:
        # Accept either a single path (args.path) or list (args.paths)
        path_arg = getattr(args, "path", None)
        if path_arg is None:
            paths_list = getattr(args, "paths", None)
            if paths_list:
                path_arg = paths_list[0]
        if path_arg is None:
            raise InvalidPathError("No input path provided")
        p = Path(path_arg)
        base = p if p.is_dir() else p.parent

        # Load config for dry-run support
        config = load_config()
        dry_run = getattr(args, "dry_run", False)
        quiet = get_config_value(config, "quiet", False)

        if dry_run:
            if not quiet:
                print(
                    f"{Fore.CYAN}DRY RUN: Would revert operations in {base}...{Style.RESET_ALL}"
                )
            # TODO: Implement dry-run preview for revert
            return 0

        removed = revert_dir(base)
        print(
            f"{Fore.CYAN}Reverted. Removed {removed} sidecar/aux files and cleared fields.{Style.RESET_ALL}"
        )
        return 0
    except Exception as e:
        return handle_error(e, f"reverting changes in {path_arg}")


def cmd_interactive(args: argparse.Namespace) -> int:
    """Interactive command implementation."""
    return interactive_mode()


def cmd_gui(args: argparse.Namespace) -> int:
    """Launch modern PyQt6 GUI interface."""
    try:
        # Respect tests that simulate missing PyQt6 by setting sys.modules["PyQt6"] = None
        if "PyQt6" in sys.modules and sys.modules["PyQt6"] is None:
            missing = ModuleNotFoundError("No module named 'PyQt6'")
            print(
                f"{Fore.YELLOW}PyQt6 is not installed. Install GUI extras with:"
                f" pip install -e .[gui]{Style.RESET_ALL}"
            )
            return handle_error(missing, "launching modern PyQt6 GUI")
        # Prefer modern PyQt6 interface
        from .gui_qt.main import main as qt_main

        return qt_main()
    except ModuleNotFoundError as e:
        # Provide friendly guidance when PyQt6 is not installed
        missing_msg = str(e)
        if "PyQt6" in missing_msg or "gui_qt" in missing_msg:
            print(
                f"{Fore.YELLOW}PyQt6 is not installed. Install GUI extras with:"
                f" pip install -e .[gui]{Style.RESET_ALL}"
            )
        return handle_error(e, "launching modern PyQt6 GUI")
    except Exception as e:
        return handle_error(e, "launching modern PyQt6 GUI")


def cmd_audit(args: argparse.Namespace) -> int:
    """Privacy audit command implementation."""
    try:
        # Get paths to audit
        paths_list = getattr(args, "paths", [])
        if not paths_list:
            print(f"{Fore.RED}No paths provided for audit{Style.RESET_ALL}")
            return 1
        
        # Handle single file vs directory
        path = Path(paths_list[0])
        if not path.exists():
            print(f"{Fore.RED}Path not found: {path}{Style.RESET_ALL}")
            return 1
        
        verbose = getattr(args, "verbose", False)
        quiet = getattr(args, "quiet", False)
        recursive = getattr(args, "recursive", False)
        max_files = getattr(args, "max_files", None)
        
        # Single file audit
        if path.is_file():
            if not quiet:
                print(f"{Fore.CYAN}Auditing file: {path.name}{Style.RESET_ALL}")
            
            file_result = audit_file(path)
            
            # Display results
            print(f"\n📁 {file_result.file_path.name}")
            print(f"Risk Score: {file_result.risk_score}/10")
            print(f"Metadata Fields: {file_result.metadata_count}")
            print(f"Privacy Risks: {len(file_result.risks)}")
            
            if file_result.risks:
                print(f"\n🔍 Privacy Risks Found:")
                for risk in file_result.risks:
                    risk_color = {
                        "critical": Fore.RED,
                        "high": Fore.YELLOW,
                        "medium": Fore.BLUE,
                        "low": Fore.GREEN,
                        "info": Fore.CYAN
                    }.get(risk.risk_level.value, "")
                    
                    print(f"  {risk_color}[{risk.risk_level.value.upper()}]{Style.RESET_ALL} {risk.field_name}")
                    if verbose:
                        print(f"    {risk.description}")
                        print(f"    💡 {risk.remediation}")
            
            if file_result.recommendations:
                print(f"\n💡 Recommendations:")
                for rec in file_result.recommendations:
                    print(f"  - {rec}")
            
            return 0
        
        # Directory audit
        if not quiet:
            print(f"{Fore.CYAN}Auditing directory: {path}{Style.RESET_ALL}")
            if recursive:
                print("Scanning recursively...")
            if max_files:
                print(f"Limited to {max_files} files")
        
        # Perform audit
        audit_report = audit_directory(path, recursive=recursive, max_files=max_files)
        
        # Handle errors
        if "error" in audit_report.summary:
            print(f"{Fore.RED}Error: {audit_report.summary['error']}{Style.RESET_ALL}")
            return 1
        
        # Display summary
        summary = audit_report.summary
        print(f"\n📊 Audit Summary")
        print(f"Files Scanned: {summary['files_scanned']}")
        print(f"Total Privacy Risks: {summary['total_risks']}")
        print(f"Average Risk Score: {summary['average_risk_score']}/10")
        print(f"High Risk Files: {summary['high_risk_files']}")
        
        # Risk distribution
        risk_dist = summary['risk_distribution']
        if any(count > 0 for count in risk_dist.values()):
            print(f"\n🎯 Risk Distribution:")
            for level, count in risk_dist.items():
                if count > 0:
                    level_color = {
                        "critical": Fore.RED,
                        "high": Fore.YELLOW,
                        "medium": Fore.BLUE,
                        "low": Fore.GREEN,
                        "info": Fore.CYAN
                    }.get(level, "")
                    print(f"  {level_color}{level.upper()}: {count}{Style.RESET_ALL}")
        
        # Category distribution
        if summary.get('category_distribution'):
            print(f"\n📋 Categories Found:")
            for category, count in summary['category_distribution'].items():
                print(f"  {category}: {count} risks")
        
        # Recommendations
        if audit_report.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in audit_report.recommendations:
                print(f"  {rec}")
        
        # Detailed file results if verbose
        if verbose and audit_report.file_results:
            print(f"\n📁 Detailed File Results:")
            for result in audit_report.file_results[:10]:  # Show first 10
                if result.risks:
                    print(f"\n  {result.file_path.name} (Score: {result.risk_score}/10)")
                    for risk in result.risks[:3]:  # Show top 3 risks per file
                        print(f"    - {risk.category}: {risk.description}")
            
            if len(audit_report.file_results) > 10:
                print(f"    ... and {len(audit_report.file_results) - 10} more files")
        
        # Generate reports
        html_report_path = getattr(args, "report", None)
        if html_report_path:
            html_path = Path(html_report_path)
            generate_html_report(audit_report, html_path)
            print(f"\n📄 HTML report saved to: {html_path}")
        
        json_report_path = getattr(args, "json", None)
        if json_report_path:
            json_path = Path(json_report_path)
            export_audit_json(audit_report, json_path)
            print(f"📊 JSON report saved to: {json_path}")
        
        # Return non-zero if critical risks found
        critical_risks = sum(1 for result in audit_report.file_results for risk in result.risks 
                           if risk.risk_level.value == "critical")
        if critical_risks > 0:
            print(f"\n{Fore.RED}⚠️  {critical_risks} CRITICAL privacy risks found!{Style.RESET_ALL}")
            return 2  # Special return code for critical risks
        
        return 0
        
    except Exception as e:
        return handle_error(e, f"auditing {path}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mm", description="Metadata Multitool")

    # Global options
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    p.add_argument(
        "--quiet", "-q", action="store_true", help="Quiet output (minimal messages)"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview operations without making changes",
    )
    p.add_argument("--config", help="Path to configuration file (.mm_config.yaml)")

    sub = p.add_subparsers(dest="command", required=True)

    pc = sub.add_parser("clean", help="Clean to safe upload")
    pc.add_argument(
        "paths",
        nargs="+",
        metavar="path",
        help="Image file(s) or directory(ies)",
    )
    pc.add_argument(
        "--copy-folder",
        default="safe_upload",
        help="Destination folder for clean copies",
    )
    pc.add_argument(
        "--batch-size", type=int, help="Batch size for processing (overrides config)"
    )
    pc.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of worker processes (overrides config)",
    )
    pc.add_argument(
        "--profile",
        help="Metadata profile to use (see --list-profiles for options)",
    )
    pc.add_argument(
        "--preserve-fields",
        nargs="+",
        help="Specific metadata fields to preserve",
    )
    pc.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available metadata profiles and exit",
    )
    pc.add_argument(
        "--preview",
        metavar="FILE",
        help="Preview what metadata would be preserved/removed for a specific file",
    )
    pc.add_argument(
        "--size",
        help="Filter by file size (e.g., '1MB', '500KB-2MB', '>1GB', '<500KB')",
    )
    pc.add_argument(
        "--date",
        help="Filter by date (e.g., '2024-01-01', '2024-01-01:2024-12-31', '>2024-01-01')",
    )
    pc.add_argument(
        "--formats",
        nargs="+",
        help="Filter by file formats (e.g., --formats .jpg .png .tiff)",
    )
    pc.add_argument(
        "--has-metadata", action="store_true", help="Include only files with metadata"
    )
    pc.add_argument(
        "--no-metadata", action="store_true", help="Include only files without metadata"
    )
    pc.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview operations without making changes",
    )
    pc.add_argument(
        "--backup", action="store_true", help="Create backup before processing"
    )
    pc.add_argument(
        "--no-backup", action="store_true", help="Do not create backup before processing"
    )
    pc.add_argument(
        "--backup-dir", help="Directory to store backups (default: .mm_backups)"
    )
    pc.set_defaults(func=cmd_clean)

    pp = sub.add_parser("poison", help="Optional label poisoning for anti-scraping")
    pp.add_argument(
        "paths",
        nargs="+",
        metavar="path",
        help="Image file(s) or directory(ies)",
    )
    pp.add_argument(
        "--preset",
        choices=["label_flip", "clip_confuse", "style_bloat"],
        default="label_flip",
    )
    pp.add_argument(
        "--true-hint", default="", help="Hint about real content (label_flip uses this)"
    )
    pp.add_argument(
        "--xmp", action="store_true", help="Write XMP title/description/subject"
    )
    pp.add_argument("--iptc", action="store_true", help="Write IPTC caption/keywords")
    pp.add_argument("--exif", action="store_true", help="Write EXIF user comment")
    pp.add_argument(
        "--sidecar", action="store_true", help="Write <image>.txt caption sidecar"
    )
    pp.add_argument(
        "--json", action="store_true", help="Write <image>.json LAION-style sidecar"
    )
    pp.add_argument(
        "--csv", default="", help="CSV mapping file (real_label,poison_label)"
    )
    pp.add_argument(
        "--rename-pattern",
        default="",
        help="Rename files using pattern, e.g. '{stem}_toaster' or 'toaster_{rand}'",
    )
    pp.add_argument(
        "--html",
        action="store_true",
        help="Emit <image>.html with poisoned alt/title snippet",
    )
    pp.add_argument(
        "--batch-size", type=int, help="Batch size for processing (overrides config)"
    )
    pp.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of worker processes (overrides config)",
    )
    pp.add_argument(
        "--size",
        help="Filter by file size (e.g., '1MB', '500KB-2MB', '>1GB', '<500KB')",
    )
    pp.add_argument(
        "--date",
        help="Filter by date (e.g., '2024-01-01', '2024-01-01:2024-12-31', '>2024-01-01')",
    )
    pp.add_argument(
        "--formats",
        nargs="+",
        help="Filter by file formats (e.g., --formats .jpg .png .tiff)",
    )
    pp.add_argument(
        "--has-metadata", action="store_true", help="Include only files with metadata"
    )
    pp.add_argument(
        "--no-metadata", action="store_true", help="Include only files without metadata"
    )
    pp.add_argument(
        "--backup", action="store_true", help="Create backup before processing"
    )
    pp.add_argument(
        "--no-backup", action="store_true", help="Do not create backup before processing"
    )
    pp.add_argument(
        "--backup-dir", help="Directory to store backups (default: .mm_backups)"
    )
    pp.set_defaults(func=cmd_poison)

    pr = sub.add_parser("revert", help="Undo Multitool outputs in a directory")
    pr.add_argument(
        "paths",
        nargs="+",
        metavar="path",
        help="Directory or one file within it",
    )
    pr.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview operations without making changes",
    )
    pr.set_defaults(func=cmd_revert)

    pi = sub.add_parser("interactive", help="Interactive mode for guided workflows")
    pi.set_defaults(func=cmd_interactive)

    pg = sub.add_parser("gui", help="Launch modern PyQt6 GUI")
    pg.set_defaults(func=cmd_gui)

    pa = sub.add_parser("audit", help="Analyze images for privacy risks in metadata")
    pa.add_argument(
        "paths",
        nargs="+",
        metavar="path",
        help="Image file(s) or directory(ies) to audit",
    )
    pa.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Scan subdirectories recursively"
    )
    pa.add_argument(
        "--max-files",
        type=int,
        help="Maximum number of files to scan (for large directories)"
    )
    pa.add_argument(
        "--report",
        help="Generate HTML report at specified path (e.g., privacy_report.html)"
    )
    pa.add_argument(
        "--json",
        help="Export JSON report at specified path (e.g., privacy_data.json)"
    )
    pa.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed findings for each file"
    )
    pa.set_defaults(func=cmd_audit)

    return p


def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments."""
    # Validate first provided path if available
    candidate_path = None
    if isinstance(getattr(args, "path", None), (str, Path)) and getattr(args, "path"):
        candidate_path = getattr(args, "path")
    elif isinstance(getattr(args, "paths", None), list) and getattr(args, "paths"):
        first = getattr(args, "paths")[0]
        if isinstance(first, (str, Path)):
            candidate_path = first
    if isinstance(candidate_path, (str, Path)) and candidate_path:
        p = Path(candidate_path)
        if not p.exists():
            raise InvalidPathError(f"Path does not exist: {p}")

    csv_value = getattr(args, "csv", None)
    if isinstance(csv_value, (str, Path)) and csv_value:
        csv_path = Path(csv_value)
        if not csv_path.exists():
            raise InvalidPathError(f"CSV file does not exist: {csv_path}")
        if not csv_path.suffix.lower() == ".csv":
            raise InvalidPathError(f"File is not a CSV: {csv_path}")

    # Require preset when using poison command
    if getattr(args, "command", "") == "poison" and not getattr(args, "preset", None):
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    try:
        parser = build_parser()
        # Ensure global help returns success for end-to-end tests
        raw_args = argv if argv is not None else sys.argv[1:]
        if any(flag in raw_args for flag in ("-h", "--help")) and len(raw_args) == 1:
            parser.print_help()
            return 0
        try:
            args = parser.parse_args(argv)
        except SystemExit as se:
            # Return non-zero exit code instead of exiting the process
            return 0 if (se.code is None or se.code == 0) else se.code

        # Validate arguments
        validate_args(args)

        # Execute command based on parsed subcommand
        cmd = getattr(args, "command", None)
        if cmd == "clean":
            return cmd_clean(args)
        if cmd == "poison":
            return cmd_poison(args)
        if cmd == "revert":
            return cmd_revert(args)
        if cmd == "interactive":
            return cmd_interactive(args)
        if cmd == "gui":
            return cmd_gui(args)
        # Unknown command
        return 1
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
        return 130
    except Exception as e:
        return handle_error(e, "parsing command line arguments")


if __name__ == "__main__":
    raise SystemExit(main())
