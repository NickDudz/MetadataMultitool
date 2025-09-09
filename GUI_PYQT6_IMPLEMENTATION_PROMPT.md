# PyQt6 GUI Implementation Prompt

## Project Overview

You are tasked with implementing a modern, production-ready desktop GUI for the Metadata Multitool using PyQt6. This tool helps photographers and content creators clean, manage, and optionally poison image metadata for privacy protection and anti-scraping purposes.

## <requirements>

### <functional_requirements>
- **Clean Mode**: Strip metadata from images and create safe copies
- **Poison Mode**: Add misleading metadata as anti-scraping defense (opt-in)
- **Revert Mode**: Undo previous operations using operation logs
- **File Management**: Drag & drop, file browsing, advanced filtering
- **Progress Tracking**: Real-time progress with cancel/pause capabilities
- **Settings Management**: Comprehensive configuration interface
- **Theme Support**: Light/dark themes with system integration
- **Keyboard Shortcuts**: Full keyboard navigation and hotkeys
</functional_requirements>

### <technical_requirements>
- **Framework**: PyQt6 with modern Qt features
- **Architecture**: MVC pattern with signal/slot communication
- **Threading**: QThread for background operations
- **Styling**: QSS (Qt Style Sheets) for modern appearance
- **Compatibility**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.9+ compatibility
- **Integration**: Seamless integration with existing CLI backend
- **Future-Proofing**: Design with future web interface in mind
</technical_requirements>

### <user_experience_requirements>
- **Professional Appearance**: Native OS integration with modern design
- **Intuitive Navigation**: Clear workflow with visual feedback
- **Responsive Interface**: Smooth interactions and animations
- **Accessibility**: Keyboard navigation, screen reader support
- **Error Handling**: User-friendly error messages with recovery options
- **Help System**: Integrated documentation and tooltips
</user_experience_requirements>

</requirements>

## <architecture>

### <design_principles>
- **Separation of Concerns**: Clear separation between UI, business logic, and data
- **API-First Design**: Structure for future web interface compatibility
- **Modular Components**: Reusable widgets and services
- **Event-Driven**: Qt signal/slot system for loose coupling
- **Testable**: Unit testable components with mock interfaces
</design_principles>

### <package_structure>
```
src/metadata_multitool/gui_qt/
├── __init__.py
├── main.py                     # Application entry point
├── main_window.py              # Main application window
├── models/                     # Data models and business logic
│   ├── __init__.py
│   ├── file_model.py          # File management with Qt models
│   ├── operation_model.py     # Operation state and progress
│   ├── config_model.py        # Configuration management
│   └── metadata_model.py      # Metadata handling and display
├── views/                      # UI components and widgets
│   ├── __init__.py
│   ├── main_view.py           # Main interface layout
│   ├── file_panel.py          # File selection and management
│   ├── operation_panels/      # Mode-specific operation interfaces
│   │   ├── __init__.py
│   │   ├── clean_panel.py     # Clean mode interface
│   │   ├── poison_panel.py    # Poison mode interface
│   │   └── revert_panel.py    # Revert mode interface
│   ├── settings_dialog.py     # Settings configuration
│   ├── progress_widget.py     # Progress tracking and display
│   └── common/                # Reusable UI components
│       ├── __init__.py
│       ├── file_tree.py       # Enhanced file tree widget
│       ├── metadata_viewer.py # Metadata display widget
│       ├── filter_widget.py   # File filtering interface
│       └── theme_manager.py   # Theme and styling management
├── controllers/                # Business logic controllers
│   ├── __init__.py
│   ├── main_controller.py     # Main application controller
│   ├── file_controller.py     # File operations coordinator
│   ├── operation_controller.py # Operation execution manager
│   └── settings_controller.py # Settings management
├── services/                   # Backend integration services
│   ├── __init__.py
│   ├── cli_service.py         # CLI backend integration
│   ├── metadata_service.py    # Metadata operations
│   ├── file_service.py        # File system operations
│   └── config_service.py      # Configuration persistence
├── utils/                      # Utility functions and helpers
│   ├── __init__.py
│   ├── threading.py           # Background processing utilities
│   ├── dialogs.py             # Custom dialog utilities
│   ├── validators.py          # Input validation
│   ├── formatters.py          # Data formatting utilities
│   └── icons.py               # Icon and resource management
├── resources/                  # Resources and assets
│   ├── icons/                 # Application icons
│   ├── styles/                # QSS theme files
│   │   ├── light_theme.qss
│   │   └── dark_theme.qss
│   └── images/                # UI images and graphics
└── tests/                      # PyQt6-specific tests
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    ├── test_controllers.py
    └── test_services.py
```
</package_structure>

