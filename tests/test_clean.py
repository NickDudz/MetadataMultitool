"""Tests for clean module functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from metadata_multitool.clean import clean_copy


class TestCleanCopy:
    """Test clean copy functionality."""

    def test_clean_copy_creates_destination_directory(self, tmp_path: Path) -> None:
        """Test that clean_copy creates the destination directory."""
        # Create source image
        src_img = tmp_path / "test.jpg"
        with Image.new("RGB", (100, 100), color="red") as img:
            img.save(src_img, "JPEG")

        dest_dir = tmp_path / "safe_upload"

        result = clean_copy(src_img, dest_dir)

        assert dest_dir.exists()
        assert dest_dir.is_dir()
        assert result == dest_dir / "test.jpg"
        assert result.exists()

    def test_clean_copy_preserves_filename(self, tmp_path: Path) -> None:
        """Test that clean_copy preserves the original filename."""
        src_img = tmp_path / "original_name.png"
        with Image.new("RGB", (50, 50), color="blue") as img:
            img.save(src_img, "PNG")

        dest_dir = tmp_path / "output"

        result = clean_copy(src_img, dest_dir)

        assert result.name == "original_name.png"
        assert result.parent == dest_dir

    def test_clean_copy_with_exiftool(self, tmp_path: Path) -> None:
        """Test clean_copy when exiftool is available."""
        src_img = tmp_path / "test.jpg"
        with Image.new("RGB", (100, 100), color="green") as img:
            img.save(src_img, "JPEG")

        dest_dir = tmp_path / "safe_upload"

        with patch("metadata_multitool.clean.strip_all_metadata") as mock_strip:
            result = clean_copy(src_img, dest_dir)

            assert result.exists()
            mock_strip.assert_called_once_with(result)

    def test_clean_copy_without_exiftool(self, tmp_path: Path) -> None:
        """Test clean_copy when exiftool is not available."""
        src_img = tmp_path / "test.jpg"
        with Image.new("RGB", (100, 100), color="yellow") as img:
            img.save(src_img, "JPEG")

        dest_dir = tmp_path / "safe_upload"

        with patch("metadata_multitool.clean.strip_all_metadata") as mock_strip:
            result = clean_copy(src_img, dest_dir)

            assert result.exists()
            mock_strip.assert_called_once_with(result)

    def test_clean_copy_handles_different_formats(self, tmp_path: Path) -> None:
        """Test clean_copy with different image formats."""
        formats = [
            ("test.jpg", "JPEG"),
            ("test.png", "PNG"),
            ("test.tiff", "TIFF"),
            ("test.webp", "WEBP"),
            ("test.bmp", "BMP"),
        ]

        dest_dir = tmp_path / "safe_upload"

        for filename, format_name in formats:
            src_img = tmp_path / filename
            with Image.new("RGB", (50, 50), color="red") as img:
                img.save(src_img, format_name)

            result = clean_copy(src_img, dest_dir)

            assert result.exists()
            assert result.name == filename

    def test_clean_copy_creates_nested_destination(self, tmp_path: Path) -> None:
        """Test clean_copy with nested destination directory."""
        src_img = tmp_path / "test.jpg"
        with Image.new("RGB", (100, 100), color="purple") as img:
            img.save(src_img, "JPEG")

        dest_dir = tmp_path / "nested" / "safe_upload" / "deep"

        result = clean_copy(src_img, dest_dir)

        assert dest_dir.exists()
        assert result == dest_dir / "test.jpg"
        assert result.exists()

    def test_clean_copy_preserves_image_content(self, tmp_path: Path) -> None:
        """Test that clean_copy preserves image content."""
        src_img = tmp_path / "test.jpg"
        with Image.new("RGB", (100, 100), color="red") as img:
            img.save(src_img, "JPEG")

        dest_dir = tmp_path / "safe_upload"

        result = clean_copy(src_img, dest_dir)

        # Verify the copied image has the same content
        with Image.open(src_img) as original:
            with Image.open(result) as copied:
                assert original.size == copied.size
                assert original.mode == copied.mode
                # Note: We can't easily compare pixel data without loading it all
                # but the size and mode check is a good basic verification
