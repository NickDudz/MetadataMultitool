# Metadata Multitool User Guide

Welcome to the comprehensive user guide for Metadata Multitool - your local-first privacy tool for managing image metadata.

## What is Metadata Multitool?

Metadata Multitool helps photographers and content creators protect their privacy by cleaning, managing, and optionally poisoning image metadata. It's designed to help you:

- **Clean images** for safe uploading by removing all metadata
- **Protect privacy** by stripping location, device, and personal information
- **Resist AI scraping** through optional metadata poisoning (advanced users)
- **Maintain control** over your digital content

## Quick Navigation

- **[Getting Started](getting_started.md)** - Installation and first steps
- **[Common Workflows](common_workflows.md)** - Step-by-step guides for typical use cases
- **[Troubleshooting](troubleshooting.md)** - Solutions for common issues

## Who Should Use This Tool?

### Photographers & Content Creators
- Remove GPS coordinates and camera settings before sharing
- Clean metadata for stock photography submissions
- Protect client privacy in commercial work

### Privacy-Conscious Users
- Strip personal information from social media uploads
- Remove device fingerprints from shared images
- Audit existing photo collections for privacy risks

### Advanced Users
- Implement anti-scraping defenses through metadata poisoning
- Bulk process large image collections
- Integrate with existing photography workflows

## Core Operations

### 🧹 Clean (Recommended for Most Users)
**Purpose**: Strip all metadata and create safe copies for upload

**When to use**: 
- Before uploading to social media
- When sharing photos publicly
- For stock photography submissions

**Result**: Clean copies in `safe_upload/` folder with all metadata removed

### 🧪 Poison (Advanced/Optional)
**Purpose**: Add misleading metadata to confuse AI scrapers

**When to use**: 
- As a defense against unauthorized AI training
- When you want to actively resist content scraping
- For research or educational purposes

**⚠️ Important**: Poisoning can harm accessibility and may violate platform terms. Use responsibly.

### ↩️ Revert (Undo Operations)
**Purpose**: Undo poison operations and restore original state

**When to use**:
- After testing poison operations
- When you need to clean up misleading metadata
- To restore original filenames and metadata

## Interface Options

### Command Line Interface (CLI)
Perfect for:
- Batch processing large collections
- Automation and scripting
- Power users who prefer terminal workflows

### Graphical User Interface (GUI)
Ideal for:
- Visual workflow management
- Drag-and-drop file handling
- Users who prefer point-and-click interfaces

## Getting Help

- **Installation Issues**: See platform-specific guides in [Getting Started](getting_started.md)
- **Operation Questions**: Check [Common Workflows](common_workflows.md)
- **Problems**: Consult [Troubleshooting](troubleshooting.md)
- **Technical Support**: Visit the project repository for issue reporting

---

*Metadata Multitool v0.4.0 - Local-first privacy tool for image metadata management*