### <core_components>

#### <main_window>
**File**: `main_window.py`
**Purpose**: Central application window with modern layout
**Features**:
- Menu bar with standard File/Edit/View/Help menus
- Toolbar with mode switching and common actions
- Dockable panels for flexible layout
- Status bar with operation indicators
- Recent files and session management
</main_window>

#### <file_panel>
**File**: `views/file_panel.py`
**Purpose**: Comprehensive file management interface
**Features**:
- Tree view with folder navigation
- Drag & drop file addition
- File list with thumbnails and metadata preview
- Advanced filtering (size, date, format, metadata presence)
- Batch selection tools
- Context menus for file operations
</file_panel>

#### <operation_panels>
**Files**: `views/operation_panels/*.py`
**Purpose**: Mode-specific operation interfaces

**Clean Panel**:
- Output folder selection with path validation
- File filtering options with live preview
- Processing settings (batch size, workers)
- Backup and safety options

**Poison Panel**:
- Visual preset selection with descriptions
- Output format checkboxes with tooltips
- CSV mapping file integration
- Rename pattern builder with preview
- True hint input with validation

**Revert Panel**:
- Directory selection with validation
- File list showing what will be reverted
- Safety confirmation with detailed preview
- Selective revert options
</operation_panels>

#### <metadata_viewer>
**File**: `views/common/metadata_viewer.py`
**Purpose**: Rich metadata display and editing
**Features**:
- Tabbed interface for EXIF/IPTC/XMP data
- Editable fields with validation
- Before/after comparison view
- Export capabilities
</metadata_viewer>

#### <progress_widget>
**File**: `views/progress_widget.py`
**Purpose**: Advanced progress tracking
**Features**:
- Multi-level progress bars (overall + current file)
- Operation status with ETA
- Cancel and pause functionality
- Operation history and logs
</progress_widget>

</core_components>

</architecture>

## <implementation_details>

### <backend_integration>
**Service Layer**: Create abstraction layer for CLI backend integration
```python
# services/cli_service.py
class CLIService(QObject):
    """Service for integrating with CLI backend operations."""
    
    progress_updated = pyqtSignal(int, int)  # current, total
    operation_completed = pyqtSignal(bool, str)  # success, message
    
    def clean_files(self, files: List[Path], options: CleanOptions) -> None:
        """Execute clean operation in background thread."""
        
    def poison_files(self, files: List[Path], options: PoisonOptions) -> None:
        """Execute poison operation in background thread."""
        
    def revert_directory(self, directory: Path) -> None:
        """Execute revert operation in background thread."""
```
</backend_integration>

### <data_models>
**Qt Model Integration**: Use Qt's model/view framework
```python
# models/file_model.py
class FileModel(QAbstractTableModel):
    """Qt model for file list display and management."""
    
    def __init__(self):
        super().__init__()
        self.files: List[FileInfo] = []
        
    def add_files(self, paths: List[Path]) -> None:
        """Add files with metadata loading."""
        
    def get_filtered_files(self, filters: FileFilters) -> List[Path]:
        """Apply filters and return matching files."""

# models/metadata_model.py  
class MetadataModel(QAbstractItemModel):
    """Qt model for metadata tree display."""
    
    def load_metadata(self, file_path: Path) -> None:
        """Load and parse metadata for display."""
```
</data_models>

