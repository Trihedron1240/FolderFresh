# FolderFresh Design Tokens - Quick Reference Guide

## Color Tokens

### Semantic Colors (Recommended)
```python
from folderfresh.ui_qt import Colors

# Primary action color (blue)
Colors.get("primary")           # #2563eb
Colors.get("primary.hover")     # #1d4ed8
Colors.get("primary.active")    # #1e40af

# Success actions (green)
Colors.get("success")           # #10b981
Colors.get("success.hover")     # #059669

# Danger/Destructive (red)
Colors.get("danger")            # #ef4444
Colors.get("danger.hover")      # #dc2626

# Warning/Caution (amber)
Colors.get("warning")           # #f59e0b
Colors.get("warning.hover")     # #d97706

# Information (cyan)
Colors.get("info")              # #0ea5e9
Colors.get("info.hover")        # #0284c7

# Background colors
Colors.get("bg.primary")        # Main background
Colors.get("bg.secondary")      # Cards/elevated
Colors.get("bg.tertiary")       # Inputs/overlays

# Text colors
Colors.get("text.primary")      # Main text
Colors.get("text.secondary")    # Secondary text
Colors.get("text.tertiary")     # Tertiary text
Colors.get("text.muted")        # Dimmed text
Colors.get("text.disabled")     # Disabled text

# Border colors
Colors.get("border.default")    # Default borders
Colors.get("border.light")      # Light borders (hover)
Colors.get("border.focus")      # Focus ring color
```

### Theme Switching
```python
# Switch between dark and light themes
Colors.set_theme("dark")        # Dark theme (default)
Colors.set_theme("light")       # Light theme

# All Colors.get() calls adapt to active theme
```

---

## Design Tokens

### Spacing Scale
```python
from folderfresh.ui_qt import DesignTokens

# Use for margins, padding, gaps
DesignTokens.Spacing.XS         # 4px   - Extra small gaps
DesignTokens.Spacing.SM         # 8px   - Small gaps
DesignTokens.Spacing.MD         # 12px  - Medium gaps (default)
DesignTokens.Spacing.LG         # 16px  - Large gaps
DesignTokens.Spacing.XL         # 24px  - Extra large gaps
DesignTokens.Spacing.XXL        # 32px  - Extra extra large gaps

# Example usage
layout.setSpacing(DesignTokens.Spacing.MD)      # Between widgets
layout.setContentsMargins(DesignTokens.Spacing.LG,
                          DesignTokens.Spacing.LG,
                          DesignTokens.Spacing.LG,
                          DesignTokens.Spacing.LG)  # Around content
```

### Shadow Elevation
```python
# Use for depth perception in QSS
DesignTokens.Shadows.NONE       # No shadow
DesignTokens.Shadows.SM         # 0 1px 2px 0 rgba(0,0,0,0.05)
DesignTokens.Shadows.MD         # Standard shadow (cards)
DesignTokens.Shadows.LG         # Prominent shadow (modals)
DesignTokens.Shadows.XL         # Maximum shadow (important dialogs)

# Example in QSS
stylesheet = f"""
    QFrame {{
        box-shadow: {DesignTokens.Shadows.MD};
        border-radius: 8px;
    }}
"""
```

### Border Radius Scale
```python
# Use for consistent corner rounding
DesignTokens.BorderRadius.NONE  # 0px - Square corners
DesignTokens.BorderRadius.SM    # 4px - Subtle rounding
DesignTokens.BorderRadius.MD    # 6px - Default rounding
DesignTokens.BorderRadius.LG    # 8px - Card rounding
DesignTokens.BorderRadius.XL    # 12px - Large elements
DesignTokens.BorderRadius.FULL  # 9999px - Perfect circles
```

