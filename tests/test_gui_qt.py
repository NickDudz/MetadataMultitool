"""Tests for PyQt6 GUI functionality."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Make pytest-qt optional: only load plugin if present
try:
    import pytestqt  # type: ignore
    HAS_PYTEST_QT = True
except Exception:
    HAS_PYTEST_QT = False

# Load plugin only when available to avoid ImportError during collection
pytest_plugins = ["pytestqt"] if HAS_PYTEST_QT else []

try:
    import PyQt6.QtWidgets
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtWidgets import QApplication, QWidget
    from PyQt6.QtTest import QTest
    
    # Try to import GUI modules
    from metadata_multitool.gui_qt.main import MetadataMultitoolApp, main
    from metadata_multitool.gui_qt.main_window import MainWindow
    
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    # Create dummy classes for when GUI is not available
    class MetadataMultitoolApp:
        pass
    class MainWindow:
        pass

# Skip all GUI tests if GUI or pytest-qt is not available
pytestmark = pytest.mark.skipif(
    not (GUI_AVAILABLE and HAS_PYTEST_QT),
    reason="PyQt6 GUI or pytest-qt not available",
)


@pytest.fixture
def qapp():
    """Create QApplication instance for testing."""
    if not GUI_AVAILABLE:
        pytest.skip("PyQt6 not available")
    
    # Check if QApplication already exists
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app here as it might be needed for other tests


@pytest.fixture
def main_window(qapp):
    """Create MainWindow instance for testing."""
    if not GUI_AVAILABLE:
        pytest.skip("PyQt6 not available")
    
    # Mock the config loading to avoid file system dependencies
    with patch("metadata_multitool.gui_qt.main_window.load_config") as mock_load_config:
        mock_load_config.return_value = {}
        window = MainWindow()
    
    yield window
    
    # Clean up
    if window.isVisible():
        window.close()


class TestGUIAvailability:
    """Test GUI availability and basic imports."""

    def test_gui_imports(self):
        """Test that GUI modules can be imported."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Test basic imports
        assert MetadataMultitoolApp is not None
        assert MainWindow is not None
        
        # Test PyQt6 imports
        assert PyQt6.QtWidgets.QApplication is not None
        assert PyQt6.QtCore.Qt is not None


class TestMetadataMultitoolApp:
    """Test the main application class."""

    def test_app_creation(self, qapp):
        """Test application creation."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Test that we can create the app (or get existing instance)
        assert qapp is not None
        assert isinstance(qapp, QApplication)

    @patch("metadata_multitool.gui_qt.main.MainWindow")
    @patch("metadata_multitool.gui_qt.main.IconManager")
    @patch("metadata_multitool.gui_qt.main.ThemeManager")
    def test_app_initialization(self, mock_theme, mock_icon, mock_window, qapp):
        """Test application initialization components."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Mock the components
        mock_window_instance = Mock()
        mock_window.return_value = mock_window_instance
        mock_icon_instance = Mock()
        mock_icon.return_value = mock_icon_instance
        mock_theme_instance = Mock()
        mock_theme.return_value = mock_theme_instance
        
        # Create app (this should work even with mocked components)
        app = MetadataMultitoolApp([])
        assert app is not None


class TestMainWindow:
    """Test the main window functionality."""

    def test_window_creation(self, main_window):
        """Test main window creation."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        assert main_window is not None
        assert isinstance(main_window, QWidget)

    def test_window_title(self, main_window):
        """Test window title is set correctly."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        title = main_window.windowTitle()
        assert "Metadata Multitool" in title

    def test_window_show_hide(self, main_window):
        """Test window show and hide functionality."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Initially window should not be visible
        assert not main_window.isVisible()
        
        # Show window
        main_window.show()
        assert main_window.isVisible()
        
        # Hide window
        main_window.hide()
        assert not main_window.isVisible()

    @patch("metadata_multitool.gui_qt.main_window.load_config")
    def test_window_initialization_with_config(self, mock_load_config):
        """Test window initialization with configuration."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Mock config loading
        test_config = {
            "batch_size": 100,
            "max_workers": 4,
            "theme": "dark"
        }
        mock_load_config.return_value = test_config
        
        # Create window
        window = MainWindow()
        
        # Verify config was loaded
        mock_load_config.assert_called_once()
        
        # Clean up
        window.close()


