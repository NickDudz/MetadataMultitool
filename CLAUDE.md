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
pip install -e .[dev]
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
mm gui                            # Launch legacy Tkinter GUI
python src/metadata_multitool/gui_qt/main.py  # Launch modern PyQt6 GUI
mm clean ./samples                 # Test clean operation
mm poison ./samples --preset label_flip --sidecar  # Test poison
mm revert ./samples                # Test revert
```

## Architecture

The project follows a modular CLI-first design with an optional GUI:

### Core Modules (`src/metadata_multitool/`)
- `cli.py` - Main CLI entry point and argument parsing
- `core.py` - Core utilities, file discovery, logging infrastructure  
- `clean.py` - Safe copy operations with metadata stripping
- `poison.py` - Label poisoning with multiple output formats
- `revert.py` - Undo operations using `.mm_poisonlog.json`
- `exif.py` - ExifTool wrapper with Pillow fallback
- `batch.py` - Parallel processing for large file sets
- `config.py` - YAML configuration management

### GUI Architecture

#### Current Implementation (`src/metadata_multitool/gui/`)
**Status**: Functional Tkinter-based GUI (legacy)
- `main_window.py` - Main application controller
- `models/` - Data models (FileModel, ConfigModel, OperationModel)
- `views/` - UI components for each mode (Clean, Poison, Revert)
- `utils/` - Threading, validation, and GUI utilities

#### Modern GUI Implementation (`src/metadata_multitool/gui_qt/`)
**Status**: ✅ Completed - Production-ready PyQt6 interface
- **Framework**: PyQt6 with modern Qt features and native styling
- **Architecture**: MVC with signal/slot communication and service layer abstraction
- **Features**: Professional appearance, file management, light/dark themes, fixed layout
- **Components**: Main window, operation panels, progress tracking, settings dialog
- **Integration**: Full CLI backend integration with background operations
- **Future**: Designed for web interface compatibility

### Key Data Flows
1. **File Discovery**: `iter_images()` in `core.py` finds supported formats
2. **Operation Logging**: `.mm_poisonlog.json` tracks changes for revert
3. **Metadata Backend**: ExifTool preferred, Pillow fallback for basic EXIF
4. **Configuration**: `.mm_config.yaml` for settings persistence

## Important Implementation Notes

### Metadata Operations
- **Clean operations** use `clean_copy()` - always create safe copies, never modify originals
- **Poison operations** log all changes in `.mm_poisonlog.json` for revert capability
- **ExifTool integration** handles complex metadata; Pillow provides fallback
- **Batch processing** available for large file sets (configurable workers/batch size)

### File Handling
- Supported formats: `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.webp`, `.bmp`
- Always validate paths with `iter_images()` before processing
- Use `Path` objects consistently throughout codebase
- Relative path handling via `rel_to_root()` for cross-platform logging

### GUI Integration

#### Legacy Tkinter GUI
- GUI shares CLI configuration system (`.mm_config.yaml`)
- Background processing via `BackgroundProcessor` class prevents UI blocking  
- Models handle data, Views handle UI, Controllers coordinate (MVC pattern)
- Thread-safe UI updates use `root.after()` for main thread scheduling

#### Modern PyQt6 GUI (Production Ready)
- **Service Layer**: Abstract CLI integration with future web compatibility
- **Data Models**: Qt-compatible models with JSON serialization support
- **Threading**: QThread for non-blocking background operations
- **UI Components**: Professional file management, operation panels, progress tracking
- **Theming**: Light/dark themes with comprehensive styling and proper contrast
- **Layout**: Fixed dock panels, non-movable interface elements
- **Integration**: Full CLI backend compatibility with real-time progress updates

### Configuration System
- Default config in `config.py`, user overrides in `.mm_config.yaml`
- CLI args override config file settings
- GUI settings auto-persist on window close/mode switch
- Support for batch processing config (batch_size, max_workers)

### Testing Approach
- Test files in `tests/` directory
- Use `pytest` with coverage reporting
- Mock external dependencies (ExifTool, file operations)
- Test both CLI and GUI components separately
- Fixtures for sample images and configurations

### Error Handling
- Custom exceptions: `MetadataMultitoolError`, `InvalidPathError`, `LogError`
- User-friendly CLI messages with colorama formatting
- GUI error dialogs with recovery suggestions
- Graceful degradation when ExifTool unavailable

## Development Guidelines

### Code Style
- Follow existing patterns for CLI argument handling in `cli.py`
- Use type hints consistently (required by mypy config)
- Keep poisoning features opt-in and clearly documented
- Maintain CLI-GUI feature parity where applicable

### Adding New Operations
1. Add core logic to appropriate module (`clean.py`, `poison.py`, etc.)
2. Add CLI command in `cli.py` with proper argument parsing
3. Add GUI view if applicable following MVC pattern
4. Update operation logging for revert capability
5. Add comprehensive tests

### External Dependencies
- **ExifTool**: Optional but recommended for full metadata support
- **Pillow**: Required for basic image handling and fallback EXIF
- **colorama**: CLI output formatting
- **tqdm**: Progress bars
- **PyYAML**: Configuration file handling
- **PyQt6**: Modern GUI framework (for new implementation)
- **tkinter**: Legacy GUI framework (existing implementation)

## GUI Development Status

### ✅ Phase 1: PyQt6 Desktop Application (Completed - v0.4.0)
**Status**: Production-ready modern desktop GUI

**Implemented Features**:
- ✅ Native OS integration with professional appearance
- ✅ File management with add files/folders functionality
- ✅ Light/dark themes with comprehensive styling
- ✅ Operation panels for Clean, Poison, and Revert modes
- ✅ Real-time progress tracking with proper layouts
- ✅ Settings dialog with configuration management
- ✅ Fixed layout with non-movable dock panels
- ✅ Full CLI backend integration

**Architecture Implemented**:
- ✅ Service layer abstraction for future web compatibility
- ✅ Modular MVC components with Qt signal/slot system
- ✅ JSON-serializable data models
- ✅ Background threading with QThread

## v0.4.0 Major Enhancements

### ✅ Performance & Reliability (Phase 2 Complete)
**Status**: Production-ready with advanced performance features

**New Features**:
- ✅ **Enhanced Batch Processing**: Memory monitoring, ETA calculation, optimized parallel processing
- ✅ **Dry-Run Mode**: Preview operations for all commands (clean, poison, revert)
- ✅ **Advanced Configuration**: YAML config files with GUI settings and performance tuning
- ✅ **Memory Management**: Configurable memory limits and usage monitoring
- ✅ **Progress Tracking**: Real-time ETA and performance metrics
- ✅ **Enhanced Error Handling**: Contextual error messages with troubleshooting suggestions

**Performance Improvements**:
- ✅ Parallel processing with configurable worker counts
- ✅ Memory-efficient handling of large file sets (1000+ images)
- ✅ Intelligent batch sizing based on file types and system resources
- ✅ Progress bars with ETA and memory usage display
- ✅ Resume capability for interrupted operations

**User Experience Enhancements**:
- ✅ Comprehensive dry-run preview for all operations
- ✅ Detailed error messages with actionable suggestions
- ✅ Configuration persistence across sessions
- ✅ Professional GUI with modern theming

### Phase 2: Web Interface (Future)
**Timeline**: 5-7 weeks (after PyQt6 completion)
**Goals**: Cross-platform web-based interface

**Technology Stack**:
- **Backend**: FastAPI with WebSocket real-time updates
- **Frontend**: React + TypeScript with modern UI framework
- **Features**: Progressive Web App, mobile responsive
- **Deployment**: Docker containers, cloud-ready

**Compatibility Strategy**:
- Shared business logic through service abstractions
- Common configuration schema
- API-first backend design from PyQt6 implementation
- Progressive enhancement for web features

### Implementation Guidelines

#### PyQt6 Development
1. **Project Structure**: Follow `GUI_PYQT6_IMPLEMENTATION_PROMPT.md`
2. **Service Layer**: Abstract CLI integration for future web use
3. **Data Models**: Design for JSON serialization compatibility
4. **Configuration**: Use schemas that work for both desktop and web
5. **Testing**: Comprehensive test coverage with pytest-qt

#### Future Web Compatibility
- Design service interfaces that can be exposed as REST APIs
- Use data structures that serialize cleanly to JSON
- Implement business logic in framework-agnostic services
- Maintain configuration compatibility between desktop and web

#### PyQt6 GUI Usage
```bash
# Install PyQt6 dependencies
pip install PyQt6

