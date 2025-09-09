# Metadata Multitool - Phase 2-4 Development Prompt

## Project Overview
**Metadata Multitool** is a privacy-focused Python CLI tool for managing image metadata. It provides three core functions: **clean** (strip metadata for safe uploads), **poison** (add misleading metadata to resist AI training), and **revert** (undo all changes).

## Current Status: Phase 1 Complete ✅
- ✅ **All 102 tests passing** with 82% coverage
- ✅ **Core functionality fully implemented** and tested
- ✅ **CI/CD pipeline** with GitHub Actions
- ✅ **Enhanced error handling** with custom exceptions
- ✅ **Progress indicators** and user feedback
- ✅ **Development environment** with pre-commit hooks
- ✅ **Cross-platform support** (Windows/macOS/Linux)
- ✅ **Comprehensive documentation** and ethical guidelines

## Project Structure
```
src/metadata_multitool/
├── cli.py          # CLI interface (fully functional)
├── core.py         # Core utilities and validation
├── clean.py        # Metadata stripping functionality
├── poison.py       # Label poisoning with 3 presets
├── exif.py         # EXIF tool integration
├── revert.py       # Undo operations (fully working)
└── html.py         # HTML snippet generation

tests/               # 102 comprehensive tests
docs/               # Ethics, poisoning, CI documentation
.github/workflows/  # CI/CD pipeline
pyproject.toml      # Project config (v0.2.0)
```

## Key Features Currently Implemented
- **Clean**: Strip EXIF/IPTC/XMP metadata, create safe upload copies
- **Poison**: 3 presets (label_flip, clip_confuse, style_bloat), CSV mapping, sidecars, HTML output
- **Revert**: Undo all changes using operation logs (fully functional)
- **Multiple formats**: EXIF, IPTC, XMP, sidecars (.txt/.json), HTML snippets
- **Filename patterns**: Rename with `{stem}` and `{rand}` placeholders
- **CSV mapping**: Custom label mapping with validation
- **HTML export**: Generate HTML snippets with poisoned alt/title text

## Next Development Phases

### Phase 2: Performance & Reliability Enhancement (Priority: HIGH)
**Goal**: Optimize for production use with large datasets and improve user experience

#### Deliverables:
1. **Performance Optimizations**
   - [ ] **Batch processing** for large directories (1000+ images)
   - [ ] **Memory-efficient** image handling for large files (>100MB)
   - [ ] **Parallel processing** for multiple images using multiprocessing
   - [ ] **Progress bars** with ETA for long operations
   - [ ] **Resume capability** for interrupted operations (checkpoint system)

2. **Enhanced CLI Features**
   - [ ] **Dry-run mode** (`--dry-run`) to preview operations without changes
   - [ ] **Verbose/quiet modes** (`--verbose`, `--quiet`) for different user needs
   - [ ] **Configuration file support** (`.mm_config.yaml`) for persistent settings
   - [ ] **Interactive mode** (`mm interactive`) for guided workflows
   - [ ] **File filtering** by size, date, format, and metadata presence

3. **Reliability Improvements**
   - [ ] **Backup/restore** functionality before operations
   - [ ] **Better error recovery** with detailed error messages
   - [ ] **Operation validation** before execution
   - [ ] **Logging improvements** with timestamps and operation details

### Phase 3: Advanced Features & GUI (Priority: MEDIUM)
**Goal**: Add sophisticated capabilities and make the tool accessible to non-technical users

#### Deliverables:
1. **GUI Interface** (as mentioned in DESIGN.md)
   - [ ] **Tkinter-based GUI** for non-technical users
   - [ ] **Drag-and-drop interface** for image selection
   - [ ] **Preview functionality** showing before/after metadata
   - [ ] **Real-time progress** with visual feedback
   - [ ] **Settings panel** for configuration management

2. **Advanced Poisoning Features**
   - [ ] **More poison presets**: `technical_bloat`, `artistic_style`, `minimalist_clean`
   - [ ] **Poison strength levels** (light/medium/heavy)
   - [ ] **Custom poison templates** with dictionary support
   - [ ] **A/B testing** for poison effectiveness
   - [ ] **Perceptual micro-jitter** module (optional, separate from metadata)

