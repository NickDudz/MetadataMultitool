# Windows Installation Guide

Complete installation instructions for Metadata Multitool on Windows systems.

## Prerequisites

- **Windows 10/11** (Windows Server 2019+ also supported)
- **Python 3.11+** (Microsoft Store, python.org, or Anaconda)
- **PowerShell** or **Command Prompt**
- **Administrator privileges** (for ExifTool installation)

## Method 1: Quick Installation (Recommended)

### Step 1: Install Python
Choose one option:

**Option A: Microsoft Store (Easiest)**
1. Open Microsoft Store
2. Search for "Python 3.11" or newer
3. Install Python from Python Software Foundation

**Option B: Python.org (Traditional)**
1. Visit [python.org/downloads](https://python.org/downloads/)
2. Download Python 3.11+ installer
3. ✅ Check "Add Python to PATH" during installation
4. ✅ Check "Install pip"

**Option C: Anaconda (Data Science Users)**
1. Download Anaconda from [anaconda.com](https://anaconda.com)
2. Install with default settings
3. Use Anaconda Prompt for all commands

### Step 2: Set Up Environment
```powershell
# Open PowerShell or Command Prompt
# Create project directory
mkdir C:\MetadataMultitool
cd C:\MetadataMultitool

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Verify activation (should show (.venv) in prompt)
```

### Step 3: Install Metadata Multitool
```powershell
# Install from source (development version)
git clone https://github.com/your-repo/metadata-multitool.git
cd metadata-multitool
pip install -e .[dev,gui]

# Or install from PyPI (when available)
# pip install metadata-multitool[gui]
```

### Step 4: Install ExifTool (Recommended)
ExifTool provides comprehensive metadata support.

**Option A: Chocolatey (Recommended)**
```powershell
# Install Chocolatey if not installed
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install ExifTool
choco install exiftool
```

**Option B: Manual Installation**
1. Download ExifTool from [exiftool.org](https://exiftool.org/)
2. Download the "Windows Executable" version
3. Extract `exiftool(-k).exe` to `C:\Windows\System32\`
4. Rename to `exiftool.exe`
5. Verify: Open new Command Prompt and run `exiftool -ver`

### Step 5: Verify Installation
```powershell
# Test CLI
mm --help

# Test GUI
mm gui

# Test ExifTool integration
mm clean --help | findstr exiftool
```

## Method 2: Development Installation

For developers or advanced users who want to contribute.

### Prerequisites
```powershell
# Install Git
winget install Git.Git
# Or download from https://git-scm.com/

# Install Visual Studio Build Tools (for some dependencies)
winget install Microsoft.VisualStudio.2022.BuildTools
```

### Development Setup
```powershell
# Clone repository
git clone https://github.com/your-repo/metadata-multitool.git
cd metadata-multitool

# Create development environment
python -m venv .venv
.venv\Scripts\activate

# Install development dependencies
pip install -e .[dev,gui]

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest
```

## Method 3: Standalone Executable (Coming Soon)

Pre-built Windows executables will include all dependencies.

```powershell
# Download from releases page
# https://github.com/your-repo/metadata-multitool/releases

# Extract to desired location
# Run metadata-multitool.exe
```

## Configuration for Windows

### Default Configuration Location
```
C:\Users\{username}\.mm_config.yaml
```

### Windows-Specific Configuration
```yaml
# .mm_config.yaml
paths:
  # Use forward slashes or double backslashes
  output_directory: "C:/Users/Username/Pictures/safe_upload"
  # Or: "C:\\Users\\Username\\Pictures\\safe_upload"
  
batch_processing:
  max_workers: 4  # Adjust based on CPU cores
  
gui:
  theme: "auto"  # Uses Windows theme preference
  
tools:
  exiftool_path: "C:/ProgramData/chocolatey/bin/exiftool.exe"
```

## Windows-Specific Troubleshooting

### Common Issues

**"Python not found" Error**
```powershell
# Check Python installation
python --version
py --version  # Alternative launcher

# Add Python to PATH manually
# Control Panel → System → Advanced → Environment Variables
# Add to PATH: C:\Users\{username}\AppData\Local\Programs\Python\Python311\
```

**"Access Denied" During Installation**
```powershell
# Run PowerShell as Administrator
# Right-click PowerShell → "Run as Administrator"

# Or install to user directory only
pip install --user -e .[dev,gui]
```

**"Execution Policy" Error**
```powershell
# Allow script execution (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or bypass for single session
powershell -ExecutionPolicy Bypass
```

**"Long Path" Issues**
```powershell
# Enable long path support (Windows 10 v1607+)
# Run as Administrator:
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

**PyQt6 Installation Issues**
```powershell
# Install Visual C++ Redistributable
winget install Microsoft.VCRedist.2015+.x64

# Or use conda instead of pip
conda install pyqt

# Alternative: install from conda-forge
conda install -c conda-forge pyqt
```

**ExifTool "Not Found" Warnings**
```powershell
# Verify ExifTool installation
where exiftool
exiftool -ver

# Check PATH variable
echo $env:PATH | Select-String exiftool

# Manual PATH addition
$env:PATH += ";C:\ProgramData\chocolatey\bin"
```

### Performance Optimization

**For Better Performance on Windows:**
```yaml
# .mm_config.yaml
batch_processing:
  batch_size: 50        # Optimal for most Windows systems
  max_workers: 8        # Set to CPU core count
  memory_limit_mb: 2048 # Adjust based on available RAM

gui:
  hardware_acceleration: true  # Use GPU if available
```

**Windows Defender Exclusions:**
```powershell
# Add to Windows Defender exclusions (optional, for performance)
# Windows Security → Virus & threat protection → Exclusions
# Add: C:\MetadataMultitool\
```

## Integration with Windows

### File Explorer Context Menu (Advanced)
Create a registry file to add "Clean Metadata" to right-click menu:

```powershell
# Save as metadata-context-menu.reg
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\SystemFileAssociations\image\shell\CleanMetadata]
@="Clean Metadata"
"Icon"="C:\\MetadataMultitool\\.venv\\Scripts\\mm.exe"

[HKEY_CLASSES_ROOT\SystemFileAssociations\image\shell\CleanMetadata\command]
@="C:\\MetadataMultitool\\.venv\\Scripts\\mm.exe clean \"%1\""
```

### Windows Task Scheduler (Automated Processing)
```powershell
# Create scheduled task for automatic processing
schtasks /create /tn "MetadataCleanup" /tr "C:\MetadataMultitool\.venv\Scripts\mm.exe clean C:\Users\%USERNAME%\Pictures\ToProcess" /sc daily
```

### PowerShell Profile Integration
Add to your PowerShell profile (`$PROFILE`):
```powershell
# Metadata Multitool aliases
function mm-clean { & "C:\MetadataMultitool\.venv\Scripts\mm.exe" clean $args }
function mm-gui { & "C:\MetadataMultitool\.venv\Scripts\mm.exe" gui }

# Auto-activate environment when in project directory
function prompt {
    if (Test-Path ".\.venv\Scripts\activate.ps1") {
        if (-not $env:VIRTUAL_ENV) {
            .\.venv\Scripts\activate.ps1
        }
    }
    "PS $($executionContext.SessionState.Path.CurrentLocation)> "
}
```

## Windows-Specific Features

### Drag and Drop Support
The GUI supports Windows drag-and-drop from File Explorer.

### Windows Theme Integration
The GUI automatically adapts to Windows light/dark theme preferences.

### UNC Path Support
Metadata Multitool supports Windows UNC paths:
```powershell
mm clean \\server\share\photos
```

### Windows Subsystem for Linux (WSL)
If using WSL, follow the Linux installation guide but note:
```bash
# In WSL, use Linux paths
mm clean /mnt/c/Users/Username/Pictures
```

## Next Steps

1. **Test Installation**: Try cleaning a sample image
2. **Configure Settings**: Edit `.mm_config.yaml` for your preferences
3. **Read User Guide**: See `docs/user_guide/` for usage instructions
4. **Join Community**: Report issues on GitHub

---

For troubleshooting, see the [Troubleshooting Guide](../user_guide/troubleshooting.md) or Windows-specific solutions above.