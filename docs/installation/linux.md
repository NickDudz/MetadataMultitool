# Linux Installation Guide

Complete installation instructions for Metadata Multitool on Linux distributions.

## Prerequisites

- **Linux Distribution**: Ubuntu 20.04+, Debian 11+, CentOS 8+, Fedora 35+, or equivalent
- **Python 3.11+** (via package manager or source)
- **Git** for source installation
- **Build tools** for compiling dependencies

## Method 1: Ubuntu/Debian Installation

### Step 1: Update System and Install Prerequisites
```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ and build tools
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
sudo apt install -y build-essential git curl

# Alternative: Install Python 3.11 from deadsnakes PPA (Ubuntu 20.04)
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

### Step 2: Set Up Environment
```bash
# Create project directory
mkdir ~/MetadataMultitool
cd ~/MetadataMultitool

# Create virtual environment with Python 3.11
python3.11 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Metadata Multitool
```bash
# Install from source
git clone https://github.com/your-repo/metadata-multitool.git
cd metadata-multitool
pip install -e .[dev,gui]

# Or install from PyPI (when available)
# pip install metadata-multitool[gui]
```

### Step 4: Install ExifTool and GUI Dependencies
```bash
# Install ExifTool
sudo apt install -y libimage-exiftool-perl

# Install Qt6 dependencies for GUI
sudo apt install -y qt6-base-dev qt6-tools-dev-tools
sudo apt install -y python3-pyqt6 python3-pyqt6-dev

# Alternative: Install PyQt6 via pip (may require build dependencies)
# sudo apt install -y qtbase5-dev qttools5-dev-tools
# pip install PyQt6
```

### Step 5: Verify Installation
```bash
# Test CLI
mm --help

# Test ExifTool integration
exiftool -ver

# Test GUI (requires X11 or Wayland display)
mm gui

# Test with sample image
mm clean /usr/share/pixmaps/debian-logo.png 2>/dev/null || echo "No sample image found"
```

## Method 2: RHEL/CentOS/Fedora Installation

### Step 1: Install Prerequisites
```bash
# CentOS/RHEL 8+
sudo dnf update -y
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y python3.11 python3.11-pip python3.11-devel git

# Fedora 35+
sudo dnf update -y
sudo dnf groupinstall -y "Development Tools" "C Development Tools and Libraries"
sudo dnf install -y python3.11 python3-pip python3-devel git

# Enable EPEL repository (RHEL/CentOS)
sudo dnf install -y epel-release
```

### Step 2: Set Up Environment
```bash
# Create and activate virtual environment
mkdir ~/MetadataMultitool && cd ~/MetadataMultitool
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Dependencies
```bash
# Install ExifTool
sudo dnf install -y perl-Image-ExifTool

# Install Qt6 for GUI (Fedora)
sudo dnf install -y qt6-qtbase-devel python3-qt6

# Install build dependencies
sudo dnf install -y gcc gcc-c++ python3-devel
```

### Step 4: Install Metadata Multitool
```bash
# Clone and install
git clone https://github.com/your-repo/metadata-multitool.git
cd metadata-multitool
pip install -e .[dev,gui]
```

## Method 3: Arch Linux Installation

### Step 1: Install Prerequisites
```bash
# Update system
sudo pacman -Syu

# Install Python and build tools
sudo pacman -S python python-pip python-virtualenv git base-devel

# Install ExifTool
sudo pacman -S perl-image-exiftool

# Install Qt6 for GUI
sudo pacman -S qt6-base python-pyqt6
```

### Step 2: Set Up Environment
```bash
# Create virtual environment
mkdir ~/MetadataMultitool && cd ~/MetadataMultitool
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### Step 3: Install Metadata Multitool
```bash
git clone https://github.com/your-repo/metadata-multitool.git
cd metadata-multitool
pip install -e .[dev,gui]
```

## Method 4: Universal Linux (AppImage - Coming Soon)

```bash
# Download AppImage from releases
wget https://github.com/your-repo/metadata-multitool/releases/latest/download/MetadataMultitool-x86_64.AppImage

# Make executable
chmod +x MetadataMultitool-x86_64.AppImage

# Run
./MetadataMultitool-x86_64.AppImage
```

## Method 5: Docker Container

### Using Docker
```bash
# Pull image (when available)
docker pull metadatamultitool/metadata-multitool:latest

# Run with volume mount
docker run -v ~/Pictures:/data metadatamultitool/metadata-multitool:latest clean /data

# Interactive mode
docker run -it -v ~/Pictures:/data metadatamultitool/metadata-multitool:latest bash
```

### Build from Source
```dockerfile
# Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libimage-exiftool-perl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -e .[dev]

ENTRYPOINT ["mm"]
CMD ["--help"]
```

```bash
# Build and run
docker build -t metadata-multitool .
docker run -v ~/Pictures:/data metadata-multitool clean /data
```

## Linux-Specific Configuration

### Default Configuration Location
```
~/.mm_config.yaml
```

### Linux-Optimized Configuration
```yaml
# .mm_config.yaml
paths:
  output_directory: "~/Pictures/safe_upload"
  
batch_processing:
  max_workers: 8  # Adjust based on CPU cores
  batch_size: 100
  
gui:
  theme: "auto"  # Follows desktop environment theme
  use_native_dialogs: true
  backend: "x11"  # or "wayland"
  
tools:
  exiftool_path: "/usr/bin/exiftool"
```

## Linux Desktop Integration