### <threading_implementation>
**Background Operations**: Use QThread for non-blocking operations
```python
# utils/threading.py
class OperationWorker(QObject):
    """Worker for background operations."""
    
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, operation_func, *args, **kwargs):
        super().__init__()
        self.operation_func = operation_func
        self.args = args
        self.kwargs = kwargs
        
    @pyqtSlot()
    def run(self):
        """Execute operation in background thread."""
        try:
            result = self.operation_func(*self.args, **self.kwargs)
            self.finished.emit(True, "Operation completed successfully")
        except Exception as e:
            self.finished.emit(False, str(e))

class OperationManager(QObject):
    """Manages background operations with Qt threading."""
    
    def start_operation(self, operation_func, *args, **kwargs):
        """Start operation in background thread."""
        worker = OperationWorker(operation_func, *args, **kwargs)
        thread = QThread()
        
        worker.moveToThread(thread)
        worker.progress.connect(self.progress_updated)
        worker.finished.connect(self.operation_finished)
        
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        thread.start()
```
</threading_implementation>

### <styling_system>
**Theme Management**: Comprehensive theming with QSS
```python
# views/common/theme_manager.py
class ThemeManager(QObject):
    """Manages application themes and styling."""
    
    theme_changed = pyqtSignal(str)  # theme_name
    
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.themes = {
            "light": "resources/styles/light_theme.qss",
            "dark": "resources/styles/dark_theme.qss"
        }
        
    def apply_theme(self, theme_name: str) -> None:
        """Apply theme to application."""
        
    def detect_system_theme(self) -> str:
        """Detect system theme preference."""
```

**QSS Styling**: Modern appearance with CSS-like styling
```css
/* resources/styles/light_theme.qss */
QMainWindow {
    background-color: #f5f5f5;
    color: #333333;
}

QToolBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #ffffff, stop:1 #e8e8e8);
    border: 1px solid #c0c0c0;
    spacing: 4px;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 6px 16px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #e8f4fd;
    border-color: #0078d4;
}

QPushButton:pressed {
    background-color: #005a9e;
    color: white;
}
```
</styling_system>

</implementation_details>

## <user_interface_design>

### <main_layout>
**Window Structure**:
```
┌─────────────────────────────────────────────────────────────┐
│ Menu Bar: File Edit View Tools Help                        │
├─────────────────────────────────────────────────────────────┤
│ Toolbar: [Clean] [Poison] [Revert] | [Settings] [Help]     │
├─────────────────────────────────────┬───────────────────────┤
│ File Panel (Dockable)              │ Operation Panel       │
│ ┌─────────────────────────────────┐ │ ┌─────────────────────┐ │
│ │ 📁 Folder Tree                  │ │ │ Mode-Specific       │ │
│ │   └── Documents/                │ │ │ Options and         │ │
│ │       ├── Images/              │ │ │ Controls            │ │
│ │       └── Photos/              │ │ │                     │ │
│ ├─────────────────────────────────┤ │ │                     │ │
│ │ 📋 File List                    │ │ │                     │ │
│ │ ☑ image1.jpg    [2.1MB] [🔍]   │ │ │                     │ │
│ │ ☑ image2.png    [1.8MB] [🔍]   │ │ │                     │ │
│ │ ☑ image3.tiff   [5.2MB] [🔍]   │ │ │                     │ │
│ └─────────────────────────────────┘ │ └─────────────────────┘ │
├─────────────────────────────────────┼───────────────────────┤
│ Metadata Viewer (Dockable)          │ Preview Panel         │
│ ┌─────────────────────────────────┐ │ ┌─────────────────────┐ │
│ │ [EXIF] [IPTC] [XMP]             │ │ │ 🖼️ Image Preview    │ │
│ │ Camera: Canon EOS R5            │ │ │                     │ │
│ │ Lens: 24-70mm f/2.8             │ │ │   [Thumbnail]       │ │
│ │ ISO: 800                        │ │ │                     │ │
│ │ Aperture: f/5.6                 │ │ │ Metadata Status:    │ │
│ │ Shutter: 1/125s                 │ │ │ ✅ EXIF Present     │ │
│ └─────────────────────────────────┘ │ │ ✅ IPTC Present     │ │
├─────────────────────────────────────┴───────────────────────┤
│ Progress Panel: ████████████████████ 75% (15/20) Processing │
│ [Cancel] [Pause] Current: image15.jpg → safe_upload/        │
├─────────────────────────────────────────────────────────────┤
│ Status Bar: Ready | 20 files selected | Theme: Light        │
└─────────────────────────────────────────────────────────────┘
```
</main_layout>

