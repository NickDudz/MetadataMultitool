# Troubleshooting Guide

This guide helps you resolve common issues with Metadata Multitool.

## Installation Issues

### Python/Package Installation

**Problem**: `Command 'mm' not found`
```bash
# Solutions:
# 1. Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 2. Use direct module call
python -m metadata_multitool.cli --help

# 3. Reinstall with correct path
pip install -e .[dev,gui]
```

**Problem**: `Permission denied during installation`
```bash
# Solutions:
# 1. Use virtual environment (recommended)
python -m venv .venv && source .venv/bin/activate

# 2. Install for user only
pip install --user -e .[dev,gui]

# 3. Check directory permissions
ls -la /path/to/installation
```

**Problem**: `PyQt6 installation fails`
```bash
# Solutions:
# 1. Install system dependencies (Linux)
sudo apt-get install python3-pyqt6 python3-pyqt6-dev

# 2. Use conda instead of pip
conda install pyqt

# 3. Install GUI dependencies separately
pip install PyQt6 PyQt6-tools
```

### ExifTool Issues

**Problem**: `ExifTool not found` warnings
```bash
# Verification:
which exiftool  # Should show path
exiftool -ver   # Should show version

# Solutions by platform:
# Windows (Chocolatey):
choco install exiftool

# macOS (Homebrew):
brew install exiftool

# Ubuntu/Debian:
sudo apt-get install libimage-exiftool-perl

# Manual installation:
# Download from https://exiftool.org/ and add to PATH
```

**Problem**: `ExifTool permission errors`
```bash
# Solutions:
# 1. Check file permissions
chmod +x /usr/local/bin/exiftool

# 2. Verify PATH
echo $PATH | grep exiftool

# 3. Use absolute path in config
export EXIFTOOL_PATH="/full/path/to/exiftool"
```

## Runtime Issues

### File Processing Problems

**Problem**: `No images found in directory`
```bash
# Diagnostics:
ls -la *.{jpg,jpeg,png,tiff,webp,bmp}  # Check for supported files
mm clean . --verbose  # See detailed file discovery

# Solutions:
# 1. Check file extensions (case sensitive on Linux)
# 2. Verify read permissions
# 3. Check for hidden files
ls -la .*jpg
```

**Problem**: `Permission denied writing to output directory`
```bash
# Diagnostics:
ls -ld safe_upload/  # Check directory permissions
touch safe_upload/test.txt  # Test write access

# Solutions:
# 1. Create output directory
mkdir -p safe_upload && chmod 755 safe_upload

# 2. Use different output location
mm clean . --output ~/my_clean_photos

# 3. Fix permissions
sudo chown -R $USER:$USER safe_upload/
```

**Problem**: `Memory errors during batch processing`
```bash
# Diagnostics:
free -h  # Check available memory
ps aux | grep metadata  # Check process memory usage

# Solutions in .mm_config.yaml:
batch_processing:
  batch_size: 25        # Reduce from default 100
  max_workers: 2        # Reduce from default 4
  memory_limit_mb: 512  # Set explicit limit

# Or use CLI:
mm clean . --batch-size 25 --max-workers 2
```

### GUI Issues

**Problem**: GUI won't start
```bash
# Diagnostics:
python -c "import PyQt6; print('PyQt6 OK')"
echo $DISPLAY  # Linux: check display variable

# Solutions:
# 1. Install GUI dependencies
pip install -e .[gui]

# 2. Set up display (Linux/headless)
export QT_QPA_PLATFORM=offscreen

# 3. Try alternative launch
python -m metadata_multitool.gui_qt.main

# 4. Check for conflicting Qt versions
pip list | grep -i qt
```

**Problem**: GUI freezes during operations
```bash
# This is expected behavior for large operations
# Solutions:
# 1. Use CLI for very large batches (1000+ files)
mm clean ./large_collection --batch-size 50

# 2. Check progress in terminal
tail -f .mm_progress.log

# 3. Adjust performance settings
# GUI → Settings → Performance → Reduce batch size
```

**Problem**: Dark/Light theme issues
```bash
# Solutions:
# 1. Reset theme in config
echo "gui:\n  theme: auto" > .mm_config.yaml

# 2. Force specific theme
mm gui --theme light
mm gui --theme dark

# 3. Clear GUI settings
rm ~/.mm_gui_settings.json
```

### Operation-Specific Issues

**Problem**: Clean operation leaves metadata
```bash
# Diagnostics:
exiftool cleaned_image.jpg  # Check remaining metadata
mm clean image.jpg --verbose  # See detailed processing

# Solutions:
# 1. Ensure ExifTool is installed for complete cleaning
# 2. Check if Pillow fallback is being used
# 3. Some metadata may be embedded in image data (not removable)
```

**Problem**: Poison operation appears to do nothing
```bash
# Diagnostics:
cat image.txt  # Check sidecar file
exiftool image.jpg | grep -i description  # Check EXIF fields
ls -la *.json *.xmp  # Check for output files

# Solutions:
# 1. Verify output format selection
mm poison image.jpg --sidecar --json --exif

# 2. Check operation log
cat .mm_poisonlog.json

# 3. Use verbose mode
mm poison image.jpg --preset label_flip --verbose
```

