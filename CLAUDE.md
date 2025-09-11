# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Metadata Multitool is a local-first privacy tool for photographers/creators to clean, manage, and optionally poison image metadata. The tool offers four core operations:
- **Clean**: Strip metadata and copy images to `safe_upload/` with selective cleaning profiles
- **Poison**: Add misleading metadata as anti-scraping defense (opt-in only)
- **Revert**: Undo metadata operations using operation logs
- **Audit**: Analyze images for privacy risks and generate detailed reports

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
python src/metadata_multitool/gui_qt/main.py  # Direct GUI launch
mm clean ./samples                 # Test clean operation
mm clean ./samples --profile social_media_safe  # Test selective cleaning
mm poison ./samples --preset label_flip --sidecar  # Test poison
mm revert ./samples                # Test revert
mm audit ./samples                 # Test privacy auditing
mm audit ./samples --report-format html  # Generate HTML audit report
```

## Architecture

The project follows a modular CLI-first design with an optional GUI.

### Core Modules (`src/metadata_multitool/`)
- `cli.py` - Main CLI entry point and argument parsing
- `core.py` - Core utilities, file discovery, logging infrastructure  
- `clean.py` - Safe copy operations with selective metadata cleaning
- `poison.py` - Label poisoning with multiple output formats
- `revert.py` - Undo operations using `.mm_poisonlog.json`
- `audit.py` - Privacy risk assessment and reporting
- `metadata_profiles.py` - Metadata profile system for selective cleaning
- `exif.py` - ExifTool wrapper with Pillow fallback
- `batch.py` - Parallel processing for large file sets
- `config.py` - YAML configuration management
- `__version__.py` - Centralized version management

### GUI Architecture (PyQt6)
- `src/metadata_multitool/gui_qt/` is the only supported GUI implementation
- Production-ready PyQt6 interface with MVC, service layer, and theming
- Supports all v0.5.0 features including selective cleaning and privacy auditing
- Professional interface with light/dark themes and drag & drop file management

### Key Data Flows
1. **File Discovery**: `iter_images()` in `core.py` finds supported formats
2. **Operation Logging**: `.mm_poisonlog.json` tracks changes for revert
3. **Metadata Backend**: ExifTool preferred, Pillow fallback for basic EXIF
4. **Configuration**: `.mm_config.yaml` for settings persistence

## Important Implementation Notes

### CLI Argument Model (v0.5.0)
- Subcommand destination is `args.command` (not `args.cmd`)
- Positional inputs use `args.paths` (list) instead of `args.path`
- `clean` command supports `--profile` and `--preserve-fields` for selective cleaning
- `audit` command supports `--report-format` (html/json) and `--output-file`
- All commands accept `--backup`/`--no-backup` and `--dry-run` options

### GUI Integration (PyQt6 only)
- `mm gui` launches the PyQt6 GUI; legacy Tkinter GUI has been removed
- Headless environments: set `QT_QPA_PLATFORM=offscreen`

### Configuration System
- Default config in `config.py`, user overrides in `.mm_config.yaml`
- CLI args override config file settings
- GUI settings auto-persist
- Batch processing config (batch_size, max_workers)

### Testing Approach
- Tests in `tests/` with comprehensive coverage (pytest + coverage)
- Integration tests in `tests/integration/` for end-to-end workflows
- Performance tests in `tests/performance/` with memory profiling
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

## v0.5.0 Major Features

### Selective Metadata Cleaning
- **6 Predefined Profiles**: Social Media Safe, Photography Portfolio, Location Privacy, Basic Camera, Minimal Creative, Timestamp Only
- **Custom Field Preservation**: `--preserve-fields` for specific metadata fields
- **Preview Mode**: See what metadata would be preserved/removed before cleaning

### Privacy Auditing
- **4-Tier Risk Assessment**: Critical, High, Medium, Low privacy risk levels
- **Comprehensive Scanning**: GPS coordinates, device info, personal data detection
- **Multiple Report Formats**: HTML and JSON reports with remediation suggestions
- **Batch Analysis**: Directory-wide privacy assessment

### Enhanced Documentation
- **Complete User Guides**: Getting started, workflows, troubleshooting
- **Platform-Specific Guides**: Windows, macOS, Linux installation
- **8+ Workflow Examples**: Social media, professional portfolio, event photography

### Distribution Ready
- **Standalone Executables**: Cross-platform PyInstaller builds
- **GitHub Actions**: Automated build workflow for Windows, macOS, Linux
- **Professional Packaging**: No Python dependency required for end users

### Version Management
- **Centralized Versioning**: Single source of truth in `__version__.py`
- **Dynamic Version Loading**: GUI and CLI automatically use current version
- **Build Integration**: PyInstaller and package builds use centralized version

## PyQt6 GUI Usage
```bash
# Install PyQt6 dependencies
pip install -e .[gui]

# Run PyQt6 GUI (v0.5.0 Production Ready)
mm gui
# or
python src/metadata_multitool/gui_qt/main.py

# Features include:
# - Selective metadata cleaning with profiles
# - Privacy auditing with risk assessment
# - Light/dark themes with professional styling
# - Drag & drop file management
# - Real-time progress tracking
```