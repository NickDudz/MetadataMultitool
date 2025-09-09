"""Shared test fixtures and configuration."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from PIL import Image


@pytest.fixture
def tmp_path() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a sample image file for testing."""
    img_path = tmp_path / "sample.jpg"
    with Image.new("RGB", (100, 100), color="red") as img:
        img.save(img_path, "JPEG")
    return img_path


@pytest.fixture
def sample_images(tmp_path: Path) -> list[Path]:
    """Create multiple sample image files for testing."""
    images = []
    for i, color in enumerate(["red", "green", "blue", "yellow", "purple"]):
        img_path = tmp_path / f"sample_{i}.jpg"
        with Image.new("RGB", (50, 50), color=color) as img:
            img.save(img_path, "JPEG")
        images.append(img_path)
    return images


@pytest.fixture
def csv_mapping_file(tmp_path: Path) -> Path:
    """Create a CSV mapping file for testing."""
    csv_file = tmp_path / "mapping.csv"
    csv_content = "real_label,poison_label\ncat,toaster\ndog,sedan\nperson,mailbox\n"
    csv_file.write_text(csv_content, encoding="utf-8")
    return csv_file


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parents[1]
