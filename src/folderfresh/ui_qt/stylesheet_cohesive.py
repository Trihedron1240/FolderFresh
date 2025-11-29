"""
Cohesive Dark Theme Stylesheet for FolderFresh.
Eliminates white space, creates unified dark appearance with subtle depth.
"""

from .styles import Colors, Fonts, DesignTokens


def get_global_stylesheet() -> str:
    """
    Generate unified dark theme stylesheet for entire application.

    Ensures:
    - No visible white space
    - Consistent dark background throughout
    - Subtle shadows for depth
    - Smooth transitions and hover effects
    - Professional, modern appearance
    """
    return f"""
    /* ========== GLOBAL STYLING ========== */

    QMainWindow {{
        background-color: {Colors.PANEL_BG};
    }}

    QWidget {{
        background-color: {Colors.PANEL_BG};
    }}

    QDialog {{
        background-color: {Colors.PANEL_BG};
    }}

    /* ========== SCROLL AREAS ========== */

    QScrollArea {{
        background-color: {Colors.PANEL_BG};
        border: none;
    }}

    QScrollBar:vertical {{
        border: none;
        background-color: {Colors.PANEL_BG};
        width: 10px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {Colors.BORDER_LIGHT};
        border-radius: 5px;
        min-height: 20px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {Colors.BORDER_FOCUS};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}

    QScrollBar:horizontal {{
        border: none;
        background-color: {Colors.PANEL_BG};
        height: 10px;
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {Colors.BORDER_LIGHT};
        border-radius: 5px;
        min-width: 20px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {Colors.BORDER_FOCUS};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        border: none;
        background: none;
    }}

    /* ========== SPLITTERS ========== */

    QSplitter {{
        background-color: {Colors.PANEL_BG};
        spacing: 0px;
    }}

    QSplitter::handle {{
        background-color: {Colors.BORDER};
        margin: 0px;
    }}

    QSplitter::handle:hover {{
        background-color: {Colors.BORDER_LIGHT};
    }}

    /* ========== BUTTONS ========== */

    QPushButton {{
        border-radius: 6px;
        font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
        font-size: {Fonts.SIZE_NORMAL}pt;
        font-weight: {Fonts.WEIGHT_MEDIUM};
        outline: none;
    }}

    QPushButton:hover {{
        opacity: 0.9;
    }}

    QPushButton:pressed {{
        transform: scale(0.98);
    }}

    QPushButton:focus {{
        border: 2px solid {Colors.get("border.focus")};
    }}

    /* ========== INPUT FIELDS ========== */

    QLineEdit {{
        background-color: {Colors.PANEL_ALT};
        color: {Colors.TEXT};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 8px 10px;
        font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
        font-size: {Fonts.SIZE_NORMAL}pt;
        selection-background-color: {Colors.get("primary")};
    }}

    QLineEdit:focus {{
        border: 2px solid {Colors.get("primary")};
        background-color: {Colors.get("bg.tertiary")};
    }}

    QLineEdit:hover {{
        border: 1px solid {Colors.BORDER_LIGHT};
    }}

    QLineEdit:disabled {{
        background-color: {Colors.PANEL_BG};
        color: {Colors.MUTED};
        border: 1px solid {Colors.BORDER};
    }}

    QPlainTextEdit,
    QTextEdit {{
        background-color: {Colors.PANEL_ALT};
        color: {Colors.TEXT};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 8px 10px;
        font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
        font-size: {Fonts.SIZE_NORMAL}pt;
        selection-background-color: {Colors.get("primary")};
    }}

    QPlainTextEdit:focus,
    QTextEdit:focus {{
        border: 2px solid {Colors.get("primary")};
        background-color: {Colors.get("bg.tertiary")};
    }}

    QPlainTextEdit:hover,
    QTextEdit:hover {{
        border: 1px solid {Colors.BORDER_LIGHT};
    }}

    QPlainTextEdit:disabled,
    QTextEdit:disabled {{
        background-color: {Colors.PANEL_BG};
        color: {Colors.MUTED};
        border: 1px solid {Colors.BORDER};
    }}

    /* ========== COMBO BOX ========== */

    QComboBox {{
        background-color: {Colors.PANEL_ALT};
        color: {Colors.TEXT};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 8px 10px;
        font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
        font-size: {Fonts.SIZE_NORMAL}pt;
    }}

    QComboBox:focus {{
        border: 2px solid {Colors.get("primary")};
        background-color: {Colors.get("bg.tertiary")};
    }}

    QComboBox:hover {{
        border: 1px solid {Colors.BORDER_LIGHT};
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
        color: {Colors.TEXT};
        selection-background-color: {Colors.ACCENT};
        outline: none;
        border: 1px solid {Colors.BORDER};
    }}

    /* ========== CHECKBOXES ========== */

    QCheckBox {{
        color: {Colors.TEXT};
        spacing: 8px;
        font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
        font-size: {Fonts.SIZE_NORMAL}pt;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 3px;
        border: 2px solid {Colors.BORDER};
        background-color: transparent;
    }}

    QCheckBox::indicator:hover {{
        border: 2px solid {Colors.BORDER_LIGHT};
    }}

    QCheckBox::indicator:checked {{
        background-color: {Colors.ACCENT};
        border: 2px solid {Colors.ACCENT};
    }}

    QCheckBox::indicator:checked:hover {{
        background-color: {Colors.get("primary.hover")};
        border: 2px solid {Colors.get("primary.hover")};
    }}

    QCheckBox:disabled {{
        color: {Colors.MUTED};
    }}

    QCheckBox::indicator:disabled {{
        border: 2px solid {Colors.BORDER};
        background-color: {Colors.PANEL_BG};
    }}

    /* ========== LABELS ========== */

    QLabel {{
        color: {Colors.TEXT};
        font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
        font-size: {Fonts.SIZE_NORMAL}pt;
    }}

    /* ========== FRAMES ========== */

    QFrame {{
        background-color: {Colors.PANEL_BG};
        border: none;
    }}

    /* ========== STATUS BAR ========== */

    QStatusBar {{
        background-color: {Colors.CARD_BG};
        color: {Colors.TEXT};
        border-top: 1px solid {Colors.BORDER};
    }}

    QStatusBar::item {{
        border: none;
        background-color: transparent;
    }}

    /* ========== PROGRESS BAR ========== */

    QProgressBar {{
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        background-color: {Colors.PANEL_ALT};
        text-align: center;
        color: {Colors.TEXT};
    }}

    QProgressBar::chunk {{
        background-color: {Colors.ACCENT};
        border-radius: 5px;
    }}

    /* ========== MENU BAR ========== */

    QMenuBar {{
        background-color: {Colors.CARD_BG};
        color: {Colors.TEXT};
        border-bottom: 1px solid {Colors.BORDER};
    }}

    QMenuBar::item:selected {{
        background-color: {Colors.HOVER_BG};
    }}

    /* ========== MENUS ========== */

    QMenu {{
        background-color: {Colors.CARD_BG};
        color: {Colors.TEXT};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
    }}

    QMenu::item:selected {{
        background-color: {Colors.ACCENT};
        color: {Colors.TEXT};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {Colors.BORDER};
        margin: 4px 0px;
    }}

    /* ========== TABWIDGET ========== */

    QTabWidget::pane {{
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
    }}

    QTabBar::tab {{
        background-color: {Colors.PANEL_ALT};
        color: {Colors.TEXT};
        padding: 8px 16px;
        border: 1px solid {Colors.BORDER};
        border-bottom: none;
        border-radius: 6px 6px 0px 0px;
        margin-right: 2px;
    }}

    QTabBar::tab:selected {{
        background-color: {Colors.ACCENT};
        border: 1px solid {Colors.ACCENT};
    }}

    QTabBar::tab:hover {{
        background-color: {Colors.HOVER_BG};
    }}

    /* ========== TREE & TABLE ========== */

    QTreeWidget,
    QTableWidget {{
        background-color: {Colors.PANEL_ALT};
        color: {Colors.TEXT};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        gridline-color: {Colors.BORDER};
    }}

    QTreeWidget::item:selected,
    QTableWidget::item:selected {{
        background-color: {Colors.ACCENT};
    }}

    QTreeWidget::item:hover,
    QTableWidget::item:hover {{
        background-color: {Colors.HOVER_BG};
    }}

    QHeaderView::section {{
        background-color: {Colors.CARD_BG};
        color: {Colors.TEXT};
        padding: 5px;
        border: 1px solid {Colors.BORDER};
    }}

    /* ========== TOOLTIPS ========== */

    QToolTip {{
        background-color: {Colors.CARD_BG};
        color: {Colors.TEXT};
        border: 1px solid {Colors.BORDER};
        border-radius: 4px;
        padding: 4px 8px;
        font-family: {Fonts.PRIMARY_FAMILY}, {Fonts.FALLBACK_FAMILY};
        font-size: {Fonts.SIZE_SMALL}pt;
    }}

    /* ========== DIALOGS ========== */

    QFileDialog,
    QMessageBox,
    QInputDialog {{
        background-color: {Colors.PANEL_BG};
    }}
    """


def apply_cohesive_theme(app) -> None:
    """
    Apply cohesive dark theme to entire application.

    Args:
        app: QApplication instance
    """
    stylesheet = get_global_stylesheet()
    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet)