### <workflow_design>
**User Journey**:
1. **File Selection**: Drag & drop or browse files/folders
2. **Mode Selection**: Choose Clean/Poison/Revert from toolbar
3. **Configuration**: Set options in operation panel
4. **Preview**: Review files and settings
5. **Execution**: Run operation with real-time progress
6. **Review**: Check results and handle any errors
</workflow_design>

### <interaction_patterns>
- **Drag & Drop**: Files, folders, and CSV mappings
- **Context Menus**: Right-click for file operations
- **Keyboard Shortcuts**: Full keyboard navigation
- **Tool Tips**: Contextual help for all controls
- **Visual Feedback**: Hover states, progress indicators
- **Error Handling**: Inline validation and clear error messages
</interaction_patterns>

</user_interface_design>

## <development_phases>

### <phase_1_foundation>
**Duration**: 1-2 weeks
**Deliverables**:
- Project setup with PyQt6 dependencies
- Basic main window with menu and toolbar
- Theme system with light/dark themes
- File model with basic operations
- CLI service integration layer

**Key Files**:
- `main.py` - Application entry point
- `main_window.py` - Main window structure
- `theme_manager.py` - Theme system
- `file_model.py` - File management model
- `cli_service.py` - Backend integration
</phase_1_foundation>

### <phase_2_core_interface>
**Duration**: 2-3 weeks
**Deliverables**:
- File panel with tree view and file list
- Operation panels for all three modes
- Progress tracking widget
- Settings dialog
- Basic operation execution

**Key Files**:
- `file_panel.py` - File management interface
- `clean_panel.py`, `poison_panel.py`, `revert_panel.py`
- `progress_widget.py` - Progress tracking
- `settings_dialog.py` - Configuration interface
</phase_2_core_interface>

### <phase_3_advanced_features>
**Duration**: 1-2 weeks
**Deliverables**:
- Metadata viewer with editing capabilities
- Drag & drop functionality
- Keyboard shortcuts and accessibility
- Enhanced error handling
- Operation history

**Key Files**:
- `metadata_viewer.py` - Metadata display and editing
- `file_tree.py` - Enhanced file tree widget
- `dialogs.py` - Custom dialog utilities
</phase_3_advanced_features>

### <phase_4_polish_and_testing>
**Duration**: 1 week
**Deliverables**:
- Comprehensive testing suite
- Performance optimization
- UI polish and animations
- Documentation and help system
- Packaging for distribution

**Key Files**:
- Complete test suite
- Performance profiling
- User documentation
- Packaging scripts
</phase_4_polish_and_testing>

</development_phases>

## <testing_strategy>

### <unit_testing>
```python
# tests/test_models.py
class TestFileModel(QTestCase):
    def test_add_files(self):
        """Test file addition and metadata loading."""
        
    def test_file_filtering(self):
        """Test file filtering functionality."""

# tests/test_services.py
class TestCLIService(QTestCase):
    def test_clean_operation(self):
        """Test clean operation integration."""
        
    def test_poison_operation(self):
        """Test poison operation integration."""
```
</unit_testing>

### <integration_testing>
- **CLI Backend Integration**: Test all operation modes
- **File System Operations**: Test file handling and permissions
- **Threading**: Test background operations and cancellation
- **UI Responsiveness**: Test interface under load
</integration_testing>

### <user_acceptance_testing>
- **Workflow Testing**: Complete user scenarios
- **Accessibility Testing**: Keyboard navigation and screen readers
- **Performance Testing**: Large file sets and batch operations
- **Cross-Platform Testing**: Windows, macOS, and Linux
</user_acceptance_testing>

</testing_strategy>

## <deployment_and_packaging>

### <dependencies>
```python
# requirements.txt
PyQt6>=6.5.0
PyQt6-Qt6>=6.5.0
Pillow>=10.0.0
# ... existing CLI dependencies
```
</dependencies>