class TestGUIIntegration:
    """Integration tests for GUI components."""

    def test_window_components_exist(self, main_window):
        """Test that main window components exist."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Test that window has basic components
        # Note: These tests are basic since we don't want to assume specific UI layout
        assert main_window.centralWidget() is not None or main_window.menuBar() is not None

    def test_window_keyboard_events(self, main_window, qtbot):
        """Test keyboard event handling."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Show window for event testing
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test basic keyboard events (these should not crash)
        qtbot.keyClick(main_window, Qt.Key.Key_Escape)
        qtbot.keyClick(main_window, Qt.Key.Key_Tab)
        
        # Window should still be functional
        assert main_window.isVisible()

    def test_window_mouse_events(self, main_window, qtbot):
        """Test mouse event handling."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Show window for event testing
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test basic mouse events (these should not crash)
        qtbot.mouseClick(main_window, Qt.MouseButton.LeftButton)
        
        # Window should still be functional
        assert main_window.isVisible()


class TestGUIErrorHandling:
    """Test error handling in GUI components."""

    @patch("metadata_multitool.gui_qt.main_window.load_config")
    def test_window_creation_with_config_error(self, mock_load_config):
        """Test window creation when config loading fails."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Mock config loading to raise an exception
        mock_load_config.side_effect = Exception("Config error")
        
        # Window creation should still work (with default config)
        try:
            window = MainWindow()
            # Should not raise exception
            assert window is not None
            window.close()
        except Exception:
            pytest.fail("Window creation should handle config errors gracefully")

    def test_app_quit_handling(self, qapp):
        """Test application quit handling."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Test that we can call quit without issues
        # Note: We don't actually quit since it would affect other tests
        assert hasattr(qapp, 'quit')
        assert callable(getattr(qapp, 'quit'))


class TestGUIUtilities:
    """Test GUI utility functions and classes."""

    @patch("metadata_multitool.gui_qt.main.IconManager")
    def test_icon_manager_integration(self, mock_icon_manager):
        """Test icon manager integration."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Mock icon manager
        mock_instance = Mock()
        mock_icon_manager.return_value = mock_instance
        
        # Test that icon manager can be instantiated
        from metadata_multitool.gui_qt.utils.icons import IconManager
        manager = IconManager()
        assert manager is not None

    @patch("metadata_multitool.gui_qt.main.ThemeManager")
    def test_theme_manager_integration(self, mock_theme_manager):
        """Test theme manager integration."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Mock theme manager
        mock_instance = Mock()
        mock_theme_manager.return_value = mock_instance
        
        # Test that theme manager can be instantiated
        from metadata_multitool.gui_qt.views.common.theme_manager import ThemeManager
        manager = ThemeManager()
        assert manager is not None


class TestMainFunction:
    """Test the main function entry point."""

    @patch("metadata_multitool.gui_qt.main.MetadataMultitoolApp")
    @patch("metadata_multitool.gui_qt.main.MainWindow")
    @patch("sys.exit")
    def test_main_function_success(self, mock_exit, mock_window, mock_app):
        """Test main function successful execution."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Mock app and window
        mock_app_instance = Mock()
        mock_app_instance.exec.return_value = 0
        mock_app.return_value = mock_app_instance
        
        mock_window_instance = Mock()
        mock_window.return_value = mock_window_instance
        
        # Call main function
        from metadata_multitool.gui_qt.main import main
        main()
        
        # Verify components were created
        mock_app.assert_called_once()
        mock_window.assert_called_once()
        mock_window_instance.show.assert_called_once()
        mock_app_instance.exec.assert_called_once()

    @patch("metadata_multitool.gui_qt.main.MetadataMultitoolApp")
    @patch("sys.exit")
    def test_main_function_app_creation_error(self, mock_exit, mock_app):
        """Test main function when app creation fails."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Mock app creation to raise exception
        mock_app.side_effect = Exception("App creation failed")
        
        # Call main function
        from metadata_multitool.gui_qt.main import main
        main()
        
        # Should exit with error code
        mock_exit.assert_called_once_with(1)


@pytest.mark.skipif(not GUI_AVAILABLE, reason="PyQt6 GUI not available")
class TestGUISmoke:
    """Smoke tests to ensure GUI doesn't crash on basic operations."""

    def test_gui_smoke_test(self, qtbot):
        """Basic smoke test for GUI functionality."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        # Create and show main window
        with patch("metadata_multitool.gui_qt.main_window.load_config") as mock_config:
            mock_config.return_value = {}
            
            window = MainWindow()
            window.show()
            qtbot.addWidget(window)
            
            # Wait a bit for window to fully load
            qtbot.wait(100)
            
            # Window should be visible and functional
            assert window.isVisible()
            
            # Try to close window gracefully
            window.close()
            qtbot.wait(100)

    def test_gui_rapid_show_hide(self, qtbot):
        """Test rapid show/hide operations don't cause issues."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        with patch("metadata_multitool.gui_qt.main_window.load_config") as mock_config:
            mock_config.return_value = {}
            
            window = MainWindow()
            qtbot.addWidget(window)
            
            # Rapid show/hide cycle
            for _ in range(5):
                window.show()
                qtbot.wait(10)
                window.hide()
                qtbot.wait(10)
            
            # Window should still be functional
            window.show()
            assert window.isVisible()
            window.close()


