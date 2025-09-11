# Getting Started with Metadata Multitool

This guide will help you install and run Metadata Multitool on your system.

## System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 2GB RAM minimum (4GB+ recommended for large batches)
- **Storage**: 50MB for installation + space for processed images

## Installation Methods

### Method 1: Python Package (Recommended)

#### Step 1: Set Up Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

#### Step 2: Install Metadata Multitool
```bash
# Clone repository (or download release)
git clone https://github.com/your-repo/metadata-multitool.git
cd metadata-multitool

# Install with all features
pip install -e .[dev,gui]
```

#### Step 3: Install ExifTool (Optional but Recommended)
ExifTool provides comprehensive metadata support. Metadata Multitool will use Pillow as a fallback if ExifTool is not available.

**Windows (Chocolatey):**
```bash
choco install exiftool
```

**macOS (Homebrew):**
```bash
brew install exiftool
```

**Ubuntu/Debian:**
```bash
sudo apt-get install -y libimage-exiftool-perl
```

### Method 2: Standalone Executable (Coming Soon)
Pre-built executables will be available for Windows, macOS, and Linux that include all dependencies.

## Verify Installation

Test your installation by running:

```bash
# Check CLI installation
mm --help

# Test GUI (requires PyQt6)
mm gui

# Alternative GUI launch
python -m metadata_multitool.gui_qt.main
```

## First Steps

### 1. Create Test Directory
```bash
mkdir ~/metadata_test
cd ~/metadata_test
```

### 2. Add Some Sample Images
Copy a few photos to your test directory (JPEG, PNG, or TIFF files work best).

### 3. Try Your First Clean Operation

**Using CLI:**
```bash
# Clean all images in current directory
mm clean .

# Check the results
ls safe_upload/
```

**Using GUI:**
1. Launch: `mm gui`
2. Click "Add Files" or "Add Folder"
3. Select your test images
4. Click the "Clean" tab
5. Click "Start Clean Operation"
6. Check the `safe_upload/` folder for cleaned images

### 4. Verify Metadata Removal

Compare original and cleaned files:
```bash
# View original metadata (if ExifTool installed)
exiftool original_image.jpg

# View cleaned metadata
exiftool safe_upload/original_image.jpg
```

The cleaned image should have minimal or no metadata.

## Configuration

Metadata Multitool uses a YAML configuration file for settings:

### Default Configuration Location
- **Windows**: `%USERPROFILE%\.mm_config.yaml`
- **macOS/Linux**: `~/.mm_config.yaml`
- **Project Directory**: `.mm_config.yaml` (takes precedence)

### Basic Configuration Example
```yaml
# .mm_config.yaml
batch_processing:
  batch_size: 100
  max_workers: 4
  memory_limit_mb: 1024

gui:
  theme: "dark"  # or "light"
  remember_window_size: true

clean:
  backup_originals: true
  output_directory: "safe_upload"

poison:
  default_preset: "label_flip"
  create_sidecars: true
```

## Next Steps

Now that you have Metadata Multitool installed:

1. **Learn Common Workflows**: Read [common_workflows.md](common_workflows.md) for step-by-step guides
2. **Explore Advanced Features**: Try poison and revert operations
3. **Customize Settings**: Modify your `.mm_config.yaml` file
4. **Process Your Photos**: Start cleaning your photo collection for safer sharing

## Troubleshooting Installation

### Common Issues

**"Command 'mm' not found"**
- Ensure your virtual environment is activated
- Try using `python -m metadata_multitool.cli` instead

**"PyQt6 not found" (GUI)**
- Install GUI dependencies: `pip install -e .[gui]`
- For headless servers, set: `export QT_QPA_PLATFORM=offscreen`

**"ExifTool not found" warnings**
- ExifTool is optional; the tool will use Pillow fallback
- Install ExifTool for full metadata support (see installation steps above)

**Permission errors**
- Ensure you have write permissions in the target directory
- Try running with elevated permissions if necessary

**Memory errors with large batches**
- Reduce `batch_size` in configuration
- Increase system memory or reduce `max_workers`

For more detailed troubleshooting, see [troubleshooting.md](troubleshooting.md).

---

Ready to start protecting your privacy? Continue to [Common Workflows](common_workflows.md) for practical examples.