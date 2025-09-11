# Metadata Multitool GUI

Graphical user interface for the Metadata Multitool, implemented with modern PyQt6.

## Features

### 🎯 Core Functionality
- **Clean Mode**: Strip metadata from images for safe upload
- **Poison Mode**: Add misleading metadata for anti-scraping
- **Revert Mode**: Undo previous operations
- **Settings Panel**: Configure all tool settings through GUI

### 🖥️ User Interface
- **Mode Selection**: Easy switching between Clean, Poison, and Revert modes
- **File Selection**: Browse files or folders, drag & drop support
- **File List**: Display selected files with metadata information
- **Progress Tracking**: Real-time progress bars and status updates
- **Settings Management**: Comprehensive configuration options

### 🔧 Advanced Features
- **File Filtering**: Filter by size, date, format, and metadata presence
- **Batch Processing**: Process large numbers of files efficiently
- **Background Processing**: Non-blocking operations with threading
- **Configuration Persistence**: Save and load settings automatically
- **Error Handling**: User-friendly error messages and recovery

## GUI Interfaces

The Metadata Multitool includes two graphical interfaces:

### 🎯 Modern PyQt6 GUI (Recommended)
**Professional Interface** with native appearance and modern features.

**Installation:**
```bash
pip install -e .[gui]  # Install with PyQt6 dependencies
```

**Launch:**
```bash
mm-gui  # Launch modern PyQt6 interface
```

**Features:**
- ✅ Native OS appearance with professional styling
- ✅ Light/Dark themes with comprehensive theming
- ✅ Drag & drop file management
- ✅ Fixed layout with non-movable panels
- ✅ Real-time progress tracking with cancel/pause
- ✅ Background operations with full CLI integration

<!-- Legacy Tkinter GUI has been removed as of v0.4.x. -->

## Usage

### GUI Modes

#### Clean Mode
1. Select files or folders using "Browse Files" or "Browse Folder"
2. Choose output folder (default: "safe_upload")
3. Configure file filters (optional)
4. Set processing options
5. Click "Process" or "Dry Run"

#### Poison Mode
1. Select files or folders
2. Choose poison preset:
   - **Label Flip**: Replace labels with misleading ones
   - **Clip Confuse**: Add confusing random tokens
   - **Style Bloat**: Add style-related keywords
3. Configure output formats (XMP, IPTC, EXIF, sidecars)
4. Set rename pattern (optional)
5. Load CSV mapping (optional)
6. Click "Process" or "Dry Run"

#### Revert Mode
1. Select directory to revert
2. Review files to be reverted
3. Click "Revert" or "Dry Run"

### Settings

Access settings through the "Settings" button in the main window:

#### General Settings
- Log level (DEBUG, INFO, WARNING, ERROR)
- Backup before operations
- Verbose/Quiet output

#### Processing Settings
- Batch size for large operations
- Maximum worker processes
- Progress bar display
- Supported file formats

#### GUI Settings
- Theme (Light/Dark)
- Window size and position
- Thumbnail display options
- Auto-backup settings

## Architecture

Both GUIs follow a Model-View-Controller (MVC) pattern:

### PyQt6 GUI Architecture (`src/metadata_multitool/gui_qt/`)
Modern implementation with Qt6 features and service layer abstraction.

