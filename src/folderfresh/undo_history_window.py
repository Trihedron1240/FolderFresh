# undo_history_window.py
"""
Undo History window for FolderFresh.

Displays the list of recent undo entries with per-entry controls
(Undo button, Details button) and supports deletion confirmation dialogs.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime


class UndoHistoryWindow(ctk.CTkToplevel):
    """
    Window displaying the undo history with per-entry controls.

    Features:
    - Scrollable list of recent undo entries (newest first)
    - Per-entry "Undo" button for selective undo
    - Per-entry "Details" button to view full entry info
    - Auto-refresh to show latest entries
    """

    def __init__(self, master=None):
        """
        Initialize the Undo History window.

        Args:
            master: Parent window
        """
        super().__init__(master)

        self.title("Undo History")
        self.geometry("700x500")
        self.minsize(600, 400)

        self.lift()
        self.focus_force()

        # Track if window is still open
        self.is_open = True
        self.last_entry_count = -1

        # Configure window close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # =====================================================
        # LAYOUT
        # =====================================================
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # =====================================================
        # HEADER
        # =====================================================
        header = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        header.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

        title_label = ctk.CTkLabel(
            header,
            text="Undo History",
            font=("Arial", 16, "bold")
        )
        title_label.pack(side="left", padx=10, pady=10)

        entry_count_label = ctk.CTkLabel(
            header,
            text="(0 entries)",
            font=("Arial", 10),
            text_color=("gray60", "gray40")
        )
        entry_count_label.pack(side="left", padx=5, pady=10)
        self.entry_count_label = entry_count_label

        # =====================================================
        # HISTORY LIST (scrollable)
        # =====================================================
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.list_scroll = ctk.CTkScrollableFrame(
            list_frame,
            corner_radius=8,
            fg_color=("gray90", "gray20")
        )
        self.list_scroll.grid(row=0, column=0, sticky="nsew")
        self.list_scroll.grid_columnconfigure(0, weight=1)

        self.entry_frames = []

        # =====================================================
        # BUTTON BAR
        # =====================================================
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))

        clear_history_btn = ctk.CTkButton(
            button_frame,
            text="Clear History",
            command=self._clear_history,
            fg_color=("#d73336", "#b83a3e"),
            font=("Arial", 11)
        )
        clear_history_btn.pack(side="left", padx=5)

        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self._on_close,
            fg_color=("gray70", "gray30"),
            font=("Arial", 11)
        )
        close_btn.pack(side="right", padx=5)

        # Initial load
        self._refresh_history()

        # Start auto-refresh
        self._auto_refresh()

    def _refresh_history(self):
        """Refresh the undo history display."""
        try:
            from folderfresh.undo_manager import UNDO_MANAGER

            # Clear old frames
            for frame in self.entry_frames:
                frame.destroy()
            self.entry_frames = []

            # Get history (newest first)
            history = UNDO_MANAGER.get_history()
            entry_count = len(history)

            if not history:
                empty_label = ctk.CTkLabel(
                    self.list_scroll,
                    text="(No undo history)",
                    font=("Arial", 11),
                    text_color=("gray60", "gray40")
                )
                empty_label.pack(fill="x", padx=10, pady=20)
            else:
                # Display each entry
                for i, entry in enumerate(history):
                    self._create_entry_row(entry, i)

            # Update entry count
            self.entry_count_label.configure(text=f"({entry_count} entries)")
            self.last_entry_count = entry_count

        except ImportError:
            messagebox.showerror("Error", "Undo system not available")

    def _create_entry_row(self, entry, index):
        """Create a UI row for an undo entry."""
        row_frame = ctk.CTkFrame(
            self.list_scroll,
            corner_radius=6,
            fg_color=("gray85", "gray25"),
            border_width=1,
            border_color=("gray70", "gray30")
        )
        row_frame.pack(fill="x", padx=8, pady=6)
        row_frame.grid_columnconfigure(0, weight=1)

        # Entry info (left side)
        info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        # Format entry summary
        action_type = entry.get("type", "unknown").upper()
        timestamp = entry.get("timestamp", "unknown")

        # Extract readable description
        if action_type == "MOVE":
            src = entry.get("src", "unknown")
            dst = entry.get("dst", "unknown")
            desc = f"Moved: {src} -> {dst}"
        elif action_type == "RENAME":
            old_name = entry.get("old_name", "unknown")
            new_name = entry.get("new_name", "unknown")
            desc = f"Renamed: {old_name} -> {new_name}"
        elif action_type == "COPY":
            src = entry.get("src", "unknown")
            dst = entry.get("dst", "unknown")
            desc = f"Copied: {src} -> {dst}"
        else:
            desc = f"Unknown action"

        # Parse timestamp for display
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = timestamp

        # Title label
        title_label = ctk.CTkLabel(
            info_frame,
            text=f"[{action_type}] {desc}",
            font=("Arial", 11, "bold"),
            text_color=("black", "white"),
            anchor="w"
        )
        title_label.pack(fill="x", anchor="w")

        # Timestamp label
        time_label = ctk.CTkLabel(
            info_frame,
            text=time_str,
            font=("Arial", 9),
            text_color=("gray60", "gray40"),
            anchor="w"
        )
        time_label.pack(fill="x", anchor="w", pady=(2, 0))

        # Buttons (right side)
        button_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        button_frame.pack(side="right", fill="y", padx=8, pady=8)

        def make_undo_handler(e):
            return lambda: self._undo_entry(e)

        def make_details_handler(e):
            return lambda: self._show_details(e)

        undo_btn = ctk.CTkButton(
            button_frame,
            text="Undo",
            command=make_undo_handler(entry),
            fg_color=("#f39c12", "#e67e22"),
            font=("Arial", 10),
            width=80
        )
        undo_btn.pack(side="left", padx=3)

        details_btn = ctk.CTkButton(
            button_frame,
            text="Details",
            command=make_details_handler(entry),
            fg_color=("#3a7bd5", "#1f6aa5"),
            font=("Arial", 10),
            width=80
        )
        details_btn.pack(side="left", padx=3)

        self.entry_frames.append(row_frame)

    def _undo_entry(self, entry):
        """Execute undo for a specific entry."""
        try:
            from folderfresh.undo_manager import UNDO_MANAGER

            action_type = entry.get("type", "unknown")

            # Confirm destructive action
            if action_type == "copy":
                confirm_msg = f"Delete the copy that was created?\n\n{entry.get('dst', 'unknown')}"
                if not messagebox.askyesno("Confirm Undo", confirm_msg):
                    return

            # Execute undo
            result = UNDO_MANAGER.undo_entry(entry)

            if result["success"]:
                messagebox.showinfo("Undo Success", result["message"])
            else:
                messagebox.showwarning("Undo Failed", result["message"])

            # Refresh history
            self._refresh_history()

        except ImportError:
            messagebox.showerror("Error", "Undo system not available")

    def _show_details(self, entry):
        """Show detailed information about an undo entry."""
        details = f"Undo Entry Details:\n\n"
        details += f"Type: {entry.get('type', 'unknown').upper()}\n"
        details += f"Source: {entry.get('src', 'N/A')}\n"
        details += f"Destination: {entry.get('dst', 'N/A')}\n"
        details += f"Old Name: {entry.get('old_name', 'N/A')}\n"
        details += f"New Name: {entry.get('new_name', 'N/A')}\n"
        details += f"Collision Handled: {entry.get('collision_handled', False)}\n"
        details += f"Was Dry Run: {entry.get('was_dry_run', False)}\n"
        details += f"Timestamp: {entry.get('timestamp', 'unknown')}\n"
        details += f"Status: {entry.get('status', 'unknown')}"

        messagebox.showinfo("Entry Details", details)

    def _clear_history(self):
        """Clear all undo history after confirmation."""
        if messagebox.askyesno(
            "Clear Undo History",
            "Are you sure you want to delete all undo history?\nThis cannot be undone."
        ):
            try:
                from folderfresh.undo_manager import UNDO_MANAGER
                UNDO_MANAGER.clear_history()
                self._refresh_history()
                messagebox.showinfo("Success", "Undo history cleared")
            except ImportError:
                messagebox.showerror("Error", "Undo system not available")

    def _auto_refresh(self):
        """Auto-refresh the history every 2 seconds if window is still open."""
        if not self.is_open:
            return

        try:
            # Import here to get live updates
            from folderfresh.undo_manager import UNDO_MANAGER

            # Only refresh if something changed
            current_count = len(UNDO_MANAGER)
            if current_count != self.last_entry_count:
                self._refresh_history()

            # Schedule next refresh
            self.after(2000, self._auto_refresh)
        except Exception:
            # Window might have been destroyed
            pass

    def _on_close(self):
        """Handle window close event."""
        self.is_open = False
        self.destroy()
