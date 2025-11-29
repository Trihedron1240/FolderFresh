# FolderFresh PySide6 UI - Manual Testing Checklist

**Application**: FolderFresh (Modern PySide6 Interface)
**Test Date**: _______________
**Tester**: _______________
**Build/Version**: _______________

---

## Overview

This checklist provides comprehensive manual testing coverage for the FolderFresh PySide6 UI. All items should be tested before release.

**Format**:
- [ ] Test description
- **Expected Result**: What should happen
- **Actual Result**: What actually happened
- **Status**: PASS / FAIL / SKIP

---

## 1. Application Launch & Initialization

### 1.1 Application Startup
- [ ] Application launches without crashes
  - **Expected Result**: Window appears with all components visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Window title displays correctly
  - **Expected Result**: Window title shows "FolderFresh"
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Window size is appropriate
  - **Expected Result**: Window opens at reasonable size (1200x800 or similar)
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] All UI components are visible
  - **Expected Result**: Buttons, checkboxes, input fields all visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 1.2 Application Themes
- [ ] Dark theme applied on startup
  - **Expected Result**: Application uses dark color scheme
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] No white space visible
  - **Expected Result**: Entire window has dark background
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Text is readable (high contrast)
  - **Expected Result**: All text clearly readable on dark background
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 2. Main Window Components

### 2.1 Header Section
- [ ] Header displays correctly
  - **Expected Result**: Header section visible with title and folder path area
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Path entry field shows placeholder text
  - **Expected Result**: Placeholder text visible (e.g., "No folder selected")
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Browse folder button is visible
  - **Expected Result**: Button with folder icon or text visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 2.2 Button Section
- [ ] Preview button is visible and clickable
  - **Expected Result**: Button displays "Preview" and responds to click
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Organise Files button is visible and clickable
  - **Expected Result**: Button displays "Organise Files" and responds to click
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Undo Last button is visible
  - **Expected Result**: Button displays "Undo Last" (may be disabled initially)
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Find Duplicates button is visible and clickable
  - **Expected Result**: Button displays "Find Duplicates" and responds to click
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Clean Desktop button is visible and clickable
  - **Expected Result**: Button displays "Clean Desktop" and responds to click
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] All buttons have proper spacing
  - **Expected Result**: Buttons evenly spaced without overlapping
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Buttons show hover effect
  - **Expected Result**: Button appearance changes when mouse hovers over it
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Buttons show press effect
  - **Expected Result**: Button appearance changes when clicked
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 2.3 Checkbox Section (Options)
- [ ] "Include subfolders" checkbox is visible
  - **Expected Result**: Checkbox with label visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] "Skip Hidden/System Files" checkbox is visible
  - **Expected Result**: Checkbox with label visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] "Safe Mode" checkbox is visible
  - **Expected Result**: Checkbox with label visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] "Smart Sorting" checkbox is visible
  - **Expected Result**: Checkbox with label visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] "Auto-tidy" checkbox is visible
  - **Expected Result**: Checkbox with label visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Include subfolders checkbox is checked by default
  - **Expected Result**: Checkbox is checked initially
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Skip Hidden checkbox is checked by default
  - **Expected Result**: Checkbox is checked initially
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Checkboxes can be toggled
  - **Expected Result**: Clicking checkbox toggles it on/off
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 2.4 Preview Box
- [ ] Preview box is visible
  - **Expected Result**: Large text area visible below buttons
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Preview box is read-only
  - **Expected Result**: Cannot type in preview box
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Preview box has placeholder text
  - **Expected Result**: Placeholder visible (e.g., "Click Preview to see results")
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 2.5 Advanced Section
- [ ] Advanced Options button is visible
  - **Expected Result**: Collapsible section button visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Advanced section is hidden by default
  - **Expected Result**: Advanced content not visible initially
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Advanced section can be expanded
  - **Expected Result**: Clicking button shows advanced options
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Advanced section can be collapsed
  - **Expected Result**: Clicking button again hides advanced options
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Advanced button text indicates state
  - **Expected Result**: Button text shows expand/collapse indicator
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 3. Window Management

