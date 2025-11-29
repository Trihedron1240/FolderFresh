import customtkinter as ctk
from typing import Callable, Optional


CONDITION_CATEGORIES = {
    "Name": [
        "Name Contains",
        "Name Starts With",
        "Name Ends With",
        "Name Equals",
        "Regex Match",
    ],
    "File Properties": [
        "Extension Is",
        "File Size > X bytes",
        "File Age > X days",
        "Last Modified Before",
    ],
    "File Attributes": [
        "Is Hidden",
        "Is Read-Only",
        "Is Directory",
    ],
    "Path": [
        "Parent Folder Contains",
        "File is in folder containing",
    ],
}


class ConditionSelectorPopup(ctk.CTkToplevel):
    """Popup for selecting a condition type from categorized list."""
    
    def __init__(
        self,
        master,
        callback: Callable[[str], None],
        overlay=None,
        position: tuple = None,
    ):
        """Initialize popup.
        
        Args:
            master: Parent window
            callback: Function called when condition selected
            overlay: Reference to overlay window (closes on popup close)
            position: Optional (x, y) position for popup
        """
        super().__init__(master)
        
        self.callback = callback
        self.overlay = overlay
        self._destroying = False
        
        # Window setup
        self.title("Select Condition Type")
        self.geometry("320x500")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.lift()
        
        # Position popup
        if position:
            self.geometry(f"+{position[0]}+{position[1]}")
        else:
            self._center_near_parent()
        
        # Build UI
        self._create_widgets()
        
        # ESC closes popup (no FocusOut handling)
        self.bind("<Escape>", lambda e: self.safe_destroy())
    
    def _center_near_parent(self):
        """Position popup near parent if no position given."""
        try:
            if self.master and self.master.winfo_exists():
                x = self.master.winfo_x() + self.master.winfo_width() // 2 - 160
                y = self.master.winfo_y() + self.master.winfo_height() // 2 - 250
                self.geometry(f"+{x}+{y}")
        except Exception:
            pass
    
    def _create_widgets(self):
        """Create categorized condition list UI."""
        main_frame = ctk.CTkFrame(self, fg_color=("gray95", "gray15"))
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Select Condition Type",
            font=("Arial", 13, "bold"),
            text_color=("gray10", "gray95"),
        )
        title.pack(pady=10, padx=15)
        
        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            fg_color="transparent",
            corner_radius=8,
        )
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Build categories and items
        for category_name, items in CONDITION_CATEGORIES.items():
            # Non-clickable header
            header = ctk.CTkLabel(
                scroll_frame,
                text=category_name,
                font=("Arial", 11, "bold"),
                text_color=("gray50", "gray60"),
            )
            header.pack(anchor="w", padx=12, pady=(8, 4))
            
            # Clickable condition items
            for item_name in items:
                btn = ctk.CTkButton(
                    scroll_frame,
                    text=item_name,
                    font=("Arial", 10),
                    fg_color="transparent",
                    hover_color=("gray85", "gray25"),
                    text_color=("gray10", "gray95"),
                    anchor="w",
                    command=lambda cond=item_name: self._select_condition(cond),
                    height=32,
                    corner_radius=6,
                )
                btn.pack(fill="x", padx=8, pady=2)
        
        # Footer with close button
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(fill="x", padx=15, pady=10)
        
        close_btn = ctk.CTkButton(
            footer,
            text="Close",
            fg_color=("gray70", "gray30"),
            text_color=("gray10", "gray95"),
            font=("Arial", 10),
            command=self.safe_destroy,
            height=28,
        )
        close_btn.pack(side="left")
    
    def _select_condition(self, condition_name: str):
        """Handle condition selection."""
        if not self.winfo_exists():
            return
        
        if self.callback:
            self.callback(condition_name)
        
        self.safe_destroy()
    
    def safe_destroy(self):
        """Safely close popup and overlay."""
        if self._destroying:
            return
        
        self._destroying = True
        
        # Close self
        try:
            if self.winfo_exists():
                super().destroy()
        except Exception:
            pass
        
        # Close overlay
        try:
            if self.overlay and self.overlay.winfo_exists():
                self.overlay.safe_destroy()
        except Exception:
            pass