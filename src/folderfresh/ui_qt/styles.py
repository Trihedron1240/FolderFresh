"""
PySide6 styling module for FolderFresh.
Centralized theme colors, fonts, and stylesheet utilities.
Includes modern design tokens with dark/light theme support.
"""

from enum import Enum
from typing import Optional, Dict


# ========== DESIGN TOKENS SYSTEM ==========
# Semantic tokens for modern design

class DesignTokens:
    """Modern design tokens for FolderFresh UI."""

    class Spacing:
        """Spacing scale (6px base unit)."""
        XS = 4      # Extra small
        SM = 8      # Small (1x)
        MD = 12     # Medium (1.5x)
        LG = 16     # Large (2x)
        XL = 24     # Extra large (3x)
        XXL = 32    # Extra extra large (4x)

    class Shadows:
        """Elevation shadows."""
        # Format: (offset_x, offset_y, blur, spread, color_hex, opacity)
        NONE = "none"
        SM = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
        MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
        LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
        XL = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"

    class BorderRadius:
        """Border radius scale."""
        NONE = 0
        SM = 4
        MD = 6
        LG = 8
        XL = 12
        FULL = 9999

    class ZIndex:
        """Z-index layers."""
        DROPDOWN = 100
        STICKY = 500
        FIXED = 600
        MODAL = 1000
        TOOLTIP = 1100


# ========== COLOR PALETTE WITH LIGHT/DARK SUPPORT ==========

class ColorScheme:
    """Color scheme definition with semantic tokens."""

    def __init__(self, name: str, colors: Dict[str, str]):
        """Initialize color scheme."""
        self.name = name
        self.colors = colors

    def get(self, token: str) -> str:
        """Get color by token name."""
        return self.colors.get(token, "#000000")


# Dark theme (default)
DARK_THEME_COLORS = {
    # Semantic: Backgrounds
    "bg.primary": "#0f1720",      # Main background
    "bg.secondary": "#0b1220",    # Card/elevated background
    "bg.tertiary": "#071018",     # Overlay/input background
    "bg.hover": "#1a2332",        # Hover state background
    "bg.active": "#2d3f5c",       # Active/pressed state

    # Semantic: Surfaces
    "surface.panel": "#0f1720",
    "surface.card": "#0b1220",
    "surface.input": "#071018",

    # Semantic: Text
    "text.primary": "#e6eef8",
    "text.secondary": "#c4d0df",
    "text.tertiary": "#9aa6b2",
    "text.muted": "#7a8696",
    "text.disabled": "#4b5563",

    # Semantic: Borders
    "border.default": "#1f2937",
    "border.light": "#374151",
    "border.focus": "#475569",

    # Semantic: Interactions
    "primary": "#2563eb",         # Blue
    "primary.hover": "#1d4ed8",
    "primary.active": "#1e40af",
    "primary.disabled": "#1e3a8a",

    "secondary": "#6366f1",       # Indigo
    "secondary.hover": "#4f46e5",
    "secondary.active": "#4338ca",

    "success": "#10b981",         # Emerald
    "success.hover": "#059669",
    "success.active": "#047857",

    "warning": "#f59e0b",         # Amber
    "warning.hover": "#d97706",
    "warning.active": "#b45309",

    "danger": "#ef4444",          # Red
    "danger.hover": "#dc2626",
    "danger.active": "#b91c1c",

    "info": "#0ea5e9",            # Cyan
    "info.hover": "#0284c7",
    "info.active": "#0369a1",

    # Legacy names for compatibility
    "ACCENT": "#2563eb",
    "SUCCESS": "#16a34a",
    "DANGER": "#dc2626",
    "WARNING": "#ea580c",
    "TEAL": "#0ea5a4",
    "TEAL_DARK": "#0a8a88",
    "LIGHT_BLUE": "#3b82f6",
    "LIGHT_BLUE_DARK": "#2f6fdc",
    "PANEL_BG": "#0f1720",
    "CARD_BG": "#0b1220",
    "PANEL_ALT": "#071018",
    "TEXT": "#e6eef8",
    "TEXT_SECONDARY": "#c4d0df",
    "MUTED": "#9aa6b2",
    "MUTED_DARK": "#7a8696",
    "BORDER": "#1f2937",
    "BORDER_LIGHT": "#374151",
    "BORDER_FOCUS": "#475569",
    "HOVER_BG": "#2d3748",
    "ACTIVE_BG": "#1a202c",
    "DISABLED": "#4b5563",
    "PLACEHOLDER": "#7a8696",
}