### Creating Desktop Entry
```bash
# Create desktop entry
cat > ~/.local/share/applications/metadata-multitool.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Metadata Multitool
Comment=Clean and manage image metadata
Exec=/home/$(whoami)/MetadataMultitool/.venv/bin/mm gui
Icon=image-x-generic
Terminal=false
Categories=Graphics;Photography;
MimeType=image/jpeg;image/png;image/tiff;
EOF

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

### Nautilus/Files Integration (GNOME)
```bash
# Create Nautilus script
mkdir -p ~/.local/share/nautilus/scripts
cat > ~/.local/share/nautilus/scripts/clean-metadata.sh << 'EOF'
#!/bin/bash
source ~/MetadataMultitool/.venv/bin/activate
mm clean "$@"
zenity --info --text="Metadata cleaning complete! Check safe_upload/ folder."
EOF
chmod +x ~/.local/share/nautilus/scripts/clean-metadata.sh
```

### Dolphin Integration (KDE)
```bash
# Create service menu
mkdir -p ~/.local/share/kservices5/ServiceMenus
cat > ~/.local/share/kservices5/ServiceMenus/metadata-multitool.desktop << EOF
[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=image/jpeg;image/png;image/tiff;
Actions=cleanmetadata;

[Desktop Action cleanmetadata]
Name=Clean Metadata
Icon=image-x-generic
Exec=konsole --hold -e ~/MetadataMultitool/.venv/bin/mm clean %f
EOF
```

## Linux-Specific Troubleshooting

### Common Issues

**"python3.11: command not found"**
```bash
# Check available Python versions
ls /usr/bin/python*

# Install Python 3.11 from source (if not in repos)
wget https://www.python.org/ftp/python/3.11.7/Python-3.11.7.tgz
tar xzf Python-3.11.7.tgz
cd Python-3.11.7
./configure --enable-optimizations
make -j $(nproc)
sudo make altinstall
```

**"Permission denied" for ExifTool**
```bash
# Check ExifTool permissions
ls -la $(which exiftool)

# Fix if needed
sudo chmod +x $(which exiftool)

# Add user to appropriate groups
sudo usermod -a -G users $USER
```

**GUI won't start (X11/Wayland issues)**
```bash
# Check display environment
echo $DISPLAY
echo $WAYLAND_DISPLAY

# For X11
export DISPLAY=:0
xauth list

# For Wayland
export QT_QPA_PLATFORM=wayland

# For headless servers
export QT_QPA_PLATFORM=offscreen
```

**"Qt platform plugin could not be loaded"**
```bash
# Install Qt platform plugins
sudo apt install -y qt6-qpa-plugins  # Ubuntu/Debian
sudo dnf install -y qt6-qtbase-gui   # Fedora
sudo pacman -S qt6-base              # Arch

# Or set fallback platform
export QT_QPA_PLATFORM=xcb
```

**Build errors with PyQt6**
```bash
# Install development headers
sudo apt install -y qt6-base-dev qt6-tools-dev  # Ubuntu/Debian
sudo dnf install -y qt6-qtbase-devel qt6-qttools-devel  # Fedora

# Alternative: use system PyQt6
sudo apt install -y python3-pyqt6
# Then install without GUI extras:
pip install -e .[dev]
```

### Performance Optimization

**For Servers/High Performance:**
```yaml
# .mm_config.yaml
batch_processing:
  batch_size: 200       # Larger batches on powerful systems
  max_workers: 16       # More workers for many cores
  memory_limit_mb: 8192 # Higher memory limits

performance:
  use_all_cores: true
  priority: "high"      # Nice value for higher priority
```

**Memory-Constrained Systems:**
```yaml
# .mm_config.yaml
batch_processing:
  batch_size: 25        # Smaller batches
  max_workers: 2        # Fewer workers
  memory_limit_mb: 512  # Conservative memory limit

performance:
  swap_handling: "conservative"
```

## Distribution-Specific Notes

### Ubuntu/Debian
- Use `apt` package manager
- PPAs available for newer Python versions
- Snap packages (future distribution method)

### RHEL/CentOS/Fedora
- Use `dnf` (or `yum` on older systems)
- EPEL repository needed for some packages
- SELinux considerations for file access

### Arch Linux
- Rolling release with latest packages
- AUR packages available for additional tools
- Minimal base system requires more manual setup

### SUSE/openSUSE
```bash
# Install prerequisites
sudo zypper install python311 python311-pip python311-devel
sudo zypper install perl-Image-ExifTool
sudo zypper install libqt6-qtbase-devel python311-qt6
```

### Alpine Linux (Containers)
```bash
# Minimal container setup
apk add --no-cache python3 py3-pip perl-image-exiftool git build-base python3-dev
```

## Systemd Integration

### Service for Batch Processing
```bash
# Create service file
sudo tee /etc/systemd/system/metadata-cleanup.service << EOF
[Unit]
Description=Metadata Multitool Cleanup Service
After=network.target

[Service]
Type=oneshot
User=metadata
Group=metadata
WorkingDirectory=/home/metadata
ExecStart=/home/metadata/MetadataMultitool/.venv/bin/mm clean /srv/photos/incoming
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create timer for regular execution
sudo tee /etc/systemd/system/metadata-cleanup.timer << EOF
[Unit]
Description=Run metadata cleanup hourly
Requires=metadata-cleanup.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start
sudo systemctl enable metadata-cleanup.timer
sudo systemctl start metadata-cleanup.timer
```

## Next Steps

1. **Test Installation**: Process a sample image
2. **Desktop Integration**: Set up file manager scripts
3. **Configuration**: Customize ~/.mm_config.yaml
4. **Automation**: Set up systemd services if needed

---

For additional troubleshooting, see the [Troubleshooting Guide](../user_guide/troubleshooting.md) or Linux-specific solutions above.