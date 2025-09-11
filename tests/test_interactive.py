"""Tests for interactive mode functionality."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch, call
from io import StringIO

import pytest

from metadata_multitool.interactive import (
    InteractiveError,
    interactive_mode,
    show_main_menu,
    handle_clean_workflow,
    handle_poison_workflow,
    handle_revert_workflow,
    handle_config_workflow,
    handle_batch_workflow,
    get_yes_no,
)


class TestInteractiveError:
    """Test InteractiveError exception."""

    def test_interactive_error(self):
        """Test InteractiveError exception."""
        error = InteractiveError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)


class TestInteractiveMode:
    """Test main interactive mode function."""

    @patch("metadata_multitool.interactive.load_config")
    @patch("metadata_multitool.interactive.show_main_menu")
    @patch("metadata_multitool.interactive.handle_clean_workflow")
    @patch("builtins.print")
    def test_interactive_mode_clean_workflow(self, mock_print, mock_handle_clean, mock_show_menu, mock_load_config):
        """Test interactive mode with clean workflow selection."""
        mock_load_config.return_value = {"test": "config"}
        mock_show_menu.side_effect = ["1", "q"]  # Select clean, then quit
        
        result = interactive_mode()
        
        assert result == 0
        mock_handle_clean.assert_called_once_with({"test": "config"})

    @patch("metadata_multitool.interactive.load_config")
    @patch("metadata_multitool.interactive.show_main_menu")
    @patch("metadata_multitool.interactive.handle_poison_workflow")
    @patch("builtins.print")
    def test_interactive_mode_poison_workflow(self, mock_print, mock_handle_poison, mock_show_menu, mock_load_config):
        """Test interactive mode with poison workflow selection."""
        mock_load_config.return_value = {"test": "config"}
        mock_show_menu.side_effect = ["2", "q"]  # Select poison, then quit
        
        result = interactive_mode()
        
        assert result == 0
        mock_handle_poison.assert_called_once_with({"test": "config"})

    @patch("metadata_multitool.interactive.load_config")
    @patch("metadata_multitool.interactive.show_main_menu")
    @patch("metadata_multitool.interactive.handle_revert_workflow")
    @patch("builtins.print")
    def test_interactive_mode_revert_workflow(self, mock_print, mock_handle_revert, mock_show_menu, mock_load_config):
        """Test interactive mode with revert workflow selection."""
        mock_load_config.return_value = {"test": "config"}
        mock_show_menu.side_effect = ["3", "q"]  # Select revert, then quit
        
        result = interactive_mode()
        
        assert result == 0
        mock_handle_revert.assert_called_once()

    @patch("metadata_multitool.interactive.load_config")
    @patch("metadata_multitool.interactive.show_main_menu")
    @patch("metadata_multitool.interactive.handle_config_workflow")
    @patch("builtins.print")
    def test_interactive_mode_config_workflow(self, mock_print, mock_handle_config, mock_show_menu, mock_load_config):
        """Test interactive mode with config workflow selection."""
        mock_load_config.return_value = {"test": "config"}
        mock_show_menu.side_effect = ["4", "q"]  # Select config, then quit
        
        result = interactive_mode()
        
        assert result == 0
        mock_handle_config.assert_called_once_with({"test": "config"})

    @patch("metadata_multitool.interactive.load_config")
    @patch("metadata_multitool.interactive.show_main_menu")
    @patch("metadata_multitool.interactive.handle_batch_workflow")
    @patch("builtins.print")
    def test_interactive_mode_batch_workflow(self, mock_print, mock_handle_batch, mock_show_menu, mock_load_config):
        """Test interactive mode with batch workflow selection."""
        mock_load_config.return_value = {"test": "config"}
        mock_show_menu.side_effect = ["5", "q"]  # Select batch, then quit
        
        result = interactive_mode()
        
        assert result == 0
        mock_handle_batch.assert_called_once_with({"test": "config"})

    @patch("metadata_multitool.interactive.load_config")
    @patch("metadata_multitool.interactive.show_main_menu")
    @patch("builtins.print")
    def test_interactive_mode_invalid_choice(self, mock_print, mock_show_menu, mock_load_config):
        """Test interactive mode with invalid choice."""
        mock_load_config.return_value = {}
        mock_show_menu.side_effect = ["invalid", "q"]  # Invalid choice, then quit
        
        result = interactive_mode()
        
        assert result == 0
        # Should print error message about invalid choice
        error_calls = [call for call in mock_print.call_args_list if "Invalid choice" in str(call)]
        assert len(error_calls) > 0

    @patch("metadata_multitool.interactive.load_config")
    @patch("metadata_multitool.interactive.show_main_menu")
    @patch("builtins.print")
    def test_interactive_mode_keyboard_interrupt(self, mock_print, mock_show_menu, mock_load_config):
        """Test interactive mode with keyboard interrupt."""
        mock_load_config.return_value = {}
        mock_show_menu.side_effect = [KeyboardInterrupt(), "q"]  # Interrupt, then quit
        
        result = interactive_mode()
        
        assert result == 0
        # Should print cancellation message
        cancel_calls = [call for call in mock_print.call_args_list if "cancelled" in str(call)]
        assert len(cancel_calls) > 0

    @patch("metadata_multitool.interactive.load_config")
    @patch("metadata_multitool.interactive.show_main_menu")
    @patch("builtins.print")
    def test_interactive_mode_exception(self, mock_print, mock_show_menu, mock_load_config):
        """Test interactive mode with general exception."""
        mock_load_config.return_value = {}
        mock_show_menu.side_effect = [Exception("Test error"), "q"]  # Exception, then quit
        
        result = interactive_mode()
        
        assert result == 0
        # Should print error message
        error_calls = [call for call in mock_print.call_args_list if "Test error" in str(call)]
        assert len(error_calls) > 0

    @patch("metadata_multitool.interactive.load_config")
    @patch("builtins.print")
    def test_interactive_mode_fatal_error(self, mock_print, mock_load_config):
        """Test interactive mode with fatal error."""
        mock_load_config.side_effect = Exception("Fatal config error")
        
        result = interactive_mode()
        
        assert result == 1
        # Should print fatal error message
        fatal_calls = [call for call in mock_print.call_args_list if "Fatal" in str(call)]
        assert len(fatal_calls) > 0


class TestShowMainMenu:
    """Test main menu display and input handling."""

    @patch("builtins.input")
    @patch("builtins.print")
    def test_show_main_menu_valid_choices(self, mock_print, mock_input):
        """Test main menu with valid choices."""
        mock_input.return_value = "1"
        result = show_main_menu()
        assert result == "1"

    @patch("builtins.input")
    @patch("builtins.print")
    def test_show_main_menu_quit(self, mock_print, mock_input):
        """Test main menu with quit choice."""
        mock_input.return_value = "q"
        result = show_main_menu()
        assert result == "q"

    @patch("builtins.input")
    @patch("builtins.print")
    def test_show_main_menu_invalid_then_valid(self, mock_print, mock_input):
        """Test main menu with invalid then valid choice."""
        mock_input.side_effect = ["invalid", "2"]
        result = show_main_menu()
        assert result == "2"

    @patch("builtins.input")
    @patch("builtins.print")
    def test_show_main_menu_case_insensitive(self, mock_print, mock_input):
        """Test main menu with uppercase Q."""
        mock_input.return_value = "Q"
        result = show_main_menu()
        assert result == "q"


class TestHandleCleanWorkflow:
    """Test clean workflow handling."""

    @patch("metadata_multitool.interactive.get_yes_no")
    @patch("metadata_multitool.interactive.iter_images")
    @patch("metadata_multitool.interactive.ensure_dir")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_clean_workflow_dry_run(self, mock_print, mock_input, mock_ensure_dir, mock_iter_images, mock_get_yes_no, tmp_path):
        """Test clean workflow with dry run."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"test")
        
        mock_input.side_effect = [str(tmp_path), ""]  # Path input, default output folder
        mock_get_yes_no.side_effect = [False, True]  # Not verbose, dry run
        mock_iter_images.return_value = [test_image]
        mock_ensure_dir.return_value = tmp_path / "safe_upload"
        
        handle_clean_workflow({})
        
        # Should print dry run message
        dry_run_calls = [call for call in mock_print.call_args_list if "DRY RUN" in str(call)]
        assert len(dry_run_calls) > 0

    @patch("metadata_multitool.interactive.get_yes_no")
    @patch("metadata_multitool.interactive.iter_images")
    @patch("metadata_multitool.interactive.ensure_dir")
    @patch("metadata_multitool.interactive.clean_copy")
    @patch("metadata_multitool.interactive.get_config_value")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_clean_workflow_small_batch(self, mock_print, mock_input, mock_get_config_value, mock_clean_copy, mock_ensure_dir, mock_iter_images, mock_get_yes_no, tmp_path):
        """Test clean workflow with small batch (sequential processing)."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"test")
        
        mock_input.side_effect = [str(tmp_path), "output"]  # Path input, custom output folder
        mock_get_yes_no.side_effect = [True, False]  # Verbose, not dry run
        mock_iter_images.return_value = [test_image]
        mock_ensure_dir.return_value = tmp_path / "output"
        mock_get_config_value.side_effect = [100, 4]  # batch_size, max_workers
        
        handle_clean_workflow({})
        
        mock_clean_copy.assert_called_once()

    @patch("metadata_multitool.interactive.get_yes_no")
    @patch("metadata_multitool.interactive.iter_images")
    @patch("metadata_multitool.interactive.ensure_dir")
    @patch("metadata_multitool.interactive.process_batch")
    @patch("metadata_multitool.interactive.get_config_value")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_clean_workflow_large_batch(self, mock_print, mock_input, mock_get_config_value, mock_process_batch, mock_ensure_dir, mock_iter_images, mock_get_yes_no, tmp_path):
        """Test clean workflow with large batch (parallel processing)."""
        # Create many test images
        test_images = []
        for i in range(150):
            test_image = tmp_path / f"test_{i}.jpg"
            test_image.write_bytes(b"test")
            test_images.append(test_image)
        
        mock_input.side_effect = [str(tmp_path), ""]
        mock_get_yes_no.side_effect = [False, False]  # Not verbose, not dry run
        mock_iter_images.return_value = test_images
        mock_ensure_dir.return_value = tmp_path / "safe_upload"
        mock_get_config_value.side_effect = [100, 4]  # batch_size, max_workers
        mock_process_batch.return_value = (150, 150, [])  # All successful
        
        handle_clean_workflow({})
        
        mock_process_batch.assert_called_once()

    @patch("metadata_multitool.interactive.get_yes_no")
    @patch("metadata_multitool.interactive.iter_images")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_clean_workflow_empty_path(self, mock_print, mock_input, mock_iter_images, mock_get_yes_no):
        """Test clean workflow with empty path input."""
        mock_input.side_effect = ["", "/valid/path", ""]  # Empty, then valid path
        mock_get_yes_no.side_effect = [False, True]  # Not verbose, dry run
        mock_iter_images.return_value = []
        
        # Mock Path.exists for valid path
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            handle_clean_workflow({})
        
        # Should print path cannot be empty error
        empty_calls = [call for call in mock_print.call_args_list if "cannot be empty" in str(call)]
        assert len(empty_calls) > 0

    @patch("metadata_multitool.interactive.get_yes_no")
    @patch("metadata_multitool.interactive.iter_images")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_clean_workflow_nonexistent_path(self, mock_print, mock_input, mock_iter_images, mock_get_yes_no):
        """Test clean workflow with nonexistent path."""
        mock_input.side_effect = ["/nonexistent/path", "/valid/path", ""]
        mock_get_yes_no.side_effect = [False, True]  # Not verbose, dry run
        mock_iter_images.return_value = []
        
        # Mock Path.exists to return False for first, True for second
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = [False, True]
            handle_clean_workflow({})
        
        # Should print path does not exist error
        exist_calls = [call for call in mock_print.call_args_list if "does not exist" in str(call)]
        assert len(exist_calls) > 0

    @patch("metadata_multitool.interactive.get_yes_no")
    @patch("metadata_multitool.interactive.iter_images")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_clean_workflow_no_images(self, mock_print, mock_input, mock_iter_images, mock_get_yes_no, tmp_path):
        """Test clean workflow with no images found."""
        mock_input.side_effect = [str(tmp_path), ""]
        mock_get_yes_no.side_effect = [False, True]  # Not verbose, dry run
        mock_iter_images.return_value = []  # No images found
        
        handle_clean_workflow({})
        
        # Should print no images found message
        no_images_calls = [call for call in mock_print.call_args_list if "No images found" in str(call)]
        assert len(no_images_calls) > 0


class TestGetYesNo:
    """Test yes/no input utility function."""

    @patch("builtins.input")
    def test_get_yes_no_yes(self, mock_input):
        """Test get_yes_no with yes input."""
        mock_input.return_value = "y"
        result = get_yes_no("Test prompt: ")
        assert result is True

    @patch("builtins.input")
    def test_get_yes_no_no(self, mock_input):
        """Test get_yes_no with no input."""
        mock_input.return_value = "n"
        result = get_yes_no("Test prompt: ")
        assert result is False

    @patch("builtins.input")
    def test_get_yes_no_yes_variations(self, mock_input):
        """Test get_yes_no with various yes inputs."""
        for yes_input in ["y", "Y", "yes", "YES", "Yes"]:
            mock_input.return_value = yes_input
            result = get_yes_no("Test prompt: ")
            assert result is True

    @patch("builtins.input")
    def test_get_yes_no_no_variations(self, mock_input):
        """Test get_yes_no with various no inputs."""
        for no_input in ["n", "N", "no", "NO", "No"]:
            mock_input.return_value = no_input
            result = get_yes_no("Test prompt: ")
            assert result is False

    @patch("builtins.input")
    def test_get_yes_no_empty_default_false(self, mock_input):
        """Test get_yes_no with empty input and default False."""
        mock_input.return_value = ""
        result = get_yes_no("Test prompt: ", default=False)
        assert result is False

    @patch("builtins.input")
    def test_get_yes_no_empty_default_true(self, mock_input):
        """Test get_yes_no with empty input and default True."""
        mock_input.return_value = ""
        result = get_yes_no("Test prompt: ", default=True)
        assert result is True

    @patch("builtins.input")
    @patch("builtins.print")
    def test_get_yes_no_invalid_then_valid(self, mock_print, mock_input):
        """Test get_yes_no with invalid then valid input."""
        mock_input.side_effect = ["invalid", "y"]
        result = get_yes_no("Test prompt: ")
        assert result is True
        
        # Should print error message
        error_calls = [call for call in mock_print.call_args_list if "Please enter" in str(call)]
        assert len(error_calls) > 0


class TestHandlePoisonWorkflow:
    """Test poison workflow handling (basic functionality)."""

    @patch("metadata_multitool.interactive.get_yes_no")
    @patch("metadata_multitool.interactive.iter_images")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_poison_workflow_dry_run(self, mock_print, mock_input, mock_iter_images, mock_get_yes_no, tmp_path):
        """Test poison workflow with dry run."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"test")
        
        # Mock inputs for path, preset selection, and options
        mock_input.side_effect = [
            str(tmp_path),  # path input
            "1",  # preset choice (label_flip)
            "",  # true hint (optional)
            "",  # rename pattern (optional)
            "",  # csv path (optional)
        ]
        # Multiple get_yes_no calls: xmp, iptc, exif, sidecar, json_sidecar, html, verbose, dry_run
        mock_get_yes_no.side_effect = [True, True, False, True, False, False, False, True]
        mock_iter_images.return_value = [test_image]
        
        handle_poison_workflow({})
        
        # Should print dry run message
        dry_run_calls = [call for call in mock_print.call_args_list if "DRY RUN" in str(call)]
        assert len(dry_run_calls) > 0

    @patch("metadata_multitool.interactive.get_yes_no")
    @patch("metadata_multitool.interactive.iter_images")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_poison_workflow_no_images(self, mock_print, mock_input, mock_iter_images, mock_get_yes_no, tmp_path):
        """Test poison workflow with no images found."""
        mock_input.side_effect = [str(tmp_path), "1", "", "", ""]
        # Multiple get_yes_no calls: xmp, iptc, exif, sidecar, json_sidecar, html, verbose, dry_run
        mock_get_yes_no.side_effect = [True, True, False, True, False, False, False, True]
        mock_iter_images.return_value = []  # No images found
        
        handle_poison_workflow({})
        
        # Should print no images found message
        no_images_calls = [call for call in mock_print.call_args_list if "No images found" in str(call)]
        assert len(no_images_calls) > 0


