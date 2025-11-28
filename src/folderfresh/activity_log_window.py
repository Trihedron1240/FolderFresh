# activity_log_window.py

import customtkinter as ctk
from tkinter import messagebox
from folderfresh.activity_log import ACTIVITY_LOG


class ActivityLogWindow(ctk.CTkToplevel):
    """
    Activity Log window showing real-time rule execution logs.

    Features:
    - Real-time log display
    - Read-only scrollable text area
    - Clear log button
    - Auto-refresh every 1 second when window is open
    """

    def __init__(self, master=None):
        """
        Initialize the Activity Log window.

        Args:
            master: Parent window
        """
        super().__init__(master)

        self.title("Activity Log")
        self.geometry("800x600")
        self.minsize(600, 400)

        self.lift()
        self.focus_force()

        # Track if window is still open for auto-refresh
        self.is_open = True
        self.last_log_count = 0

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
            text="Activity Log",
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
        # LOG TEXT AREA
        # =====================================================
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(
            log_frame,
            corner_radius=8,
            state="disabled",
            font=("Courier", 10),
            wrap="word"
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # =====================================================
        # BUTTON BAR
        # =====================================================
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))

        # Left side buttons
        undo_last_btn = ctk.CTkButton(
            button_frame,
            text="Undo Last",
            command=self._undo_last,
            fg_color=("#f39c12", "#e67e22"),
            font=("Arial", 11)
        )
        undo_last_btn.pack(side="left", padx=5)

        undo_history_btn = ctk.CTkButton(
            button_frame,
            text="Undo History",
            command=self._undo_history,
            fg_color=("#9b59b6", "#8e44ad"),
            font=("Arial", 11)
        )
        undo_history_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(
            button_frame,
            text="Clear Log",
            command=self._clear_log,
            fg_color=("#d73336", "#b83a3e"),
            font=("Arial", 11)
        )
        clear_btn.pack(side="left", padx=5)

        # Save button for future use
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Log",
            command=self._save_log,
            fg_color=("#3a7bd5", "#1f6aa5"),
            font=("Arial", 11)
        )
        save_btn.pack(side="left", padx=5)

        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self._on_close,
            fg_color=("gray70", "gray30"),
            font=("Arial", 11)
        )
        close_btn.pack(side="right", padx=5)

        # Initial load
        self._refresh_log()

        # Start auto-refresh
        self._auto_refresh()

    def _refresh_log(self):
        """Refresh the log text area with current activity log entries."""
        log_text = ACTIVITY_LOG.get_log_text()
        entry_count = len(ACTIVITY_LOG)

        # Update the textbox
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", log_text if log_text else "(No activity yet)")
        self.log_text.configure(state="disabled")

        # Scroll to end
        self.log_text.see("end")

        # Update entry count
        self.entry_count_label.configure(
            text=f"({entry_count} entries)"
        )

        self.last_log_count = entry_count

    def _auto_refresh(self):
        """Auto-refresh the log every 1 second if window is still open."""
        if not self.is_open:
            return

        try:
            # Only refresh if something changed
            if len(ACTIVITY_LOG) != self.last_log_count:
                self._refresh_log()

            # Schedule next refresh
            self.after(1000, self._auto_refresh)
        except Exception:
            # Window might have been destroyed
            pass

    def _clear_log(self):
        """Clear the activity log after confirmation."""
        if messagebox.askyesno("Clear Log", "Are you sure you want to clear the activity log?"):
            ACTIVITY_LOG.clear()
            self._refresh_log()

    def _save_log(self):
        """Save the activity log to a file."""
        from tkinter import filedialog

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Activity Log",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )

        if not file_path:
            return

        # Save as JSON
        if file_path.endswith(".json"):
            if ACTIVITY_LOG.save_to_file(file_path):
                messagebox.showinfo("Success", f"Activity log saved to:\n{file_path}")
            else:
                messagebox.showerror("Error", "Failed to save activity log")
        else:
            # Save as plain text
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(ACTIVITY_LOG.get_log_text())
                messagebox.showinfo("Success", f"Activity log saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save activity log:\n{str(e)}")

    def _undo_last(self):
        """Undo the last recorded action."""
        try:
            from folderfresh.undo_manager import UNDO_MANAGER

            result = UNDO_MANAGER.undo_last()

            if result["success"]:
                messagebox.showinfo("Undo Success", result["message"])
            else:
                messagebox.showwarning("Undo Failed", result["message"])

            # Refresh log to show the undo result
            self._refresh_log()

        except ImportError:
            messagebox.showerror("Error", "Undo system not available")

    def _undo_history(self):
        """Open the undo history window."""
        try:
            from folderfresh.undo_history_window import UndoHistoryWindow
            UndoHistoryWindow(self)
        except ImportError:
            messagebox.showerror("Error", "Undo history window not available")

    def _on_close(self):
        """Handle window close event."""
        self.is_open = False
        self.destroy()
