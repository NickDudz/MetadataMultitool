"""Tests for core module functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from metadata_multitool.core import (
    InvalidPathError,
    ensure_dir,
    iter_images,
    rand_token,
    read_log,
    rel_to_root,
    write_log,
)


class TestIterImages:
    """Test image discovery functionality."""

    def test_iter_images_single_file(self, tmp_path: Path) -> None:
        """Test iterating a single image file."""
        img_file = tmp_path / "test.jpg"
        img_file.touch()

        result = list(iter_images(img_file))
        assert len(result) == 1
        assert result[0] == img_file

    def test_iter_images_nonexistent_file(self, tmp_path: Path) -> None:
        """Test iterating a nonexistent file."""
        nonexistent = tmp_path / "nonexistent.jpg"

        with pytest.raises(InvalidPathError):
            list(iter_images(nonexistent))

    def test_iter_images_non_image_file(self, tmp_path: Path) -> None:
        """Test iterating a non-image file."""
        txt_file = tmp_path / "test.txt"
        txt_file.touch()

        result = list(iter_images(txt_file))
        assert len(result) == 0

    def test_iter_images_directory(self, tmp_path: Path) -> None:
        """Test iterating a directory with multiple images."""
        # Create various image files
        (tmp_path / "test1.jpg").touch()
        (tmp_path / "test2.png").touch()
        (tmp_path / "test3.tiff").touch()
        (tmp_path / "test4.webp").touch()
        (tmp_path / "test5.bmp").touch()
        (tmp_path / "test6.jpeg").touch()
        (tmp_path / "test7.tif").touch()
        # Non-image files
        (tmp_path / "test8.txt").touch()
        (tmp_path / "test9.doc").touch()

        result = list(iter_images(tmp_path))
        assert len(result) == 7
        extensions = {f.suffix.lower() for f in result}
        expected = {".jpg", ".png", ".tiff", ".webp", ".bmp", ".jpeg", ".tif"}
        assert extensions == expected

    def test_iter_images_nested_directory(self, tmp_path: Path) -> None:
        """Test iterating a nested directory structure."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.jpg").touch()
        (tmp_path / "root.png").touch()

        result = list(iter_images(tmp_path))
        assert len(result) == 2
        names = {f.name for f in result}
        assert names == {"nested.jpg", "root.png"}


class TestEnsureDir:
    """Test directory creation functionality."""

    def test_ensure_dir_creates_directory(self, tmp_path: Path) -> None:
        """Test that ensure_dir creates a directory."""
        new_dir = tmp_path / "new_directory"

        result = ensure_dir(new_dir)
        assert result == new_dir
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_dir_creates_nested_directory(self, tmp_path: Path) -> None:
        """Test that ensure_dir creates nested directories."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"

        result = ensure_dir(nested_dir)
        assert result == nested_dir
        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_ensure_dir_existing_directory(self, tmp_path: Path) -> None:
        """Test that ensure_dir handles existing directories."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        result = ensure_dir(existing_dir)
        assert result == existing_dir
        assert existing_dir.exists()


class TestRandToken:
    """Test random token generation."""

    def test_rand_token_default_length(self) -> None:
        """Test default token length."""
        token = rand_token()
        assert len(token) == 6
        assert token.isalnum()
        assert token.islower()

    def test_rand_token_custom_length(self) -> None:
        """Test custom token length."""
        token = rand_token(10)
        assert len(token) == 10
        assert token.isalnum()
        assert token.islower()

    def test_rand_token_uniqueness(self) -> None:
        """Test that tokens are reasonably unique."""
        tokens = {rand_token() for _ in range(100)}
        assert len(tokens) > 90  # Allow for some collisions


class TestRelToRoot:
    """Test relative path calculation."""

    def test_rel_to_root_file_to_dir(self, tmp_path: Path) -> None:
        """Test relative path from file to directory."""
        root = tmp_path / "root"
        root.mkdir()
        target = root / "subdir" / "file.jpg"
        target.parent.mkdir()
        target.touch()

        result = rel_to_root(target, root)
        # Use pathlib to handle cross-platform path separators
        expected = Path("subdir/file.jpg")
        assert Path(result) == expected

    def test_rel_to_root_file_to_file(self, tmp_path: Path) -> None:
        """Test relative path from file to file."""
        root_file = tmp_path / "root.jpg"
        root_file.touch()
        target = tmp_path / "subdir" / "file.jpg"
        target.parent.mkdir()
        target.touch()

        result = rel_to_root(target, root_file)
        # Use pathlib to handle cross-platform path separators
        expected = Path("subdir/file.jpg")
        assert Path(result) == expected

    def test_rel_to_root_same_directory(self, tmp_path: Path) -> None:
        """Test relative path within same directory."""
        root = tmp_path / "root"
        root.mkdir()
        target = root / "file.jpg"
        target.touch()

        result = rel_to_root(target, root)
        assert result == "file.jpg"


class TestLogOperations:
    """Test log reading and writing functionality."""

    def test_read_log_nonexistent(self, tmp_path: Path) -> None:
        """Test reading from nonexistent log file."""
        result = read_log(tmp_path)
        assert result == {"entries": {}}

    def test_write_and_read_log(self, tmp_path: Path) -> None:
        """Test writing and reading log data."""
        test_data = {
            "entries": {
                "test.jpg": {
                    "caption": "test caption",
                    "tags": ["test", "tag"],
                    "surfaces": {"xmp": True, "iptc": False},
                    "original_name": None,
                }
            }
        }

        write_log(tmp_path, test_data)
        result = read_log(tmp_path)
        assert result == test_data

    def test_log_file_creation(self, tmp_path: Path) -> None:
        """Test that log file is created."""
        test_data = {"entries": {}}
        write_log(tmp_path, test_data)

        log_file = tmp_path / ".mm_poisonlog.json"
        assert log_file.exists()
        assert log_file.read_text(encoding="utf-8") == '{\n  "entries": {}\n}'

    def test_log_unicode_handling(self, tmp_path: Path) -> None:
        """Test that log handles unicode properly."""
        test_data = {
            "entries": {
                "test.jpg": {"caption": "café naïve résumé", "tags": ["café", "naïve"]}
            }
        }

        write_log(tmp_path, test_data)
        result = read_log(tmp_path)
        assert result == test_data