# Run PyQt6 GUI (Production Ready)
python src/metadata_multitool/gui_qt/main.py

# Run legacy Tkinter GUI
mm gui

# Test GUI functionality
python test_light_mode_fixes.py  # Test light mode fixes
python test_black_sections_fix.py  # Test UI improvements

# Package for distribution (future)
pyinstaller --onefile src/metadata_multitool/gui_qt/main.py
```

## PyQt6 GUI Implementation Details

### Project Structure
```
src/metadata_multitool/gui_qt/
├── main.py                     # Application entry point
├── main_window.py              # Main application window
├── models/                     # Qt-compatible data models
│   ├── file_model.py          # File management with Qt models
│   ├── operation_model.py     # Operation state and progress
│   ├── config_model.py        # Configuration management
├── views/                      # UI components and widgets
│   ├── main_view.py           # Main interface with tabs
│   ├── file_panel.py          # File selection and management
│   ├── operation_panels/      # Mode-specific operation interfaces
│   │   ├── clean_panel.py     # Clean mode interface
│   │   ├── poison_panel.py    # Poison mode interface
│   │   └── revert_panel.py    # Revert mode interface
│   ├── settings_dialog.py     # Settings configuration
│   ├── progress_widget.py     # Progress tracking and display
│   └── common/                # Reusable UI components
│       └── theme_manager.py   # Theme and styling management
├── controllers/                # Business logic controllers
│   └── main_controller.py     # Main application controller
├── services/                   # Backend integration services
│   ├── cli_service.py         # CLI backend integration
│   └── config_service.py      # Configuration persistence
└── utils/                      # Utility functions and helpers
    └── icons.py               # Icon and resource management
```

### Key Features Implemented
- **File Management**: Drag & drop interface with file/folder selection
- **Operation Modes**: Clean, Poison, and Revert with dedicated panels
- **Real-time Progress**: Background operations with progress tracking
- **Theme Support**: Light/dark themes with proper contrast
- **Settings Management**: Comprehensive configuration interface
- **Fixed Layout**: Professional interface with non-movable panels
- **CLI Integration**: Full backend compatibility with existing CLI tools