"""Tests for GUI functionality."""

import pytest
import tkinter as tk
from pathlib import Path
from unittest.mock import Mock, patch

from metadata_multitool.gui.main_window import MainWindow
from metadata_multitool.gui.models.file_model import FileModel
from metadata_multitool.gui.models.config_model import ConfigModel
from metadata_multitool.gui.models.operation_model import OperationModel


class TestFileModel:
    """Test FileModel functionality."""

    def test_add_files(self):
        """Test adding files to the model."""
        model = FileModel()
        test_files = [Path("test1.jpg"), Path("test2.png")]

        model.add_files(test_files)

        assert len(model.get_files()) == 2
        assert Path("test1.jpg") in model.get_files()
        assert Path("test2.png") in model.get_files()

    def test_remove_file(self):
        """Test removing a file from the model."""
        model = FileModel()
        test_files = [Path("test1.jpg"), Path("test2.png")]

        model.add_files(test_files)
        model.remove_file(Path("test1.jpg"))

        assert len(model.get_files()) == 1
        assert Path("test1.jpg") not in model.get_files()
        assert Path("test2.png") in model.get_files()

    def test_clear_files(self):
        """Test clearing all files from the model."""
        model = FileModel()
        test_files = [Path("test1.jpg"), Path("test2.png")]

        model.add_files(test_files)
        model.clear_files()

        assert len(model.get_files()) == 0

    def test_filter_files(self):
        """Test filtering files."""
        model = FileModel()
        test_files = [Path("test1.jpg"), Path("test2.png"), Path("test3.txt")]

        model.add_files(test_files)

        # Filter by extension
        filtered = model.filter_files(extensions=[".jpg", ".png"])
        assert len(filtered) == 2
        assert Path("test1.jpg") in filtered
        assert Path("test2.png") in filtered
        assert Path("test3.txt") not in filtered


class TestConfigModel:
    """Test ConfigModel functionality."""

    def test_get_set_value(self):
        """Test getting and setting configuration values."""
        config = {"test_key": "test_value"}
        model = ConfigModel(config)

        assert model.get_value("test_key") == "test_value"
        assert model.get_value("missing_key", "default") == "default"

        model.set_value("new_key", "new_value")
        assert model.get_value("new_key") == "new_value"

    def test_gui_settings(self):
        """Test GUI-specific settings."""
        config = {}
        model = ConfigModel(config)

        model.set_gui_setting("theme", "dark")
        assert model.get_gui_setting("theme") == "dark"
        assert model.get_gui_setting("missing", "light") == "light"

    def test_batch_settings(self):
        """Test batch processing settings."""
        config = {"batch_size": 50, "max_workers": 2}
        model = ConfigModel(config)

        batch_settings = model.get_batch_settings()
        assert batch_settings["batch_size"] == 50
        assert batch_settings["max_workers"] == 2


class TestOperationModel:
    """Test OperationModel functionality."""

    def test_start_operation(self):
        """Test starting an operation."""
        model = OperationModel()

        model.start_operation(10, "test_operation")

        assert model.total_files == 10
        assert model.processed_files == 0
        assert model.progress == 0.0

    def test_update_progress(self):
        """Test updating operation progress."""
        model = OperationModel()
        model.start_operation(10, "test_operation")

        model.update_progress(5, "test_file.jpg")

        assert model.processed_files == 5
        assert model.progress == 0.5
        assert model.current_file == "test_file.jpg"

    def test_file_completed(self):
        """Test marking files as completed."""
        model = OperationModel()
        model.start_operation(2, "test_operation")

        model.file_completed(True)
        model.file_completed(False, "Test error")

        assert model.successful_files == 1
        assert model.failed_files == 1
        assert len(model.errors) == 1
        assert "Test error" in model.errors[0]

    def test_complete_operation(self):
        """Test completing an operation."""
        model = OperationModel()
        model.start_operation(5, "test_operation")

        model.complete_operation(True)

        assert model.progress == 1.0
        assert model.status_message == "Completed successfully. 0 files processed."


class TestMainWindow:
    """Test MainWindow functionality."""

    def test_main_window_import(self):
        """Test that MainWindow can be imported."""
        # This should not raise an exception
        from metadata_multitool.gui.main_window import MainWindow

        assert MainWindow is not None


@pytest.mark.skipif(not hasattr(tk, "Tk"), reason="Tkinter not available")
class TestGUIIntegration:
    """Test GUI integration with CLI."""

    def test_gui_command_available(self):
        """Test that GUI command is available in CLI."""
        from metadata_multitool.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["gui"])

        assert args.func is not None
        assert args.cmd == "gui"

    @patch("metadata_multitool.gui.main_window.MainWindow")
    def test_gui_command_execution(self, mock_main_window):
        """Test GUI command execution."""
        from metadata_multitool.cli import cmd_gui

        mock_app = Mock()
        mock_main_window.return_value = mock_app

        result = cmd_gui(Mock())

        assert result == 0
        mock_main_window.assert_called_once()
        mock_app.run.assert_called_once()
