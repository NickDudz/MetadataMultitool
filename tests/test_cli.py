"""Unit tests for CLI functionality."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch, call

import pytest

from metadata_multitool.cli import (
    apply_filters,
    handle_error,
    cmd_clean,
    cmd_poison,
    cmd_revert,
    cmd_interactive,
    cmd_gui,
    build_parser,
    validate_args,
    main,
)
from metadata_multitool.core import MetadataMultitoolError, InvalidPathError, LogError


class TestApplyFilters:
    """Test filter application functionality."""

    def test_apply_filters_no_filters(self, sample_images):
        """Test apply_filters with no filters specified."""
        args = argparse.Namespace()
        result = apply_filters(args, sample_images)
        assert result == sample_images

    def test_apply_filters_size_filter(self, sample_images):
        """Test apply_filters with size filter."""
        args = argparse.Namespace()
        args.size = "1000"  # Using bytes due to parsing bug in filters.py
        args.date = None
        args.formats = None
        args.has_metadata = False
        args.no_metadata = False
        
        with patch("metadata_multitool.cli.FileFilter") as mock_filter_class:
            mock_filter = Mock()
            # Mock the filters list with a function that returns True for first 2 images
            def mock_filter_func(path):
                return path in sample_images[:2]
            mock_filter.filters = [mock_filter_func]
            mock_filter_class.return_value = mock_filter
            
            result = apply_filters(args, sample_images)
            
            mock_filter.add_size_filter.assert_called_once_with(min_size=1000, max_size=1000)
            assert result == sample_images[:2]

    def test_apply_filters_date_filter(self, sample_images):
        """Test apply_filters with date filter."""
        args = argparse.Namespace()
        args.size = None
        args.date = "2024-01-01"
        args.formats = None
        args.has_metadata = False
        args.no_metadata = False
        
        with patch("metadata_multitool.cli.FileFilter") as mock_filter_class:
            mock_filter = Mock()
            mock_filter_class.return_value = mock_filter
            # Create mock filter function that returns True for first 3 images
            def mock_filter_func(path):
                return path in sample_images[:3]
            mock_filter.filters = [mock_filter_func]
            
            result = apply_filters(args, sample_images)
            
            mock_filter.add_date_filter.assert_called_once()
            assert result == sample_images[:3]

    def test_apply_filters_format_filter(self, sample_images):
        """Test apply_filters with format filter."""
        args = argparse.Namespace()
        args.size = None
        args.date = None
        args.formats = [".jpg", ".png"]
        args.has_metadata = False
        args.no_metadata = False
        
        with patch("metadata_multitool.cli.FileFilter") as mock_filter_class:
            mock_filter = Mock()
            mock_filter_class.return_value = mock_filter
            # Create mock filter function that returns True for all images
            mock_filter.filters = [Mock(return_value=True)]
            
            result = apply_filters(args, sample_images)
            
            mock_filter.add_format_filter.assert_called_once_with([".jpg", ".png"])
            assert result == sample_images

    def test_apply_filters_has_metadata(self, sample_images):
        """Test apply_filters with has_metadata filter."""
        args = argparse.Namespace()
        args.size = None
        args.date = None
        args.formats = None
        args.has_metadata = True
        args.no_metadata = False
        
        with patch("metadata_multitool.cli.FileFilter") as mock_filter_class:
            mock_filter = Mock()
            mock_filter_class.return_value = mock_filter
            # Create mock filter function that returns True for first image only
            def mock_filter_func(path):
                return path == sample_images[0]
            mock_filter.filters = [mock_filter_func]
            
            result = apply_filters(args, sample_images)
            
            mock_filter.add_metadata_filter.assert_called_once_with(has_metadata=True)
            assert result == sample_images[:1]

    def test_apply_filters_no_metadata(self, sample_images):
        """Test apply_filters with no_metadata filter."""
        args = argparse.Namespace()
        args.size = None
        args.date = None
        args.formats = None
        args.has_metadata = False
        args.no_metadata = True
        
        with patch("metadata_multitool.cli.FileFilter") as mock_filter_class:
            mock_filter = Mock()
            mock_filter_class.return_value = mock_filter
            # Create mock filter function that returns True for first 2 images
            def mock_filter_func(path):
                return path in sample_images[:2]
            mock_filter.filters = [mock_filter_func]
            
            result = apply_filters(args, sample_images)
            
            mock_filter.add_metadata_filter.assert_called_once_with(has_metadata=False)
            assert result == sample_images[:2]

    @patch("builtins.print")
    def test_apply_filters_invalid_size(self, mock_print, sample_images):
        """Test apply_filters with invalid size filter."""
        args = argparse.Namespace()
        args.size = "invalid-size"
        args.date = None
        args.formats = None
        args.has_metadata = False
        args.no_metadata = False
        
        with patch("metadata_multitool.cli.parse_size_filter") as mock_parse_size:
            mock_parse_size.side_effect = ValueError("Invalid size")
            
            result = apply_filters(args, sample_images)
            
            # Should print warning and return unfiltered results
            assert any("Warning" in str(call) for call in mock_print.call_args_list)
            assert result == sample_images

    @patch("builtins.print")
    def test_apply_filters_invalid_date(self, mock_print, sample_images):
        """Test apply_filters with invalid date filter."""
        args = argparse.Namespace()
        args.size = None
        args.date = "invalid-date"
        args.formats = None
        args.has_metadata = False
        args.no_metadata = False
        
        with patch("metadata_multitool.cli.parse_date_filter") as mock_parse_date:
            mock_parse_date.side_effect = ValueError("Invalid date")
            
            result = apply_filters(args, sample_images)
            
            # Should print warning and return unfiltered results
            assert any("Warning" in str(call) for call in mock_print.call_args_list)
            assert result == sample_images


class TestHandleError:
    """Test error handling functionality."""

    @patch("builtins.print")
    def test_handle_error_metadata_error(self, mock_print):
        """Test handling MetadataMultitoolError."""
        error = MetadataMultitoolError("Test error message")
        result = handle_error(error, "test context")
        
        assert result == 1
        error_calls = [call for call in mock_print.call_args_list if "Test error message" in str(call)]
        assert len(error_calls) > 0

    @patch("builtins.print")
    def test_handle_error_invalid_path_error(self, mock_print):
        """Test handling InvalidPathError."""
        error = InvalidPathError("Invalid path")
        result = handle_error(error, "path validation")
        
        assert result == 1
        error_calls = [call for call in mock_print.call_args_list if "Invalid path" in str(call)]
        assert len(error_calls) > 0

    @patch("builtins.print")
    def test_handle_error_log_error(self, mock_print):
        """Test handling LogError."""
        error = LogError("Log error")
        result = handle_error(error, "logging")
        
        assert result == 1
        error_calls = [call for call in mock_print.call_args_list if "Log error" in str(call)]
        assert len(error_calls) > 0

    @patch("builtins.print")
    def test_handle_error_keyboard_interrupt(self, mock_print):
        """Test handling KeyboardInterrupt."""
        error = KeyboardInterrupt()
        result = handle_error(error, "user interrupt")
        
        assert result == 1
        interrupt_calls = [call for call in mock_print.call_args_list if "interrupted" in str(call)]
        assert len(interrupt_calls) > 0

    @patch("builtins.print")
    def test_handle_error_generic_exception(self, mock_print):
        """Test handling generic Exception."""
        error = ValueError("Generic error")
        result = handle_error(error, "generic context")
        
        assert result == 1
        error_calls = [call for call in mock_print.call_args_list if "Generic error" in str(call)]
        assert len(error_calls) > 0

    @patch("builtins.print")
    def test_handle_error_with_context(self, mock_print):
        """Test error handling with context."""
        error = MetadataMultitoolError("Test error")
        result = handle_error(error, "test operation")
        
        assert result == 1
        # Should include context in error message
        context_calls = [call for call in mock_print.call_args_list if "test operation" in str(call)]
        assert len(context_calls) > 0


class TestCmdClean:
    """Test clean command functionality."""

    @patch("metadata_multitool.cli.iter_images")
    @patch("metadata_multitool.cli.ensure_dir")
    @patch("metadata_multitool.cli.clean_copy")
    @patch("metadata_multitool.cli.load_config")
    @patch("builtins.print")
    def test_cmd_clean_basic(self, mock_print, mock_load_config, mock_clean_copy, mock_ensure_dir, mock_iter_images, tmp_path):
        """Test basic clean command execution."""
        # Setup
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"test")
        
        args = argparse.Namespace()
        args.paths = [str(tmp_path)]
        args.output = None
        args.dry_run = False
        args.verbose = False
        args.no_backup = True
        args.batch_size = None
        args.max_workers = None
        
        mock_iter_images.return_value = [test_image]
        mock_ensure_dir.return_value = tmp_path / "safe_upload"
        mock_load_config.return_value = {}
        
        result = cmd_clean(args)
        
        assert result == 0
        mock_clean_copy.assert_called()

    @patch("metadata_multitool.cli.iter_images")
    @patch("metadata_multitool.cli.load_config")
    @patch("builtins.print")
    def test_cmd_clean_no_images(self, mock_print, mock_load_config, mock_iter_images, tmp_path):
        """Test clean command with no images found."""
        args = argparse.Namespace()
        args.paths = [str(tmp_path)]
        args.output = None
        args.dry_run = False
        args.verbose = False
        args.no_backup = True
        
        mock_iter_images.return_value = []
        mock_load_config.return_value = {}
        
        result = cmd_clean(args)
        
        assert result == 0
        # Should print message about no images found
        no_images_calls = [call for call in mock_print.call_args_list if "No images found" in str(call)]
        assert len(no_images_calls) > 0

    @patch("metadata_multitool.cli.iter_images")
    @patch("metadata_multitool.cli.ensure_dir")
    @patch("metadata_multitool.cli.load_config")
    @patch("builtins.print")
    def test_cmd_clean_dry_run(self, mock_print, mock_load_config, mock_ensure_dir, mock_iter_images, tmp_path):
        """Test clean command with dry run."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"test")
        
        args = argparse.Namespace()
        args.paths = [str(tmp_path)]
        args.output = None
        args.dry_run = True
        args.verbose = False
        args.no_backup = True
        
        mock_iter_images.return_value = [test_image]
        mock_ensure_dir.return_value = tmp_path / "safe_upload"
        mock_load_config.return_value = {}
        
        result = cmd_clean(args)
        
        assert result == 0
        # Should print dry run message
        dry_run_calls = [call for call in mock_print.call_args_list if "DRY RUN" in str(call)]
        assert len(dry_run_calls) > 0

    @patch("metadata_multitool.cli.iter_images")
    @patch("metadata_multitool.cli.load_config")
    def test_cmd_clean_invalid_path(self, mock_load_config, mock_iter_images):
        """Test clean command with invalid path."""
        args = argparse.Namespace()
        args.paths = ["/nonexistent/path"]
        args.output = None
        args.dry_run = False
        args.verbose = False
        args.no_backup = True
        
        mock_iter_images.side_effect = InvalidPathError("Path not found")
        mock_load_config.return_value = {}
        
        result = cmd_clean(args)
        
        assert result == 1  # Should return error code


