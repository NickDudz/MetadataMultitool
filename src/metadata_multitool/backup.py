"""Backup and restore functionality for the Metadata Multitool."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import MetadataMultitoolError


class BackupError(MetadataMultitoolError):
    """Raised when backup/restore operations fail."""

    pass


class BackupManager:
    """Manages backup and restore operations for image files."""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize the backup manager.
        
        Args:
            backup_dir: Directory to store backups (if None, uses default)
        """
        self.backup_dir = backup_dir or Path(".mm_backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_index_file = self.backup_dir / "backup_index.json"
        self.backup_index = self._load_backup_index()
    
    def _load_backup_index(self) -> Dict[str, Any]:
        """Load the backup index from file."""
        if not self.backup_index_file.exists():
            return {"backups": {}, "next_id": 1}
        
        try:
            with open(self.backup_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {"backups": {}, "next_id": 1}
    
    def _save_backup_index(self) -> None:
        """Save the backup index to file."""
        try:
            with open(self.backup_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.backup_index, f, indent=2, ensure_ascii=False)
        except OSError as e:
            raise BackupError(f"Failed to save backup index: {e}")
    
    def create_backup(self, source_path: Path, operation: str = "unknown") -> str:
        """
        Create a backup of a file or directory.
        
        Args:
            source_path: Path to the file or directory to backup
            operation: Name of the operation that triggered the backup
            
        Returns:
            Backup ID for later restoration
            
        Raises:
            BackupError: If backup creation fails
        """
        if not source_path.exists():
            raise BackupError(f"Source path does not exist: {source_path}")
        
        # Generate backup ID
        backup_id = str(self.backup_index["next_id"])
        self.backup_index["next_id"] += 1
        
        # Create backup directory
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if source_path.is_file():
                # Backup single file
                backup_file = backup_path / source_path.name
                shutil.copy2(source_path, backup_file)
                
                # Store backup info
                self.backup_index["backups"][backup_id] = {
                    "type": "file",
                    "source_path": str(source_path),
                    "backup_path": str(backup_file),
                    "operation": operation,
                    "created_at": datetime.now().isoformat(),
                    "size": source_path.stat().st_size
                }
            else:
                # Backup directory
                backup_dir = backup_path / source_path.name
                shutil.copytree(source_path, backup_dir, dirs_exist_ok=True)
                
                # Store backup info
                self.backup_index["backups"][backup_id] = {
                    "type": "directory",
                    "source_path": str(source_path),
                    "backup_path": str(backup_dir),
                    "operation": operation,
                    "created_at": datetime.now().isoformat(),
                    "size": sum(f.stat().st_size for f in source_path.rglob('*') if f.is_file())
                }
            
            # Save backup index
            self._save_backup_index()
            
            return backup_id
            
        except OSError as e:
            raise BackupError(f"Failed to create backup of {source_path}: {e}")
    
    def restore_backup(self, backup_id: str) -> None:
        """
        Restore a file or directory from backup.
        
        Args:
            backup_id: ID of the backup to restore
            
        Raises:
            BackupError: If restoration fails
        """
        if backup_id not in self.backup_index["backups"]:
            raise BackupError(f"Backup ID not found: {backup_id}")
        
        backup_info = self.backup_index["backups"][backup_id]
        source_path = Path(backup_info["source_path"])
        backup_path = Path(backup_info["backup_path"])
        
        if not backup_path.exists():
            raise BackupError(f"Backup file not found: {backup_path}")
        
        try:
            if backup_info["type"] == "file":
                # Restore single file
                shutil.copy2(backup_path, source_path)
            else:
                # Restore directory
                if source_path.exists():
                    shutil.rmtree(source_path)
                shutil.copytree(backup_path, source_path)
            
            # Update backup info
            backup_info["restored_at"] = datetime.now().isoformat()
            self._save_backup_index()
            
        except OSError as e:
            raise BackupError(f"Failed to restore backup {backup_id}: {e}")
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        for backup_id, info in self.backup_index["backups"].items():
            backup_info = {
                "id": backup_id,
                "source_path": info["source_path"],
                "operation": info["operation"],
                "created_at": info["created_at"],
                "size": info["size"],
                "restored": "restored_at" in info
            }
            backups.append(backup_info)
        
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    
    def delete_backup(self, backup_id: str) -> None:
        """
        Delete a backup.
        
        Args:
            backup_id: ID of the backup to delete
            
        Raises:
            BackupError: If backup deletion fails
        """
        if backup_id not in self.backup_index["backups"]:
            raise BackupError(f"Backup ID not found: {backup_id}")
        
        backup_info = self.backup_index["backups"][backup_id]
        backup_path = Path(backup_info["backup_path"])
        
        try:
            if backup_path.exists():
                if backup_info["type"] == "file":
                    backup_path.unlink()
                else:
                    shutil.rmtree(backup_path)
            
            # Remove from index
            del self.backup_index["backups"][backup_id]
            self._save_backup_index()
            
        except OSError as e:
            raise BackupError(f"Failed to delete backup {backup_id}: {e}")
    
    def cleanup_old_backups(self, max_age_days: int = 30) -> int:
        """
        Clean up old backups.
        
        Args:
            max_age_days: Maximum age of backups to keep (in days)
            
        Returns:
            Number of backups deleted
        """
        cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        deleted_count = 0
        
        backups_to_delete = []
        for backup_id, info in self.backup_index["backups"].items():
            created_at = datetime.fromisoformat(info["created_at"]).timestamp()
            if created_at < cutoff_date:
                backups_to_delete.append(backup_id)
        
        for backup_id in backups_to_delete:
            try:
                self.delete_backup(backup_id)
                deleted_count += 1
            except BackupError:
                # Continue with other deletions even if one fails
                continue
        
        return deleted_count
    
    def get_backup_size(self) -> int:
        """
        Get total size of all backups in bytes.
        
        Returns:
            Total size in bytes
        """
        total_size = 0
        for info in self.backup_index["backups"].values():
            total_size += info["size"]
        return total_size


def create_backup_manager(backup_dir: Optional[Path] = None) -> BackupManager:
    """
    Create a backup manager instance.
    
    Args:
        backup_dir: Directory to store backups (if None, uses default)
        
    Returns:
        BackupManager instance
    """
    return BackupManager(backup_dir)


def backup_before_operation(
    source_path: Path, 
    operation: str, 
    backup_manager: Optional[BackupManager] = None
) -> Optional[str]:
    """
    Create a backup before performing an operation.
    
    Args:
        source_path: Path to backup
        operation: Name of the operation
        backup_manager: Backup manager instance (if None, creates new one)
        
    Returns:
        Backup ID if backup was created, None if backup was skipped
    """
    if backup_manager is None:
        backup_manager = BackupManager()
    
    try:
        return backup_manager.create_backup(source_path, operation)
    except BackupError as e:
        # Log warning but don't fail the operation
        print(f"Warning: Failed to create backup: {e}")
        return None


def restore_from_backup(backup_id: str, backup_manager: Optional[BackupManager] = None) -> None:
    """
    Restore from a backup.
    
    Args:
        backup_id: ID of the backup to restore
        backup_manager: Backup manager instance (if None, creates new one)
        
    Raises:
        BackupError: If restoration fails
    """
    if backup_manager is None:
        backup_manager = BackupManager()
    
    backup_manager.restore_backup(backup_id)
