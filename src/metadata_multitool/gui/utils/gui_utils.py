"""GUI utility functions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional


def show_error(title: str, message: str, details: Optional[str] = None) -> None:
    """Show error dialog with optional details."""
    if details:
        message += f"\n\nDetails: {details}"
    messagebox.showerror(title, message)


def show_warning(title: str, message: str) -> None:
    """Show warning dialog."""
    messagebox.showwarning(title, message)


def show_info(title: str, message: str) -> None:
    """Show info dialog."""
    messagebox.showinfo(title, message)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


def create_tooltip(widget: tk.Widget, text: str) -> None:
    """Create a tooltip for a widget."""

    def on_enter(event):
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

        label = tk.Label(
            tooltip,
            text=text,
            background="lightyellow",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9),
        )
        label.pack()

        widget.tooltip = tooltip

    def on_leave(event):
        if hasattr(widget, "tooltip"):
            widget.tooltip.destroy()
            del widget.tooltip

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def center_window(window: tk.Toplevel, parent: Optional[tk.Widget] = None) -> None:
    """Center a window on the screen or relative to parent."""
    window.update_idletasks()

    if parent:
        # Center relative to parent
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        window_width = window.winfo_width()
        window_height = window.winfo_height()

        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
    else:
        # Center on screen
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        window_width = window.winfo_width()
        window_height = window.winfo_height()

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

    window.geometry(f"{window_width}x{window_height}+{x}+{y}")


def create_scrollable_frame(
    parent: tk.Widget,
) -> tuple[tk.Frame, tk.Canvas, tk.Scrollbar]:
    """Create a scrollable frame with canvas and scrollbar."""
    # Create canvas and scrollbar
    canvas = tk.Canvas(parent)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    # Configure scrolling
    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    return scrollable_frame, canvas, scrollbar