### <packaging>
```python
# setup.py additions
entry_points={
    'console_scripts': [
        'mm=metadata_multitool.cli:main',
        'mm-gui=metadata_multitool.gui_qt.main:main',
    ],
}
```

**Distribution**:
- **PyInstaller**: Create standalone executables
- **Windows**: MSI installer with Qt runtime
- **macOS**: DMG package with app bundle
- **Linux**: AppImage or distribution packages
</packaging>

</deployment_and_packaging>

## <future_compatibility>

### <api_design>
Design the PyQt6 implementation with future web interface in mind:

**Service Layer Abstraction**:
```python
# services/operation_service.py
class OperationService(ABC):
    """Abstract service for operations - can be implemented for both Qt and web."""
    
    @abstractmethod
    def execute_clean(self, files: List[Path], options: CleanOptions) -> OperationResult:
        pass
        
    @abstractmethod
    def execute_poison(self, files: List[Path], options: PoisonOptions) -> OperationResult:
        pass
```

**Configuration Schema**:
- Use JSON Schema for configuration validation
- Ensure settings translate between desktop and web versions
- Maintain backward compatibility

**Data Models**:
- Design models that can serialize to JSON for web API
- Use standardized data types and formats
- Implement clean interfaces for data access
</api_design>

### <modular_architecture>
Structure components for reusability:
- **Business Logic**: Separate from UI components
- **Configuration**: Environment-agnostic settings management
- **File Operations**: Abstract file handling for different contexts
- **Progress Tracking**: Generic progress interfaces
</modular_architecture>

</future_compatibility>

## <success_criteria>

### <functional_requirements_checklist>
- [ ] All CLI functionality available in GUI
- [ ] Drag & drop file selection works
- [ ] All three operation modes functional
- [ ] Real-time progress tracking
- [ ] Settings persistence and management
- [ ] Error handling with user feedback
- [ ] Keyboard shortcuts and accessibility
- [ ] Theme switching (light/dark)
- [ ] Cross-platform compatibility
</functional_requirements_checklist>

### <quality_requirements_checklist>
- [ ] Professional, native appearance
- [ ] Responsive interface (no blocking operations)
- [ ] Comprehensive test coverage (>90%)
- [ ] Memory efficient with large file sets
- [ ] Fast startup time (<2 seconds)
- [ ] Proper error recovery
- [ ] User documentation complete
- [ ] Code documentation and comments
</quality_requirements_checklist>

### <user_experience_checklist>
- [ ] Intuitive workflow for non-technical users
- [ ] Clear visual feedback for all operations
- [ ] Consistent UI patterns throughout
- [ ] Helpful error messages with solutions
- [ ] Efficient keyboard navigation
- [ ] Accessible design for screen readers
- [ ] Professional visual design
- [ ] Smooth animations and transitions
</user_experience_checklist>

</success_criteria>

## <getting_started>

### <development_setup>
1. **Install Dependencies**:
   ```bash
   pip install PyQt6 PyQt6-tools
   pip install -e .[dev]  # Install project in development mode
   ```

2. **IDE Configuration**:
   - Use Qt Designer for complex layouts
   - Configure Qt Creator for debugging
   - Set up pytest-qt for GUI testing

3. **Project Structure**:
   ```bash
   mkdir -p src/metadata_multitool/gui_qt/{models,views,controllers,services,utils,resources,tests}
   ```

4. **First Implementation**:
   - Start with `main.py` and basic window
   - Implement theme system early
   - Create file model with sample data
   - Build basic file panel interface
</development_setup>

### <development_workflow>
1. **Feature Development**: Implement in feature branches
2. **Testing**: Write tests for each component
3. **Integration**: Test with existing CLI backend
4. **Review**: Code review for architecture consistency
5. **Documentation**: Update docs with each feature
</development_workflow>

</getting_started>

This implementation will deliver a modern, professional desktop GUI that significantly enhances the user experience while maintaining the powerful functionality of the CLI tool. The modular architecture ensures it can serve as a foundation for future web interface development.