# Light theme (for future use)
LIGHT_THEME_COLORS = {
    # Semantic: Backgrounds
    "bg.primary": "#ffffff",
    "bg.secondary": "#f9fafb",
    "bg.tertiary": "#f3f4f6",
    "bg.hover": "#f0f1f3",
    "bg.active": "#e5e7eb",

    # Semantic: Surfaces
    "surface.panel": "#ffffff",
    "surface.card": "#f9fafb",
    "surface.input": "#f3f4f6",

    # Semantic: Text
    "text.primary": "#111827",
    "text.secondary": "#374151",
    "text.tertiary": "#6b7280",
    "text.muted": "#9ca3af",
    "text.disabled": "#d1d5db",

    # Semantic: Borders
    "border.default": "#e5e7eb",
    "border.light": "#f3f4f6",
    "border.focus": "#3b82f6",

    # Semantic: Interactions
    "primary": "#2563eb",
    "primary.hover": "#1d4ed8",
    "primary.active": "#1e40af",
    "primary.disabled": "#9ca3af",

    "secondary": "#6366f1",
    "secondary.hover": "#4f46e5",
    "secondary.active": "#4338ca",

    "success": "#10b981",
    "success.hover": "#059669",
    "success.active": "#047857",

    "warning": "#f59e0b",
    "warning.hover": "#d97706",
    "warning.active": "#b45309",

    "danger": "#ef4444",
    "danger.hover": "#dc2626",
    "danger.active": "#b91c1c",

    "info": "#0ea5e9",
    "info.hover": "#0284c7",
    "info.active": "#0369a1",
}


class Colors:
    """FolderFresh color palette with legacy support."""

    # Default to dark theme
    _current_theme = DARK_THEME_COLORS

    # Primary colors
    ACCENT = "#2563eb"           # Blue - primary action buttons
    SUCCESS = "#16a34a"          # Green - success/organize actions
    DANGER = "#dc2626"           # Red - delete/destructive actions
    WARNING = "#ea580c"          # Orange - warning states

    # Teal/Cyan
    TEAL = "#0ea5a4"             # Teal - desktop clean, etc.
    TEAL_DARK = "#0a8a88"        # Darker teal (hover)

    # Light blue variants
    LIGHT_BLUE = "#3b82f6"       # Light blue - find duplicates, etc.
    LIGHT_BLUE_DARK = "#2f6fdc"  # Darker light blue (hover)

    # Background colors
    PANEL_BG = "#0f1720"         # Main window background (very dark)
    CARD_BG = "#0b1220"          # Card/section background (darker)
    PANEL_ALT = "#071018"        # Alternate background (text input, etc.)

    # Text colors
    TEXT = "#e6eef8"             # Primary text (light)
    TEXT_SECONDARY = "#c4d0df"   # Secondary text (slightly dimmer)
    MUTED = "#9aa6b2"            # Muted text (for hints, secondary info)
    MUTED_DARK = "#7a8696"       # Even more muted

    # Borders and dividers
    BORDER = "#1f2937"           # Default border color
    BORDER_LIGHT = "#374151"     # Lighter border (for hover states)
    BORDER_FOCUS = "#475569"     # Border color on focus

    # Hover/Active states
    HOVER_BG = "#2d3748"         # Hover background for non-interactive elements
    ACTIVE_BG = "#1a202c"        # Pressed/active state background

    # Special colors
    DISABLED = "#4b5563"         # Disabled text/button color
    PLACEHOLDER = "#7a8696"      # Placeholder text color

    @staticmethod
    def set_theme(theme: str) -> None:
        """
        Switch between light and dark themes.

        Args:
            theme: "light" or "dark"
        """
        if theme.lower() == "light":
            Colors._current_theme = LIGHT_THEME_COLORS
        else:
            Colors._current_theme = DARK_THEME_COLORS

    @staticmethod
    def get(token: str) -> str:
        """
        Get color by semantic token name.

        Args:
            token: Semantic token name (e.g., "primary", "text.primary", "bg.secondary")

        Returns:
            Hex color string
        """
        return Colors._current_theme.get(token, Colors.TEXT)


# ========== TYPOGRAPHY SYSTEM ==========