**Problem**: Revert operation fails
```bash
# Diagnostics:
ls -la .mm_poisonlog.json  # Check log file exists
cat .mm_poisonlog.json | head  # Verify log format

# Solutions:
# 1. Ensure you're in the same directory as the original operation
# 2. Check log file permissions
chmod 644 .mm_poisonlog.json

# 3. Use specific log file
mm revert . --log-file path/to/specific.mm_poisonlog.json

# 4. Check log integrity
mm verify-log .mm_poisonlog.json
```

## Performance Issues

### Slow Processing

**Problem**: Operations taking too long
```bash
# Diagnostics:
time mm clean test_image.jpg  # Time single operation
htop  # Monitor CPU/memory usage

# Solutions:
# 1. Adjust worker count to match CPU cores
mm clean . --max-workers $(nproc)

# 2. Optimize batch size for your system
mm clean . --batch-size 10  # Start small, increase

# 3. Use SSD storage for temporary files
export TMPDIR=/path/to/ssd/tmp

# 4. Close other applications during processing
```

**Problem**: High memory usage
```bash
# Diagnostics:
ps aux | grep metadata | awk '{print $6}'  # Memory usage in KB

# Solutions in .mm_config.yaml:
batch_processing:
  memory_limit_mb: 1024  # Set hard limit
  batch_size: 25         # Process fewer files at once
  max_workers: 2         # Reduce parallel processing

# Monitor memory during operation:
watch -n 1 'ps aux | grep metadata'
```

### Network/Storage Issues

**Problem**: Processing network drives is slow
```bash
# Solutions:
# 1. Copy to local drive first
cp /network/photos/* /tmp/local_photos/
mm clean /tmp/local_photos/

# 2. Use smaller batches for network storage
mm clean /network/photos --batch-size 10

# 3. Process subset at a time
find /network/photos -name "*.jpg" | head -100 | xargs mm clean
```

## Configuration Issues

### Config File Problems

**Problem**: Settings not saving/loading
```bash
# Diagnostics:
find . -name ".mm_config.yaml" -type f  # Find config files
cat .mm_config.yaml  # Check syntax

# Solutions:
# 1. Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.mm_config.yaml'))"

# 2. Reset to defaults
mv .mm_config.yaml .mm_config.yaml.backup
mm --help  # Will create new default config

# 3. Check file permissions
chmod 644 .mm_config.yaml
```

**Problem**: GUI settings not persisting
```bash
# Solutions:
# 1. Check GUI settings file
ls -la ~/.mm_gui_settings.json

# 2. Ensure write permissions to home directory
touch ~/.test_write && rm ~/.test_write

# 3. Reset GUI settings
rm ~/.mm_gui_settings.json
```

## Error Messages Reference

### Common Error Messages

**`MetadataMultitoolError: Invalid path`**
- Check file/directory exists and is readable
- Verify file extensions are supported
- Ensure no special characters in paths

**`LogError: Cannot parse operation log`**
- Operation log file is corrupted
- Try with `--ignore-log` flag to skip log
- Restore from backup if available

**`InvalidPathError: Directory not writable`**
- Check write permissions on output directory
- Ensure sufficient disk space
- Try different output location

**`ExifTool execution failed`**
- ExifTool not in PATH or not installed
- File may be corrupted or unsupported format
- Try with `--use-pillow-fallback` flag

### Recovery Procedures

**Corrupted Operation Log**
```bash
# 1. Backup corrupted log
cp .mm_poisonlog.json .mm_poisonlog.json.corrupted

# 2. Try to extract valid entries
jq '.[]' .mm_poisonlog.json > temp_log.json

# 3. Manual cleanup (edit temp_log.json)
# 4. Restore or continue without log
mm revert . --ignore-log
```

**Interrupted Operation Recovery**
```bash
# 1. Check for partial progress files
ls -la .mm_progress_*

# 2. Resume if supported
mm clean . --resume

# 3. Or clean up and restart
rm .mm_progress_* && mm clean .
```

**System Crash Recovery**
```bash
# 1. Check for lock files
rm .mm_lock_*

# 2. Verify file integrity
find . -name "*.jpg" -exec file {} \; | grep -v "JPEG"

# 3. Clean up temporary files
find . -name ".mm_temp_*" -delete

# 4. Restart operation
mm clean . --verify-integrity
```

## Getting Help

### Collecting Debug Information

**Create Debug Report**
```bash
# System information
uname -a > debug_report.txt
python --version >> debug_report.txt
pip list | grep -E "(metadata|PyQt|Pillow)" >> debug_report.txt

# Tool information
mm --version >> debug_report.txt
which exiftool >> debug_report.txt
exiftool -ver >> debug_report.txt

# Configuration
cat .mm_config.yaml >> debug_report.txt

# Recent logs
tail -50 ~/.mm_debug.log >> debug_report.txt
```

**Run with Maximum Verbosity**
```bash
# CLI debug mode
mm clean . --verbose --debug

# Save debug output
mm clean . --verbose --debug > debug_output.log 2>&1
```

### Reporting Issues

When reporting issues, include:

1. **System Information**: OS, Python version, installation method
2. **Error Message**: Full error text and stack trace
3. **Steps to Reproduce**: Exact commands and file types used
4. **Expected vs Actual**: What should happen vs what happens
5. **Configuration**: Your `.mm_config.yaml` file (remove sensitive paths)
6. **Debug Output**: Output from verbose/debug mode

### Community Resources

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check latest docs for updates
- **Examples**: See `examples/` directory for sample configurations
- **FAQ**: Check project wiki for frequently asked questions

---

Still having issues? Create a GitHub issue with your debug information for community support.