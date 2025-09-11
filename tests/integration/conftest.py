"""
Pytest configuration and fixtures for integration tests.

Provides common fixtures and utilities for integration testing.
"""

import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, List
import pytest
from PIL import Image
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture(scope="session")
def sample_image_data() -> Dict[str, Dict]:
    """Sample image configurations for consistent test data."""
    return {
        "small_rgb.jpg": {
            "size": (100, 100),
            "mode": "RGB",
            "color": (255, 0, 0),
            "format": "JPEG",
            "quality": 95
        },
        "medium_rgba.png": {
            "size": (300, 200),
            "mode": "RGBA",
            "color": (0, 255, 0, 128),
            "format": "PNG"
        },
        "large_grayscale.tiff": {
            "size": (800, 600),
            "mode": "L",
            "color": 128,
            "format": "TIFF"
        },
        "tiny_webp.webp": {
            "size": (50, 50),
            "mode": "RGB",
            "color": (0, 0, 255),
            "format": "WEBP"
        }
    }


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Create temporary workspace for integration tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="mm_integration_"))
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def populated_workspace(temp_workspace: Path, sample_image_data: Dict) -> Path:
    """Create workspace populated with sample images."""
    for filename, config in sample_image_data.items():
        img_path = temp_workspace / filename
        
        img = Image.new(
            config["mode"],
            config["size"],
            config["color"]
        )
        
        save_kwargs = {}
        if config["format"] == "JPEG":
            save_kwargs["quality"] = config.get("quality", 95)
        
        img.save(str(img_path), config["format"], **save_kwargs)
    
    return temp_workspace


@pytest.fixture
def nested_workspace(temp_workspace: Path, sample_image_data: Dict) -> Path:
    """Create workspace with nested directory structure."""
    # Create nested directories
    subdirs = [
        temp_workspace / "photos" / "2024" / "january",
        temp_workspace / "photos" / "2024" / "february",
        temp_workspace / "archive" / "old_photos",
        temp_workspace / "work" / "projects"
    ]
    
    for subdir in subdirs:
        subdir.mkdir(parents=True)
        
        # Add subset of sample images to each directory
        for i, (filename, config) in enumerate(sample_image_data.items()):
            if i % 2 == subdirs.index(subdir) % 2:  # Distribute images
                img_path = subdir / filename
                
                img = Image.new(
                    config["mode"],
                    config["size"],
                    config["color"]
                )
                
                save_kwargs = {}
                if config["format"] == "JPEG":
                    save_kwargs["quality"] = config.get("quality", 95)
                
                img.save(str(img_path), config["format"], **save_kwargs)
    
    return temp_workspace


@pytest.fixture
def large_workspace(temp_workspace: Path) -> Path:
    """Create workspace with many images for performance testing."""
    # Create 100 small test images
    for i in range(100):
        img_path = temp_workspace / f"perf_test_{i:03d}.jpg"
        
        # Vary colors and sizes slightly
        size = (100 + (i % 50), 100 + (i % 30))
        color = (i % 255, (i * 2) % 255, (i * 3) % 255)
        
        img = Image.new("RGB", size, color)
        img.save(str(img_path), "JPEG", quality=85)
    
    return temp_workspace


@pytest.fixture
def config_workspace(temp_workspace: Path) -> Path:
    """Create workspace with various configuration files."""
    # Create different config scenarios
    configs = {
        ".mm_config.yaml": """
batch_processing:
  batch_size: 10
  max_workers: 2
  memory_limit_mb: 512

clean:
  backup_originals: true
  output_directory: "cleaned_output"

poison:
  default_preset: "label_flip"
  create_sidecars: true
""",
        "subdir/.mm_config.yaml": """
batch_processing:
  batch_size: 5
  max_workers: 1

poison:
  default_preset: "clip_confuse"
""",
        "custom_config.yaml": """
clean:
  backup_originals: false
  preserve_structure: true
"""
    }
    
    for config_path, config_content in configs.items():
        full_path = temp_workspace / config_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(config_content)
    
    return temp_workspace


class IntegrationTestHelper:
    """Helper class for common integration test operations."""
    
    @staticmethod
    def count_files_by_extension(directory: Path, extension: str) -> int:
        """Count files with specific extension in directory."""
        return len(list(directory.glob(f"*{extension}")))
    
    @staticmethod
    def get_all_files(directory: Path, recursive: bool = False) -> List[Path]:
        """Get all files in directory, optionally recursive."""
        if recursive:
            return [f for f in directory.rglob("*") if f.is_file()]
        else:
            return [f for f in directory.iterdir() if f.is_file()]
    
    @staticmethod
    def create_corrupted_image(path: Path) -> None:
        """Create a corrupted image file for error testing."""
        path.write_text("This is not a valid image file content")
    
    @staticmethod
    def create_readonly_file(path: Path, content: bytes = b"") -> None:
        """Create a read-only file for permission testing."""
        path.write_bytes(content)
        path.chmod(0o444)
    
    @staticmethod
    def verify_no_sidecars(directory: Path, recursive: bool = False) -> bool:
        """Verify no sidecar files exist in directory."""
        sidecar_extensions = ['.txt', '.json', '.xmp']
        
        if recursive:
            files = directory.rglob("*")
        else:
            files = directory.iterdir()
        
        sidecars = [f for f in files 
                   if f.is_file() and f.suffix.lower() in sidecar_extensions]
        return len(sidecars) == 0
    
    @staticmethod
    def verify_log_file_exists(directory: Path) -> bool:
        """Verify operation log file exists."""
        log_files = list(directory.glob("*.mm_poisonlog.json"))
        return len(log_files) > 0
    
    @staticmethod
    def get_directory_size(directory: Path) -> int:
        """Get total size of all files in directory."""
        total_size = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size


@pytest.fixture
def test_helper() -> IntegrationTestHelper:
    """Provide test helper instance."""
    return IntegrationTestHelper()


# Skip tests if required dependencies are not available
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "requires_exiftool: mark test as requiring ExifTool"
    )
    config.addinivalue_line(
        "markers", "requires_gui: mark test as requiring PyQt6 GUI"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_runtest_setup(item):
    """Set up test runs with dependency checks."""
    # Check for ExifTool requirement
    if item.get_closest_marker("requires_exiftool"):
        try:
            import subprocess
            subprocess.run(["exiftool", "-ver"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("ExifTool not available")
    
    # Check for GUI requirement
    if item.get_closest_marker("requires_gui"):
        try:
            import PyQt6
        except ImportError:
            pytest.skip("PyQt6 not available")


# Custom assertion helpers
def assert_images_equal_count(dir1: Path, dir2: Path) -> None:
    """Assert two directories have same number of image files."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.bmp'}
    
    dir1_images = [f for f in dir1.iterdir() 
                   if f.suffix.lower() in image_extensions]
    dir2_images = [f for f in dir2.iterdir() 
                   if f.suffix.lower() in image_extensions]
    
    assert len(dir1_images) == len(dir2_images), \
        f"Image count mismatch: {len(dir1_images)} vs {len(dir2_images)}"


def assert_no_metadata_leakage(directory: Path) -> None:
    """Assert no metadata files or logs are left in directory."""
    metadata_patterns = [
        "*.mm_poisonlog.json",
        "*.mm_progress.json",
        "*.mm_temp*"
    ]
    
    for pattern in metadata_patterns:
        files = list(directory.glob(pattern))
        assert len(files) == 0, f"Found metadata files: {files}"


# Add custom assertions to pytest namespace
pytest.assert_images_equal_count = assert_images_equal_count
pytest.assert_no_metadata_leakage = assert_no_metadata_leakage