### Z-Index Layers
```python
# Use for stacking context management
DesignTokens.ZIndex.DROPDOWN    # 100  - Dropdown menus
DesignTokens.ZIndex.STICKY      # 500  - Sticky elements
DesignTokens.ZIndex.FIXED       # 600  - Fixed positioning
DesignTokens.ZIndex.MODAL       # 1000 - Modal dialogs
DesignTokens.ZIndex.TOOLTIP     # 1100 - Tooltips
```

---

## Typography

### Font Sizes
```python
from folderfresh.ui_qt import Fonts

Fonts.SIZE_DISPLAY              # 32pt - Hero/display text
Fonts.SIZE_TITLE                # 24pt - Page titles
Fonts.SIZE_HEADING              # 18pt - Section headers
Fonts.SIZE_SUBHEADING           # 14pt - Subsection headers
Fonts.SIZE_NORMAL               # 11pt - Body text (default)
Fonts.SIZE_SMALL                # 10pt - Small text/labels
Fonts.SIZE_TINY                 # 9pt  - Extra small text

# Example: Create large heading
label = StyledLabel("Page Title")
label.setStyleSheet(get_label_stylesheet(
    font_size=Fonts.SIZE_TITLE,
    font_weight=Fonts.WEIGHT_BOLD,
))
```

### Font Weights
```python
Fonts.WEIGHT_NORMAL             # 400 - Standard text
Fonts.WEIGHT_MEDIUM             # 500 - Labels/emphasis
Fonts.WEIGHT_SEMIBOLD           # 600 - Headings
Fonts.WEIGHT_BOLD               # 700 - Titles/strong
Fonts.WEIGHT_EXTRABOLD          # 800 - Hero text
```

### Line Heights
```python
Fonts.LINEHEIGHT_TIGHT          # 1.2  - Headings (compact)
Fonts.LINEHEIGHT_NORMAL         # 1.5  - Body text (default)
Fonts.LINEHEIGHT_RELAXED        # 1.75 - Long-form content
Fonts.LINEHEIGHT_LOOSE          # 2.0  - Extra spacing
```

### Letter Spacing
```python
Fonts.LETTERSPACING_TIGHT       # -0.01em - Condensed
Fonts.LETTERSPACING_NORMAL      # 0em     - Standard
Fonts.LETTERSPACING_WIDE        # 0.02em  - Expanded
```

### Font Families
```python
Fonts.PRIMARY_FAMILY            # "Segoe UI Variable"
Fonts.FALLBACK_FAMILY           # "Segoe UI"
Fonts.MONOSPACE_FAMILY          # "Courier New"
```

---

## Component Usage Examples

### Modern Buttons
```python
from folderfresh.ui_qt import StyledButton, SuccessButton, DangerButton

# Primary button (blue)
btn = StyledButton("Click Me")

# Success button (green)
btn = SuccessButton("Organize Files")

# Danger button (red)
btn = DangerButton("Delete")

# Custom color button
btn = StyledButton(
    "Custom",
    bg_color=Colors.get("secondary"),
    text_color=Colors.TEXT,
)
```

### Form Inputs
```python
from folderfresh.ui_qt import StyledLineEdit, StyledTextEdit, StyledComboBox, StyledCheckBox

# Text input
input = StyledLineEdit("Type here...")

# Multi-line text
textarea = StyledTextEdit("Multi-line text...")

# Dropdown
dropdown = StyledComboBox(["Option 1", "Option 2", "Option 3"])

# Checkbox
checkbox = StyledCheckBox("Agree to terms", checked=True)
```

### Containers
```python
from folderfresh.ui_qt import CardFrame, VerticalFrame, HorizontalFrame

# Card container (elevated, rounded)
card = CardFrame()
card_layout = QVBoxLayout(card)
card_layout.addWidget(StyledLabel("Card Content"))

# Vertical layout container
v_container = VerticalFrame(spacing=DesignTokens.Spacing.MD)
v_container.add_widget(widget1)
v_container.add_widget(widget2)

# Horizontal layout container
h_container = HorizontalFrame(spacing=DesignTokens.Spacing.LG)
h_container.add_widget(button1)
h_container.add_widget(button2)
h_container.add_stretch()
```

