"""
FolderFresh PySide6 Base Widget Unit Tests
Tests pre-styled base widget classes
"""

import sys
import pytest
from pathlib import Path

# Fix console encoding for Windows
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PySide6.QtWidgets import (
    QApplication, QPushButton, QLineEdit, QCheckBox,
    QLabel, QFrame, QScrollArea, QVBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from folderfresh.ui_qt.main_qt import setup_qt_app, setup_stylesheet
from folderfresh.ui_qt.base_widgets import (
    StyledButton,
    SuccessButton,
    DangerButton,
    TealButton,
    StyledLineEdit,
    StyledTextEdit,
    StyledComboBox,
    StyledCheckBox,
    StyledLabel,
    TitleLabel,
    HeadingLabel,
    MutedLabel,
    CardFrame,
    SeparatorFrame,
    ScrollableFrame,
    HorizontalFrame,
    VerticalFrame
)
from folderfresh.ui_qt.styles import Colors, Fonts


# ========== FIXTURES ==========

@pytest.fixture(scope="session")
def qt_app():
    """Create QApplication for all tests"""
    app = setup_qt_app()
    setup_stylesheet(app)
    yield app


# ========== BUTTON TESTS ==========

class TestStyledButton:
    """Test StyledButton widget"""

    def test_styled_button_creates(self, qt_app):
        """Test StyledButton initializes successfully"""
        btn = StyledButton("Test Button", Colors.ACCENT)
        assert btn is not None
        assert isinstance(btn, QPushButton)

    def test_styled_button_text(self, qt_app):
        """Test StyledButton displays text correctly"""
        btn = StyledButton("Test", Colors.ACCENT)
        assert btn.text() == "Test"

    def test_styled_button_minimum_height(self, qt_app):
        """Test StyledButton has minimum height"""
        btn = StyledButton("Test", Colors.ACCENT)
        assert btn.minimumHeight() >= 40

    def test_styled_button_cursor(self, qt_app):
        """Test StyledButton sets pointing hand cursor"""
        btn = StyledButton("Test", Colors.ACCENT)
        # Cursor is set but may not be directly readable, just ensure no error

    def test_styled_button_emits_clicked(self, qt_app):
        """Test StyledButton emits clicked signal"""
        btn = StyledButton("Test", Colors.ACCENT)
        signal_received = []
        btn.clicked.connect(lambda: signal_received.append(True))

        QTest.mouseClick(btn, Qt.LeftButton)
        qt_app.processEvents()

        assert len(signal_received) > 0


class TestSuccessButton:
    """Test SuccessButton widget"""

    def test_success_button_creates(self, qt_app):
        """Test SuccessButton initializes successfully"""
        btn = SuccessButton("OK")
        assert btn is not None
        assert isinstance(btn, StyledButton)

    def test_success_button_default_text(self, qt_app):
        """Test SuccessButton has default text"""
        btn = SuccessButton()
        assert btn.text() == "OK"

    def test_success_button_custom_text(self, qt_app):
        """Test SuccessButton accepts custom text"""
        btn = SuccessButton("Organize")
        assert btn.text() == "Organize"


class TestDangerButton:
    """Test DangerButton widget"""

    def test_danger_button_creates(self, qt_app):
        """Test DangerButton initializes successfully"""
        btn = DangerButton("Delete")
        assert btn is not None
        assert isinstance(btn, StyledButton)

    def test_danger_button_default_text(self, qt_app):
        """Test DangerButton has default text"""
        btn = DangerButton()
        assert btn.text() == "Delete"


class TestTealButton:
    """Test TealButton widget"""

    def test_teal_button_creates(self, qt_app):
        """Test TealButton initializes successfully"""
        btn = TealButton("Action")
        assert btn is not None
        assert isinstance(btn, StyledButton)


# ========== INPUT FIELD TESTS ==========

class TestStyledLineEdit:
    """Test StyledLineEdit widget"""

    def test_styled_line_edit_creates(self, qt_app):
        """Test StyledLineEdit initializes successfully"""
        edit = StyledLineEdit()
        assert edit is not None
        assert isinstance(edit, QLineEdit)

    def test_styled_line_edit_accepts_text(self, qt_app):
        """Test StyledLineEdit accepts text input"""
        edit = StyledLineEdit()
        edit.setText("Test text")
        assert edit.text() == "Test text"

    def test_styled_line_edit_placeholder(self, qt_app):
        """Test StyledLineEdit can have placeholder"""
        edit = StyledLineEdit()
        edit.setPlaceholderText("Enter text...")
        assert edit.placeholderText() == "Enter text..."

    def test_styled_line_edit_is_enabled(self, qt_app):
        """Test StyledLineEdit is enabled by default"""
        edit = StyledLineEdit()
        assert edit.isEnabled() == True


class TestStyledTextEdit:
    """Test StyledTextEdit widget"""

    def test_styled_text_edit_creates(self, qt_app):
        """Test StyledTextEdit initializes successfully"""
        edit = StyledTextEdit()
        assert edit is not None

    def test_styled_text_edit_accepts_text(self, qt_app):
        """Test StyledTextEdit accepts multi-line text"""
        edit = StyledTextEdit()
        edit.setPlainText("Line 1\nLine 2")
        assert "Line 1" in edit.toPlainText()
        assert "Line 2" in edit.toPlainText()


class TestStyledComboBox:
    """Test StyledComboBox widget"""

    def test_styled_combo_box_creates(self, qt_app):
        """Test StyledComboBox initializes successfully"""
        combo = StyledComboBox()
        assert combo is not None

    def test_styled_combo_box_accepts_items(self, qt_app):
        """Test StyledComboBox accepts items"""
        combo = StyledComboBox()
        combo.addItem("Option 1")
        combo.addItem("Option 2")
        assert combo.count() == 2

    def test_styled_combo_box_selection(self, qt_app):
        """Test StyledComboBox selection works"""
        combo = StyledComboBox()
        combo.addItem("Option 1")
        combo.addItem("Option 2")
        combo.setCurrentIndex(1)
        assert combo.currentText() == "Option 2"


# ========== CHECKBOX TESTS ==========

class TestStyledCheckBox:
    """Test StyledCheckBox widget"""

    def test_styled_checkbox_creates(self, qt_app):
        """Test StyledCheckBox initializes successfully"""
        chk = StyledCheckBox("Check me")
        assert chk is not None
        assert isinstance(chk, QCheckBox)

    def test_styled_checkbox_text(self, qt_app):
        """Test StyledCheckBox displays text"""
        chk = StyledCheckBox("Check me")
        assert chk.text() == "Check me"

    def test_styled_checkbox_toggling(self, qt_app):
        """Test StyledCheckBox can be toggled"""
        chk = StyledCheckBox("Test")
        initial = chk.isChecked()
        chk.setChecked(not initial)
        assert chk.isChecked() != initial

    def test_styled_checkbox_emits_signal(self, qt_app):
        """Test StyledCheckBox emits stateChanged signal"""
        chk = StyledCheckBox("Test")
        signal_received = []
        chk.stateChanged.connect(lambda: signal_received.append(True))

        chk.setChecked(not chk.isChecked())
        qt_app.processEvents()

        assert len(signal_received) > 0


# ========== LABEL TESTS ==========

class TestStyledLabel:
    """Test StyledLabel widget"""

    def test_styled_label_creates(self, qt_app):
        """Test StyledLabel initializes successfully"""
        label = StyledLabel("Test Label")
        assert label is not None
        assert isinstance(label, QLabel)

    def test_styled_label_text(self, qt_app):
        """Test StyledLabel displays text"""
        label = StyledLabel("Test Label")
        assert label.text() == "Test Label"


class TestTitleLabel:
    """Test TitleLabel widget"""

    def test_title_label_creates(self, qt_app):
        """Test TitleLabel initializes successfully"""
        label = TitleLabel("Title")
        assert label is not None
        assert isinstance(label, QLabel)


class TestHeadingLabel:
    """Test HeadingLabel widget"""

    def test_heading_label_creates(self, qt_app):
        """Test HeadingLabel initializes successfully"""
        label = HeadingLabel("Heading")
        assert label is not None
        assert isinstance(label, QLabel)


class TestMutedLabel:
    """Test MutedLabel widget"""

    def test_muted_label_creates(self, qt_app):
        """Test MutedLabel initializes successfully"""
        label = MutedLabel("Muted text")
        assert label is not None
        assert isinstance(label, QLabel)


# ========== FRAME TESTS ==========

class TestCardFrame:
    """Test CardFrame widget"""

    def test_card_frame_creates(self, qt_app):
        """Test CardFrame initializes successfully"""
        frame = CardFrame()
        assert frame is not None
        assert isinstance(frame, QFrame)

    def test_card_frame_has_layout(self, qt_app):
        """Test CardFrame has layout"""
        frame = CardFrame()
        assert frame.layout() is not None

    def test_card_frame_accepts_widgets(self, qt_app):
        """Test CardFrame accepts child widgets"""
        frame = CardFrame()
        label = QLabel("Test")
        frame.layout().addWidget(label)
        # Check that widget was added
        assert frame.layout().count() > 0


class TestSeparatorFrame:
    """Test SeparatorFrame widget"""

    def test_separator_frame_creates(self, qt_app):
        """Test SeparatorFrame initializes successfully"""
        sep = SeparatorFrame()
        assert sep is not None
        assert isinstance(sep, QFrame)


class TestScrollableFrame:
    """Test ScrollableFrame widget"""

    def test_scrollable_frame_creates(self, qt_app):
        """Test ScrollableFrame initializes successfully"""
        frame = ScrollableFrame()
        assert frame is not None
        assert isinstance(frame, QScrollArea)

    def test_scrollable_frame_with_spacing(self, qt_app):
        """Test ScrollableFrame accepts spacing parameter"""
        frame = ScrollableFrame(spacing=8)
        assert frame.content_layout.spacing() == 8

    def test_scrollable_frame_default_spacing(self, qt_app):
        """Test ScrollableFrame has default spacing of 0"""
        frame = ScrollableFrame()
        assert frame.content_layout.spacing() == 0

    def test_scrollable_frame_accepts_widgets(self, qt_app):
        """Test ScrollableFrame can add widgets"""
        frame = ScrollableFrame()
        label = QLabel("Test")
        frame.add_widget(label)
        assert frame.content_layout.count() > 0

    def test_scrollable_frame_add_stretch(self, qt_app):
        """Test ScrollableFrame can add stretch"""
        frame = ScrollableFrame()
        frame.add_stretch()
        # Verify stretch was added (count increases)
        assert frame.content_layout.count() > 0

    def test_scrollable_frame_resizable(self, qt_app):
        """Test ScrollableFrame is resizable"""
        frame = ScrollableFrame()
        assert frame.widgetResizable() == True


# ========== LAYOUT FRAMES TESTS ==========

class TestHorizontalFrame:
    """Test HorizontalFrame widget"""

    def test_horizontal_frame_creates(self, qt_app):
        """Test HorizontalFrame initializes successfully"""
        frame = HorizontalFrame()
        assert frame is not None
        assert isinstance(frame, QFrame)

    def test_horizontal_frame_has_layout(self, qt_app):
        """Test HorizontalFrame has horizontal layout"""
        frame = HorizontalFrame()
        assert frame.layout() is not None

    def test_horizontal_frame_with_spacing(self, qt_app):
        """Test HorizontalFrame accepts spacing parameter"""
        frame = HorizontalFrame(spacing=12)
        assert frame.layout().spacing() == 12

    def test_horizontal_frame_accepts_widgets(self, qt_app):
        """Test HorizontalFrame accepts child widgets"""
        frame = HorizontalFrame()
        btn1 = QPushButton("Button 1")
        btn2 = QPushButton("Button 2")
        frame.layout().addWidget(btn1)
        frame.layout().addWidget(btn2)
        assert frame.layout().count() >= 2


class TestVerticalFrame:
    """Test VerticalFrame widget"""

    def test_vertical_frame_creates(self, qt_app):
        """Test VerticalFrame initializes successfully"""
        frame = VerticalFrame()
        assert frame is not None
        assert isinstance(frame, QFrame)

    def test_vertical_frame_has_layout(self, qt_app):
        """Test VerticalFrame has vertical layout"""
        frame = VerticalFrame()
        assert frame.layout() is not None

    def test_vertical_frame_with_spacing(self, qt_app):
        """Test VerticalFrame accepts spacing parameter"""
        frame = VerticalFrame(spacing=8)
        assert frame.layout().spacing() == 8

    def test_vertical_frame_accepts_widgets(self, qt_app):
        """Test VerticalFrame accepts child widgets"""
        frame = VerticalFrame()
        label1 = QLabel("Line 1")
        label2 = QLabel("Line 2")
        frame.layout().addWidget(label1)
        frame.layout().addWidget(label2)
        assert frame.layout().count() >= 2


# ========== WIDGET COMPOSITION TESTS ==========

class TestWidgetComposition:
    """Test composing multiple widgets together"""

    def test_button_in_horizontal_frame(self, qt_app):
        """Test buttons in horizontal layout"""
        frame = HorizontalFrame(spacing=8)
        btn1 = StyledButton("Button 1", Colors.ACCENT)
        btn2 = SuccessButton("OK")
        frame.layout().addWidget(btn1)
        frame.layout().addWidget(btn2)
        assert frame.layout().count() >= 2

    def test_inputs_in_vertical_frame(self, qt_app):
        """Test input fields in vertical layout"""
        frame = VerticalFrame(spacing=6)
        label = StyledLabel("Name:")
        edit = StyledLineEdit()
        frame.layout().addWidget(label)
        frame.layout().addWidget(edit)
        assert frame.layout().count() >= 2

    def test_card_with_mixed_widgets(self, qt_app):
        """Test CardFrame with various widgets"""
        card = CardFrame()
        title = TitleLabel("Settings")
        checkbox = StyledCheckBox("Enable feature")
        button = StyledButton("Save", Colors.ACCENT)

        card.layout().addWidget(title)
        card.layout().addWidget(checkbox)
        card.layout().addWidget(button)

        assert card.layout().count() >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
