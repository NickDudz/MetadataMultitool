# macOS Installation Guide

Complete installation instructions for Metadata Multitool on macOS systems.

## Prerequisites

- **macOS 11 Big Sur** or newer (Intel and Apple Silicon supported)
- **Python 3.11+** (via Homebrew, python.org, or Xcode)
- **Xcode Command Line Tools**
- **Homebrew** (recommended for dependencies)

## Method 1: Quick Installation (Recommended)

### Step 1: Install Prerequisites
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+
brew install python@3.11

# Verify Python installation
python3 --version  # Should show 3.11 or newer
```

### Step 2: Set Up Environment
```bash
# Create project directory
mkdir ~/MetadataMultitool
cd ~/MetadataMultitool

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Verify activation (should show (.venv) in prompt)
which python  # Should show path in .venv
```

### Step 3: Install Metadata Multitool
```bash
# Install from source (development version)
git clone https://github.com/your-repo/metadata-multitool.git
cd metadata-multitool
pip install -e .[dev,gui]

# Or install from PyPI (when available)
# pip install metadata-multitool[gui]
```

### Step 4: Install ExifTool (Recommended)
```bash
# Install via Homebrew (recommended)
brew install exiftool

# Verify installation
exiftool -ver
which exiftool
```

### Step 5: Verify Installation
```bash
# Test CLI
mm --help

# Test GUI
mm gui

# Test with sample image
# Download a test image or use existing photo
mm clean ~/Pictures/sample.jpg
ls safe_upload/
```

## Method 2: Alternative Python Installations

### Using Python.org Installer
```bash
# Download from python.org/downloads
# Install Python 3.11+ with default settings

# Create virtual environment
python3 -m venv ~/.venv/metadata-multitool
source ~/.venv/metadata-multitool/bin/activate

# Continue with installation steps above
```

### Using pyenv (Version Management)
```bash
# Install pyenv
brew install pyenv

# Add to shell profile (~/.zshrc or ~/.bash_profile)
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Install and use Python 3.11
pyenv install 3.11.7
pyenv global 3.11.7

# Verify
python --version
```

### Using Anaconda/Miniconda
```bash
# Install Miniconda
brew install --cask miniconda

# Create environment
conda create -n metadata-multitool python=3.11
conda activate metadata-multitool

# Install dependencies
pip install -e .[dev,gui]
```

## Method 3: Development Installation

For developers or advanced users.

### Prerequisites
```bash
# Install development tools
brew install git
brew install --cask visual-studio-code  # Optional IDE

# Install build dependencies
xcode-select --install
```

### Development Setup
```bash
# Clone repository
git clone https://github.com/your-repo/metadata-multitool.git
cd metadata-multitool

# Create development environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e .[dev,gui]

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest
```

## Method 4: App Bundle (Coming Soon)

Native macOS application bundle with all dependencies included.

```bash
# Download .dmg from releases page
# https://github.com/your-repo/metadata-multitool/releases

# Drag to Applications folder
# Run from Applications or Spotlight
```

## macOS-Specific Configuration

### Default Configuration Location
```
~/.mm_config.yaml
```

### macOS-Optimized Configuration
```yaml
# .mm_config.yaml
paths:
  output_directory: "~/Pictures/safe_upload"
  
batch_processing:
  max_workers: 8  # Adjust for M1/M2 (more cores) vs Intel
  
gui:
  theme: "auto"  # Follows macOS appearance preference
  use_native_dialogs: true
  
tools:
  exiftool_path: "/opt/homebrew/bin/exiftool"  # M1/M2 Macs
  # exiftool_path: "/usr/local/bin/exiftool"   # Intel Macs
```

## Architecture-Specific Notes

### Apple Silicon (M1/M2/M3) Macs
```bash
# Homebrew installs to /opt/homebrew on Apple Silicon
# Update PATH in ~/.zshrc
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Install Python and dependencies
arch -arm64 brew install python@3.11
arch -arm64 brew install exiftool

# For maximum performance
export ARCHFLAGS="-arch arm64"
pip install -e .[dev,gui]
```

### Intel Macs
```bash
# Homebrew installs to /usr/local on Intel
# PATH should be automatic

# Install dependencies
brew install python@3.11 exiftool

# Standard installation
pip install -e .[dev,gui]
```

### Universal Builds (Both Architectures)
```bash
# For developers creating universal binaries
export ARCHFLAGS="-arch x86_64 -arch arm64"
pip install --force-reinstall -e .[dev,gui]
```

## macOS-Specific Troubleshooting

### Common Issues

**"Command not found: python3"**
```bash
# Check if Python is installed
ls /usr/bin/python*
brew list | grep python

# Install Python via Homebrew
brew install python@3.11