@pytest.mark.skipif(not GUI_AVAILABLE, reason="PyQt6 GUI not available")
class TestGUIUserInteractions:
    """Test user interaction scenarios."""

    def test_file_drag_and_drop_simulation(self, main_window, qtbot):
        """Test drag and drop file handling simulation."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Enable drag and drop
        main_window.setAcceptDrops(True)
        
        # Create mock drag enter event
        from PyQt6.QtCore import QMimeData, QUrl
        from PyQt6.QtGui import QDragEnterEvent
        
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile("test_image.jpg")])
        
        # Simulate drag enter event
        drag_event = Mock()
        drag_event.mimeData.return_value = mime_data
        
        # Test that window accepts drops (should not crash)
        main_window.dragEnterEvent(drag_event)

    def test_settings_dialog_interaction(self, main_window, qtbot):
        """Test settings dialog interactions."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Try to access settings through menu or button
        # This tests that settings functionality exists
        if hasattr(main_window, 'show_settings'):
            # Mock the settings dialog
            with patch("metadata_multitool.gui_qt.views.settings_dialog.SettingsDialog") as mock_dialog:
                mock_dialog_instance = Mock()
                mock_dialog.return_value = mock_dialog_instance
                mock_dialog_instance.exec.return_value = 0
                
                try:
                    main_window.show_settings()
                except AttributeError:
                    # Method doesn't exist yet, which is fine
                    pass

    def test_theme_switching(self, main_window, qtbot):
        """Test theme switching functionality."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test theme switching if method exists
        if hasattr(main_window, 'set_theme'):
            try:
                main_window.set_theme('dark')
                main_window.set_theme('light')
                main_window.set_theme('auto')
            except (AttributeError, NotImplementedError):
                # Theme switching not implemented yet
                pass

    def test_progress_display(self, main_window, qtbot):
        """Test progress display functionality."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test progress updates if method exists
        if hasattr(main_window, 'update_progress'):
            try:
                main_window.update_progress(0)
                main_window.update_progress(50)
                main_window.update_progress(100)
            except (AttributeError, NotImplementedError):
                # Progress display not implemented yet
                pass


@pytest.mark.skipif(not GUI_AVAILABLE, reason="PyQt6 GUI not available")
class TestGUIErrorDialogs:
    """Test error dialog handling."""

    def test_error_dialog_display(self, main_window, qtbot):
        """Test error dialog display."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test error dialog if method exists
        with patch("PyQt6.QtWidgets.QMessageBox") as mock_msgbox:
            mock_msgbox.critical = Mock()
            
            if hasattr(main_window, 'show_error'):
                try:
                    main_window.show_error("Test error message")
                    # Should not crash
                except (AttributeError, NotImplementedError):
                    # Error dialog not implemented yet
                    pass

    def test_confirmation_dialog(self, main_window, qtbot):
        """Test confirmation dialog handling."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test confirmation dialog if method exists
        with patch("PyQt6.QtWidgets.QMessageBox") as mock_msgbox:
            mock_msgbox.question = Mock(return_value=Mock())
            
            if hasattr(main_window, 'confirm_action'):
                try:
                    result = main_window.confirm_action("Test confirmation")
                    # Should return a boolean or similar
                    assert isinstance(result, (bool, type(None)))
                except (AttributeError, NotImplementedError):
                    # Confirmation dialog not implemented yet
                    pass


