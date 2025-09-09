"""Tests for EXIF module functionality."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from metadata_multitool.exif import has_exiftool, run_exiftool, strip_all_metadata


class TestHasExiftool:
    """Test exiftool availability detection."""

    def test_has_exiftool_when_available(self) -> None:
        """Test has_exiftool returns True when exiftool is available."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = has_exiftool()
            assert result is True
            mock_run.assert_called_once_with(
                ["exiftool", "-ver"], check=True, capture_output=True, text=True
            )

    def test_has_exiftool_when_not_available(self) -> None:
        """Test has_exiftool returns False when exiftool is not available."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "exiftool")

            result = has_exiftool()
            assert result is False

    def test_has_exiftool_on_exception(self) -> None:
        """Test has_exiftool returns False on any exception."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = has_exiftool()
            assert result is False


class TestRunExiftool:
    """Test exiftool execution."""

    def test_run_exiftool_success(self) -> None:
        """Test successful exiftool execution."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock(returncode=0, stdout="", stderr="")
            mock_run.return_value = mock_result

            run_exiftool(["-ver"])
            mock_run.assert_called_once_with(
                ["exiftool", "-ver"], check=True, text=True, capture_output=True
            )

    def test_run_exiftool_with_args(self) -> None:
        """Test exiftool execution with various arguments."""
        with patch("subprocess.run") as mock_run:
            mock_result = Mock(returncode=0, stdout="", stderr="")
            mock_run.return_value = mock_result

            args = ["-overwrite_original", "-all=", "/path/to/image.jpg"]
            run_exiftool(args)
            mock_run.assert_called_once_with(["exiftool"] + args, check=True, text=True, capture_output=True)

    def test_run_exiftool_raises_on_error(self) -> None:
        """Test that run_exiftool raises on subprocess error."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "exiftool")

            with pytest.raises(subprocess.CalledProcessError):
                run_exiftool(["-ver"])


class TestStripAllMetadata:
    """Test metadata stripping functionality."""

    def test_strip_all_metadata_with_exiftool(self, tmp_path: Path) -> None:
        """Test metadata stripping when exiftool is available."""
        img_path = tmp_path / "test.jpg"
        with Image.new("RGB", (100, 100), color="red") as img:
            img.save(img_path, "JPEG")

        with patch("metadata_multitool.exif.has_exiftool", return_value=True):
            with patch("metadata_multitool.exif.run_exiftool") as mock_run:
                strip_all_metadata(img_path)

                mock_run.assert_called_once_with(
                    ["-overwrite_original", "-all=", str(img_path)]
                )

    def test_strip_all_metadata_without_exiftool(self, tmp_path: Path) -> None:
        """Test metadata stripping when exiftool is not available."""
        img_path = tmp_path / "test.jpg"
        with Image.new("RGB", (100, 100), color="red") as img:
            img.save(img_path, "JPEG")

        with patch("metadata_multitool.exif.has_exiftool", return_value=False):
            with patch("metadata_multitool.exif.run_exiftool") as mock_run:
                strip_all_metadata(img_path)

                # Should not call exiftool
                mock_run.assert_not_called()

                # Should still process the image with PIL
                assert img_path.exists()

    def test_strip_all_metadata_pil_fallback(self, tmp_path: Path) -> None:
        """Test PIL fallback for metadata stripping."""
        img_path = tmp_path / "test.jpg"
        with Image.new("RGB", (100, 100), color="red") as img:
            img.save(img_path, "JPEG")

        with patch("metadata_multitool.exif.has_exiftool", return_value=False):
            strip_all_metadata(img_path)

            # Verify the file still exists and is readable
            assert img_path.exists()
            with Image.open(img_path) as img:
                assert img.size == (100, 100)
                assert img.mode == "RGB"

    def test_strip_all_metadata_different_formats(self, tmp_path: Path) -> None:
        """Test metadata stripping with different image formats."""
        formats = [
            ("test.jpg", "JPEG"),
            ("test.png", "PNG"),
            ("test.tiff", "TIFF"),
            ("test.webp", "WEBP"),
            ("test.bmp", "BMP"),
        ]

        for filename, format_name in formats:
            img_path = tmp_path / filename
            with Image.new("RGB", (50, 50), color="blue") as img:
                img.save(img_path, format_name)

            with patch("metadata_multitool.exif.has_exiftool", return_value=True):
                with patch("metadata_multitool.exif.run_exiftool") as mock_run:
                    strip_all_metadata(img_path)

                    if filename.endswith('.bmp'):
                        # BMP files are skipped, so run_exiftool should not be called
                        mock_run.assert_not_called()
                    else:
                        mock_run.assert_called_once_with(
                            ["-overwrite_original", "-all=", str(img_path)]
                        )

    def test_strip_all_metadata_nonexistent_file(self, tmp_path: Path) -> None:
        """Test metadata stripping with nonexistent file."""
        nonexistent_path = tmp_path / "nonexistent.jpg"

        with patch("metadata_multitool.exif.has_exiftool", return_value=True):
            with patch("metadata_multitool.exif.run_exiftool") as mock_run:
                # This should raise an exception when exiftool tries to process
                # a nonexistent file
                mock_run.side_effect = subprocess.CalledProcessError(1, "exiftool")

                with pytest.raises(subprocess.CalledProcessError):
                    strip_all_metadata(nonexistent_path)
