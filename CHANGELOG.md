# Changelog

## 0.5.0 (2024-09-10)

### 🎯 Major Features
- **Selective Metadata Cleaning**: Granular control over which metadata fields to preserve or remove
- **Metadata Profiles**: 6 predefined profiles (Social Media Safe, Photography Portfolio, Location Privacy, etc.)
- **Privacy Auditing**: Comprehensive risk assessment with 4-tier privacy risk levels
- **Advanced Testing Suite**: Performance benchmarking, memory profiling, and comprehensive integration tests
- **Standalone Executables**: Cross-platform PyInstaller builds with automated GitHub Actions workflow

### 🔒 Enhanced Security & Privacy
- **Privacy Risk Assessment**: Automatic detection of GPS coordinates, device info, personal data
- **Risk Categorization**: Critical/High/Medium/Low risk levels with actionable remediation
- **HTML & JSON Reports**: Detailed privacy audit reports with remediation suggestions
- **Batch Privacy Scanning**: Directory-wide privacy analysis with comprehensive reporting

### 🛠️ Advanced Metadata Operations
- **Metadata Profile System**: Predefined profiles for different use cases and privacy needs
- **Selective Field Preservation**: `--preserve-fields` and `--profile` CLI options
- **Preview Functionality**: See what metadata would be preserved/removed before cleaning
- **ExifTool Integration**: Advanced selective metadata removal with verification

### 📚 Comprehensive Documentation
- **Complete User Guide**: Getting started, workflows, troubleshooting guides
- **Platform-Specific Guides**: Windows, macOS, Linux installation with package managers
- **8+ Workflow Examples**: Social media, professional portfolio, event photography workflows
- **Troubleshooting Guide**: Common issues and platform-specific solutions

### ⚡ Performance & Quality
- **Memory Profiling**: Leak detection and usage analysis for large file sets
- **Performance Benchmarking**: Scaling analysis and regression detection
- **Enhanced GUI Testing**: Comprehensive PyQt6 test coverage with user interaction simulation
- **Integration Testing**: End-to-end workflow testing with sample image generation

### 📦 Distribution Ready
- **Cross-Platform Builds**: Windows, macOS, Linux standalone executables
- **GitHub Actions**: Automated build workflow with testing and release creation
- **Local Build Scripts**: Development build tools with verification and packaging
- **Professional Packaging**: Ready for distribution without Python dependency

### 🔧 CLI Enhancements
- **New Commands**: `mm audit` for privacy analysis, `mm clean --profile` for selective cleaning
- **Enhanced Options**: `--list-profiles`, `--preserve-fields`, `--report-format` (HTML/JSON)
- **Better Integration**: Seamless integration between CLI and GUI functionality
- **Improved Error Handling**: Contextual error messages with troubleshooting suggestions

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
### Removed
- Legacy Tkinter GUI removed; `mm gui` now launches modern PyQt6 interface
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