# Add to PATH (Apple Silicon)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**"xcrun: error: invalid active developer path"**
```bash
# Install/reinstall Xcode Command Line Tools
sudo xcode-select --reset
xcode-select --install
```

**Permission Denied Errors**
```bash
# Fix Homebrew permissions
sudo chown -R $(whoami) $(brew --prefix)/*

# Use user installation
pip install --user -e .[dev,gui]
```

**"Library not loaded" for PyQt6**
```bash
# Install Qt dependencies
brew install qt6

# Reinstall PyQt6
pip uninstall PyQt6
pip install PyQt6

# Alternative: use conda
conda install pyqt
```

**"ExifTool not found" with Homebrew**
```bash
# Check Homebrew installation
brew list exiftool
brew --prefix exiftool

# Manually link if needed
brew link exiftool

# Verify PATH
echo $PATH | grep $(brew --prefix)/bin
```

**Gatekeeper Warnings (App Bundle)**
```bash
# Allow app through Gatekeeper
xattr -dr com.apple.quarantine /Applications/MetadataMultitool.app
```

### Performance Optimization

**For M1/M2/M3 Macs:**
```yaml
# .mm_config.yaml
batch_processing:
  batch_size: 100       # Higher batch sizes work well
  max_workers: 12       # More cores available
  memory_limit_mb: 4096 # Usually have more RAM

performance:
  use_metal_acceleration: true  # GPU acceleration when available
```

**For Intel Macs:**
```yaml
# .mm_config.yaml
batch_processing:
  batch_size: 50        # Conservative batch size
  max_workers: 8        # Typical Intel core count
  memory_limit_mb: 2048
```

## Integration with macOS

### Finder Integration
```bash
# Create Automator Quick Action
# 1. Open Automator
# 2. Create "Quick Action"
# 3. Add "Run Shell Script"
# 4. Script: /path/to/.venv/bin/mm clean "$@"
# 5. Save as "Clean Metadata"
```

### Spotlight Integration
```bash
# Add to PATH for Spotlight access
echo 'export PATH="$HOME/MetadataMultitool/.venv/bin:$PATH"' >> ~/.zshrc

# Now you can run 'mm' from Spotlight
```

### Launch Agent (Automatic Processing)
Create `~/Library/LaunchAgents/com.metadatamultitool.cleanup.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.metadatamultitool.cleanup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/username/MetadataMultitool/.venv/bin/mm</string>
        <string>clean</string>
        <string>/Users/username/Pictures/ToProcess</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
</dict>
</plist>
```

Load with:
```bash
launchctl load ~/Library/LaunchAgents/com.metadatamultitool.cleanup.plist
```

### Photos.app Integration
```bash
# Export from Photos.app, then clean
# Create shell script for workflow:
#!/bin/bash
EXPORT_DIR="$HOME/Pictures/Photos Export"
CLEAN_DIR="$HOME/Pictures/Clean Export"

# Export photos from Photos.app to EXPORT_DIR
# Then run:
mm clean "$EXPORT_DIR" --output "$CLEAN_DIR"
open "$CLEAN_DIR"
```

## macOS Security Considerations

### Privacy & Security Settings
```bash
# Grant Terminal/iTerm2 full disk access
# System Preferences → Security & Privacy → Privacy → Full Disk Access
# Add Terminal or iTerm2

# For GUI app, may need camera/photos access
# System Preferences → Security & Privacy → Privacy → Photos
```

### Sandboxing Considerations
```bash
# If using App Store distribution (future)
# Some file system access may be limited
# Use security-scoped bookmarks for persistent access
```

### Code Signing (Development)
```bash
# For distribution, sign the application
codesign --force --deep --sign "Developer ID Application: Your Name" MetadataMultitool.app

# Verify signature
codesign --verify --deep --strict MetadataMultitool.app
```

## Performance Tips for macOS

### SSD Optimization
```bash
# Use APFS snapshots for backup (macOS 10.13+)
tmutil localsnapshot

# Optimize for SSD storage
sudo trimforce enable  # If needed for older SSDs
```

### Memory Management
```bash
# Monitor memory usage
activity monitor
# Or command line:
vm_stat

# Optimize virtual memory settings in config
```

### Network Drives
```bash
# For processing files on network drives
# Mount with caching options
mount -t smbfs -o soft,intr,rsize=8192,wsize=8192 //server/share /mnt/network
```

## Next Steps

1. **Test Installation**: Clean a sample photo from ~/Pictures
2. **Configure Preferences**: Edit ~/.mm_config.yaml
3. **Set Up Integration**: Add Finder Quick Actions or Automator workflows
4. **Read Documentation**: Review user guide for detailed usage

---

For additional help, see the [Troubleshooting Guide](../user_guide/troubleshooting.md) or macOS-specific solutions above.