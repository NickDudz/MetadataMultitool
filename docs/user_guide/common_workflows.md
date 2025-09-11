# Common Workflows

This guide covers the most common use cases for Metadata Multitool with step-by-step instructions.

## Workflow 1: Social Media Upload Preparation

**Goal**: Clean photos before uploading to Facebook, Instagram, Twitter, etc.

### CLI Method
```bash
# Navigate to your photos folder
cd ~/Pictures/vacation_photos

# Clean all images for safe upload
mm clean . --backup

# Upload files from the safe_upload/ folder
ls safe_upload/
```

### GUI Method
1. Open Metadata Multitool: `mm gui`
2. Click **"Add Folder"** and select your photos directory
3. Switch to the **"Clean"** tab
4. Enable **"Backup originals"** if desired
5. Click **"Start Clean Operation"**
6. Upload files from the newly created `safe_upload/` folder

**Result**: All GPS coordinates, camera settings, and personal metadata removed.

---

## Workflow 2: Stock Photography Preparation

**Goal**: Clean metadata while preserving copyright information.

### CLI Method
```bash
# Clean photos but preserve specific metadata fields
mm clean ./stock_photos --preserve-fields "Copyright,Artist,ImageDescription"

# Verify metadata was preserved
exiftool safe_upload/photo.jpg | grep -E "(Copyright|Artist|Description)"
```

### GUI Method
1. Launch GUI and add your stock photos
2. Go to **"Clean"** tab
3. In **"Advanced Options"**, check **"Preserve copyright fields"**
4. Select specific fields to preserve
5. Start the clean operation

**Result**: Technical metadata removed, but copyright and attribution preserved.

---

## Workflow 3: Bulk Photo Collection Cleaning

**Goal**: Process large collections (1000+ photos) efficiently.

### CLI Method
```bash
# Process large batch with performance optimization
mm clean ~/Pictures --batch-size 50 --max-workers 8 --dry-run

# If dry-run looks good, run for real
mm clean ~/Pictures --batch-size 50 --max-workers 8

# Monitor progress
tail -f .mm_progress.log
```

### GUI Method
1. Open GUI and go to **"Settings"** → **"Performance"**
2. Set **"Batch Size"** to 50-100
3. Set **"Max Workers"** to your CPU core count
4. Add your photo collection folder
5. Enable **"Show Progress Details"**
6. Start cleaning operation

**Result**: Efficient processing with progress tracking and memory management.

---

## Workflow 4: Privacy Audit Before Sharing

**Goal**: Check what personal information is in your photos.

### CLI Method
```bash
# Audit photos for privacy risks
mm audit ~/Pictures/family_photos --report privacy_report.html

# View detailed metadata
mm audit ~/Pictures/family_photos --verbose
```

### GUI Method
1. Add photos to GUI
2. Go to **"Tools"** → **"Privacy Audit"**
3. Select **"Generate Report"**
4. Review the HTML report for privacy risks
5. Follow recommendations for cleaning

**Result**: Detailed privacy assessment with recommendations.

---

## Workflow 5: Anti-Scraping Defense (Advanced)

**Goal**: Add misleading metadata to discourage AI training.

⚠️ **Warning**: Use responsibly. May violate platform terms and harm accessibility.

### CLI Method
```bash
# Add misleading labels with sidecars
mm poison ./art_portfolio --preset label_flip --sidecar --true-hint "abstract sculpture"

# Create multiple output formats
mm poison ./photos --preset clip_confuse --sidecar --json --xmp --html

# Verify poisoning was applied
cat photo.txt  # Check sidecar file
exiftool photo.jpg | grep -i description
```

### GUI Method
1. Add images to GUI
2. Switch to **"Poison"** tab
3. Select preset: **"Label Flip"** or **"CLIP Confuse"**
4. Choose output formats: **Sidecars**, **EXIF**, **JSON**
5. Enter a **"True Hint"** describing the actual content
6. Click **"Start Poison Operation"**

**Result**: Misleading metadata added to confuse automated scrapers.

---

## Workflow 6: Undoing Poison Operations

**Goal**: Remove misleading metadata and restore original state.

### CLI Method
```bash
# Revert all poison operations in directory
mm revert ./poisoned_photos

# Check what would be reverted (dry run)
mm revert ./poisoned_photos --dry-run

# Revert specific operation log
mm revert ./photos --log-file specific_operation.mm_poisonlog.json
```

### GUI Method
1. Add the previously poisoned directory
2. Switch to **"Revert"** tab
3. GUI will automatically detect operation logs
4. Review **"Operations to Revert"** list
5. Click **"Start Revert Operation"**

**Result**: All poisoning metadata removed, original filenames restored.

---

## Workflow 7: Photography Workflow Integration

**Goal**: Integrate with existing photo editing workflow.

### Lightroom Integration
```bash
# Create action/script in Lightroom export
# Export to: ~/exported_photos
# Post-process: mm clean ~/exported_photos
```

### Batch Processing Script
```bash
#!/bin/bash
# process_photos.sh

# 1. Import from camera
cp /media/camera/* ~/raw_photos/

# 2. Clean for web sharing
mm clean ~/raw_photos --output ~/web_ready/

# 3. Create archive copies
mm clean ~/raw_photos --preserve-fields "Copyright,Artist" --output ~/archive/

echo "Photos processed successfully!"
```

### GUI Automation
1. Set up **"Watch Folder"** in GUI settings
2. Configure automatic cleaning on file detection
3. Set custom output directories for different purposes

---

## Workflow 8: Team/Client Work

**Goal**: Protect client privacy in commercial photography.

### CLI Method
```bash
# Clean client photos with custom settings
mm clean ./client_shoot --preserve-fields "Copyright,Artist" --backup

# Generate privacy compliance report
mm audit ./client_shoot --report client_privacy_report.html

# Archive with metadata removed
zip client_delivery.zip safe_upload/*
```

### GUI Method
1. Create **"Client Project"** template in settings
2. Set default privacy settings for client work
3. Add client photos and apply template
4. Generate privacy compliance report
5. Package cleaned photos for delivery

**Result**: Client privacy protected while maintaining professional metadata.

---

## Best Practices

### For All Workflows
- **Always backup originals** before processing
- **Test with a few images** before bulk processing
- **Verify results** by checking output metadata
- **Keep operation logs** for potential revert needs

### Performance Tips
- **Adjust batch size** based on image size and system memory
- **Use fewer workers** on systems with limited CPU cores
- **Enable progress tracking** for long operations
- **Close other applications** during large batch processing

### Privacy Tips
- **Audit first** before cleaning to understand privacy exposure
- **Use dry-run mode** to preview operations
- **Check safe_upload folder** before sharing images
- **Consider selective cleaning** instead of removing all metadata

### Security Tips
- **Keep operation logs secure** (contain file paths and metadata)
- **Use secure deletion** when processing sensitive content
- **Verify tool integrity** by checking checksums
- **Update regularly** for latest privacy protection features

---

## Troubleshooting Common Issues

**"No images found"**
- Check file extensions are supported (.jpg, .png, .tiff, .webp, .bmp)
- Verify directory permissions

**"Memory errors during batch processing"**
- Reduce batch size in settings
- Close other applications
- Process in smaller chunks

**"GUI not responding"**
- Large operations run in background
- Check progress in status bar
- Wait for completion or use CLI for very large batches

For more detailed troubleshooting, see [troubleshooting.md](troubleshooting.md).

---

Ready to implement advanced features? Check the project documentation for custom configurations and plugin development.