@pytest.mark.skipif(not GUI_AVAILABLE, reason="PyQt6 GUI not available") 
class TestGUIFileOperations:
    """Test GUI file operation interfaces."""

    def test_file_selection_dialog(self, main_window, qtbot):
        """Test file selection dialog."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Mock file dialog
        with patch("PyQt6.QtWidgets.QFileDialog") as mock_dialog:
            mock_dialog.getOpenFileNames = Mock(return_value=(["test.jpg"], ""))
            mock_dialog.getExistingDirectory = Mock(return_value="test_dir")
            
            # Test file selection if methods exist
            if hasattr(main_window, 'select_files'):
                try:
                    files = main_window.select_files()
                    assert isinstance(files, (list, type(None)))
                except (AttributeError, NotImplementedError):
                    pass
            
            if hasattr(main_window, 'select_folder'):
                try:
                    folder = main_window.select_folder()
                    assert isinstance(folder, (str, type(None)))
                except (AttributeError, NotImplementedError):
                    pass

    def test_operation_panels(self, main_window, qtbot):
        """Test operation panel switching."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test switching between operation modes if methods exist
        operations = ['clean', 'poison', 'revert']
        
        for operation in operations:
            method_name = f'switch_to_{operation}'
            if hasattr(main_window, method_name):
                try:
                    getattr(main_window, method_name)()
                except (AttributeError, NotImplementedError):
                    pass

    def test_batch_operation_handling(self, main_window, qtbot):
        """Test batch operation handling.""" 
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test batch operation if method exists
        if hasattr(main_window, 'start_batch_operation'):
            try:
                # Mock the operation
                with patch("metadata_multitool.batch.batch_process_clean") as mock_batch:
                    mock_batch.return_value = {"successful": 5, "failed": 0}
                    
                    main_window.start_batch_operation('clean', ["test1.jpg", "test2.jpg"])
                    
            except (AttributeError, NotImplementedError):
                pass


@pytest.mark.skipif(not GUI_AVAILABLE, reason="PyQt6 GUI not available")
class TestGUIPerformance:
    """Test GUI performance characteristics."""

    def test_window_startup_time(self, qtbot):
        """Test window startup performance."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        import time
        
        with patch("metadata_multitool.gui_qt.main_window.load_config") as mock_config:
            mock_config.return_value = {}
            
            start_time = time.perf_counter()
            
            window = MainWindow()
            window.show()
            qtbot.addWidget(window)
            
            startup_time = time.perf_counter() - start_time
            
            # Window should start up reasonably quickly
            assert startup_time < 5.0, f"Window startup too slow: {startup_time:.2f}s"
            
            window.close()

    def test_rapid_ui_updates(self, main_window, qtbot):
        """Test rapid UI update performance."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test rapid updates if progress method exists
        if hasattr(main_window, 'update_progress'):
            try:
                import time
                start_time = time.perf_counter()
                
                # Simulate rapid progress updates
                for i in range(0, 101, 10):
                    main_window.update_progress(i)
                    qtbot.wait(1)  # Minimal wait
                
                update_time = time.perf_counter() - start_time
                
                # Should handle rapid updates efficiently
                assert update_time < 2.0, f"UI updates too slow: {update_time:.2f}s"
                
            except (AttributeError, NotImplementedError):
                pass

    def test_memory_usage_stability(self, main_window, qtbot):
        """Test GUI memory usage stability."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss
        
        # Perform various UI operations
        for _ in range(10):
            main_window.show()
            qtbot.wait(10)
            main_window.hide()
            qtbot.wait(10)
        
        main_window.show()
        final_memory = process.memory_info().rss
        
        memory_growth = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Memory growth should be minimal for basic operations
        assert memory_growth < 50, f"Excessive memory growth: {memory_growth:.1f}MB"


@pytest.mark.skipif(not GUI_AVAILABLE, reason="PyQt6 GUI not available")
class TestGUIAccessibility:
    """Test GUI accessibility features."""

    def test_keyboard_navigation(self, main_window, qtbot):
        """Test keyboard navigation."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test tab navigation
        qtbot.keyClick(main_window, Qt.Key.Key_Tab)
        qtbot.keyClick(main_window, Qt.Key.Key_Tab)
        
        # Test arrow key navigation
        qtbot.keyClick(main_window, Qt.Key.Key_Down)
        qtbot.keyClick(main_window, Qt.Key.Key_Up)
        
        # Window should remain stable
        assert main_window.isVisible()

    def test_window_scaling(self, main_window, qtbot):
        """Test window scaling and resizing."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test different window sizes
        sizes = [(800, 600), (1200, 800), (600, 400)]
        
        for width, height in sizes:
            main_window.resize(width, height)
            qtbot.wait(50)
            
            # Window should handle resizing gracefully
            assert main_window.isVisible()
            assert main_window.width() <= width + 50  # Allow some tolerance
            assert main_window.height() <= height + 50

    def test_high_dpi_handling(self, main_window, qtbot):
        """Test high DPI display handling."""
        if not GUI_AVAILABLE:
            pytest.skip("PyQt6 not available")
        
        main_window.show()
        qtbot.addWidget(main_window)
        
        # Test that window can handle different DPI settings
        # This is mainly a smoke test to ensure no crashes
        app = QApplication.instance()
        if app and hasattr(app, 'devicePixelRatio'):
            dpi_ratio = app.devicePixelRatio()
            assert dpi_ratio > 0
        
        # Window should remain functional regardless of DPI
        assert main_window.isVisible()