### 3.1 Main Window Controls
- [ ] Window can be minimized
  - **Expected Result**: Window minimizes to taskbar
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Window can be maximized
  - **Expected Result**: Window expands to fill screen
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Window can be resized
  - **Expected Result**: Window resizes smoothly
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Window can be closed
  - **Expected Result**: Clicking X button closes application
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 3.2 Menu Bar / Top Controls
- [ ] Menu bar is visible (if implemented)
  - **Expected Result**: Menu items visible or hamburger menu present
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Settings menu accessible
  - **Expected Result**: Can open settings/preferences
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 4. Folder Selection & Path Display

### 4.1 Folder Selection
- [ ] Browse button opens folder dialog
  - **Expected Result**: Folder selection dialog appears
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can select a folder
  - **Expected Result**: Can navigate and select folder from dialog
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Selected folder path displays in path entry
  - **Expected Result**: Full path shown in path field
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Invalid paths show error message
  - **Expected Result**: Error dialog appears if invalid folder selected
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 4.2 Path Display
- [ ] Path entry shows full path
  - **Expected Result**: Absolute path visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Path can be copied (if right-click enabled)
  - **Expected Result**: Can copy path to clipboard
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 5. Button Functionality

### 5.1 Preview Button
- [ ] Preview button is enabled when folder selected
  - **Expected Result**: Button becomes enabled after folder selection
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Preview button disabled without folder
  - **Expected Result**: Button disabled when no folder selected
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Clicking Preview shows results
  - **Expected Result**: Preview box populates with file list/organization preview
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Preview doesn't modify files
  - **Expected Result**: Files unchanged after preview
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 5.2 Organise Button
- [ ] Organise button is enabled when folder selected
  - **Expected Result**: Button becomes enabled after folder selection
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Organise button disabled without folder
  - **Expected Result**: Button disabled when no folder selected
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Clicking Organise applies organization
  - **Expected Result**: Files organized according to rules
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Safe Mode prevents actual changes
  - **Expected Result**: With Safe Mode checked, preview only (no actual changes)
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Success message shows after organization
  - **Expected Result**: Dialog or message shows number of files organized
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 5.3 Undo Button
- [ ] Undo button disabled initially
  - **Expected Result**: Button disabled when no history
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Undo button enabled after organization
  - **Expected Result**: Button becomes enabled after files organized
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Undo reverses last operation
  - **Expected Result**: Files returned to original state
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Undo button text shows action
  - **Expected Result**: Button shows "Undo Move", "Undo Rename", etc.
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 5.4 Find Duplicates Button
- [ ] Find Duplicates dialog opens
  - **Expected Result**: Duplicates dialog appears when clicked
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Duplicates are identified correctly
  - **Expected Result**: Duplicate files shown in dialog
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 5.5 Clean Desktop Button
- [ ] Clean Desktop dialog opens
  - **Expected Result**: Desktop cleanup dialog appears
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 6. Checkbox & Option Management

### 6.1 Include Subfolders
- [ ] When checked, includes subfolders
  - **Expected Result**: Organization includes nested folders
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] When unchecked, excludes subfolders
  - **Expected Result**: Organization only processes folder root
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] State persists between sessions (if implemented)
  - **Expected Result**: Checkbox state remembered
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 6.2 Skip Hidden/System Files
- [ ] When checked, skips hidden files
  - **Expected Result**: Hidden files not processed
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] When unchecked, includes hidden files
  - **Expected Result**: Hidden files are processed
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 6.3 Safe Mode
- [ ] When checked, preview only
  - **Expected Result**: No actual file changes
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] When unchecked, applies changes
  - **Expected Result**: Files actually moved/organized
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Warning displayed about Safe Mode
  - **Expected Result**: Clear indication when Safe Mode active
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 6.4 Smart Sorting
- [ ] When checked, uses smart categorization
  - **Expected Result**: Files organized by category
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 6.5 Auto-tidy
- [ ] When checked, enables watch mode
  - **Expected Result**: Automatic organization on file changes
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 7. Window Management Features

