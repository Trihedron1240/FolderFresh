"""
FolderFresh Component Showcase Window.
Interactive demo of all UI components, design tokens, and styling.
Perfect for design review and component library reference.
"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QScrollArea,
    QFrame,
    QLabel,
    QGridLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPixmap

from .styles import (
    Colors,
    Fonts,
    DesignTokens,
    DARK_THEME_COLORS,
    LIGHT_THEME_COLORS,
    get_button_stylesheet,
    get_label_stylesheet,
    get_frame_stylesheet,
)
from .base_widgets import (
    StyledButton,
    SuccessButton,
    DangerButton,
    TealButton,
    StyledLabel,
    TitleLabel,
    HeadingLabel,
    MutedLabel,
    StyledLineEdit,
    StyledTextEdit,
    StyledComboBox,
    StyledCheckBox,
    CardFrame,
    VerticalFrame,
    HorizontalFrame,
)


class ColorSwatch(QFrame):
    """Visual color swatch with hex code and name."""

    def __init__(self, color: str, name: str, parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 80)
        self.setMaximumSize(120, 80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Color square
        swatch = QFrame()
        swatch.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        swatch.setMinimumHeight(50)
        layout.addWidget(swatch)

        # Color name
        name_label = QLabel(name)
        name_label.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 9pt; font-weight: 500;"
        )
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        # Color hex code
        hex_label = QLabel(color)
        hex_label.setStyleSheet(
            f"color: {Colors.MUTED}; font-size: 8pt; font-family: {Fonts.MONOSPACE_FAMILY};"
        )
        layout.addWidget(hex_label)

        layout.addStretch()

        self.setStyleSheet(f"background-color: {Colors.CARD_BG}; border-radius: 6px;")


class ComponentShowcaseWindow(QMainWindow):
    """Main showcase window with tabs for different component categories."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FolderFresh Component Showcase")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(f"background-color: {Colors.PANEL_BG};")

        # Create central widget with tab layout
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Title
        title = TitleLabel("FolderFresh Component Showcase")
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(
            f"""
            QTabBar::tab {{
                background-color: {Colors.CARD_BG};
                color: {Colors.TEXT};
                padding: 8px 16px;
                border: 1px solid {Colors.BORDER};
                border-bottom: none;
                border-radius: 6px 6px 0px 0px;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.ACCENT};
                border: 1px solid {Colors.ACCENT};
            }}
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER};
                border-radius: 0px 6px 6px 6px;
            }}
        """
        )

        tabs.addTab(self._create_colors_tab(), "Colors & Tokens")
        tabs.addTab(self._create_buttons_tab(), "Buttons")
        tabs.addTab(self._create_forms_tab(), "Form Controls")
        tabs.addTab(self._create_typography_tab(), "Typography")
        tabs.addTab(self._create_containers_tab(), "Containers")

        layout.addWidget(tabs)
        self.setCentralWidget(central)

    def _create_colors_tab(self) -> QWidget:
        """Create color palette showcase tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(24)

        # Semantic colors
        semantic_frame = CardFrame()
        semantic_layout = QVBoxLayout(semantic_frame)

        semantic_title = HeadingLabel("Semantic Colors (Dark Theme)")
        semantic_layout.addWidget(semantic_title)

        # Create grid of semantic colors
        semantic_grid = QGridLayout()
        semantic_colors = {
            "Primary": Colors.get("primary"),
            "Secondary": Colors.get("secondary"),
            "Success": Colors.get("success"),
            "Warning": Colors.get("warning"),
            "Danger": Colors.get("danger"),
            "Info": Colors.get("info"),
            "Text Primary": Colors.get("text.primary"),
            "Text Secondary": Colors.get("text.secondary"),
            "Background": Colors.get("bg.primary"),
            "Card Background": Colors.get("bg.secondary"),
            "Border": Colors.get("border.default"),
            "Border Focus": Colors.get("border.focus"),
        }

        row, col = 0, 0
        for name, color in semantic_colors.items():
            swatch = ColorSwatch(color, name)
            semantic_grid.addWidget(swatch, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1

        semantic_layout.addLayout(semantic_grid)

        layout.addWidget(semantic_frame)

        # Design tokens
        tokens_frame = CardFrame()
        tokens_layout = QVBoxLayout(tokens_frame)

        tokens_title = HeadingLabel("Design Tokens")
        tokens_layout.addWidget(tokens_title)

        # Spacing tokens
        spacing_label = StyledLabel("Spacing Scale (px):", bold=True)
        tokens_layout.addWidget(spacing_label)

        spacing_info = StyledLabel(
            f"XS: {DesignTokens.Spacing.XS}, "
            f"SM: {DesignTokens.Spacing.SM}, "
            f"MD: {DesignTokens.Spacing.MD}, "
            f"LG: {DesignTokens.Spacing.LG}, "
            f"XL: {DesignTokens.Spacing.XL}, "
            f"XXL: {DesignTokens.Spacing.XXL}"
        )
        spacing_info.setStyleSheet(
            get_label_stylesheet(
                text_color=Colors.TEXT_SECONDARY, font_size=Fonts.SIZE_SMALL
            )
        )
        tokens_layout.addWidget(spacing_info)

        # Border radius tokens
        tokens_layout.addSpacing(12)
        radius_label = StyledLabel("Border Radius (px):", bold=True)
        tokens_layout.addWidget(radius_label)

        radius_info = StyledLabel(
            f"SM: {DesignTokens.BorderRadius.SM}, "
            f"MD: {DesignTokens.BorderRadius.MD}, "
            f"LG: {DesignTokens.BorderRadius.LG}, "
            f"XL: {DesignTokens.BorderRadius.XL}"
        )
        radius_info.setStyleSheet(
            get_label_stylesheet(
                text_color=Colors.TEXT_SECONDARY, font_size=Fonts.SIZE_SMALL
            )
        )
        tokens_layout.addWidget(radius_info)

        layout.addWidget(tokens_frame)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    def _create_buttons_tab(self) -> QWidget:
        """Create button showcase tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Standard buttons
        standard_frame = CardFrame()
        standard_layout = QVBoxLayout(standard_frame)

        standard_title = HeadingLabel("Standard Buttons")
        standard_layout.addWidget(standard_title)

        button_grid = QGridLayout()
        buttons = [
            ("Primary", StyledButton("Primary Button")),
            ("Success", SuccessButton("Success Button")),
            ("Danger", DangerButton("Danger Button")),
            ("Teal", TealButton("Teal Button")),
        ]

        for i, (name, button) in enumerate(buttons):
            label = StyledLabel(name, bold=True)
            button_grid.addWidget(label, i, 0)
            button_grid.addWidget(button, i, 1)
            button_grid.addWidget(
                StyledLabel("Hover over to see effect"), i, 2
            )  # Placeholder

        button_grid.setSpacing(12)
        standard_layout.addLayout(button_grid)

        layout.addWidget(standard_frame)

        # Button sizes
        sizes_frame = CardFrame()
        sizes_layout = QVBoxLayout(sizes_frame)

        sizes_title = HeadingLabel("Button Sizes")
        sizes_layout.addWidget(sizes_title)

        small_btn = StyledButton("Small Button")
        small_btn.setMaximumWidth(100)
        normal_btn = StyledButton("Normal Button")
        normal_btn.setMaximumWidth(150)
        large_btn = StyledButton("Large Button")
        large_btn.setMaximumWidth(200)

        sizes_layout.addWidget(small_btn)
        sizes_layout.addWidget(normal_btn)
        sizes_layout.addWidget(large_btn)

        layout.addWidget(sizes_frame)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    def _create_forms_tab(self) -> QWidget:
        """Create form controls showcase tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Text inputs
        form_frame = CardFrame()
        form_layout = QVBoxLayout(form_frame)

        form_title = HeadingLabel("Form Controls")
        form_layout.addWidget(form_title)

        form_layout.addWidget(StyledLabel("Text Input:", bold=True))
        form_layout.addWidget(StyledLineEdit("Enter text here..."))

        form_layout.addSpacing(12)
        form_layout.addWidget(StyledLabel("Text Area:", bold=True))
        form_layout.addWidget(
            StyledTextEdit("Multi-line text input...\nType here...")
        )

        form_layout.addSpacing(12)
        form_layout.addWidget(StyledLabel("Dropdown:", bold=True))
        combo = StyledComboBox(["Option 1", "Option 2", "Option 3"])
        form_layout.addWidget(combo)

        form_layout.addSpacing(12)
        form_layout.addWidget(StyledLabel("Checkboxes:", bold=True))
        form_layout.addWidget(StyledCheckBox("Option 1", checked=True))
        form_layout.addWidget(StyledCheckBox("Option 2"))
        form_layout.addWidget(StyledCheckBox("Option 3"))

        layout.addWidget(form_frame)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    def _create_typography_tab(self) -> QWidget:
        """Create typography showcase tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Typography examples
        typo_frame = CardFrame()
        typo_layout = QVBoxLayout(typo_frame)

        typo_title = HeadingLabel("Typography Scale")
        typo_layout.addWidget(typo_title)

        # Different font sizes
        examples = [
            ("Display", Fonts.SIZE_DISPLAY, Fonts.WEIGHT_BOLD),
            ("Title", Fonts.SIZE_TITLE, Fonts.WEIGHT_BOLD),
            ("Heading", Fonts.SIZE_HEADING, Fonts.WEIGHT_SEMIBOLD),
            ("Subheading", Fonts.SIZE_SUBHEADING, Fonts.WEIGHT_SEMIBOLD),
            ("Body", Fonts.SIZE_NORMAL, Fonts.WEIGHT_NORMAL),
            ("Small", Fonts.SIZE_SMALL, Fonts.WEIGHT_NORMAL),
            ("Tiny", Fonts.SIZE_TINY, Fonts.WEIGHT_NORMAL),
        ]

        for name, size, weight in examples:
            label = StyledLabel(f"{name}: The quick brown fox jumps")
            label_style = get_label_stylesheet(
                text_color=Colors.TEXT,
                font_size=size,
                font_weight=weight,
            )
            label.setStyleSheet(label_style)
            typo_layout.addWidget(label)
            typo_layout.addSpacing(8)

        layout.addWidget(typo_frame)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll

    def _create_containers_tab(self) -> QWidget:
        """Create container showcase tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Horizontal containers
        h_frame = CardFrame()
        h_layout = QVBoxLayout(h_frame)

        h_title = HeadingLabel("Horizontal Container")
        h_layout.addWidget(h_title)

        h_container = HorizontalFrame(spacing=12)
        h_container.add_widget(StyledButton("Button 1"))
        h_container.add_widget(StyledButton("Button 2"))
        h_container.add_widget(StyledButton("Button 3"))
        h_container.add_stretch()
        h_layout.addWidget(h_container)

        layout.addWidget(h_frame)

        # Vertical containers
        v_frame = CardFrame()
        v_layout = QVBoxLayout(v_frame)

        v_title = HeadingLabel("Vertical Container")
        v_layout.addWidget(v_title)

        v_container = VerticalFrame(spacing=12)
        v_container.add_widget(StyledLabel("Item 1"))
        v_container.add_widget(StyledLabel("Item 2"))
        v_container.add_widget(StyledLabel("Item 3"))
        v_container.add_stretch()
        v_layout.addWidget(v_container)

        layout.addWidget(v_frame)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        return scroll