#### Core Components
- **main.py**: Application entry point with MetadataMultitoolApp class
- **main_window.py**: Main application window with menu bar and fixed dock widgets
- **services/**: Service layer for CLI integration (CLIService, ConfigService)
- **models/**: Qt-compatible data models with signals
- **views/**: UI components following Qt patterns
- **utils/**: Theme management and common utilities

#### Key Features
- QThread for background operations
- Qt signal/slot communication system
- JSON-serializable data models for future web compatibility
- Fixed dock widget layout (non-movable)
- Professional theming with QSS stylesheets

<!-- Legacy Tkinter GUI Architecture removed -->

### Models
- **FileModel**: Manages selected files and metadata
- **ConfigModel**: Handles configuration settings
- **OperationModel**: Tracks processing state and progress

### Views
- **MainWindow**: Main application window
- **CleanView**: Clean mode interface
- **PoisonView**: Poison mode interface
- **RevertView**: Revert mode interface
- **SettingsView**: Configuration panel
- **FileListView**: File selection and display
- **ProgressView**: Progress tracking

### Controllers
- **CleanController**: Clean mode logic
- **PoisonController**: Poison mode logic
- **RevertController**: Revert mode logic
- **SettingsController**: Settings management

### Utils
- **GUI Utils**: Common GUI functions
- **Threading Utils**: Background processing
- **Validation Utils**: Input validation

## File Structure

### PyQt6 GUI Structure
```
src/metadata_multitool/gui_qt/
├── __init__.py
├── main.py                     # Application entry point
├── main_window.py              # Main window with dock layout
├── services/
│   ├── __init__.py
│   ├── cli_service.py         # CLI backend integration
│   └── config_service.py      # Configuration management
├── models/
│   ├── __init__.py
│   ├── file_model.py          # Qt table model for files
│   ├── config_model.py        # Configuration state
│   └── operation_model.py     # Operation progress tracking
├── views/
│   ├── __init__.py
│   ├── main_view.py           # Central tabbed interface
│   ├── file_panel.py          # File management panel
│   ├── progress_widget.py     # Progress display
│   ├── clean/
│   │   └── clean_view.py      # Clean operation panel
│   ├── poison/
│   │   └── poison_view.py     # Poison operation panel
│   ├── revert/
│   │   └── revert_view.py     # Revert operation panel
│   └── common/
│       ├── settings_dialog.py # Settings configuration
│       └── theme_manager.py   # Theme management
└── utils/
    ├── __init__.py
    └── validators.py          # Input validation
```

<!-- Legacy Tkinter GUI Structure removed -->

## Configuration

GUI settings are stored in `.mm_config.yaml`:

```yaml
# Core settings
batch_size: 100
max_workers: 4
progress_bar: true
verbose: false
quiet: false
backup_before_operations: true
log_level: "INFO"

# GUI-specific settings
gui_settings:
  theme: "light"
  window_size: [1000, 700]
  window_position: [100, 100]
  show_thumbnails: true
  thumbnail_size: 64
  auto_backup: true
  remember_last_folder: true
```

## Testing

Run GUI tests:
```bash
python -m pytest tests/test_gui.py -v
```

## Development

### Adding New Features

1. **Models**: Add data management logic
2. **Views**: Create UI components
3. **Controllers**: Implement business logic
4. **Utils**: Add helper functions

### Threading

Use `BackgroundProcessor` for long-running operations:
```python
from metadata_multitool.gui.utils.threading_utils import BackgroundProcessor

processor = BackgroundProcessor()
processor.submit(long_running_function, callback=update_ui)
```

### Error Handling

Use GUI utility functions for user feedback:
```python
from metadata_multitool.gui.utils.gui_utils import show_error, show_warning, show_info

show_error("Error Title", "Error message")
show_warning("Warning Title", "Warning message")
show_info("Info Title", "Info message")
```

## Troubleshooting

### Common Issues

1. **GUI won't start**: Ensure PyQt6 is installed
2. **Files not loading**: Verify file permissions and paths
3. **Settings not saving**: Check write permissions for config file
4. **Slow performance**: Reduce batch size or max workers

### Debug Mode

Enable debug logging:
1. Open Settings
2. Set Log Level to "DEBUG"
3. Check console output for detailed information

## Future Enhancements

- [ ] Drag & drop file support
- [ ] Image preview functionality
- [ ] Dark theme implementation
- [ ] Keyboard shortcuts
- [ ] Batch operation queuing
- [ ] Plugin system for custom presets
- [ ] Multi-language support

## Contributing

See the main project CONTRIBUTING.md for guidelines.

## License

Same as the main Metadata Multitool project (MIT License).
