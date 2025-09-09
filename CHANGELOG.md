# Changelog

## 0.4.0 (2024-09-09)

### 🎯 Major Features
- **Professional PyQt6 GUI**: Modern desktop interface with native OS integration
- **Enhanced Batch Processing**: Parallel processing with memory monitoring and ETA calculation
- **Dry-Run Mode**: Preview operations for all commands (`--dry-run`)
- **Advanced Configuration**: YAML config files (`.mm_config.yaml`) with GUI settings

### ⚡ Performance Improvements
- Memory-efficient handling of large file sets (1000+ images)
- Intelligent batch sizing based on file types and system resources
- Real-time progress tracking with ETA and memory usage display
- Configurable memory limits and performance monitoring

### 🔧 Configuration & Usability
- YAML configuration system with auto-discovery
- GUI settings persistence (theme, window size, behavior)
- Performance tuning options (batch size, worker count, memory limits)
- Enhanced error handling with contextual suggestions

### 🛠️ Technical Improvements
- Comprehensive error types with troubleshooting guidance
- Memory usage monitoring and limit checking
- Improved time estimation based on file characteristics
- Enhanced progress bars with detailed metrics

### 📦 Dependencies
- Added PyQt6 for modern GUI framework
- Enhanced batch processing utilities
- Improved configuration management

## 0.3.0
- Legacy Tkinter GUI implementation
- Basic CLI functionality
- Core metadata operations

## 0.2.0
- CSV-driven label map (`--csv`)
- Filename poisoning (`--rename-pattern`), revert support
- HTML snippet export (`--html`)
- Expanded docs & ethics note

## 0.1.0
- CLI with clean/poison/revert
- EXIF/IPTC/XMP writing (if exiftool present)
- Sidecars `.txt`/`.json`
- Per-dir change log for undo
- Initial tests & CI