class Fonts:
    """Enhanced typography definitions with line-height."""

    # Primary font (Segoe UI Variable on Windows, fallback for other platforms)
    PRIMARY_FAMILY = "Segoe UI Variable"
    FALLBACK_FAMILY = "Segoe UI"
    MONOSPACE_FAMILY = "Courier New"

    # Font sizes (pt)
    SIZE_DISPLAY = 32     # Large display/hero text
    SIZE_TITLE = 24       # Page titles
    SIZE_HEADING = 18     # Section headers
    SIZE_SUBHEADING = 14  # Subsection headers
    SIZE_NORMAL = 11      # Body text
    SIZE_SMALL = 10       # Small text
    SIZE_TINY = 9        # Extra small text

    # Font weights (CSS values)
    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700
    WEIGHT_EXTRABOLD = 800

    # Line heights (relative to font size)
    LINEHEIGHT_TIGHT = 1.2       # Headings
    LINEHEIGHT_NORMAL = 1.5      # Body text
    LINEHEIGHT_RELAXED = 1.75    # Long-form content
    LINEHEIGHT_LOOSE = 2.0       # Extra spacing

    # Letter spacing (em)
    LETTERSPACING_TIGHT = -0.01
    LETTERSPACING_NORMAL = 0
    LETTERSPACING_WIDE = 0.02


# ========== BUTTON STYLES ==========

def get_button_stylesheet(
    bg_color: str = Colors.ACCENT,
    hover_color: Optional[str] = None,
    text_color: str = Colors.TEXT,
    border_color: Optional[str] = None,
    border_radius: int = 6,
    padding: int = 10,
    font_size: int = Fonts.SIZE_NORMAL,
    font_weight: int = Fonts.WEIGHT_MEDIUM,
    with_shadow: bool = True,
) -> str:
    """
    Generate modern button stylesheet with hover/pressed states and optional shadow.

    Args:
        bg_color: Button background color
        hover_color: Hover state color (defaults to darkened bg_color)
        text_color: Text color
        border_color: Border color (defaults to bg_color)
        border_radius: Corner radius in pixels
        padding: Internal padding in pixels
        font_size: Font size in points
        font_weight: Font weight (100-900)
        with_shadow: Add drop shadow to button (default True)

    Returns:
        QSS stylesheet string
    """
    if hover_color is None:
        # Automatically darken on hover
        hover_color = _darken_color(bg_color, 0.15)

    if border_color is None:
        border_color = _darken_color(bg_color, 0.1)

    pressed_color = _darken_color(bg_color, 0.25)
    shadow = DesignTokens.Shadows.SM if with_shadow else DesignTokens.Shadows.NONE

    return f"""
        QPushButton {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: {border_radius}px;
            padding: {padding}px {padding + 4}px;
            font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
            font-size: {font_size}pt;
            font-weight: {font_weight};
            outline: none;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
            border: 1px solid {_darken_color(border_color, 0.1)};
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
            padding: {padding}px {padding + 2}px;
        }}
        QPushButton:focus {{
            border: 2px solid {Colors.get("border.focus")};
        }}
        QPushButton:disabled {{
            background-color: {Colors.DISABLED};
            color: {Colors.MUTED_DARK};
            border: 1px solid {Colors.BORDER};
        }}
    """


# ========== ENTRY/LINEEDIT STYLES ==========

def get_lineedit_stylesheet(
    bg_color: str = Colors.PANEL_ALT,
    text_color: str = Colors.TEXT,
    border_color: str = Colors.BORDER,
    focus_border_color: str = Colors.ACCENT,
    border_radius: int = 6,
    padding: int = 10,
    font_size: int = Fonts.SIZE_NORMAL,
) -> str:
    """
    Generate modern QLineEdit stylesheet with enhanced focus states.

    Args:
        bg_color: Input background color
        text_color: Text color
        border_color: Default border color
        focus_border_color: Border color when focused
        border_radius: Corner radius
        padding: Internal padding
        font_size: Font size in points

    Returns:
        QSS stylesheet string
    """
    return f"""
        QLineEdit {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: {border_radius}px;
            padding: {padding}px;
            font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
            font-size: {font_size}pt;
            selection-background-color: {Colors.get("primary")};
            selection-color: {Colors.TEXT};
        }}
        QLineEdit:focus {{
            border: 2px solid {focus_border_color};
            background-color: {Colors.get("bg.tertiary")};
        }}
        QLineEdit:hover {{
            border: 1px solid {Colors.get("border.light")};
        }}
        QLineEdit:disabled {{
            background-color: {Colors.PANEL_BG};
            color: {Colors.MUTED};
            border: 1px solid {Colors.BORDER};
        }}
    """