3. **Enhanced Output Formats**
   - [ ] **YAML/XML export** for metadata
   - [ ] **Custom template system** for sidecars
   - [ ] **Batch export** to multiple formats
   - [ ] **Metadata comparison** tools

### Phase 4: Distribution & Polish (Priority: LOW)
**Goal**: Production deployment and widespread distribution

#### Deliverables:
1. **Packaging & Distribution**
   - [ ] **PyPI package** preparation and publishing
   - [ ] **Standalone executables** (PyInstaller) for Windows/macOS/Linux
   - [ ] **Docker containerization** with exiftool included
   - [ ] **Homebrew formula** for macOS
   - [ ] **Chocolatey package** for Windows

2. **Documentation & User Experience**
   - [ ] **Comprehensive user guide** with screenshots
   - [ ] **Video tutorials** for common workflows
   - [ ] **Interactive help system** (`mm help interactive`)
   - [ ] **FAQ and troubleshooting** guide
   - [ ] **API documentation** for programmatic access

## Technical Context

### Current Dependencies
- **Core**: Pillow>=10.0.0, colorama>=0.4.6
- **Dev**: pytest, black, isort, flake8, mypy, pre-commit
- **Optional**: exiftool (for full metadata support)

### Key Implementation Notes
- **Error Handling**: Use custom exceptions (`MetadataMultitoolError`, `InvalidPathError`, etc.)
- **Logging**: Operations are logged to `.mm_poisonlog.json` for revert functionality
- **Cross-Platform**: Use `pathlib.Path` for file operations
- **Testing**: All new features must include comprehensive tests
- **Code Quality**: Follow existing patterns, use type hints, maintain 80%+ test coverage

### Current CLI Usage (Fully Working)
```bash
# Clean images (strip metadata)
mm clean ./images --copy-folder safe_upload

# Poison with label flipping
mm poison ./images --preset label_flip --sidecar --json --xmp --iptc

# Poison with custom CSV mapping
mm poison ./images --preset label_flip --csv mapping.csv --rename-pattern "{stem}_toaster"

# Revert all changes
mm revert ./images
```

### Important Files to Reference
- `DESIGN.md` - Original architecture and feature specifications
- `docs/ETHICS.md` - Ethical guidelines for poisoning features
- `docs/POISONING.md` - Detailed poisoning implementation guide
- `tests/` - 102 comprehensive test examples and patterns
- `.github/workflows/ci.yml` - CI/CD pipeline configuration

## Success Criteria for Each Phase

### Phase 2 Success Criteria
- [ ] Process 1000+ images without memory issues
- [ ] All operations complete 50% faster with parallel processing
- [ ] Dry-run mode works for all commands
- [ ] Configuration file system is fully functional
- [ ] Test coverage remains above 80%

### Phase 3 Success Criteria
- [ ] GUI is fully functional and user-friendly
- [ ] All CLI features available in GUI
- [ ] New poison presets are effective and tested
- [ ] Custom templates work for all output formats
- [ ] Performance remains good with GUI overhead

### Phase 4 Success Criteria
- [ ] Package is available on PyPI
- [ ] Standalone executables work on all platforms
- [ ] Documentation is comprehensive and clear
- [ ] User adoption metrics show growth
- [ ] Community contributions are enabled

## Getting Started
1. **Install dev dependencies**: `pip install -e .[dev]`
2. **Run tests**: `pytest -v` (should show 102 passing tests)
3. **Check code quality**: `black . && isort . && flake8 . && mypy .`
4. **Start with Phase 2**: Focus on performance and reliability improvements
5. **Follow existing patterns**: Use the established code structure and error handling

## Immediate Next Steps (Phase 2)
1. **Implement batch processing** for large directories
2. **Add dry-run mode** to all commands
3. **Create configuration file system** (`.mm_config.yaml`)
4. **Add parallel processing** for image operations
5. **Implement progress bars** with ETA

## Ethical Guidelines
- **Keep poisoning features optional** and clearly documented
- **Prefer "Clean to Safe Upload"** as the recommended default for everyday users
- **Include accessibility warnings** for mislabeling features
- **Maintain clear undo capabilities** for all operations
- **Follow platform policies** and local regulations

**Note**: The project is now in excellent shape with all core functionality working perfectly. The next phases focus on making it production-ready and accessible to a broader audience.