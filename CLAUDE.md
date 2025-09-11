# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Metadata Multitool is a local-first privacy tool for photographers/creators to clean, manage, and optionally poison image metadata. The tool offers three core operations:
- **Clean**: Strip metadata and copy images to `safe_upload/`
- **Poison**: Add misleading metadata as anti-scraping defense (opt-in only)
- **Revert**: Undo metadata operations using operation logs

## Development Commands

### Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -e .[dev,gui]
```

### Testing
```bash
pytest -q                           # Run tests quietly
pytest --cov=src/metadata_multitool --cov-report=term-missing  # With coverage
pytest tests/                       # Run all tests
pytest tests/test_specific.py       # Run specific test file
```

### Code Quality
```bash
black .                            # Format code
isort .                            # Sort imports
flake8 .                           # Lint code
mypy src/                          # Type checking
```

### Development Tools
```bash
mm --help                          # CLI help
mm gui                             # Launch modern PyQt6 GUI
python -m metadata_multitool.gui_qt.main   # Alternative direct launch
mm clean ./samples                 # Test clean operation
mm poison ./samples --preset label_flip --sidecar  # Test poison
mm revert ./samples                # Test revert
```

## Architecture

The project follows a modular CLI-first design with an optional GUI.

### Core Modules (`src/metadata_multitool/`)
- `cli.py` - Main CLI entry point and argument parsing
- `core.py` - Core utilities, file discovery, logging infrastructure  
- `clean.py` - Safe copy operations with metadata stripping
- `poison.py` - Label poisoning with multiple output formats
- `revert.py` - Undo operations using `.mm_poisonlog.json`
- `exif.py` - ExifTool wrapper with Pillow fallback
- `batch.py` - Parallel processing for large file sets
- `config.py` - YAML configuration management

### GUI Architecture (PyQt6)
- `src/metadata_multitool/gui_qt/` is the only supported GUI implementation
- Production-ready PyQt6 interface with MVC, service layer, and theming

### Key Data Flows
1. **File Discovery**: `iter_images()` in `core.py` finds supported formats
2. **Operation Logging**: `.mm_poisonlog.json` tracks changes for revert
3. **Metadata Backend**: ExifTool preferred, Pillow fallback for basic EXIF
4. **Configuration**: `.mm_config.yaml` for settings persistence

## Important Implementation Notes

### CLI Argument Model (updated)
- Subcommand destination is `args.command` (not `args.cmd`)
- Positional inputs use `args.paths` (list) instead of `args.path`
- `clean` and `poison` accept `--backup` and `--no-backup`

### GUI Integration (PyQt6 only)
- `mm gui` launches the PyQt6 GUI; legacy Tkinter GUI has been removed
- Headless environments: set `QT_QPA_PLATFORM=offscreen`

### Configuration System
- Default config in `config.py`, user overrides in `.mm_config.yaml`
- CLI args override config file settings
- GUI settings auto-persist
- Batch processing config (batch_size, max_workers)

### Testing Approach
- Tests in `tests/` (pytest + coverage)
- GUI tests use `pytest-qt`; tests skip gracefully if plugin or PyQt6 is missing
- External dependencies (ExifTool) are mocked in tests

### Error Handling
- Custom exceptions: `MetadataMultitoolError`, `InvalidPathError`, `LogError`
- User-friendly CLI messages with colorama formatting

## External Dependencies
- **ExifTool** (optional), **Pillow**, **colorama**, **tqdm**, **PyYAML**
- **PyQt6** (GUI), **pytest-qt** (GUI tests, optional locally; installed in CI)

## CI Notes
- GitHub Actions installs `-e .[dev,gui]`
- Set `QT_QPA_PLATFORM=offscreen` for headless PyQt6
- OS matrix covers Ubuntu and Windows

## PyQt6 GUI Usage
```bash
# Install PyQt6 dependencies
pip install -e .[gui]

# Run PyQt6 GUI (Production Ready)
mm gui
# or
python -m metadata_multitool.gui_qt.main
```