# ========== TEXTEDIT STYLES ==========

def get_textedit_stylesheet(
    bg_color: str = Colors.PANEL_ALT,
    text_color: str = Colors.TEXT,
    border_color: str = Colors.BORDER,
    focus_border_color: str = Colors.ACCENT,
    border_radius: int = 6,
    padding: int = 10,
    font_size: int = Fonts.SIZE_NORMAL,
) -> str:
    """
    Generate modern QPlainTextEdit/QTextEdit stylesheet with enhanced states.

    Args:
        bg_color: Background color
        text_color: Text color
        border_color: Default border color
        focus_border_color: Border color when focused
        border_radius: Corner radius
        padding: Internal padding
        font_size: Font size in points

    Returns:
        QSS stylesheet string
    """
    return f"""
        QPlainTextEdit, QTextEdit {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: {border_radius}px;
            padding: {padding}px;
            font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
            font-size: {font_size}pt;
            selection-background-color: {Colors.get("primary")};
            selection-color: {Colors.TEXT};
        }}
        QPlainTextEdit:focus, QTextEdit:focus {{
            border: 2px solid {focus_border_color};
            background-color: {Colors.get("bg.tertiary")};
        }}
        QPlainTextEdit:hover, QTextEdit:hover {{
            border: 1px solid {Colors.get("border.light")};
        }}
        QPlainTextEdit:disabled, QTextEdit:disabled {{
            background-color: {Colors.PANEL_BG};
            color: {Colors.MUTED};
            border: 1px solid {Colors.BORDER};
        }}
    """


# ========== COMBOBOX STYLES ==========

def get_combobox_stylesheet(
    bg_color: str = Colors.PANEL_ALT,
    text_color: str = Colors.TEXT,
    border_color: str = Colors.BORDER,
    focus_border_color: str = Colors.ACCENT,
    border_radius: int = 6,
    padding: int = 8,
    font_size: int = Fonts.SIZE_NORMAL,
) -> str:
    """
    Generate QComboBox stylesheet with dropdown styling.

    Args:
        bg_color: Box background color
        text_color: Text color
        border_color: Default border color
        focus_border_color: Border color when focused
        border_radius: Corner radius
        padding: Internal padding
        font_size: Font size in points

    Returns:
        QSS stylesheet string
    """
    return f"""
        QComboBox {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: {border_radius}px;
            padding: {padding}px;
            font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
            font-size: {font_size}pt;
        }}
        QComboBox:focus {{
            border: 2px solid {focus_border_color};
        }}
        QComboBox::drop-down {{
            border: none;
            background-color: transparent;
        }}
        QComboBox::down-arrow {{
            image: none;
            color: {Colors.ACCENT};
        }}
        QAbstractItemView {{
            background-color: {Colors.CARD_BG};
            color: {text_color};
            selection-background-color: {Colors.ACCENT};
            outline: none;
        }}
    """


# ========== CHECKBOX STYLES ==========

def get_checkbox_stylesheet(
    text_color: str = Colors.TEXT,
    checked_color: str = Colors.ACCENT,
    unchecked_color: str = Colors.BORDER,
    font_size: int = Fonts.SIZE_NORMAL,
) -> str:
    """
    Generate QCheckBox stylesheet.

    Args:
        text_color: Text color
        checked_color: Color when checked
        unchecked_color: Color when unchecked
        font_size: Font size in points

    Returns:
        QSS stylesheet string
    """
    return f"""
        QCheckBox {{
            color: {text_color};
            spacing: 8px;
            font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
            font-size: {font_size}pt;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 3px;
            border: 2px solid {unchecked_color};
            background-color: transparent;
        }}
        QCheckBox::indicator:hover {{
            border: 2px solid {_lighten_color(unchecked_color, 0.1)};
        }}
        QCheckBox::indicator:checked {{
            background-color: {checked_color};
            border: 2px solid {checked_color};
        }}
        QCheckBox::indicator:checked:hover {{
            background-color: {_darken_color(checked_color, 0.1)};
        }}
        QCheckBox:disabled {{
            color: {Colors.MUTED};
        }}
        QCheckBox::indicator:disabled {{
            border: 2px solid {Colors.BORDER};
            background-color: {Colors.PANEL_BG};
        }}
    """


