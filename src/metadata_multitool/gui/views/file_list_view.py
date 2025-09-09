"""File list view for displaying selected files."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional

from ..models.file_model import FileModel
from ..utils.gui_utils import format_file_size, create_tooltip


class FileListView:
    """View for displaying and managing selected files."""

    def __init__(self, parent: tk.Widget, file_model: FileModel):
        """Initialize the file list view."""
        self.parent = parent
        self.file_model = file_model
        self.frame: Optional[tk.Frame] = None
        self.tree: Optional[ttk.Treeview] = None
        self.scrollbar: Optional[ttk.Scrollbar] = None

    def setup(self, parent: tk.Widget) -> None:
        """Setup the file list view."""
        self.frame = ttk.Frame(parent)
        self.frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create treeview with scrollbar
        self.tree = ttk.Treeview(
            self.frame,
            columns=("size", "modified", "metadata"),
            show="tree headings",
            height=8,
        )

        # Configure columns
        self.tree.heading("#0", text="File Name", anchor=tk.W)
        self.tree.heading("size", text="Size", anchor=tk.E)
        self.tree.heading("modified", text="Modified", anchor=tk.W)
        self.tree.heading("metadata", text="Metadata", anchor=tk.W)

        self.tree.column("#0", width=300, minwidth=200)
        self.tree.column("size", width=100, minwidth=80)
        self.tree.column("modified", width=120, minwidth=100)
        self.tree.column("metadata", width=80, minwidth=60)

        # Add scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Grid widgets
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Bind events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)  # Right-click context menu

        # Initial refresh
        self.refresh()

    def refresh(self) -> None:
        """Refresh the file list display."""
        if not self.tree:
            return

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add files
        files = self.file_model.get_files()
        for file_path in files:
            info = self.file_model.get_file_info(file_path)
            if info:
                self._add_file_item(file_path, info)

        # Update file count display
        self._update_file_count()

    def _add_file_item(self, file_path: Path, info: dict) -> None:
        """Add a file item to the tree."""
        # Format file size
        size_str = format_file_size(info.get("size", 0))

        # Format modification date
        import time

        modified_time = info.get("modified", 0)
        if modified_time > 0:
            modified_str = time.strftime(
                "%Y-%m-%d %H:%M", time.localtime(modified_time)
            )
        else:
            modified_str = "Unknown"

        # Format metadata status
        has_metadata = info.get("has_metadata", False)
        metadata_str = "Yes" if has_metadata else "No"

        # Insert item
        item = self.tree.insert(
            "",
            "end",
            text=file_path.name,
            values=(size_str, modified_str, metadata_str),
            tags=("file",),
        )

        # Store file path in item
        self.tree.set(item, "#0", file_path.name)

        # Add tooltip with full path
        create_tooltip(self.tree, str(file_path))

    def _update_file_count(self) -> None:
        """Update file count display."""
        count = self.file_model.get_file_count()
        if hasattr(self.parent, "file_count_var"):
            self.parent.file_count_var.set(f"Selected Files: {count}")

    def _on_double_click(self, event) -> None:
        """Handle double-click on file item."""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item:
            # Get file path from item
            file_name = self.tree.item(item, "text")
            files = self.file_model.get_files()
            for file_path in files:
                if file_path.name == file_name:
                    self._preview_file(file_path)
                    break

    def _on_right_click(self, event) -> None:
        """Handle right-click on file item."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self._show_context_menu(event)

    def _preview_file(self, file_path: Path) -> None:
        """Preview a file (placeholder implementation)."""
        # TODO: Implement file preview
        print(f"Preview file: {file_path}")

    def _show_context_menu(self, event) -> None:
        """Show context menu for file item."""
        context_menu = tk.Menu(self.parent, tearoff=0)
        context_menu.add_command(label="Preview", command=self._preview_selected)
        context_menu.add_command(label="Remove", command=self._remove_selected)
        context_menu.add_separator()
        context_menu.add_command(label="Show in Folder", command=self._show_in_folder)

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def _preview_selected(self) -> None:
        """Preview the selected file."""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            file_name = self.tree.item(item, "text")
            files = self.file_model.get_files()
            for file_path in files:
                if file_path.name == file_name:
                    self._preview_file(file_path)
                    break

    def _remove_selected(self) -> None:
        """Remove the selected file."""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            file_name = self.tree.item(item, "text")
            files = self.file_model.get_files()
            for file_path in files:
                if file_path.name == file_name:
                    self.file_model.remove_file(file_path)
                    self.refresh()
                    break

    def _show_in_folder(self) -> None:
        """Show the selected file in its folder."""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            file_name = self.tree.item(item, "text")
            files = self.file_model.get_files()
            for file_path in files:
                if file_path.name == file_name:
                    import subprocess
                    import platform

                    folder_path = file_path.parent
                    if platform.system() == "Windows":
                        subprocess.run(["explorer", str(folder_path)])
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", str(folder_path)])
                    else:  # Linux
                        subprocess.run(["xdg-open", str(folder_path)])
                    break
