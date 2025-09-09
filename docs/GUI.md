# Metadata Multitool GUI

Graphical user interfaces for the Metadata Multitool, featuring both modern PyQt6 and legacy Tkinter implementations.

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

### 1. PyQt6 Desktop GUI (Recommended)

**Status**: Production-ready (v0.4.0+)

**Features**:
- Modern, professional desktop interface
- Native OS integration and theming
- Light/dark theme support
- Advanced file management with drag & drop
- Real-time progress tracking with ETA
- Comprehensive settings dialog
- Keyboard shortcuts and accessibility
- Cross-platform compatibility (Windows, macOS, Linux)

**Launch**:
```bash
# Module execution (recommended)
python -m metadata_multitool.gui_qt.main

# Or if installed
mm-gui
```

**Architecture**:
- MVC pattern with PyQt6
- Service layer abstraction for CLI integration
- QThread for background operations
- QSS styling for modern appearance

### 2. Legacy Tkinter GUI

**Status**: Functional but deprecated

**Features**:
- Basic file selection and processing
- Simple progress tracking
- Configuration management
- Cross-platform compatibility

**Launch**:
```bash
mm gui
```

## Configuration

### GUI Settings

The GUI automatically saves your preferences in `.mm_config.yaml`:

```yaml
gui_settings:
  theme: "dark"  # "light" or "dark"
  window_size: [1200, 800]
  window_position: [100, 100]
  show_progress_details: true
  auto_save_settings: true

operation_defaults:
  clean:
    output_directory: "safe_upload"
    preserve_originals: true
  poison:
    preset: "label_flip"
    output_formats: ["exif", "iptc", "sidecar"]
  revert:
    confirm_before_revert: true

general:
  batch_size: 50
  max_workers: 2
  progress_bar: true
  verbose: false
```

### Theme Support

**Light Theme**: Clean, professional appearance with light colors
**Dark Theme**: Modern dark interface with high contrast

Themes automatically adapt to system preferences and can be changed in Settings.

## Development

### PyQt6 GUI Structure

```
src/metadata_multitool/gui_qt/
├── main.py                 # Entry point
├── main_window.py          # Main window controller
├── models/                 # Data models
│   ├── config_model.py
│   ├── file_model.py
│   └── operation_model.py
├── views/                  # UI components
│   ├── common/
│   │   └── theme_manager.py
│   ├── operation_panels/
│   │   ├── clean_panel.py
│   │   ├── poison_panel.py
│   │   └── revert_panel.py
│   ├── file_panel.py
│   ├── main_view.py
│   ├── progress_widget.py
│   └── settings_dialog.py
├── controllers/            # Business logic
│   └── main_controller.py
├── services/              # Backend integration
│   ├── cli_service.py
│   └── config_service.py
└── utils/                 # Utilities
    └── icons.py
```

### Testing

```bash
# Run GUI tests
pytest tests/test_gui.py

# Test PyQt6 components
pytest tests/ -k "gui_qt"
```

## Troubleshooting

### Common Issues

1. **PyQt6 Import Error**: Ensure PyQt6 is installed
   ```bash
   pip install PyQt6
   ```

2. **Theme Not Loading**: Check `.mm_config.yaml` permissions

3. **File Operations Failing**: Verify file permissions and paths

4. **GUI Not Responding**: Check for background operations in progress

### Debug Mode

Enable debug logging in Settings → Advanced → Debug Logging for detailed error information.

## Future Development

See [GUI Development Roadmap](development/GUI_DEVELOPMENT_ROADMAP.md) for planned features and improvements.