class TestHandleRevertWorkflow:
    """Test revert workflow handling."""

    @patch("metadata_multitool.interactive.revert_dir")
    @patch("metadata_multitool.interactive.get_yes_no")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_revert_workflow_success(self, mock_print, mock_input, mock_get_yes_no, mock_revert_dir, tmp_path):
        """Test revert workflow with successful revert."""
        mock_input.return_value = str(tmp_path)
        mock_get_yes_no.return_value = True  # Confirm revert
        mock_revert_dir.return_value = 5  # Return number of files removed
        
        # Mock path.exists() and path.is_dir() 
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.is_dir", return_value=True):
            handle_revert_workflow()
        
        mock_revert_dir.assert_called_once()

    @patch("metadata_multitool.interactive.get_yes_no")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_revert_workflow_cancelled(self, mock_print, mock_input, mock_get_yes_no):
        """Test revert workflow when user cancels."""
        mock_input.return_value = "/some/path"
        mock_get_yes_no.return_value = False  # Don't confirm revert
        
        # Mock path.exists() and path.is_dir()
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.is_dir", return_value=True):
            handle_revert_workflow()
        
        # Should print cancelled message
        cancel_calls = [call for call in mock_print.call_args_list if "cancelled" in str(call)]
        assert len(cancel_calls) > 0


