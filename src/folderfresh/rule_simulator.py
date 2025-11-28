# rule_simulator.py

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from folderfresh.rule_engine import Rule, RuleExecutor


class RuleSimulator(ctk.CTkToplevel):
    """
    Popup window to simulate a rule against a test file.
    Lets user choose a file, runs the rule executor, and shows log output.
    """

    def __init__(self, master, rule: Rule):
        super().__init__(master)

        self.rule = rule
        self.test_file_path = None

        self.title(f"Simulate Rule: {rule.name}")
        self.geometry("600x500")
        self.minsize(500, 600)

        self.lift()
        self.focus_force()
        self.grab_set()

        # =========================================================
        # Title
        # =========================================================
        title = ctk.CTkLabel(
            self,
            text=f"Simulate: {rule.name}",
            font=("Arial", 16, "bold")
        )
        title.pack(pady=(15, 10))

        # =========================================================
        # File selection area
        # =========================================================
        file_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray95", "gray15"))
        file_frame.pack(fill="x", padx=15, pady=10)

        file_label = ctk.CTkLabel(
            file_frame,
            text="Test File:",
            font=("Arial", 11)
        )
        file_label.pack(anchor="w", padx=10, pady=(8, 0))

        # Selected file display
        self.file_display = ctk.CTkLabel(
            file_frame,
            text="(No file selected)",
            font=("Arial", 10),
            text_color=("gray60", "gray40")
        )
        self.file_display.pack(anchor="w", padx=10, pady=(0, 5))

        # Button to browse
        browse_btn = ctk.CTkButton(
            file_frame,
            text="Browse for a file...",
            command=self._browse_file,
            font=("Arial", 11),
            fg_color=("#3a7bd5", "#1f6aa5")
        )
        browse_btn.pack(fill="x", padx=10, pady=10)

        # =========================================================
        # Rule info area
        # =========================================================
        info_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray20"))
        info_frame.pack(fill="x", padx=15, pady=10)

        info_label = ctk.CTkLabel(
            info_frame,
            text="Rule Configuration:",
            font=("Arial", 11, "bold")
        )
        info_label.pack(anchor="w", padx=10, pady=(8, 5))

        info_text = (
            f"Conditions: {len(self.rule.conditions)} (Match Mode: {self.rule.match_mode})\n"
            f"Actions: {len(self.rule.actions)}\n"
            f"Stop on Match: {self.rule.stop_on_match}"
        )

        info_display = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=("Arial", 10),
            justify="left"
        )
        info_display.pack(anchor="w", padx=10, pady=(0, 10))

        # =========================================================
        # Simulation Results / Log
        # =========================================================
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="both", expand=True, padx=15, pady=10)

        log_label = ctk.CTkLabel(
            log_frame,
            text="Simulation Log:",
            font=("Arial", 11, "bold")
        )
        log_label.pack(anchor="w", pady=(0, 5))

        # Log textbox
        self.log_text = ctk.CTkTextbox(
            log_frame,
            corner_radius=8,
            state="disabled",
            font=("Courier", 10)
        )
        self.log_text.pack(fill="both", expand=True, padx=0, pady=0)

        # =========================================================
        # Action buttons
        # =========================================================
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        run_btn = ctk.CTkButton(
            btn_frame,
            text="Run Simulation",
            command=self._run_simulation,
            fg_color=("#2a5f2e", "#4a8f4e"),
            font=("Arial", 12)
        )
        run_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(
            btn_frame,
            text="Clear Log",
            command=self._clear_log,
            fg_color=("gray70", "gray30"),
            font=("Arial", 12)
        )
        clear_btn.pack(side="left", padx=5)

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            command=self.destroy,
            fg_color=("gray70", "gray30"),
            font=("Arial", 12)
        )
        close_btn.pack(side="right", padx=5)

    def _browse_file(self):
        """Open file browser to select a test file."""
        file_path = filedialog.askopenfilename(
            title="Select a test file to simulate against",
            parent=self
        )

        if file_path:
            self.test_file_path = file_path
            # Display the filename only, not full path
            filename = os.path.basename(file_path)
            self.file_display.configure(
                text=f"📄 {filename}",
                text_color=("black", "white")
            )

    def _run_simulation(self):
        """Run the rule simulation against the selected file."""
        if not self.test_file_path:
            messagebox.showwarning("No File Selected", "Please select a test file first.")
            return

        try:
            # Build file info from the selected file
            file_stat = os.stat(self.test_file_path)
            filename = os.path.basename(self.test_file_path)
            file_ext = os.path.splitext(filename)[1]

            file_info = {
                "name": filename,
                "ext": file_ext,
                "path": self.test_file_path,
                "size": file_stat.st_size,
            }

            # Run the executor with dry_run enabled for simulations
            executor = RuleExecutor()
            simulation_config = {
                "dry_run": True,  # Don't actually perform operations
                "safe_mode": True,  # Avoid overwriting files
            }
            log_lines = executor.execute([self.rule], file_info, simulation_config)

            # Display the log
            self._display_log(log_lines)

        except Exception as e:
            messagebox.showerror("Simulation Error", f"Failed to run simulation:\n{str(e)}")

    def _display_log(self, log_lines):
        """Display log output in the text box."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")

        for line in log_lines:
            self.log_text.insert("end", line + "\n")

        self.log_text.configure(state="disabled")

    def _clear_log(self):
        """Clear the log display."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