### 7.1 Manage Profiles
- [ ] Manage Profiles menu item is accessible
  - **Expected Result**: Menu or button opens profiles window
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Profiles window opens without errors
  - **Expected Result**: ProfileManagerWindow displays
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Profile list displays
  - **Expected Result**: List of profiles visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can create new profile
  - **Expected Result**: New Profile button creates profile
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can edit profile
  - **Expected Result**: Can modify profile settings
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can delete profile
  - **Expected Result**: Can remove profile
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Cannot delete active profile
  - **Expected Result**: Error shown if trying to delete active profile
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 7.2 Manage Rules
- [ ] Manage Rules menu item is accessible
  - **Expected Result**: Menu or button opens rules window
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Rules window opens without errors
  - **Expected Result**: RuleManager window displays
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Rule list displays
  - **Expected Result**: List of rules visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can create new rule
  - **Expected Result**: New Rule button opens rule editor
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can edit rule
  - **Expected Result**: Can modify rule settings
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can delete rule
  - **Expected Result**: Can remove rule
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can test rule
  - **Expected Result**: Test button shows rule results
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 7.3 Manage Watched Folders
- [ ] Manage Watched Folders menu item is accessible
  - **Expected Result**: Menu or button opens watched folders window
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Watched Folders window opens
  - **Expected Result**: WatchedFoldersWindow displays
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Folder list displays
  - **Expected Result**: List of watched folders visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can add watched folder
  - **Expected Result**: Add button adds folder
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can remove watched folder
  - **Expected Result**: Can remove folder from watch list
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 7.4 Activity Log
- [ ] Activity Log menu item is accessible
  - **Expected Result**: Menu or button opens activity log
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Activity Log window opens
  - **Expected Result**: ActivityLogWindow displays
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Log entries are displayed
  - **Expected Result**: Activity log shows entries
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Log updates in real-time
  - **Expected Result**: New entries appear without refresh
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can clear log
  - **Expected Result**: Clear button removes all entries
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 7.5 Help
- [ ] Help menu item is accessible
  - **Expected Result**: Help button or menu item visible
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Help window opens
  - **Expected Result**: Help information displays
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 8. Styling & Appearance

### 8.1 Color Scheme
- [ ] Dark theme is applied consistently
  - **Expected Result**: All UI elements use dark colors
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] No white/light areas visible
  - **Expected Result**: Entire interface is dark
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Text is readable on dark background
  - **Expected Result**: High contrast between text and background
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Accent colors are used appropriately
  - **Expected Result**: Blue accents for primary actions
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 8.2 Spacing & Layout
- [ ] Spacing is cohesive
  - **Expected Result**: Consistent spacing throughout UI
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] No visible gaps between sections
  - **Expected Result**: Seamless transitions
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Buttons are properly aligned
  - **Expected Result**: Buttons in straight row, even spacing
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Text alignment is correct
  - **Expected Result**: Left-aligned text is readable
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 8.3 Visual Feedback
- [ ] Buttons show hover effect
  - **Expected Result**: Button appearance changes on hover
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Buttons show pressed effect
  - **Expected Result**: Button appearance changes when clicked
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Input fields show focus state
  - **Expected Result**: Visible focus border when field active
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Disabled buttons appear grayed out
  - **Expected Result**: Disabled buttons have different appearance
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 8.4 Icons & Graphics
- [ ] Icons display correctly
  - **Expected Result**: All icons render properly
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Icons are appropriately sized
  - **Expected Result**: Icons not too large or too small
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 9. Keyboard Navigation

### 9.1 Tab Navigation
- [ ] Tab navigates through controls
  - **Expected Result**: Can tab through all controls
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Tab order is logical
  - **Expected Result**: Tab moves through controls in sensible order
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Shift+Tab goes backward
  - **Expected Result**: Can navigate backward with Shift+Tab
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 9.2 Keyboard Shortcuts
- [ ] Ctrl+O opens organization
  - **Expected Result**: Shortcut works (if implemented)
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Ctrl+Z triggers undo
  - **Expected Result**: Shortcut works (if implemented)
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Ctrl+P opens profiles
  - **Expected Result**: Shortcut works (if implemented)
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] F1 opens help
  - **Expected Result**: Shortcut works (if implemented)
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Escape closes dialogs
  - **Expected Result**: Can close dialogs with Escape key
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 9.3 Enter Key
- [ ] Enter activates focused button
  - **Expected Result**: Pressing Enter clicks focused button
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Enter toggles checkbox
  - **Expected Result**: Pressing Enter toggles checkbox
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 10. Error Handling