# ========== LABEL STYLES ==========

def get_label_stylesheet(
    text_color: str = Colors.TEXT,
    font_size: int = Fonts.SIZE_NORMAL,
    font_weight: int = Fonts.WEIGHT_NORMAL,
    bold: bool = False,
) -> str:
    """
    Generate QLabel stylesheet.

    Args:
        text_color: Text color
        font_size: Font size in points
        font_weight: Font weight (100-900)
        bold: Whether text should be bold

    Returns:
        QSS stylesheet string
    """
    if bold:
        font_weight = Fonts.WEIGHT_BOLD

    return f"""
        QLabel {{
            color: {text_color};
            font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
            font-size: {font_size}pt;
            font-weight: {font_weight};
        }}
    """


# ========== FRAME STYLES ==========

def get_frame_stylesheet(
    bg_color: str = Colors.CARD_BG,
    border_color: Optional[str] = None,
    border_width: int = 0,
    border_radius: int = 8,
    shadow: str = DesignTokens.Shadows.SM,
) -> str:
    """
    Generate modern QFrame stylesheet with optional shadow elevation.

    Args:
        bg_color: Background color
        border_color: Border color (None for no border)
        border_width: Border width in pixels
        border_radius: Corner radius in pixels
        shadow: Shadow elevation (from DesignTokens.Shadows)

    Returns:
        QSS stylesheet string
    """
    if border_color is None or border_width == 0:
        border_style = "none"
    else:
        border_style = f"{border_width}px solid {border_color}"

    return f"""
        QFrame {{
            background-color: {bg_color};
            border: {border_style};
            border-radius: {border_radius}px;
        }}
    """


# ========== SCROLLBAR STYLES ==========

def get_scrollbar_stylesheet(
    handle_color: str = Colors.BORDER_LIGHT,
    bg_color: str = Colors.PANEL_BG,
) -> str:
    """
    Generate scrollbar stylesheet (vertical and horizontal).

    Args:
        handle_color: Slider handle color
        bg_color: Background color

    Returns:
        QSS stylesheet string
    """
    return f"""
        QScrollBar:vertical {{
            border: none;
            background-color: {bg_color};
            width: 12px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {handle_color};
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {_lighten_color(handle_color, 0.1)};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}

        QScrollBar:horizontal {{
            border: none;
            background-color: {bg_color};
            height: 12px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {handle_color};
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {_lighten_color(handle_color, 0.1)};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
        }}
    """


# ========== PROGRESS BAR STYLES ==========

def get_progressbar_stylesheet(
    chunk_color: str = Colors.ACCENT,
    bg_color: str = Colors.PANEL_ALT,
    border_radius: int = 6,
) -> str:
    """
    Generate QProgressBar stylesheet.

    Args:
        chunk_color: Progress fill color
        bg_color: Background color
        border_radius: Corner radius

    Returns:
        QSS stylesheet string
    """
    return f"""
        QProgressBar {{
            border: 1px solid {Colors.BORDER};
            border-radius: {border_radius}px;
            background-color: {bg_color};
            text-align: center;
            color: {Colors.TEXT};
        }}
        QProgressBar::chunk {{
            background-color: {chunk_color};
            border-radius: {border_radius - 1}px;
        }}
    """


# ========== WINDOW STYLES ==========

def get_mainwindow_stylesheet() -> str:
    """Get stylesheet for main window and dialogs."""
    return f"""
        QMainWindow, QDialog {{
            background-color: {Colors.PANEL_BG};
        }}
        QWidget {{
            background-color: {Colors.PANEL_BG};
        }}
    """


# ========== HELPER FUNCTIONS ==========

def _darken_color(hex_color: str, amount: float = 0.1) -> str:
    """
    Darken a hex color by a given amount (0.0-1.0).

    Args:
        hex_color: Hex color string (e.g., "#ffffff")
        amount: Darkening amount (0.0 = no change, 1.0 = black)

    Returns:
        Darkened hex color string
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))

    return f"#{r:02x}{g:02x}{b:02x}"


def _lighten_color(hex_color: str, amount: float = 0.1) -> str:
    """
    Lighten a hex color by a given amount (0.0-1.0).

    Args:
        hex_color: Hex color string (e.g., "#000000")
        amount: Lightening amount (0.0 = no change, 1.0 = white)

    Returns:
        Lightened hex color string
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))

    return f"#{r:02x}{g:02x}{b:02x}"
