"""
Integration tests for complete workflows in Metadata Multitool.

These tests verify end-to-end functionality by running actual operations
on test images and verifying results.
"""

import json
import tempfile
import shutil
from pathlib import Path
from typing import Generator, List
import pytest
from PIL import Image, ExifTags
import subprocess
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from metadata_multitool import clean, poison, revert, core
from metadata_multitool.cli import main as cli_main


class TestWorkflows:
    """Test complete workflows from start to finish."""

    @pytest.fixture
    def test_images_dir(self) -> Generator[Path, None, None]:
        """Create temporary directory with test images."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test images with metadata
            test_images = []
            for i in range(3):
                img_path = temp_path / f"test_image_{i}.jpg"
                
                # Create a simple test image
                img = Image.new('RGB', (100, 100), color=(255, 0, 0))
                
                # Add some EXIF metadata
                exif_dict = {
                    "0th": {
                        ExifTags.TAGS_V2[256]: 100,  # ImageWidth
                        ExifTags.TAGS_V2[257]: 100,  # ImageLength
                        ExifTags.TAGS_V2[272]: "Test Camera",  # Make
                        ExifTags.TAGS_V2[306]: "2024:01:01 12:00:00",  # DateTime
                    },
                    "GPS": {
                        ExifTags.GPSTAGS[1]: "N",  # GPSLatitudeRef
                        ExifTags.GPSTAGS[2]: (40, 0, 0),  # GPSLatitude
                        ExifTags.GPSTAGS[3]: "W",  # GPSLongitudeRef
                        ExifTags.GPSTAGS[4]: (74, 0, 0),  # GPSLongitude
                    }
                }
                
                # Save with metadata (simplified - real implementation would use piexif)
                img.save(str(img_path), "JPEG", quality=95)
                test_images.append(img_path)
            
            yield temp_path

    def test_clean_workflow(self, test_images_dir: Path) -> None:
        """Test complete clean workflow."""
        # Setup
        safe_upload_dir = test_images_dir / "safe_upload"
        
        # Get list of original images
        original_images = list(test_images_dir.glob("*.jpg"))
        assert len(original_images) == 3
        
        # Run clean operation
        clean.clean_directory(
            input_path=test_images_dir,
            output_path=safe_upload_dir,
            backup=True
        )
        
        # Verify results
        assert safe_upload_dir.exists()
        cleaned_images = list(safe_upload_dir.glob("*.jpg"))
        assert len(cleaned_images) == 3
        
        # Verify each cleaned image exists and has different size (metadata removed)
        for original in original_images:
            cleaned = safe_upload_dir / original.name
            assert cleaned.exists()
            
            # Size should be different (metadata removed)
            original_size = original.stat().st_size
            cleaned_size = cleaned.stat().st_size
            assert cleaned_size <= original_size  # Should be same or smaller

    def test_poison_revert_workflow(self, test_images_dir: Path) -> None:
        """Test complete poison → revert workflow."""
        # Setup
        original_images = list(test_images_dir.glob("*.jpg"))
        assert len(original_images) == 3
        
        # Record original state
        original_files = {f.name: f.stat().st_mtime for f in original_images}
        
        # Run poison operation
        poison_result = poison.poison_directory(
            input_path=test_images_dir,
            preset="label_flip",
            create_sidecars=True,
            true_hint="test image"
        )
        
        # Verify poison operation created files
        assert poison_result["poisoned_count"] == 3
        
        # Check for sidecar files
        sidecar_files = list(test_images_dir.glob("*.txt"))
        assert len(sidecar_files) == 3
        
        # Check operation log was created
        log_file = test_images_dir / ".mm_poisonlog.json"
        assert log_file.exists()
        
        # Verify log content
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        assert len(log_data) == 3
        assert all("sidecar_files" in entry for entry in log_data)
        
        # Run revert operation
        revert_result = revert.revert_directory(test_images_dir)
        
        # Verify revert cleaned up poison artifacts
        assert revert_result["reverted_count"] == 3
        
        # Check sidecar files were removed
        remaining_sidecars = list(test_images_dir.glob("*.txt"))
        assert len(remaining_sidecars) == 0
        
        # Check log file was cleaned up or marked as processed
        if log_file.exists():
            with open(log_file, 'r') as f:
                log_data = json.load(f)
            # Log should be empty or contain only processed entries
            assert len(log_data) == 0 or all(entry.get("reverted", False) for entry in log_data)

    def test_batch_processing_workflow(self, test_images_dir: Path) -> None:
        """Test batch processing with larger number of files."""
        # Create more test images for batch processing
        additional_images = []
        for i in range(10):  # Total of 13 images
            img_path = test_images_dir / f"batch_test_{i}.jpg"
            img = Image.new('RGB', (50, 50), color=(0, 255, 0))
            img.save(str(img_path), "JPEG")
            additional_images.append(img_path)
        
        # Test batch clean with specific batch size
        from metadata_multitool.batch import batch_process_clean
        
        result = batch_process_clean(
            input_paths=[test_images_dir],
            output_dir=test_images_dir / "batch_output",
            batch_size=5,
            max_workers=2
        )
        
        # Verify batch processing results
        assert result["total_processed"] == 13  # 3 original + 10 additional
        assert result["successful"] == 13
        assert result["failed"] == 0
        
        # Verify output directory
        output_dir = test_images_dir / "batch_output"
        assert output_dir.exists()
        output_images = list(output_dir.glob("*.jpg"))
        assert len(output_images) == 13

    def test_cli_integration(self, test_images_dir: Path) -> None:
        """Test CLI integration for all major commands."""
        # Change to test directory
        original_cwd = Path.cwd()
        try:
            os.chdir(test_images_dir)
            
            # Test CLI clean command
            result = subprocess.run([
                sys.executable, "-m", "metadata_multitool.cli",
                "clean", ".", "--backup"
            ], capture_output=True, text=True, cwd=test_images_dir)
            
            assert result.returncode == 0
            assert (test_images_dir / "safe_upload").exists()
            
            # Test CLI poison command
            result = subprocess.run([
                sys.executable, "-m", "metadata_multitool.cli",
                "poison", ".", "--preset", "label_flip", "--sidecar"
            ], capture_output=True, text=True, cwd=test_images_dir)
            
            assert result.returncode == 0
            assert len(list(test_images_dir.glob("*.txt"))) >= 3
            
            # Test CLI revert command
            result = subprocess.run([
                sys.executable, "-m", "metadata_multitool.cli",
                "revert", "."
            ], capture_output=True, text=True, cwd=test_images_dir)
            
            assert result.returncode == 0
            assert len(list(test_images_dir.glob("*.txt"))) == 0
            
        finally:
            os.chdir(original_cwd)

    def test_error_handling_workflow(self, test_images_dir: Path) -> None:
        """Test error handling in workflows."""
        # Create invalid image file
        invalid_file = test_images_dir / "invalid.jpg"
        invalid_file.write_text("This is not a valid image")
        
        # Create read-only file (permission test)
        readonly_file = test_images_dir / "readonly.jpg"
        img = Image.new('RGB', (50, 50), color=(0, 0, 255))
        img.save(str(readonly_file), "JPEG")
        readonly_file.chmod(0o444)  # Read-only
        
        try:
            # Test clean operation with mixed valid/invalid files
            result = clean.clean_directory(
                input_path=test_images_dir,
                output_path=test_images_dir / "error_test_output",
                backup=False
            )
            
            # Should handle errors gracefully
            assert "errors" in result
            # Should still process valid files
            valid_files = [f for f in test_images_dir.glob("*.jpg") 
                          if f.name not in ["invalid.jpg", "readonly.jpg"]]
            assert result["successful"] == len(valid_files)
            
        finally:
            # Restore permissions for cleanup
            if readonly_file.exists():
                readonly_file.chmod(0o644)

    def test_configuration_workflow(self, test_images_dir: Path) -> None:
        """Test workflow with custom configuration."""
        # Create custom config
        config_file = test_images_dir / ".mm_config.yaml"
        config_content = """
