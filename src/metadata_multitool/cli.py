"""Command-line interface for the Metadata Multitool."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, List, Tuple

from colorama import Fore, Style
from colorama import init as color_init

from .batch import process_batch
from .clean import clean_copy
from .config import load_config, get_config_value
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
from .html import html_snippet
from .poison import (
    load_csv_mapping,
    make_caption,
    rename_with_pattern,
    write_metadata,
    write_sidecars,
)
from .revert import revert_dir
from .interactive import interactive_mode
from .filters import FileFilter, create_filter_from_args, parse_size_filter, parse_date_filter
from .logging import get_logger, log_operation_summary
from .backup import create_backup_manager, backup_before_operation

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
    has_filters = any([
        getattr(args, 'size', None),
        getattr(args, 'date', None),
        getattr(args, 'formats', None),
        getattr(args, 'has_metadata', False),
        getattr(args, 'no_metadata', False),
    ])
    
    if not has_filters:
        return images
    
    # Create filter
    file_filter = FileFilter()
    
    # Apply size filter
    if hasattr(args, 'size') and args.size:
        try:
            min_size, max_size = parse_size_filter(args.size)
            file_filter.add_size_filter(min_size=min_size, max_size=max_size)
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Invalid size filter '{args.size}': {e}{Style.RESET_ALL}")
    
    # Apply date filter
    if hasattr(args, 'date') and args.date:
        try:
            min_date, max_date = parse_date_filter(args.date)
            file_filter.add_date_filter(min_date=min_date, max_date=max_date)
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Invalid date filter '{args.date}': {e}{Style.RESET_ALL}")
    
    # Apply format filter
    if hasattr(args, 'formats') and args.formats:
        file_filter.add_format_filter(args.formats)
    
    # Apply metadata filter
    if hasattr(args, 'has_metadata') and args.has_metadata:
        file_filter.add_metadata_filter(has_metadata=True)
    elif hasattr(args, 'no_metadata') and args.no_metadata:
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
        if isinstance(error, InvalidPathError):
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
        print(f"Error: {error}")
        if context:
            print(f"Context: {context}")

    return 1


def cmd_clean(args: argparse.Namespace) -> int:
    """Clean command implementation."""
    try:
        # Load configuration
        config_path = getattr(args, 'config', None)
        if config_path:
            config = load_config(Path(config_path))
        else:
            config = load_config()
        
        # Override config with command line arguments
        verbose = getattr(args, 'verbose', False) or get_config_value(config, 'verbose', False)
        quiet = getattr(args, 'quiet', False) or get_config_value(config, 'quiet', False)
        dry_run = getattr(args, 'dry_run', False)
        batch_size = getattr(args, 'batch_size', None) or get_config_value(config, 'batch_size', 100)
        max_workers = getattr(args, 'max_workers', None) or get_config_value(config, 'max_workers', 4)
        progress_bar = get_config_value(config, 'progress_bar', True) and not quiet
        log_level = get_config_value(config, 'log_level', 'INFO')
        
        # Set up logging
        logger = get_logger(log_level=log_level)
        
        # Set up backup if requested
        backup_manager = None
        if getattr(args, 'backup', False) or get_config_value(config, 'backup_before_operations', False):
            backup_dir = getattr(args, 'backup_dir', None)
            if backup_dir:
                backup_manager = create_backup_manager(Path(backup_dir))
            else:
                backup_manager = create_backup_manager()
        
        src = Path(args.path)
        
        # Make output directory relative to input directory
        if src.is_dir():
            out_dir = ensure_dir(src / args.copy_folder)
        else:
            out_dir = ensure_dir(src.parent / args.copy_folder)

        # Get list of images first for progress tracking
        images = list(iter_images(src))
        images = apply_filters(args, images)
        total = len(images)

        if total == 0:
            if not quiet:
                print(f"{Fore.YELLOW}No images found in {src}{Style.RESET_ALL}")
            return 0

        if dry_run:
            if not quiet:
                print(f"{Fore.CYAN}DRY RUN: Would process {total} images...{Style.RESET_ALL}")
                for i, img in enumerate(images, 1):
                    print(f"  [{i}/{total}] {img.name} → {out_dir / img.name}")
            logger.log_info(f"Dry run completed for {total} images")
            return 0

        if not quiet:
            print(f"{Fore.CYAN}Processing {total} images...{Style.RESET_ALL}")

        # Create backup if requested
        backup_id = None
        if backup_manager and not dry_run:
            try:
                backup_id = backup_before_operation(src, "clean", backup_manager)
                if backup_id and not quiet:
                    print(f"{Fore.CYAN}Created backup: {backup_id}{Style.RESET_ALL}")
            except Exception as e:
                if not quiet:
                    print(f"{Fore.YELLOW}Warning: Failed to create backup: {e}{Style.RESET_ALL}")

        # Use batch processing for large directories
        if total >= batch_size and max_workers > 1:
            logger.log_operation_start("clean_batch", {
                "total_images": total,
                "batch_size": batch_size,
                "max_workers": max_workers,
                "output_dir": str(out_dir)
            })
            
            def process_single_image(img_path: Path) -> Tuple[bool, str]:
                try:
                    clean_copy(img_path, out_dir)
                    logger.log_file_processed(img_path, "clean", True)
                    return True, ""
                except Exception as e:
                    logger.log_file_processed(img_path, "clean", False, {"error": str(e)})
                    return False, str(e)
            
            successful, total_processed, errors = process_batch(
                images,
                process_single_image,
                batch_size=batch_size,
                max_workers=max_workers,
                progress_bar=progress_bar,
                desc="Cleaning images",
                disable_progress=quiet
            )
            
            if not quiet:
                for error in errors:
                    print(f"{Fore.RED}✗{Style.RESET_ALL} {error}")
                
                print(f"{Fore.GREEN}Cleaned {successful}/{total_processed} images → {out_dir}{Style.RESET_ALL}")
            
            logger.log_operation_end("clean_batch", successful == total_processed, {
                "successful": successful,
                "total_processed": total_processed,
                "errors": len(errors)
            })
            
            return 0 if successful == total_processed else 1
        else:
            # Sequential processing for small batches
            logger.log_operation_start("clean_sequential", {
                "total_images": total,
                "output_dir": str(out_dir)
            })
            
            count = 0
            errors = []
            for i, img in enumerate(images, 1):
                try:
                    clean_copy(img, out_dir)
                    count += 1
                    logger.log_file_processed(img, "clean", True)
                    if verbose and not quiet:
                        try:
                            print(f"{Fore.GREEN}✓{Style.RESET_ALL} [{i}/{total}] {img.name}")
                        except UnicodeEncodeError:
                            print(f"[OK] [{i}/{total}] {img.name}")
                except Exception as e:
                    errors.append(str(e))
                    logger.log_file_processed(img, "clean", False, {"error": str(e)})
                    if not quiet:
                        try:
                            print(f"{Fore.RED}✗{Style.RESET_ALL} [{i}/{total}] {img.name} - {e}")
                        except UnicodeEncodeError:
                            print(f"[ERROR] [{i}/{total}] {img.name} - {e}")
                    continue

            if not quiet:
                try:
                    print(f"{Fore.GREEN}Cleaned {count}/{total} images → {out_dir}{Style.RESET_ALL}")
                except UnicodeEncodeError:
                    print(f"Cleaned {count}/{total} images -> {out_dir}")
            
            logger.log_operation_end("clean_sequential", count == total, {
                "successful": count,
                "total": total,
                "errors": len(errors)
            })
            
            return 0
    except Exception as e:
        return handle_error(e, f"cleaning images from {args.path}")


def cmd_poison(args: argparse.Namespace) -> int:
    """Poison command implementation."""
    try:
        # Load configuration
        config_path = getattr(args, 'config', None)
        if config_path:
            config = load_config(Path(config_path))
        else:
            config = load_config()
        
        # Override config with command line arguments
        verbose = getattr(args, 'verbose', False) or get_config_value(config, 'verbose', False)
        quiet = getattr(args, 'quiet', False) or get_config_value(config, 'quiet', False)
        dry_run = getattr(args, 'dry_run', False)
        batch_size = getattr(args, 'batch_size', None) or get_config_value(config, 'batch_size', 100)
        max_workers = getattr(args, 'max_workers', None) or get_config_value(config, 'max_workers', 4)
        progress_bar = get_config_value(config, 'progress_bar', True) and not quiet
        
        target = Path(args.path)
        base = target if target.is_dir() else target.parent
        log = read_log(base)
        entries = log.setdefault("entries", {})

        # Load CSV mapping if provided
        mapping = {}
        if args.csv:
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
                print(f"{Fore.CYAN}DRY RUN: Would poison {total} images with preset '{args.preset}'...{Style.RESET_ALL}")
                for i, img in enumerate(images, 1):
                    caption, tags = make_caption(args.preset, args.true_hint or img.stem, mapping)
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
                            img_path, caption, tags, xmp=args.xmp, iptc=args.iptc, exif=args.exif
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
                disable_progress=quiet
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
                            img, caption, tags, xmp=args.xmp, iptc=args.iptc, exif=args.exif
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
                            print(f"{Fore.GREEN}✓{Style.RESET_ALL} [{i}/{total}] {img.name}")
                        except UnicodeEncodeError:
                            print(f"[OK] [{i}/{total}] {img.name}")
                except Exception as e:
                    if not quiet:
                        try:
                            print(f"{Fore.RED}✗{Style.RESET_ALL} [{i}/{total}] {img.name} - {e}")
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
        return handle_error(e, f"poisoning images in {args.path}")


def cmd_revert(args: argparse.Namespace) -> int:
    """Revert command implementation."""
    try:
        p = Path(args.path)
        base = p if p.is_dir() else p.parent
        removed = revert_dir(base)
        print(
            f"{Fore.CYAN}Reverted. Removed {removed} sidecar/aux files and cleared fields.{Style.RESET_ALL}"
        )
        return 0
    except Exception as e:
        return handle_error(e, f"reverting changes in {args.path}")


def cmd_interactive(args: argparse.Namespace) -> int:
    """Interactive command implementation."""
    return interactive_mode()


def cmd_gui(args: argparse.Namespace) -> int:
    """Launch GUI interface."""
    try:
        from .gui.main_window import MainWindow
        app = MainWindow()
        app.run()
        return 0
    except Exception as e:
        return handle_error(e, "launching GUI interface")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mm", description="Metadata Multitool")
    
    # Global options
    p.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    p.add_argument(
        "--quiet", "-q", action="store_true", help="Quiet output (minimal messages)"
    )
    p.add_argument(
        "--dry-run", action="store_true", help="Preview operations without making changes"
    )
    p.add_argument(
        "--config", help="Path to configuration file (.mm_config.yaml)"
    )
    
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser(
        "clean", help="Clean to safe upload"
    )
    pc.add_argument("path", help="Image file or directory")
    pc.add_argument(
        "--copy-folder",
        default="safe_upload",
        help="Destination folder for clean copies",
    )
    pc.add_argument(
        "--batch-size", type=int, help="Batch size for processing (overrides config)"
    )
    pc.add_argument(
        "--max-workers", type=int, help="Maximum number of worker processes (overrides config)"
    )
    pc.add_argument(
        "--size", help="Filter by file size (e.g., '1MB', '500KB-2MB', '>1GB', '<500KB')"
    )
    pc.add_argument(
        "--date", help="Filter by date (e.g., '2024-01-01', '2024-01-01:2024-12-31', '>2024-01-01')"
    )
    pc.add_argument(
        "--formats", nargs="+", help="Filter by file formats (e.g., --formats .jpg .png .tiff)"
    )
    pc.add_argument(
        "--has-metadata", action="store_true", help="Include only files with metadata"
    )
    pc.add_argument(
        "--no-metadata", action="store_true", help="Include only files without metadata"
    )
    pc.add_argument(
        "--backup", action="store_true", help="Create backup before processing"
    )
    pc.add_argument(
        "--backup-dir", help="Directory to store backups (default: .mm_backups)"
    )
    pc.set_defaults(func=cmd_clean)

    pp = sub.add_parser("poison", help="Optional label poisoning for anti-scraping")
    pp.add_argument("path", help="Image file or directory")
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
        "--max-workers", type=int, help="Maximum number of worker processes (overrides config)"
    )
    pp.add_argument(
        "--size", help="Filter by file size (e.g., '1MB', '500KB-2MB', '>1GB', '<500KB')"
    )
    pp.add_argument(
        "--date", help="Filter by date (e.g., '2024-01-01', '2024-01-01:2024-12-31', '>2024-01-01')"
    )
    pp.add_argument(
        "--formats", nargs="+", help="Filter by file formats (e.g., --formats .jpg .png .tiff)"
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
        "--backup-dir", help="Directory to store backups (default: .mm_backups)"
    )
    pp.set_defaults(func=cmd_poison)

    pr = sub.add_parser("revert", help="Undo Multitool outputs in a directory")
    pr.add_argument("path", help="Directory or one file within it")
    pr.set_defaults(func=cmd_revert)

    pi = sub.add_parser("interactive", help="Interactive mode for guided workflows")
    pi.set_defaults(func=cmd_interactive)

    pg = sub.add_parser("gui", help="Launch graphical user interface")
    pg.set_defaults(func=cmd_gui)

    return p


def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments."""
    if hasattr(args, "path") and args.path:
        path = Path(args.path)
        if not path.exists():
            raise InvalidPathError(f"Path does not exist: {path}")

    if hasattr(args, "csv") and args.csv:
        csv_path = Path(args.csv)
        if not csv_path.exists():
            raise InvalidPathError(f"CSV file does not exist: {csv_path}")
        if not csv_path.suffix.lower() == ".csv":
            raise InvalidPathError(f"File is not a CSV: {csv_path}")


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    try:
        parser = build_parser()
        args = parser.parse_args(argv)

        # Validate arguments
        validate_args(args)

        # Execute command
        return args.func(args)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
        return 130
    except Exception as e:
        return handle_error(e, "parsing command line arguments")


if __name__ == "__main__":
    raise SystemExit(main())
