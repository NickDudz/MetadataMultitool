"""Tests for backup functionality."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from metadata_multitool.backup import (
    BackupError,
    BackupManager,
    backup_before_operation,
    create_backup_manager,
    restore_from_backup,
)


class TestBackupError:
    """Test BackupError exception."""

    def test_backup_error(self):
        """Test BackupError exception."""
        error = BackupError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)


class TestBackupManager:
    """Test BackupManager class."""

    def test_init_default_backup_dir(self, tmp_path):
        """Test BackupManager initialization with default backup directory."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            manager = BackupManager()
            
        assert manager.backup_dir.name == ".mm_backups"
        assert manager.backup_dir.exists()
        assert manager.backup_index_file.exists()

    def test_init_custom_backup_dir(self, tmp_path):
        """Test BackupManager initialization with custom backup directory."""
        custom_dir = tmp_path / "custom_backups"
        manager = BackupManager(backup_dir=custom_dir)
        
        assert manager.backup_dir == custom_dir
        assert manager.backup_dir.exists()
        # The backup index file is created when needed, not on init
        assert manager.backup_index == {"backups": {}, "next_id": 1}

    def test_load_backup_index_new(self, tmp_path):
        """Test loading backup index when file doesn't exist."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        expected = {"backups": {}, "next_id": 1}
        assert manager.backup_index == expected

    def test_load_backup_index_existing(self, tmp_path):
        """Test loading backup index from existing file."""
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        
        index_file = backup_dir / "backup_index.json"
        test_data = {
            "backups": {"1": {"path": "/test/path", "timestamp": "2024-01-01T00:00:00"}},
            "next_id": 2
        }
        index_file.write_text(json.dumps(test_data))
        
        manager = BackupManager(backup_dir=backup_dir)
        assert manager.backup_index == test_data

    def test_load_backup_index_corrupted(self, tmp_path):
        """Test loading backup index from corrupted file."""
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        
        index_file = backup_dir / "backup_index.json"
        index_file.write_text("invalid json")
        
        manager = BackupManager(backup_dir=backup_dir)
        expected = {"backups": {}, "next_id": 1}
        assert manager.backup_index == expected

    def test_save_backup_index(self, tmp_path):
        """Test saving backup index to file."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        test_data = {
            "backups": {"1": {"path": "/test/path"}},
            "next_id": 2
        }
        manager.backup_index = test_data
        manager._save_backup_index()
        
        # Verify file was written correctly
        with open(manager.backup_index_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data == test_data

    def test_save_backup_index_write_error(self, tmp_path):
        """Test saving backup index when write fails."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        # Mock open to raise OSError
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(BackupError, match="Failed to save backup index"):
                manager._save_backup_index()

    def test_create_backup_file(self, tmp_path):
        """Test creating backup of a single file."""
        # Create source file
        source_file = tmp_path / "source.txt"
        source_file.write_text("test content")
        
        # Create backup manager
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        # Create backup
        backup_id = manager.create_backup(source_file, "test_operation")
        
        # Verify backup was created
        assert backup_id in manager.backup_index["backups"]
        backup_info = manager.backup_index["backups"][backup_id]
        assert backup_info["source_path"] == str(source_file)
        assert backup_info["operation"] == "test_operation"
        assert backup_info["type"] == "file"
        
        # Verify backup file exists
        backup_path = Path(backup_info["backup_path"])
        assert backup_path.exists()
        assert backup_path.read_text() == "test content"

    def test_create_backup_directory(self, tmp_path):
        """Test creating backup of a directory."""
        # Create source directory with files
        source_dir = tmp_path / "source_dir"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.txt").write_text("content2")
        subdir = source_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        
        # Create backup manager
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        # Create backup
        backup_id = manager.create_backup(source_dir, "test_operation")
        
        # Verify backup was created
        assert backup_id in manager.backup_index["backups"]
        backup_info = manager.backup_index["backups"][backup_id]
        assert backup_info["source_path"] == str(source_dir)
        assert backup_info["type"] == "directory"
        
        # Verify backup directory structure
        backup_path = Path(backup_info["backup_path"])
        assert backup_path.is_dir()
        assert (backup_path / "file1.txt").read_text() == "content1"
        assert (backup_path / "file2.txt").read_text() == "content2"
        assert (backup_path / "subdir" / "file3.txt").read_text() == "content3"

    def test_create_backup_nonexistent_source(self, tmp_path):
        """Test creating backup of nonexistent source."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        nonexistent = tmp_path / "nonexistent.txt"
        
        with pytest.raises(BackupError, match="Source path does not exist"):
            manager.create_backup(nonexistent, "test")

    def test_create_backup_disk_space_error(self, tmp_path):
        """Test creating backup when disk space is insufficient."""
        source_file = tmp_path / "source.txt"
        source_file.write_text("test content")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        # Mock shutil.copy2 to raise OSError
        with patch("shutil.copy2", side_effect=OSError("No space left on device")):
            with pytest.raises(BackupError, match="Failed to create backup"):
                manager.create_backup(source_file, "test")

    def test_restore_backup_file(self, tmp_path):
        """Test restoring backup of a file."""
        # Create source file and backup
        source_file = tmp_path / "source.txt"
        source_file.write_text("original content")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        backup_id = manager.create_backup(source_file, "test")
        
        # Modify source file
        source_file.write_text("modified content")
        
        # Restore backup
        manager.restore_backup(backup_id)
        
        # Verify restoration
        assert source_file.read_text() == "original content"

    def test_restore_backup_directory(self, tmp_path):
        """Test restoring backup of a directory."""
        # Create source directory
        source_dir = tmp_path / "source_dir"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        backup_id = manager.create_backup(source_dir, "test")
        
        # Remove source directory
        shutil.rmtree(source_dir)
        
        # Restore backup
        manager.restore_backup(backup_id)
        
        # Verify restoration
        assert source_dir.is_dir()
        assert (source_dir / "file1.txt").read_text() == "content1"

    def test_restore_backup_nonexistent(self, tmp_path):
        """Test restoring nonexistent backup."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        with pytest.raises(BackupError, match="Backup ID not found"):
            manager.restore_backup("nonexistent_id")

    def test_restore_backup_missing_backup_file(self, tmp_path):
        """Test restoring backup when backup file is missing."""
        source_file = tmp_path / "source.txt"
        source_file.write_text("content")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        backup_id = manager.create_backup(source_file, "test")
        
        # Delete backup file
        backup_info = manager.backup_index["backups"][backup_id]
        backup_path = Path(backup_info["backup_path"])
        backup_path.unlink()
        
        with pytest.raises(BackupError, match="Backup file not found"):
            manager.restore_backup(backup_id)

    def test_list_backups_empty(self, tmp_path):
        """Test listing backups when none exist."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        backups = manager.list_backups()
        assert backups == []

    def test_list_backups_with_data(self, tmp_path):
        """Test listing backups with existing data."""
        source_file = tmp_path / "source.txt"
        source_file.write_text("content")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        backup_id = manager.create_backup(source_file, "test_operation")
        
        backups = manager.list_backups()
        assert len(backups) == 1
        backup = backups[0]
        assert backup["id"] == backup_id
        assert backup["source_path"] == str(source_file)
        assert backup["operation"] == "test_operation"
        assert "created_at" in backup
        assert "size" in backup

    def test_delete_backup_file(self, tmp_path):
        """Test deleting a file backup."""
        source_file = tmp_path / "source.txt"
        source_file.write_text("content")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        backup_id = manager.create_backup(source_file, "test")
        
        # Verify backup exists
        assert backup_id in manager.backup_index["backups"]
        backup_info = manager.backup_index["backups"][backup_id]
        backup_path = Path(backup_info["backup_path"])
        assert backup_path.exists()
        
        # Delete backup
        manager.delete_backup(backup_id)
        
        # Verify backup is gone
        assert backup_id not in manager.backup_index["backups"]
        assert not backup_path.exists()

    def test_delete_backup_directory(self, tmp_path):
        """Test deleting a directory backup."""
        source_dir = tmp_path / "source_dir"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("content")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        backup_id = manager.create_backup(source_dir, "test")
        
        backup_info = manager.backup_index["backups"][backup_id]
        backup_path = Path(backup_info["backup_path"])
        assert backup_path.is_dir()
        
        # Delete backup
        manager.delete_backup(backup_id)
        
        # Verify backup is gone
        assert backup_id not in manager.backup_index["backups"]
        assert not backup_path.exists()

    def test_delete_backup_nonexistent(self, tmp_path):
        """Test deleting nonexistent backup."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        with pytest.raises(BackupError, match="Backup ID not found"):
            manager.delete_backup("nonexistent_id")

    def test_cleanup_old_backups(self, tmp_path):
        """Test cleaning up old backups."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        # Create old backup entry
        old_timestamp = (datetime.now() - timedelta(days=35)).isoformat()
        recent_timestamp = datetime.now().isoformat()
        
        manager.backup_index = {
            "backups": {
                "old_backup": {
                    "created_at": old_timestamp,
                    "backup_path": str(backup_dir / "old_backup.txt"),
                    "source_path": "/old/path",
                    "operation": "test",
                    "type": "file",
                    "size": 100
                },
                "recent_backup": {
                    "created_at": recent_timestamp,
                    "backup_path": str(backup_dir / "recent_backup.txt"),
                    "source_path": "/recent/path",
                    "operation": "test",
                    "type": "file",
                    "size": 200
                }
            },
            "next_id": 3
        }
        
        # Create backup files
        (backup_dir / "old_backup.txt").write_text("old")
        (backup_dir / "recent_backup.txt").write_text("recent")
        
        # Cleanup old backups (older than 30 days)
        removed_count = manager.cleanup_old_backups(max_age_days=30)
        
        assert removed_count == 1
        assert "old_backup" not in manager.backup_index["backups"]
        assert "recent_backup" in manager.backup_index["backups"]
        assert not (backup_dir / "old_backup.txt").exists()
        assert (backup_dir / "recent_backup.txt").exists()

    def test_get_backup_size_empty(self, tmp_path):
        """Test getting backup size when no backups exist."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        size = manager.get_backup_size()
        assert size == 0

    def test_get_backup_size_with_files(self, tmp_path):
        """Test getting backup size with existing backups."""
        source_file1 = tmp_path / "file1.txt"
        source_file1.write_text("content1")
        source_file2 = tmp_path / "file2.txt"  
        source_file2.write_text("content22")  # Different length
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        manager.create_backup(source_file1, "test1")
        manager.create_backup(source_file2, "test2")
        
        size = manager.get_backup_size()
        assert size > 0  # Should include both files


class TestModuleFunctions:
    """Test module-level functions."""

    def test_create_backup_manager_default(self):
        """Test creating backup manager with default settings."""
        with patch("metadata_multitool.backup.BackupManager") as mock_manager:
            create_backup_manager()
            mock_manager.assert_called_once_with(None)

    def test_create_backup_manager_custom_dir(self, tmp_path):
        """Test creating backup manager with custom directory."""
        custom_dir = tmp_path / "custom"
        with patch("metadata_multitool.backup.BackupManager") as mock_manager:
            create_backup_manager(backup_dir=custom_dir)
            mock_manager.assert_called_once_with(custom_dir)

    def test_backup_before_operation(self, tmp_path):
        """Test backup_before_operation function."""
        source_file = tmp_path / "file1.txt"
        source_file.write_text("content")
        
        with patch("metadata_multitool.backup.BackupManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.create_backup.return_value = "backup_id"
            
            backup_id = backup_before_operation(source_file, "test_operation", mock_manager)
            
            assert backup_id == "backup_id"
            mock_manager.create_backup.assert_called_once_with(source_file, "test_operation")

    def test_backup_before_operation_with_error(self, tmp_path):
        """Test backup_before_operation when backup fails."""
        source_file = tmp_path / "file1.txt"
        source_file.write_text("content")
        
        with patch("metadata_multitool.backup.BackupManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.create_backup.side_effect = BackupError("Backup failed")
            
            # Function should return None and print warning, not raise
            with patch("builtins.print") as mock_print:
                result = backup_before_operation(source_file, "test_operation")
                assert result is None
                mock_print.assert_called_once()

    def test_restore_from_backup(self, tmp_path):
        """Test restore_from_backup function."""
        backup_id = "backup1"
        
        with patch("metadata_multitool.backup.BackupManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            restore_from_backup(backup_id, mock_manager)
            
            mock_manager.restore_backup.assert_called_once_with("backup1")

    def test_restore_from_backup_with_error(self, tmp_path):
        """Test restore_from_backup when restore fails."""
        backup_id = "backup1"
        
        with patch("metadata_multitool.backup.BackupManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.restore_backup.side_effect = BackupError("Restore failed")
            
            with pytest.raises(BackupError, match="Restore failed"):
                restore_from_backup(backup_id)


class TestIntegration:
    """Integration tests for backup functionality."""

    def test_full_backup_restore_cycle_file(self, tmp_path):
        """Test complete backup and restore cycle for files."""
        # Create source file
        source_file = tmp_path / "file1.txt"
        source_file.write_text("original content")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir)
        
        # Create backup
        backup_id = backup_before_operation(source_file, "test_operation", manager)
        assert backup_id is not None
        
        # Modify original file
        source_file.write_text("modified content")
        
        # Restore from backup
        restore_from_backup(backup_id, manager)
        
        # Verify restoration
        assert source_file.read_text() == "original content"

    def test_full_backup_restore_cycle_directory(self, tmp_path):
        """Test complete backup and restore cycle for directories."""
        # Create source directory
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.txt").write_text("content2")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir)
        
        # Create backup
        backup_id = backup_before_operation(source_dir, "test_operation", manager)
        assert backup_id is not None
        
        # Remove source directory
        shutil.rmtree(source_dir)
        assert not source_dir.exists()
        
        # Restore from backup
        restore_from_backup(backup_id, manager)
        
        # Verify restoration
        assert source_dir.is_dir()
        assert (source_dir / "file1.txt").read_text() == "content1"
        assert (source_dir / "file2.txt").read_text() == "content2"

    def test_backup_cleanup_workflow(self, tmp_path):
        """Test backup creation and cleanup workflow."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        # Create multiple backups
        source_files = []
        backup_ids = []
        for i in range(3):
            source_file = tmp_path / f"file{i}.txt"
            source_file.write_text(f"content{i}")
            source_files.append(source_file)
            backup_id = manager.create_backup(source_file, f"operation{i}")
            backup_ids.append(backup_id)
        
        # Verify all backups exist
        backups = manager.list_backups()
        assert len(backups) == 3
        
        # Delete one backup
        manager.delete_backup(backup_ids[1])
        
        # Verify deletion
        backups = manager.list_backups()
        assert len(backups) == 2
        
        # Get backup size
        size = manager.get_backup_size()
        assert size > 0
        
        # Cleanup old backups (this shouldn't remove any since they're recent)
        removed = manager.cleanup_old_backups(max_age_days=30)
        assert removed == 0
        
        # Verify backups still exist
        backups = manager.list_backups()
        assert len(backups) == 2

    def test_restore_directory_with_existing_target(self, tmp_path):
        """Test restoring directory when target already exists."""
        # Create source directory
        source_dir = tmp_path / "source_dir"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        backup_id = manager.create_backup(source_dir, "test")
        
        # Modify source directory
        (source_dir / "file2.txt").write_text("new content")
        
        # Restore backup - should replace existing directory
        manager.restore_backup(backup_id)
        
        # Verify restoration
        assert (source_dir / "file1.txt").read_text() == "content1"
        assert not (source_dir / "file2.txt").exists()  # Should be removed

    def test_restore_backup_disk_error(self, tmp_path):
        """Test restoring backup when disk error occurs."""
        source_file = tmp_path / "source.txt"
        source_file.write_text("content")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        backup_id = manager.create_backup(source_file, "test")
        
        # Mock shutil.copy2 to raise OSError
        with patch("shutil.copy2", side_effect=OSError("Disk full")):
            with pytest.raises(BackupError, match="Failed to restore backup"):
                manager.restore_backup(backup_id)

    def test_delete_backup_disk_error(self, tmp_path):
        """Test deleting backup when disk error occurs."""
        source_file = tmp_path / "source.txt"
        source_file.write_text("content")
        
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        backup_id = manager.create_backup(source_file, "test")
        
        # Mock unlink to raise OSError
        with patch("pathlib.Path.unlink", side_effect=OSError("Permission denied")):
            with pytest.raises(BackupError, match="Failed to delete backup"):
                manager.delete_backup(backup_id)

    def test_cleanup_old_backups_with_delete_error(self, tmp_path):
        """Test cleanup when some backups fail to delete."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)
        
        # Create old backup entry
        old_timestamp = (datetime.now() - timedelta(days=35)).isoformat()
        
        manager.backup_index = {
            "backups": {
                "old_backup": {
                    "created_at": old_timestamp,
                    "backup_path": str(backup_dir / "old_backup.txt"),
                    "source_path": "/old/path",
                    "operation": "test",
                    "type": "file",
                    "size": 100
                }
            },
            "next_id": 2
        }
        
        # Create backup file
        (backup_dir / "old_backup.txt").write_text("old")
        
        # Mock delete_backup to raise BackupError
        with patch.object(manager, 'delete_backup', side_effect=BackupError("Delete failed")):
            removed_count = manager.cleanup_old_backups(max_age_days=30)
            
        # Should continue despite error and return 0
        assert removed_count == 0