class TestHandleConfigWorkflow:
    """Test config workflow handling."""

    @patch("metadata_multitool.interactive.save_config")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_config_workflow_view_config(self, mock_print, mock_input, mock_save_config):
        """Test config workflow with view current config."""
        mock_input.side_effect = ["1", "q"]  # View config, then quit
        
        config = {"batch_size": 100, "max_workers": 4}
        handle_config_workflow(config)
        
        # Should display config values
        config_calls = [call for call in mock_print.call_args_list if "batch_size" in str(call)]
        assert len(config_calls) > 0

    @patch("metadata_multitool.interactive.save_config")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_config_workflow_set_batch_size(self, mock_print, mock_input, mock_save_config):
        """Test config workflow with setting batch size."""
        mock_input.side_effect = ["2", "200", "q"]  # Set batch size, value 200, quit
        
        config = {}
        handle_config_workflow(config)
        
        mock_save_config.assert_called()
        assert config["batch_size"] == 200


class TestHandleBatchWorkflow:
    """Test batch workflow handling."""

    @patch("metadata_multitool.interactive.get_yes_no")
    @patch("metadata_multitool.interactive.iter_images")
    @patch("metadata_multitool.interactive.process_batch")
    @patch("metadata_multitool.interactive.get_config_value")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_handle_batch_workflow_clean_operation(self, mock_print, mock_input, mock_get_config_value, mock_process_batch, mock_iter_images, mock_get_yes_no, tmp_path):
        """Test batch workflow with clean operation."""
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"test")
        
        mock_input.side_effect = [
            str(tmp_path),  # path input
            "1",  # operation choice (clean)
            "",  # default output folder
        ]
        mock_get_yes_no.side_effect = [False, False]  # Not verbose, not dry run
        mock_iter_images.return_value = [test_image]
        mock_get_config_value.side_effect = [100, 4]  # batch_size, max_workers
        mock_process_batch.return_value = (1, 1, [])  # Successful
        
        handle_batch_workflow({})
        
        mock_process_batch.assert_called_once()


class TestIntegration:
    """Integration tests for interactive workflows."""

    @patch("metadata_multitool.interactive.load_config")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_full_interactive_session(self, mock_print, mock_input, mock_load_config):
        """Test a complete interactive session."""
        mock_load_config.return_value = {}
        
        # Simulate: view main menu -> invalid choice -> quit
        mock_input.side_effect = ["invalid", "q"]
        
        result = interactive_mode()
        
        assert result == 0
        
        # Should show main menu and handle invalid choice
        menu_calls = [call for call in mock_print.call_args_list if "Main Menu" in str(call)]
        assert len(menu_calls) > 0
        
        invalid_calls = [call for call in mock_print.call_args_list if "Invalid choice" in str(call)]
        assert len(invalid_calls) > 0