class TestCmdPoison:
    """Test poison command functionality."""

    @patch("metadata_multitool.cli.iter_images")
    @patch("metadata_multitool.cli.write_sidecars")
    @patch("metadata_multitool.cli.load_config")
    @patch("builtins.print")
    def test_cmd_poison_basic(self, mock_print, mock_load_config, mock_write_sidecars, mock_iter_images, tmp_path):
        """Test basic poison command execution."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"test")
        
        args = argparse.Namespace()
        args.paths = [str(tmp_path)]
        args.preset = "label_flip"
        args.dry_run = False
        args.verbose = False
        args.sidecar = True
        args.json = False
        args.html = False
        args.xmp = False
        args.iptc = False
        args.exif = False
        args.csv = None
        args.rename_pattern = None
        args.true_hint = None
        args.no_backup = True
        args.batch_size = None
        args.max_workers = None
        
        mock_iter_images.return_value = [test_image]
        mock_load_config.return_value = {}
        
        result = cmd_poison(args)
        
        assert result == 0
        mock_write_sidecars.assert_called()

    @patch("metadata_multitool.cli.iter_images")
    @patch("metadata_multitool.cli.load_config")
    @patch("builtins.print")
    def test_cmd_poison_dry_run(self, mock_print, mock_load_config, mock_iter_images, tmp_path):
        """Test poison command with dry run."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"test")
        
        args = argparse.Namespace()
        args.paths = [str(tmp_path)]
        args.preset = "label_flip"
        args.dry_run = True
        args.verbose = False
        args.sidecar = True
        args.json = False
        args.html = False
        args.xmp = False
        args.iptc = False
        args.exif = False
        args.csv = None
        args.rename_pattern = None
        args.true_hint = None
        args.no_backup = True
        
        mock_iter_images.return_value = [test_image]
        mock_load_config.return_value = {}
        
        result = cmd_poison(args)
        
        assert result == 0
        # Should print dry run message
        dry_run_calls = [call for call in mock_print.call_args_list if "DRY RUN" in str(call)]
        assert len(dry_run_calls) > 0

    @patch("metadata_multitool.cli.iter_images")
    @patch("metadata_multitool.cli.load_csv_mapping")
    @patch("metadata_multitool.cli.load_config")
    @patch("builtins.print")
    def test_cmd_poison_with_csv(self, mock_print, mock_load_config, mock_load_csv, mock_iter_images, tmp_path):
        """Test poison command with CSV mapping."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"test")
        csv_file = tmp_path / "mapping.csv"
        csv_file.write_text("real,fake\n")
        
        args = argparse.Namespace()
        args.paths = [str(tmp_path)]
        args.preset = "label_flip"
        args.dry_run = True
        args.verbose = False
        args.sidecar = True
        args.json = False
        args.html = False
        args.xmp = False
        args.iptc = False
        args.exif = False
        args.csv = str(csv_file)
        args.rename_pattern = None
        args.true_hint = None
        args.no_backup = True
        
        mock_iter_images.return_value = [test_image]
        mock_load_config.return_value = {}
        mock_load_csv.return_value = {"real": "fake"}
        
        result = cmd_poison(args)
        
        assert result == 0
        mock_load_csv.assert_called_once_with(csv_file)


class TestCmdRevert:
    """Test revert command functionality."""

    @patch("metadata_multitool.cli.revert_dir")
    @patch("builtins.print")
    def test_cmd_revert_success(self, mock_print, mock_revert_dir, tmp_path):
        """Test successful revert command."""
        args = argparse.Namespace()
        args.paths = [str(tmp_path)]
        args.dry_run = False
        args.verbose = False
        
        mock_revert_dir.return_value = 5  # 5 files reverted
        
        result = cmd_revert(args)
        
        assert result == 0
        mock_revert_dir.assert_called_once_with(tmp_path)
        
        # Should print success message
        success_calls = [call for call in mock_print.call_args_list if "Reverted" in str(call)]
        assert len(success_calls) > 0

    @patch("metadata_multitool.cli.revert_dir")
    @patch("builtins.print")
    def test_cmd_revert_dry_run(self, mock_print, mock_revert_dir, tmp_path):
        """Test revert command with dry run."""
        args = argparse.Namespace()
        args.paths = [str(tmp_path)]
        args.dry_run = True
        args.verbose = False
        
        # In dry run, should not call revert_dir
        result = cmd_revert(args)
        
        assert result == 0
        mock_revert_dir.assert_not_called()
        
        # Should print dry run message
        dry_run_calls = [call for call in mock_print.call_args_list if "DRY RUN" in str(call)]
        assert len(dry_run_calls) > 0

    @patch("metadata_multitool.cli.revert_dir")
    def test_cmd_revert_error(self, mock_revert_dir, tmp_path):
        """Test revert command with error."""
        args = argparse.Namespace()
        args.paths = [str(tmp_path)]
        args.dry_run = False
        args.verbose = False
        
        mock_revert_dir.side_effect = LogError("Revert failed")
        
        result = cmd_revert(args)
        
        assert result == 1  # Should return error code


class TestCmdInteractive:
    """Test interactive command functionality."""

    @patch("metadata_multitool.cli.interactive_mode")
    def test_cmd_interactive_success(self, mock_interactive):
        """Test successful interactive command."""
        args = argparse.Namespace()
        mock_interactive.return_value = 0
        
        result = cmd_interactive(args)
        
        assert result == 0
        mock_interactive.assert_called_once()

    @patch("metadata_multitool.cli.interactive_mode")
    def test_cmd_interactive_error(self, mock_interactive):
        """Test interactive command with error."""
        args = argparse.Namespace()
        mock_interactive.return_value = 1
        
        result = cmd_interactive(args)
        
        assert result == 1
        mock_interactive.assert_called_once()


class TestCmdGui:
    """Test GUI command functionality."""

    @patch("builtins.print")
    def test_cmd_gui_no_pyqt6(self, mock_print):
        """Test GUI command when PyQt6 is not available."""
        args = argparse.Namespace()
        
        with patch.dict("sys.modules", {"PyQt6": None}):
            result = cmd_gui(args)
        
        assert result == 1
        # Should print error about PyQt6 not being available
        error_calls = [call for call in mock_print.call_args_list if "PyQt6" in str(call)]
        assert len(error_calls) > 0

    @patch("metadata_multitool.gui_qt.main.main")
    def test_cmd_gui_success(self, mock_gui_main):
        """Test successful GUI command when PyQt6 is available."""
        args = argparse.Namespace()
        mock_gui_main.return_value = 0
        
        # Mock PyQt6 being available
        with patch.dict("sys.modules", {"PyQt6.QtWidgets": Mock()}):
            result = cmd_gui(args)
        
        assert result == 0
        mock_gui_main.assert_called_once()


class TestBuildParser:
    """Test argument parser building."""

    def test_build_parser(self):
        """Test parser creation."""
        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        
        # Test parsing help doesn't crash
        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

    def test_parser_clean_command(self):
        """Test clean command parsing."""
        parser = build_parser()
        args = parser.parse_args(["clean", "/test/path"])
        
        assert args.command == "clean"
        assert args.paths == ["/test/path"]

    def test_parser_poison_command(self):
        """Test poison command parsing."""
        parser = build_parser()
        args = parser.parse_args(["poison", "/test/path", "--preset", "label_flip"])
        
        assert args.command == "poison"
        assert args.paths == ["/test/path"]
        assert args.preset == "label_flip"

    def test_parser_revert_command(self):
        """Test revert command parsing."""
        parser = build_parser()
        args = parser.parse_args(["revert", "/test/path"])
        
        assert args.command == "revert"
        assert args.paths == ["/test/path"]

    def test_parser_interactive_command(self):
        """Test interactive command parsing."""
        parser = build_parser()
        args = parser.parse_args(["interactive"])
        
        assert args.command == "interactive"

    def test_parser_gui_command(self):
        """Test GUI command parsing."""
        parser = build_parser()
        args = parser.parse_args(["gui"])
        
        assert args.command == "gui"


class TestValidateArgs:
    """Test argument validation."""

    def test_validate_args_valid(self):
        """Test validation with valid arguments."""
        args = argparse.Namespace()
        args.command = "clean"
        args.paths = [str(Path.cwd())]
        
        # Should not raise any exceptions
        validate_args(args)

    def test_validate_args_poison_no_preset(self):
        """Test validation for poison command without preset."""
        args = argparse.Namespace()
        args.command = "poison"
        args.paths = [str(Path.cwd())]
        args.preset = None
        
        with pytest.raises(SystemExit):
            validate_args(args)

    def test_validate_args_poison_with_preset(self):
        """Test validation for poison command with preset."""
        args = argparse.Namespace()
        args.command = "poison"
        args.paths = [str(Path.cwd())]
        args.preset = "label_flip"
        
        # Should not raise any exceptions
        validate_args(args)


class TestMain:
    """Test main function."""

    @patch("metadata_multitool.cli.build_parser")
    @patch("metadata_multitool.cli.cmd_clean")
    def test_main_clean_command(self, mock_cmd_clean, mock_build_parser):
        """Test main function with clean command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "clean"
        mock_args.paths = [str(Path.cwd())]
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        mock_cmd_clean.return_value = 0
        
        result = main(["clean", "/test/path"])
        
        assert result == 0
        mock_cmd_clean.assert_called_once_with(mock_args)

    @patch("metadata_multitool.cli.build_parser")
    @patch("metadata_multitool.cli.cmd_poison")
    def test_main_poison_command(self, mock_cmd_poison, mock_build_parser):
        """Test main function with poison command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "poison"
        mock_args.paths = [str(Path.cwd())]
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        mock_cmd_poison.return_value = 0
        
        result = main(["poison", "/test/path"])
        
        assert result == 0
        mock_cmd_poison.assert_called_once_with(mock_args)

    @patch("metadata_multitool.cli.build_parser")
    @patch("metadata_multitool.cli.cmd_revert")
    def test_main_revert_command(self, mock_cmd_revert, mock_build_parser):
        """Test main function with revert command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "revert"
        mock_args.paths = [str(Path.cwd())]
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        mock_cmd_revert.return_value = 0
        
        result = main(["revert", "/test/path"])
        
        assert result == 0
        mock_cmd_revert.assert_called_once_with(mock_args)

    @patch("metadata_multitool.cli.build_parser")
    @patch("metadata_multitool.cli.cmd_interactive")
    def test_main_interactive_command(self, mock_cmd_interactive, mock_build_parser):
        """Test main function with interactive command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "interactive"
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        mock_cmd_interactive.return_value = 0
        
        result = main(["interactive"])
        
        assert result == 0
        mock_cmd_interactive.assert_called_once_with(mock_args)

    @patch("metadata_multitool.cli.build_parser")
    @patch("metadata_multitool.cli.cmd_gui")
    def test_main_gui_command(self, mock_cmd_gui, mock_build_parser):
        """Test main function with GUI command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "gui"
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        mock_cmd_gui.return_value = 0
        
        result = main(["gui"])
        
        assert result == 0
        mock_cmd_gui.assert_called_once_with(mock_args)

    @patch("metadata_multitool.cli.build_parser")
    def test_main_invalid_command(self, mock_build_parser):
        """Test main function with invalid command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "invalid"
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        
        result = main(["invalid"])
        
        assert result == 1  # Should return error code

    @patch("metadata_multitool.cli.build_parser")
    @patch("metadata_multitool.cli.handle_error")
    def test_main_exception_handling(self, mock_handle_error, mock_build_parser):
        """Test main function exception handling."""
        mock_build_parser.side_effect = Exception("Parser error")
        mock_handle_error.return_value = 1
        
        result = main(["test"])
        
        assert result == 1
        mock_handle_error.assert_called_once()

    def test_main_no_args(self):
        """Test main function with no arguments (should show help)."""
        with patch("sys.argv", ["mm"]):
            result = main([])
            # Should return error code when no command specified
            assert result != 0


class TestIntegration:
    """Integration tests for CLI functionality."""

    @patch("metadata_multitool.cli.iter_images")
    @patch("metadata_multitool.cli.ensure_dir")
    @patch("metadata_multitool.cli.clean_copy")
    @patch("metadata_multitool.cli.load_config")
    def test_full_clean_workflow(self, mock_load_config, mock_clean_copy, mock_ensure_dir, mock_iter_images, tmp_path):
        """Test complete clean workflow through main function."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"test")
        
        mock_iter_images.return_value = [test_image]
        mock_ensure_dir.return_value = tmp_path / "safe_upload"
        mock_load_config.return_value = {}
        
        result = main(["clean", str(tmp_path), "--no-backup"])
        
        assert result == 0
        mock_clean_copy.assert_called()

    @patch("metadata_multitool.cli.iter_images")
    @patch("metadata_multitool.cli.write_sidecars")
    @patch("metadata_multitool.cli.load_config")
    def test_full_poison_workflow(self, mock_load_config, mock_write_sidecars, mock_iter_images, tmp_path):
        """Test complete poison workflow through main function."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"test")
        
        mock_iter_images.return_value = [test_image]
        mock_load_config.return_value = {}
        
        result = main(["poison", str(tmp_path), "--preset", "label_flip", "--sidecar", "--no-backup"])
        
        assert result == 0
        mock_write_sidecars.assert_called()

    @patch("metadata_multitool.cli.revert_dir")
    def test_full_revert_workflow(self, mock_revert_dir, tmp_path):
        """Test complete revert workflow through main function."""
        mock_revert_dir.return_value = 3
        
        result = main(["revert", str(tmp_path)])
        
        assert result == 0
        mock_revert_dir.assert_called_once_with(tmp_path)