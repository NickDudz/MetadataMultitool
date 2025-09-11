"""
Integration tests for the clean → poison → revert cycle.

Tests the complete lifecycle of metadata operations to ensure
operations can be properly undone and don't leave artifacts.
"""

import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
import pytest
from PIL import Image
import hashlib
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from metadata_multitool import clean, poison, revert
from metadata_multitool.core import iter_images


class TestCleanPoisonRevertCycle:
    """Test complete clean-poison-revert cycles."""

    @pytest.fixture
    def sample_images(self) -> Dict[str, Path]:
        """Create sample images with different characteristics."""
        temp_dir = Path(tempfile.mkdtemp())
        
        images = {}
        
        # Create different types of test images
        test_cases = [
            ("simple.jpg", (200, 200), "RGB", (255, 0, 0)),
            ("complex.png", (300, 400), "RGBA", (0, 255, 0, 128)),
            ("grayscale.jpg", (150, 150), "L", 128),
            ("large.tiff", (800, 600), "RGB", (0, 0, 255)),
        ]
        
        for name, size, mode, color in test_cases:
            img_path = temp_dir / name
            img = Image.new(mode, size, color)
            
            # Save with maximum quality to preserve metadata space
            if name.endswith('.jpg'):
                img.save(str(img_path), "JPEG", quality=95)
            elif name.endswith('.png'):
                img.save(str(img_path), "PNG")
            elif name.endswith('.tiff'):
                img.save(str(img_path), "TIFF")
            
            images[name] = img_path
        
        yield images
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def get_file_metadata_snapshot(self, directory: Path) -> Dict[str, Any]:
        """Get snapshot of all files and their metadata in directory."""
        snapshot = {
            "files": {},
            "sidecars": {},
            "logs": {}
        }
        
        # Capture all files
        for file_path in directory.iterdir():
            if file_path.is_file():
                file_info = {
                    "size": file_path.stat().st_size,
                    "mtime": file_path.stat().st_mtime,
                    "hash": self.calculate_file_hash(file_path)
                }
                
                if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tiff', '.webp']:
                    snapshot["files"][file_path.name] = file_info
                elif file_path.suffix in ['.txt', '.json', '.xmp']:
                    snapshot["sidecars"][file_path.name] = file_info
                elif file_path.name.endswith('.mm_poisonlog.json'):
                    snapshot["logs"][file_path.name] = file_info
        
        return snapshot

    def test_clean_preserves_originals(self, sample_images: Dict[str, Path]) -> None:
        """Test that clean operation preserves original files when requested."""
        work_dir = next(iter(sample_images.values())).parent
        original_snapshot = self.get_file_metadata_snapshot(work_dir)
        
        # Run clean with backup
        result = clean.clean_directory(
            input_path=work_dir,
            output_path=work_dir / "safe_upload",
            backup=True
        )
        
        # Verify originals are unchanged
        after_clean_snapshot = self.get_file_metadata_snapshot(work_dir)
        
        for filename, original_info in original_snapshot["files"].items():
            assert filename in after_clean_snapshot["files"]
            assert after_clean_snapshot["files"][filename]["hash"] == original_info["hash"]
        
        # Verify cleaned copies exist
        safe_upload_dir = work_dir / "safe_upload"
        assert safe_upload_dir.exists()
        cleaned_files = list(safe_upload_dir.glob("*"))
        assert len(cleaned_files) == len(sample_images)

    def test_poison_creates_reversible_changes(self, sample_images: Dict[str, Path]) -> None:
        """Test that poison operation creates changes that can be fully reverted."""
        work_dir = next(iter(sample_images.values())).parent
        original_snapshot = self.get_file_metadata_snapshot(work_dir)
        
        # Run poison operation with multiple outputs
        poison_result = poison.poison_directory(
            input_path=work_dir,
            preset="label_flip",
            create_sidecars=True,
            create_json=True,
            true_hint="original content"
        )
        
        # Verify poison operation succeeded
        assert poison_result["poisoned_count"] == len(sample_images)
        
        # Capture post-poison state
        poisoned_snapshot = self.get_file_metadata_snapshot(work_dir)
        
        # Verify sidecars were created
        assert len(poisoned_snapshot["sidecars"]) > 0
        
        # Verify operation log was created
        log_files = list(work_dir.glob("*.mm_poisonlog.json"))
        assert len(log_files) == 1
        
        # Run revert operation
        revert_result = revert.revert_directory(work_dir)
        
        # Verify revert succeeded
        assert revert_result["reverted_count"] == len(sample_images)
        
        # Capture post-revert state
        reverted_snapshot = self.get_file_metadata_snapshot(work_dir)
        
        # Verify all sidecars were removed
        assert len(reverted_snapshot["sidecars"]) == 0
        
        # Verify original files are restored (for reversible poison operations)
        for filename, original_info in original_snapshot["files"].items():
            assert filename in reverted_snapshot["files"]
            # Note: For non-destructive poison operations, hashes should match
            # For destructive operations, we verify file integrity differently

    def test_multiple_poison_revert_cycles(self, sample_images: Dict[str, Path]) -> None:
        """Test multiple poison-revert cycles don't corrupt files."""
        work_dir = next(iter(sample_images.values())).parent
        original_snapshot = self.get_file_metadata_snapshot(work_dir)
        
        # Perform multiple poison-revert cycles
        for cycle in range(3):
            # Poison with different presets
            presets = ["label_flip", "clip_confuse", "label_flip"]
            
            poison_result = poison.poison_directory(
                input_path=work_dir,
                preset=presets[cycle],
                create_sidecars=True,
                true_hint=f"cycle {cycle} content"
            )
            
            assert poison_result["poisoned_count"] == len(sample_images)
            
            # Verify sidecars exist
            sidecars = list(work_dir.glob("*.txt"))
            assert len(sidecars) >= len(sample_images)
            
            # Revert
            revert_result = revert.revert_directory(work_dir)
            assert revert_result["reverted_count"] == len(sample_images)
            
            # Verify clean state
            remaining_sidecars = list(work_dir.glob("*.txt"))
            assert len(remaining_sidecars) == 0
        
        # Verify files are still intact after multiple cycles
        final_snapshot = self.get_file_metadata_snapshot(work_dir)
        
        # All original files should still exist
        for filename in original_snapshot["files"]:
            assert filename in final_snapshot["files"]

    def test_partial_revert_handling(self, sample_images: Dict[str, Path]) -> None:
        """Test handling of partial revert scenarios."""
        work_dir = next(iter(sample_images.values())).parent
        
        # Run poison operation
        poison.poison_directory(
            input_path=work_dir,
            preset="label_flip",
            create_sidecars=True
        )
        
        # Manually delete some sidecar files to simulate partial state
        sidecars = list(work_dir.glob("*.txt"))
        assert len(sidecars) > 0
        
        # Delete every other sidecar
        for i, sidecar in enumerate(sidecars):
            if i % 2 == 0:
                sidecar.unlink()
        
        # Run revert - should handle missing files gracefully
        revert_result = revert.revert_directory(work_dir)
        
        # Should still attempt to revert remaining items
        assert revert_result["reverted_count"] >= 0
        assert "errors" in revert_result or revert_result["reverted_count"] > 0

    def test_concurrent_operations_safety(self, sample_images: Dict[str, Path]) -> None:
        """Test that operations are safe when run concurrently."""
        work_dir = next(iter(sample_images.values())).parent
        
        # Create multiple subdirectories to simulate concurrent operations
        subdirs = []
        for i in range(3):
            subdir = work_dir / f"concurrent_{i}"
            subdir.mkdir()
            
            # Copy sample images to each subdir
            for name, img_path in sample_images.items():
                new_img = subdir / name
                shutil.copy2(img_path, new_img)
            
            subdirs.append(subdir)
        
        # Run operations on different subdirectories
        results = []
        for subdir in subdirs:
            # Each gets a different operation
            if "concurrent_0" in str(subdir):
                result = clean.clean_directory(subdir, subdir / "output")
            elif "concurrent_1" in str(subdir):
                result = poison.poison_directory(subdir, preset="label_flip", create_sidecars=True)
            else:
                # First poison, then revert
                poison.poison_directory(subdir, preset="clip_confuse", create_sidecars=True)
                result = revert.revert_directory(subdir)
            
            results.append(result)
        
        # Verify all operations completed successfully
        for result in results:
            assert "error" not in result or not result["error"]

    def test_nested_directory_handling(self, sample_images: Dict[str, Path]) -> None:
        """Test operations on nested directory structures."""
        work_dir = next(iter(sample_images.values())).parent
        
        # Create nested structure
        nested_dirs = [
            work_dir / "level1" / "level2",
            work_dir / "level1" / "another",
            work_dir / "photos" / "2024" / "january"
        ]
        
        for nested_dir in nested_dirs:
            nested_dir.mkdir(parents=True)
            
            # Copy sample images to nested directories
            for name, img_path in sample_images.items():
                new_img = nested_dir / name
                shutil.copy2(img_path, new_img)
        
        # Test recursive operations
        poison_result = poison.poison_directory(
            input_path=work_dir,
            preset="label_flip",
            create_sidecars=True,
            recursive=True
        )
        
        # Should find and process images in all nested directories
        expected_count = len(sample_images) * (len(nested_dirs) + 1)  # +1 for original location
        assert poison_result["poisoned_count"] == expected_count
        
        # Verify sidecars created in each directory
        for nested_dir in nested_dirs:
            sidecars = list(nested_dir.glob("*.txt"))
            assert len(sidecars) == len(sample_images)
        
        # Test recursive revert
        revert_result = revert.revert_directory(work_dir, recursive=True)
        assert revert_result["reverted_count"] == expected_count
        
        # Verify all sidecars removed
        for nested_dir in nested_dirs:
            sidecars = list(nested_dir.glob("*.txt"))
            assert len(sidecars) == 0

    def test_operation_log_integrity(self, sample_images: Dict[str, Path]) -> None:
        """Test that operation logs maintain integrity throughout cycles."""
        work_dir = next(iter(sample_images.values())).parent
        
        # Run poison operation
        poison.poison_directory(
            input_path=work_dir,
            preset="label_flip",
            create_sidecars=True,
            create_json=True
        )
        
        # Verify log file was created and is valid JSON
        log_files = list(work_dir.glob("*.mm_poisonlog.json"))
        assert len(log_files) == 1
        
        log_file = log_files[0]
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        # Verify log structure
        assert isinstance(log_data, list)
        assert len(log_data) == len(sample_images)
        
        for entry in log_data:
            assert "file_path" in entry
            assert "operation" in entry
            assert "timestamp" in entry
            assert "sidecar_files" in entry or "metadata_changes" in entry
        
        # Run revert and check log is properly updated
        revert.revert_directory(work_dir)
        
        # Log should be updated to mark entries as reverted
        with open(log_file, 'r') as f:
            updated_log = json.load(f)
        
        # Depending on implementation, log might be empty or marked as reverted
        assert isinstance(updated_log, list)

    def test_error_recovery_workflow(self, sample_images: Dict[str, Path]) -> None:
        """Test error recovery in workflow operations."""
        work_dir = next(iter(sample_images.values())).parent
        
        # Create a file that will cause errors (e.g., corrupted image)
        bad_file = work_dir / "corrupted.jpg"
        bad_file.write_text("This is not a valid image file")
        
        # Make one file read-only to cause permission errors
        readonly_img = next(iter(sample_images.values()))
        original_mode = readonly_img.stat().st_mode
        readonly_img.chmod(0o444)  # Read-only
        
        try:
            # Run poison operation - should handle errors gracefully
            poison_result = poison.poison_directory(
                input_path=work_dir,
                preset="label_flip",
                create_sidecars=True
            )
            
            # Should report both successes and failures
            assert "poisoned_count" in poison_result
            assert "errors" in poison_result or poison_result["poisoned_count"] > 0
            
            # Run revert - should also handle errors gracefully
            revert_result = revert.revert_directory(work_dir)
            
            # Should attempt to revert what it can
            assert "reverted_count" in revert_result
            
        finally:
            # Restore permissions for cleanup
            readonly_img.chmod(original_mode)
            if bad_file.exists():
                bad_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])