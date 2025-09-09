"""Interactive mode for the Metadata Multitool."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from colorama import Fore, Style
from colorama import init as color_init

from .batch import process_batch
from .clean import clean_copy
from .config import load_config, get_config_value, save_config
from .core import ensure_dir, iter_images, read_log, write_log, rel_to_root
from .poison import load_csv_mapping, make_caption, rename_with_pattern, write_metadata, write_sidecars
from .html import html_snippet
from .revert import revert_dir

color_init()


class InteractiveError(Exception):
    """Raised when interactive operations fail."""

    pass


def interactive_mode() -> int:
    """
    Run the interactive mode for guided workflows.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        print(f"{Fore.CYAN}=== Metadata Multitool Interactive Mode ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Welcome! This mode will guide you through common workflows.{Style.RESET_ALL}\n")
        
        # Load configuration
        config = load_config()
        
        while True:
            try:
                choice = show_main_menu()
                
                if choice == "1":
                    handle_clean_workflow(config)
                elif choice == "2":
                    handle_poison_workflow(config)
                elif choice == "3":
                    handle_revert_workflow()
                elif choice == "4":
                    handle_config_workflow(config)
                elif choice == "5":
                    handle_batch_workflow(config)
                elif choice == "q":
                    print(f"{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
                    return 0
                else:
                    print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Operation cancelled.{Style.RESET_ALL}")
                continue
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                continue
                
    except Exception as e:
        print(f"{Fore.RED}Fatal error in interactive mode: {e}{Style.RESET_ALL}")
        return 1


def show_main_menu() -> str:
    """Display the main menu and get user choice."""
    print(f"\n{Fore.CYAN}Main Menu:{Style.RESET_ALL}")
    print("1. Clean images (strip metadata for safe upload)")
    print("2. Poison images (add misleading metadata)")
    print("3. Revert changes (undo previous operations)")
    print("4. Configure settings")
    print("5. Batch operations")
    print("q. Quit")
    
    while True:
        choice = input(f"\n{Fore.GREEN}Choose an option (1-5, q): {Style.RESET_ALL}").strip().lower()
        if choice in ["1", "2", "3", "4", "5", "q"]:
            return choice
        print(f"{Fore.RED}Please enter 1-5 or 'q'.{Style.RESET_ALL}")


def handle_clean_workflow(config: Dict[str, Any]) -> None:
    """Handle the clean workflow interactively."""
    print(f"\n{Fore.CYAN}=== Clean Images Workflow ==={Style.RESET_ALL}")
    
    # Get input path
    while True:
        path_input = input(f"{Fore.GREEN}Enter path to images (file or directory): {Style.RESET_ALL}").strip()
        if not path_input:
            print(f"{Fore.RED}Path cannot be empty.{Style.RESET_ALL}")
            continue
            
        path = Path(path_input)
        if not path.exists():
            print(f"{Fore.RED}Path does not exist: {path}{Style.RESET_ALL}")
            continue
        break
    
    # Get output folder
    copy_folder = input(f"{Fore.GREEN}Output folder (default: safe_upload): {Style.RESET_ALL}").strip()
    if not copy_folder:
        copy_folder = "safe_upload"
    
    # Get processing options
    verbose = get_yes_no("Verbose output? (y/n): ", default=False)
    dry_run = get_yes_no("Dry run (preview only)? (y/n): ", default=True)
    
    # Process images
    try:
        src = Path(path_input)
        if src.is_dir():
            out_dir = ensure_dir(src / copy_folder)
        else:
            out_dir = ensure_dir(src.parent / copy_folder)

        images = list(iter_images(src))
        total = len(images)

        if total == 0:
            print(f"{Fore.YELLOW}No images found in {src}{Style.RESET_ALL}")
            return

        if dry_run:
            print(f"{Fore.CYAN}DRY RUN: Would process {total} images...{Style.RESET_ALL}")
            for i, img in enumerate(images, 1):
                print(f"  [{i}/{total}] {img.name} → {out_dir / img.name}")
            return

        print(f"{Fore.CYAN}Processing {total} images...{Style.RESET_ALL}")
        
        # Use batch processing for large directories
        batch_size = get_config_value(config, 'batch_size', 100)
        max_workers = get_config_value(config, 'max_workers', 4)
        
        if total >= batch_size and max_workers > 1:
            def process_single_image(img_path: Path) -> tuple[bool, str]:
                try:
                    clean_copy(img_path, out_dir)
                    return True, ""
                except Exception as e:
                    return False, str(e)
            
            successful, total_processed, errors = process_batch(
                images,
                process_single_image,
                batch_size=batch_size,
                max_workers=max_workers,
                progress_bar=True,
                desc="Cleaning images"
            )
            
            for error in errors:
                print(f"{Fore.RED}✗{Style.RESET_ALL} {error}")
            
            print(f"{Fore.GREEN}Cleaned {successful}/{total_processed} images → {out_dir}{Style.RESET_ALL}")
        else:
            # Sequential processing
            count = 0
            for i, img in enumerate(images, 1):
                try:
                    clean_copy(img, out_dir)
                    count += 1
                    if verbose:
                        print(f"{Fore.GREEN}✓{Style.RESET_ALL} [{i}/{total}] {img.name}")
                except Exception as e:
                    print(f"{Fore.RED}✗{Style.RESET_ALL} [{i}/{total}] {img.name} - {e}")
                    continue

            print(f"{Fore.GREEN}Cleaned {count}/{total} images → {out_dir}{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}Error during clean operation: {e}{Style.RESET_ALL}")


def handle_poison_workflow(config: Dict[str, Any]) -> None:
    """Handle the poison workflow interactively."""
    print(f"\n{Fore.CYAN}=== Poison Images Workflow ==={Style.RESET_ALL}")
    
    # Get input path
    while True:
        path_input = input(f"{Fore.GREEN}Enter path to images (file or directory): {Style.RESET_ALL}").strip()
        if not path_input:
            print(f"{Fore.RED}Path cannot be empty.{Style.RESET_ALL}")
            continue
            
        path = Path(path_input)
        if not path.exists():
            print(f"{Fore.RED}Path does not exist: {path}{Style.RESET_ALL}")
            continue
        break
    
    # Get preset
    print(f"\n{Fore.CYAN}Choose poison preset:{Style.RESET_ALL}")
    print("1. label_flip - Replace labels with misleading ones")
    print("2. clip_confuse - Add confusing random tokens")
    print("3. style_bloat - Add style-related keywords")
    
    while True:
        preset_choice = input(f"{Fore.GREEN}Choose preset (1-3): {Style.RESET_ALL}").strip()
        if preset_choice == "1":
            preset = "label_flip"
            break
        elif preset_choice == "2":
            preset = "clip_confuse"
            break
        elif preset_choice == "3":
            preset = "style_bloat"
            break
        print(f"{Fore.RED}Please enter 1-3.{Style.RESET_ALL}")
    
    # Get true hint for label_flip
    true_hint = ""
    if preset == "label_flip":
        true_hint = input(f"{Fore.GREEN}Enter true content hint (optional): {Style.RESET_ALL}").strip()
    
    # Get output options
    print(f"\n{Fore.CYAN}Choose output formats:{Style.RESET_ALL}")
    xmp = get_yes_no("Write XMP metadata? (y/n): ", default=True)
    iptc = get_yes_no("Write IPTC metadata? (y/n): ", default=True)
    exif = get_yes_no("Write EXIF metadata? (y/n): ", default=False)
    sidecar = get_yes_no("Write .txt sidecar files? (y/n): ", default=True)
    json_sidecar = get_yes_no("Write .json sidecar files? (y/n): ", default=False)
    html = get_yes_no("Write .html snippet files? (y/n): ", default=False)
    
    # Get rename pattern
    rename_pattern = input(f"{Fore.GREEN}Rename pattern (optional, e.g., '{stem}_toaster'): {Style.RESET_ALL}").strip()
    
    # Get CSV mapping
    csv_path = input(f"{Fore.GREEN}CSV mapping file (optional): {Style.RESET_ALL}").strip()
    mapping = {}
    if csv_path:
        try:
            mapping = load_csv_mapping(Path(csv_path))
            print(f"{Fore.CYAN}Loaded {len(mapping)} mappings from CSV{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Failed to load CSV mapping: {e}{Style.RESET_ALL}")
    
    # Get processing options
    verbose = get_yes_no("Verbose output? (y/n): ", default=False)
    dry_run = get_yes_no("Dry run (preview only)? (y/n): ", default=True)
    
    # Process images
    try:
        target = Path(path_input)
        base = target if target.is_dir() else target.parent
        log = read_log(base)
        entries = log.setdefault("entries", {})

        images = list(iter_images(target))
        total = len(images)

        if total == 0:
            print(f"{Fore.YELLOW}No images found in {target}{Style.RESET_ALL}")
            return

        if dry_run:
            print(f"{Fore.CYAN}DRY RUN: Would poison {total} images with preset '{preset}'...{Style.RESET_ALL}")
            for i, img in enumerate(images, 1):
                caption, tags = make_caption(preset, true_hint or img.stem, mapping)
                print(f"  [{i}/{total}] {img.name} → '{caption}' {tags}")
            return

        print(f"{Fore.CYAN}Poisoning {total} images with preset '{preset}'...{Style.RESET_ALL}")
        
        # Use batch processing for large directories
        batch_size = get_config_value(config, 'batch_size', 100)
        max_workers = get_config_value(config, 'max_workers', 4)
        
        if total >= batch_size and max_workers > 1:
            def process_single_image(img_path: Path) -> tuple[bool, str]:
                try:
                    caption, tags = make_caption(preset, true_hint or img_path.stem, mapping)
                    
                    original_name = img_path.name
                    if rename_pattern:
                        img_path = rename_with_pattern(img_path, rename_pattern)
                    
                    if sidecar or json_sidecar:
                        write_sidecars(img_path, caption, tags, emit_json=json_sidecar)
                    
                    try:
                        write_metadata(img_path, caption, tags, xmp=xmp, iptc=iptc, exif=exif)
                    except Exception as e:
                        return False, f"Failed to write metadata: {e}"
                    
                    if html:
                        snippet = html_snippet(img_path.name, caption, caption)
                        html_file = img_path.parent / f"{img_path.stem}.html"
                        html_file.write_text(snippet, encoding="utf-8")
                    
                    rel = rel_to_root(img_path, target)
                    entries[rel] = {
                        "caption": caption,
                        "tags": tags,
                        "surfaces": {
                            "xmp": xmp,
                            "iptc": iptc,
                            "exif": exif,
                            "sidecar": sidecar,
                            "json": json_sidecar,
                            "html": html,
                        },
                        "original_name": original_name if rename_pattern else None,
                    }
                    
                    return True, ""
                except Exception as e:
                    return False, str(e)
            
            successful, total_processed, errors = process_batch(
                images,
                process_single_image,
                batch_size=batch_size,
                max_workers=max_workers,
                progress_bar=True,
                desc="Poisoning images"
            )
            
            write_log(base, log)
            
            for error in errors:
                print(f"{Fore.RED}✗{Style.RESET_ALL} {error}")
            
            print(f"{Fore.YELLOW}Poisoned labels for {successful}/{total_processed} image(s) with preset '{preset}'.{Style.RESET_ALL}")
        else:
            # Sequential processing
            count = 0
            for i, img in enumerate(images, 1):
                try:
                    caption, tags = make_caption(preset, true_hint or img.stem, mapping)
                    
                    original_name = img.name
                    if rename_pattern:
                        img = rename_with_pattern(img, rename_pattern)
                    
                    if sidecar or json_sidecar:
                        write_sidecars(img, caption, tags, emit_json=json_sidecar)
                    
                    try:
                        write_metadata(img, caption, tags, xmp=xmp, iptc=iptc, exif=exif)
                    except Exception as e:
                        if verbose:
                            print(f"{Fore.YELLOW}Warning: Failed to write metadata for {img}: {e}{Style.RESET_ALL}")
                    
                    if html:
                        snippet = html_snippet(img.name, caption, caption)
                        html_file = img.parent / f"{img.stem}.html"
                        html_file.write_text(snippet, encoding="utf-8")
                    
                    rel = rel_to_root(img, target)
                    entries[rel] = {
                        "caption": caption,
                        "tags": tags,
                        "surfaces": {
                            "xmp": xmp,
                            "iptc": iptc,
                            "exif": exif,
                            "sidecar": sidecar,
                            "json": json_sidecar,
                            "html": html,
                        },
                        "original_name": original_name if rename_pattern else None,
                    }
                    count += 1
                    if verbose:
                        print(f"{Fore.GREEN}✓{Style.RESET_ALL} [{i}/{total}] {img.name}")
                except Exception as e:
                    print(f"{Fore.RED}✗{Style.RESET_ALL} [{i}/{total}] {img.name} - {e}")
                    continue

            write_log(base, log)
            print(f"{Fore.YELLOW}Poisoned labels for {count}/{total} image(s) with preset '{preset}'.{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}Error during poison operation: {e}{Style.RESET_ALL}")


def handle_revert_workflow() -> None:
    """Handle the revert workflow interactively."""
    print(f"\n{Fore.CYAN}=== Revert Changes Workflow ==={Style.RESET_ALL}")
    
    # Get input path
    while True:
        path_input = input(f"{Fore.GREEN}Enter path to directory: {Style.RESET_ALL}").strip()
        if not path_input:
            print(f"{Fore.RED}Path cannot be empty.{Style.RESET_ALL}")
            continue
            
        path = Path(path_input)
        if not path.exists():
            print(f"{Fore.RED}Path does not exist: {path}{Style.RESET_ALL}")
            continue
        if not path.is_dir():
            print(f"{Fore.RED}Path must be a directory: {path}{Style.RESET_ALL}")
            continue
        break
    
    # Confirm revert
    confirm = get_yes_no(f"Revert all changes in {path}? (y/n): ", default=False)
    if not confirm:
        print(f"{Fore.YELLOW}Revert cancelled.{Style.RESET_ALL}")
        return
    
    try:
        removed = revert_dir(path)
        print(f"{Fore.CYAN}Reverted. Removed {removed} sidecar/aux files and cleared fields.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error during revert operation: {e}{Style.RESET_ALL}")


def handle_config_workflow(config: Dict[str, Any]) -> None:
    """Handle the configuration workflow interactively."""
    print(f"\n{Fore.CYAN}=== Configuration Workflow ==={Style.RESET_ALL}")
    
    while True:
        print(f"\n{Fore.CYAN}Current Configuration:{Style.RESET_ALL}")
        print(f"  Batch size: {get_config_value(config, 'batch_size', 100)}")
        print(f"  Max workers: {get_config_value(config, 'max_workers', 4)}")
        print(f"  Progress bar: {get_config_value(config, 'progress_bar', True)}")
        print(f"  Verbose: {get_config_value(config, 'verbose', False)}")
        print(f"  Quiet: {get_config_value(config, 'quiet', False)}")
        print(f"  Backup before operations: {get_config_value(config, 'backup_before_operations', True)}")
        
        print(f"\n{Fore.CYAN}Options:{Style.RESET_ALL}")
        print("1. Change batch size")
        print("2. Change max workers")
        print("3. Toggle progress bar")
        print("4. Toggle verbose mode")
        print("5. Toggle quiet mode")
        print("6. Toggle backup before operations")
        print("7. Save configuration")
        print("8. Back to main menu")
        
        choice = input(f"{Fore.GREEN}Choose an option (1-8): {Style.RESET_ALL}").strip()
        
        if choice == "1":
            try:
                new_batch_size = int(input(f"{Fore.GREEN}Enter new batch size (current: {get_config_value(config, 'batch_size', 100)}): {Style.RESET_ALL}"))
                if new_batch_size > 0:
                    config['batch_size'] = new_batch_size
                    print(f"{Fore.GREEN}Batch size updated to {new_batch_size}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Batch size must be positive{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Invalid number{Style.RESET_ALL}")
        elif choice == "2":
            try:
                new_max_workers = int(input(f"{Fore.GREEN}Enter new max workers (current: {get_config_value(config, 'max_workers', 4)}): {Style.RESET_ALL}"))
                if new_max_workers > 0:
                    config['max_workers'] = new_max_workers
                    print(f"{Fore.GREEN}Max workers updated to {new_max_workers}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Max workers must be positive{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Invalid number{Style.RESET_ALL}")
        elif choice == "3":
            config['progress_bar'] = not get_config_value(config, 'progress_bar', True)
            print(f"{Fore.GREEN}Progress bar {'enabled' if config['progress_bar'] else 'disabled'}{Style.RESET_ALL}")
        elif choice == "4":
            config['verbose'] = not get_config_value(config, 'verbose', False)
            print(f"{Fore.GREEN}Verbose mode {'enabled' if config['verbose'] else 'disabled'}{Style.RESET_ALL}")
        elif choice == "5":
            config['quiet'] = not get_config_value(config, 'quiet', False)
            print(f"{Fore.GREEN}Quiet mode {'enabled' if config['quiet'] else 'disabled'}{Style.RESET_ALL}")
        elif choice == "6":
            config['backup_before_operations'] = not get_config_value(config, 'backup_before_operations', True)
            print(f"{Fore.GREEN}Backup before operations {'enabled' if config['backup_before_operations'] else 'disabled'}{Style.RESET_ALL}")
        elif choice == "7":
            try:
                config_path = Path(".mm_config.yaml")
                save_config(config, config_path)
                print(f"{Fore.GREEN}Configuration saved to {config_path}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Failed to save configuration: {e}{Style.RESET_ALL}")
        elif choice == "8":
            break
        else:
            print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")


def handle_batch_workflow(config: Dict[str, Any]) -> None:
    """Handle batch operations workflow."""
    print(f"\n{Fore.CYAN}=== Batch Operations Workflow ==={Style.RESET_ALL}")
    print("This workflow helps you process large directories efficiently.")
    
    # Get input path
    while True:
        path_input = input(f"{Fore.GREEN}Enter path to images directory: {Style.RESET_ALL}").strip()
        if not path_input:
            print(f"{Fore.RED}Path cannot be empty.{Style.RESET_ALL}")
            continue
            
        path = Path(path_input)
        if not path.exists():
            print(f"{Fore.RED}Path does not exist: {path}{Style.RESET_ALL}")
            continue
        if not path.is_dir():
            print(f"{Fore.RED}Path must be a directory: {path}{Style.RESET_ALL}")
            continue
        break
    
    # Count images
    images = list(iter_images(path))
    total = len(images)
    
    if total == 0:
        print(f"{Fore.YELLOW}No images found in {path}{Style.RESET_ALL}")
        return
    
    print(f"{Fore.CYAN}Found {total} images in {path}{Style.RESET_ALL}")
    
    # Get batch settings
    batch_size = get_config_value(config, 'batch_size', 100)
    max_workers = get_config_value(config, 'max_workers', 4)
    
    print(f"\n{Fore.CYAN}Current batch settings:{Style.RESET_ALL}")
    print(f"  Batch size: {batch_size}")
    print(f"  Max workers: {max_workers}")
    
    # Ask if user wants to change settings
    if get_yes_no("Change batch settings? (y/n): ", default=False):
        try:
            new_batch_size = int(input(f"{Fore.GREEN}Enter batch size (current: {batch_size}): {Style.RESET_ALL}"))
            if new_batch_size > 0:
                batch_size = new_batch_size
        except ValueError:
            print(f"{Fore.RED}Invalid number, keeping current value{Style.RESET_ALL}")
        
        try:
            new_max_workers = int(input(f"{Fore.GREEN}Enter max workers (current: {max_workers}): {Style.RESET_ALL}"))
            if new_max_workers > 0:
                max_workers = new_max_workers
        except ValueError:
            print(f"{Fore.RED}Invalid number, keeping current value{Style.RESET_ALL}")
    
    # Choose operation
    print(f"\n{Fore.CYAN}Choose operation:{Style.RESET_ALL}")
    print("1. Clean images (strip metadata)")
    print("2. Poison images (add misleading metadata)")
    print("3. Back to main menu")
    
    while True:
        choice = input(f"{Fore.GREEN}Choose operation (1-3): {Style.RESET_ALL}").strip()
        if choice in ["1", "2", "3"]:
            break
        print(f"{Fore.RED}Please enter 1-3.{Style.RESET_ALL}")
    
    if choice == "3":
        return
    
    # Get output folder for clean
    if choice == "1":
        copy_folder = input(f"{Fore.GREEN}Output folder (default: safe_upload): {Style.RESET_ALL}").strip()
        if not copy_folder:
            copy_folder = "safe_upload"
        
        try:
            out_dir = ensure_dir(path / copy_folder)
            
            def process_single_image(img_path: Path) -> tuple[bool, str]:
                try:
                    clean_copy(img_path, out_dir)
                    return True, ""
                except Exception as e:
                    return False, str(e)
            
            print(f"{Fore.CYAN}Starting batch clean operation...{Style.RESET_ALL}")
            successful, total_processed, errors = process_batch(
                images,
                process_single_image,
                batch_size=batch_size,
                max_workers=max_workers,
                progress_bar=True,
                desc="Cleaning images"
            )
            
            for error in errors:
                print(f"{Fore.RED}✗{Style.RESET_ALL} {error}")
            
            print(f"{Fore.GREEN}Cleaned {successful}/{total_processed} images → {out_dir}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error during batch clean operation: {e}{Style.RESET_ALL}")
    
    elif choice == "2":
        print(f"{Fore.YELLOW}Poison workflow would be implemented here.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}For now, use the main poison workflow or command line.{Style.RESET_ALL}")


def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Get yes/no input from user with default."""
    while True:
        response = input(prompt).strip().lower()
        if not response:
            return default
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print(f"{Fore.RED}Please enter 'y' or 'n'.{Style.RESET_ALL}")