batch_processing:
  batch_size: 2
  max_workers: 1
  memory_limit_mb: 512

clean:
  backup_originals: true
  output_directory: "custom_output"

poison:
  default_preset: "clip_confuse"
  create_sidecars: true
"""
        config_file.write_text(config_content)
        
        # Test that configuration is used
        from metadata_multitool.config import load_config
        config = load_config(config_file)
        
        assert config["batch_processing"]["batch_size"] == 2
        assert config["clean"]["output_directory"] == "custom_output"
        
        # Test clean operation uses custom config
        clean.clean_directory(
            input_path=test_images_dir,
            config_path=config_file
        )
        
        # Verify custom output directory was used
        custom_output = test_images_dir / "custom_output"
        assert custom_output.exists()

    def test_dry_run_workflow(self, test_images_dir: Path) -> None:
        """Test dry-run functionality across operations."""
        original_files = list(test_images_dir.glob("*"))
        original_count = len(original_files)
        
        # Test dry-run clean
        result = clean.clean_directory(
            input_path=test_images_dir,
            output_path=test_images_dir / "dry_run_output",
            dry_run=True
        )
        
        # Should report what would be done without making changes
        assert "would_process" in result
        assert result["would_process"] >= 3
        
        # No files should be created
        assert not (test_images_dir / "dry_run_output").exists()
        assert len(list(test_images_dir.glob("*"))) == original_count
        
        # Test dry-run poison
        result = poison.poison_directory(
            input_path=test_images_dir,
            preset="label_flip",
            create_sidecars=True,
            dry_run=True
        )
        
        # Should report what would be done
        assert "would_poison" in result
        assert result["would_poison"] >= 3
        
        # No sidecar files should be created
        assert len(list(test_images_dir.glob("*.txt"))) == 0


class TestPerformanceWorkflows:
    """Test performance-related workflows."""

    def test_memory_limited_workflow(self, tmp_path: Path) -> None:
        """Test workflow with memory constraints."""
        # Create test images
        for i in range(5):
            img_path = tmp_path / f"memory_test_{i}.jpg"
            # Create larger image to test memory usage
            img = Image.new('RGB', (1000, 1000), color=(i * 50, 100, 150))
            img.save(str(img_path), "JPEG")
        
        # Test with very low memory limit
        from metadata_multitool.batch import batch_process_clean
        
        result = batch_process_clean(
            input_paths=[tmp_path],
            output_dir=tmp_path / "memory_output",
            batch_size=1,  # Process one at a time
            max_workers=1,
            memory_limit_mb=100  # Very low limit
        )
        
        # Should complete successfully despite memory constraints
        assert result["successful"] == 5
        assert result["failed"] == 0

    def test_large_batch_workflow(self, tmp_path: Path) -> None:
        """Test workflow with larger number of files."""
        # Create many small test images
        for i in range(50):
            img_path = tmp_path / f"large_batch_{i:03d}.jpg"
            img = Image.new('RGB', (100, 100), color=(i % 255, 100, 150))
            img.save(str(img_path), "JPEG")
        
        # Test large batch processing
        from metadata_multitool.batch import batch_process_clean
        
        result = batch_process_clean(
            input_paths=[tmp_path],
            output_dir=tmp_path / "large_output",
            batch_size=10,
            max_workers=2
        )
        
        # Verify all files processed
        assert result["total_processed"] == 50
        assert result["successful"] == 50
        
        # Verify output
        output_files = list((tmp_path / "large_output").glob("*.jpg"))
        assert len(output_files) == 50


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])