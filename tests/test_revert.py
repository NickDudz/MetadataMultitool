"""Tests for revert module functionality."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from metadata_multitool.revert import revert_dir


class TestRevertDir:
    """Test directory reversion functionality."""

    def test_revert_dir_nonexistent_log(self, tmp_path: Path) -> None:
        """Test reverting directory with no log file."""
        result = revert_dir(tmp_path)
        assert result == 0

    def test_revert_dir_empty_log(self, tmp_path: Path) -> None:
        """Test reverting directory with empty log."""
        log_file = tmp_path / ".mm_poisonlog.json"
        log_file.write_text('{"entries": {}}', encoding="utf-8")

        result = revert_dir(tmp_path)
        assert result == 0

    def test_revert_dir_with_sidecars(self, tmp_path: Path) -> None:
        """Test reverting directory with sidecar files."""
        # Create test files
        img_file = tmp_path / "test.jpg"
        img_file.touch()
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("test caption", encoding="utf-8")
        json_file = tmp_path / "test.json"
        json_file.write_text('{"caption": "test"}', encoding="utf-8")
        html_file = tmp_path / "test.html"
        html_file.write_text("<img>", encoding="utf-8")

        # Create log
        log_data = {
            "entries": {
                "test.jpg": {
                    "caption": "test caption",
                    "tags": ["test"],
                    "surfaces": {"sidecar": True, "json": True, "html": True},
                    "original_name": None,
                }
            }
        }
        log_file = tmp_path / ".mm_poisonlog.json"
        log_file.write_text(json.dumps(log_data), encoding="utf-8")

        result = revert_dir(tmp_path)

        # Should remove 3 sidecar files
        assert result == 3
        assert not txt_file.exists()
        assert not json_file.exists()
        assert not html_file.exists()
        assert img_file.exists()  # Original image should remain

    def test_revert_dir_with_renamed_files(self, tmp_path: Path) -> None:
        """Test reverting directory with renamed files."""
        # Create renamed file
        renamed_file = tmp_path / "test_toaster.jpg"
        renamed_file.touch()

        # Create log with original name
        log_data = {
            "entries": {
                "test_toaster.jpg": {
                    "caption": "test caption",
                    "tags": ["test"],
                    "surfaces": {},
                    "original_name": "test.jpg",
                }
            }
        }
        log_file = tmp_path / ".mm_poisonlog.json"
        log_file.write_text(json.dumps(log_data), encoding="utf-8")

        result = revert_dir(tmp_path)

        # Should restore original filename
        original_file = tmp_path / "test.jpg"
        assert original_file.exists()
        assert not renamed_file.exists()
        assert result == 0  # No sidecars to remove

    def test_revert_dir_with_metadata_clearing(self, tmp_path: Path) -> None:
        """Test reverting directory with metadata clearing."""
        img_file = tmp_path / "test.jpg"
        img_file.touch()

        log_data = {
            "entries": {
                "test.jpg": {
                    "caption": "test caption",
                    "tags": ["test"],
                    "surfaces": {"xmp": True, "iptc": True, "exif": True},
                    "original_name": None,
                }
            }
        }
        log_file = tmp_path / ".mm_poisonlog.json"
        log_file.write_text(json.dumps(log_data), encoding="utf-8")

        with patch("metadata_multitool.revert.has_exiftool", return_value=True):
            with patch("metadata_multitool.revert.run_exiftool") as mock_run:
                result = revert_dir(tmp_path)

                # Should call exiftool to clear metadata
                mock_run.assert_called_once()
                args = mock_run.call_args[0][0]
                assert "-overwrite_original" in args
                assert str(img_file) in args
                assert "-XMP-dc:Title=" in args
                assert "-XMP-dc:Description=" in args
                assert "-IPTC:Caption-Abstract=" in args
                assert "-EXIF:UserComment=" in args

    def test_revert_dir_without_exiftool(self, tmp_path: Path) -> None:
        """Test reverting directory without exiftool."""
        img_file = tmp_path / "test.jpg"
        img_file.touch()

        log_data = {
            "entries": {
                "test.jpg": {
                    "caption": "test caption",
                    "tags": ["test"],
                    "surfaces": {"xmp": True, "iptc": True, "exif": True},
                    "original_name": None,
                }
            }
        }
        log_file = tmp_path / ".mm_poisonlog.json"
        log_file.write_text(json.dumps(log_data), encoding="utf-8")

        with patch("metadata_multitool.revert.has_exiftool", return_value=False):
            with patch("metadata_multitool.revert.run_exiftool") as mock_run:
                result = revert_dir(tmp_path)

                # Should not call exiftool
                mock_run.assert_not_called()
                assert result == 0

    def test_revert_dir_mixed_operations(self, tmp_path: Path) -> None:
        """Test reverting directory with mixed operations."""
        # Create renamed file (this is the only image file that exists)
        renamed_file = tmp_path / "test_toaster.jpg"
        renamed_file.touch()
        renamed_txt = tmp_path / "test_toaster.txt"
        renamed_txt.write_text("test caption", encoding="utf-8")

        log_data = {
            "entries": {
                "test_toaster.jpg": {
                    "caption": "test caption",
                    "tags": ["test"],
                    "surfaces": {"sidecar": True},
                    "original_name": "test.jpg",
                },
            }
        }
        log_file = tmp_path / ".mm_poisonlog.json"
        log_file.write_text(json.dumps(log_data), encoding="utf-8")

        result = revert_dir(tmp_path)

        # Should remove 1 sidecar file and restore 1 filename
        assert result == 1
        assert not renamed_txt.exists()
        assert not renamed_file.exists()
        # The original file should exist after rename
        assert (tmp_path / "test.jpg").exists()

    def test_revert_dir_handles_missing_files(self, tmp_path: Path) -> None:
        """Test reverting directory when some files are missing."""
        # Create log referencing non-existent files
        log_data = {
            "entries": {
                "missing.jpg": {
                    "caption": "test caption",
                    "tags": ["test"],
                    "surfaces": {"sidecar": True},
                    "original_name": None,
                }
            }
        }
        log_file = tmp_path / ".mm_poisonlog.json"
        log_file.write_text(json.dumps(log_data), encoding="utf-8")

        result = revert_dir(tmp_path)

        # Should handle missing files gracefully
        assert result == 0

    def test_revert_dir_handles_rename_errors(self, tmp_path: Path) -> None:
        """Test reverting directory when rename operations fail."""
        # Create file that can't be renamed (simulate permission error)
        img_file = tmp_path / "test_toaster.jpg"
        img_file.touch()

        log_data = {
            "entries": {
                "test_toaster.jpg": {
                    "caption": "test caption",
                    "tags": ["test"],
                    "surfaces": {},
                    "original_name": "test.jpg",
                }
            }
        }
        log_file = tmp_path / ".mm_poisonlog.json"
        log_file.write_text(json.dumps(log_data), encoding="utf-8")

        # Mock the rename to raise an exception
        with patch("pathlib.Path.rename", side_effect=OSError("Permission denied")):
            result = revert_dir(tmp_path)

            # Should handle the error gracefully
            assert result == 0

    def test_revert_dir_updates_log_after_rename(self, tmp_path: Path) -> None:
        """Test that log is updated after successful rename."""
        # Create renamed file
        renamed_file = tmp_path / "test_toaster.jpg"
        renamed_file.touch()

        log_data = {
            "entries": {
                "test_toaster.jpg": {
                    "caption": "test caption",
                    "tags": ["test"],
                    "surfaces": {},
                    "original_name": "test.jpg",
                }
            }
        }
        log_file = tmp_path / ".mm_poisonlog.json"
        log_file.write_text(json.dumps(log_data), encoding="utf-8")

        result = revert_dir(tmp_path)

        # Check that log was updated
        updated_log = json.loads(log_file.read_text(encoding="utf-8"))
        assert "test_toaster.jpg" not in updated_log["entries"]
        assert "test.jpg" in updated_log["entries"]

    def test_revert_dir_clears_all_entries(self, tmp_path: Path) -> None:
        """Test that all entries are cleared from log after revert."""
        img_file = tmp_path / "test.jpg"
        img_file.touch()

        log_data = {
            "entries": {
                "test.jpg": {
                    "caption": "test caption",
                    "tags": ["test"],
                    "surfaces": {},
                    "original_name": None,
                }
            }
        }
        log_file = tmp_path / ".mm_poisonlog.json"
        log_file.write_text(json.dumps(log_data), encoding="utf-8")

        result = revert_dir(tmp_path)

        # Check that log is empty
        updated_log = json.loads(log_file.read_text(encoding="utf-8"))
        assert updated_log["entries"] == {}