### Typography
```python
from folderfresh.ui_qt import TitleLabel, HeadingLabel, StyledLabel, MutedLabel

# Page title
title = TitleLabel("Page Title")

# Section heading
heading = HeadingLabel("Section Heading")

# Body text
text = StyledLabel("Regular text content")

# Secondary/dimmed text
muted = MutedLabel("Secondary information")
```

---

## Custom Styling with Design Tokens

### Creating Custom Components
```python
from folderfresh.ui_qt import Colors, DesignTokens, Fonts, get_label_stylesheet

# Create custom styled label
custom_label = QLabel("Custom Text")
custom_label.setStyleSheet(f"""
    QLabel {{
        color: {Colors.get("text.primary")};
        font-size: {Fonts.SIZE_NORMAL}pt;
        font-weight: {Fonts.WEIGHT_MEDIUM};
        padding: {DesignTokens.Spacing.MD}px;
        background-color: {Colors.get("bg.secondary")};
        border-radius: {DesignTokens.BorderRadius.MD}px;
        border: 1px solid {Colors.get("border.default")};
    }}
    QLabel:hover {{
        background-color: {Colors.get("bg.primary")};
        border-color: {Colors.get("border.light")};
    }}
""")
```

### Using Semantic Colors in QSS
```python
# Bad: Hardcoded colors
stylesheet = "background-color: #0f1720;"

# Good: Use semantic tokens
stylesheet = f"background-color: {Colors.get('bg.primary')};"

# Benefits:
# 1. Theme switching works automatically
# 2. Easy to maintain and update
# 3. Consistent with design system
# 4. Self-documenting intent
```

---

## Design Consistency Tips

1. **Always use semantic tokens** instead of hardcoded colors
   - Use `Colors.get("primary")` not `"#2563eb"`

2. **Spacing should follow the scale** (4px increments)
   - Use `DesignTokens.Spacing.MD` not arbitrary values like `13px`

3. **Typography hierarchy matters**
   - Use `Fonts.SIZE_TITLE` for titles, `Fonts.SIZE_NORMAL` for body text
   - Don't use random font sizes

4. **Respect the border radius scale**
   - Use `DesignTokens.BorderRadius.MD` (6px) for most components
   - Use `DesignTokens.BorderRadius.LG` (8px) for cards/panels

5. **Use the right shadow level**
   - Cards: `DesignTokens.Shadows.MD`
   - Modals: `DesignTokens.Shadows.LG`
   - Dropdowns: No shadow or `SM`

6. **Color psychology**
   - Success actions: Green (`Colors.get("success")`)
   - Dangerous/destructive: Red (`Colors.get("danger")`)
   - Warnings: Amber (`Colors.get("warning")`)
   - Primary actions: Blue (`Colors.get("primary")`)

---

## Component Showcase

Want to see all components in action?

```python
from folderfresh.ui_qt import ComponentShowcaseWindow

window = ComponentShowcaseWindow()
window.show()
```

This opens an interactive demo with:
- Color palette display
- All button variants
- Form controls showcase
- Typography hierarchy
- Container examples

---

## Migration Checklist (For Updating Existing Code)

- [ ] Replace hardcoded colors with `Colors.get(token)`
- [ ] Use `DesignTokens.Spacing` for all margins/padding
- [ ] Use `Fonts.SIZE_*` constants instead of magic numbers
- [ ] Use `DesignTokens.BorderRadius` for consistency
- [ ] Add focus states to interactive elements
- [ ] Test with both themes: `Colors.set_theme("dark")` and `Colors.set_theme("light")`

---

## Version History

- **v1.0** (2025-11-29): Initial release with dark/light theme support

---

*Last Updated: 2025-11-29*
*Ready for Production Use ✅*