### 10.1 Invalid Input
- [ ] Invalid folder path shows error
  - **Expected Result**: Error message if non-existent folder selected
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] File operation errors show message
  - **Expected Result**: Error dialog shown for failed operations
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Permission denied shows appropriate message
  - **Expected Result**: Clear error if insufficient permissions
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 10.2 Data Validation
- [ ] Rule names cannot be empty
  - **Expected Result**: Error if rule created with no name
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Duplicate profile names prevented
  - **Expected Result**: Error if duplicate name used
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Invalid rules rejected
  - **Expected Result**: Error dialog if invalid rule configuration
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 10.3 Exception Handling
- [ ] Application doesn't crash on errors
  - **Expected Result**: Errors handled gracefully
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Error messages are helpful
  - **Expected Result**: Messages explain problem and solution
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 11. Performance & Responsiveness

### 11.1 Responsiveness
- [ ] UI responds quickly to clicks
  - **Expected Result**: No lag when clicking buttons
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Dialogs open quickly
  - **Expected Result**: Windows open without delay
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Preview processes quickly
  - **Expected Result**: Preview results show within 1-2 seconds
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Organization completes in reasonable time
  - **Expected Result**: File operations complete smoothly
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 11.2 Resource Usage
- [ ] Application doesn't consume excessive CPU
  - **Expected Result**: CPU usage reasonable when idle
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Application doesn't consume excessive memory
  - **Expected Result**: Memory usage reasonable
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 12. Accessibility

### 12.1 Visual Accessibility
- [ ] High contrast between text and background
  - **Expected Result**: Text is clearly readable
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Font size is appropriate
  - **Expected Result**: Text is not too small
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Focus indicators visible
  - **Expected Result**: Can see which control has focus
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 12.2 Input Accessibility
- [ ] All buttons have text labels
  - **Expected Result**: Clear indication of button purpose
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Checkboxes have associated labels
  - **Expected Result**: Can click label to toggle checkbox
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Keyboard navigation works completely
  - **Expected Result**: All controls accessible via keyboard
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 13. Integration Testing

### 13.1 Multi-Window Operations
- [ ] Can open multiple windows
  - **Expected Result**: Multiple windows can exist simultaneously
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Windows communicate correctly
  - **Expected Result**: Changes in one window reflected in others
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Can close individual windows
  - **Expected Result**: Closing one window doesn't affect others
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 13.2 Feature Integration
- [ ] Rules work with profiles
  - **Expected Result**: Rules in profile execute correctly
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Watched folders use correct profile
  - **Expected Result**: Folder-specific profile applied
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Undo works after organization
  - **Expected Result**: Can undo files organized via rules
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Activity log records all operations
  - **Expected Result**: All actions logged to activity log
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 14. Data Persistence

### 14.1 Configuration Saving
- [ ] Options persist between sessions
  - **Expected Result**: Checkbox states saved
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Profiles persist between sessions
  - **Expected Result**: Profiles saved to disk
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Rules persist between sessions
  - **Expected Result**: Rules saved to disk
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Watched folders persist
  - **Expected Result**: Folder list saved between sessions
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 14.2 Data Recovery
- [ ] Corrupted config is handled
  - **Expected Result**: App recovers or warns user
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] Missing files don't crash app
  - **Expected Result**: App handles missing config gracefully
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## 15. Cross-Platform Testing (If Applicable)

### 15.1 Windows Testing
- [ ] Application launches on Windows
  - **Expected Result**: No Windows-specific errors
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

- [ ] File paths work correctly on Windows
  - **Expected Result**: Backslashes handled correctly
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 15.2 Linux Testing (If Supported)
- [ ] Application launches on Linux
  - **Expected Result**: No Linux-specific errors
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

### 15.3 macOS Testing (If Supported)
- [ ] Application launches on macOS
  - **Expected Result**: No macOS-specific errors
  - **Actual Result**: _______________________
  - **Status**: [ ] PASS [ ] FAIL [ ] SKIP

---

## Summary

### Test Results
- **Total Tests**: ____
- **Passed**: ____
- **Failed**: ____
- **Skipped**: ____
- **Pass Rate**: ____%

### Critical Issues Found
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________

### Minor Issues Found
1. _________________________________________________________________
2. _________________________________________________________________
3. _________________________________________________________________

### Recommendations
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

### Overall Assessment
[ ] PASS - Ready for release
[ ] PASS WITH NOTES - Ready with minor issues
[ ] FAIL - Do not release, critical issues found

### Sign-Off
**Tested By**: ___________________________
**Date**: ___________________________
**Signature**: ___________________________

---

**Document Version**: 1.0
**Last Updated**: 2025-11-29
**Status**: Complete
