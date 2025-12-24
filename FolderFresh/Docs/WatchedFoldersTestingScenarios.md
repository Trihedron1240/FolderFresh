# Watched Folders Testing Scenarios

This document outlines manual testing scenarios for the Watched Folders feature.

## Basic Functionality Tests

### 1. Add Watched Folder
**Steps:**
1. Click "Add Folder" button
2. Select a folder using the folder picker
3. Configure display name, profile, and options
4. Click "Add"

**Expected Results:**
- Folder appears in the list with correct display name
- Status shows "Idle" or "Watching" based on IsEnabled setting
- Profile name is displayed correctly
- File count is accurate

### 2. Enable/Disable Watcher
**Steps:**
1. Toggle the enable switch on a watched folder
2. Observe status badge changes

**Expected Results:**
- Enabling: Status changes from "Idle" to "Watching"
- Disabling: Status changes from "Watching" to "Idle"
- File system watcher is started/stopped accordingly

### 3. Manual Organization
**Steps:**
1. Add files to a watched folder (not matching organization rules)
2. Click "Organize" button on the folder card
3. Observe the organization progress

**Expected Results:**
- Button shows loading spinner during operation
- Files are moved according to profile rules/categories
- Success dialog shows count of files moved
- Last organized timestamp updates

### 4. Preview Organization
**Steps:**
1. Add files to a watched folder
2. Click "Preview" button
3. Review the preview dialog

**Expected Results:**
- Preview dialog shows correct file counts
- Files are grouped by destination folder
- Match type (Rule/Category) is displayed
- "Organize Now" button is available if files need organizing

### 5. Remove Watched Folder
**Steps:**
1. Click More button (three dots) on a folder card
2. Select "Remove"
3. Confirm removal

**Expected Results:**
- Confirmation dialog appears
- Folder is removed from the list
- Watcher is stopped
- Files in the folder are NOT deleted

## Auto-Organization Tests

### 6. Auto-Organize on File Creation
**Prerequisites:** Folder with AutoOrganize enabled

**Steps:**
1. Create/copy a new file into the watched folder
2. Wait for debounce period (500ms)

**Expected Results:**
- File is automatically organized
- Status briefly shows "Organizing..."
- File moves to appropriate destination

### 7. Auto-Organize on File Modification
**Prerequisites:** Folder with AutoOrganize enabled

**Steps:**
1. Modify an existing file in the watched folder
2. Wait for debounce period

**Expected Results:**
- File is re-evaluated for organization
- Moves if it now matches different rules

### 8. Debouncing Multiple Changes
**Steps:**
1. Rapidly add multiple files (within 500ms)
2. Observe organization behavior

**Expected Results:**
- All files are processed in a single batch
- Only one organization operation occurs

## Edge Case Tests

### 9. Inaccessible Folder
**Steps:**
1. Add a watched folder
2. Delete/rename the folder in Windows Explorer
3. Trigger a refresh or observe watcher error

**Expected Results:**
- Status changes to "Error"
- Error message is displayed
- Retry button appears
- Other watchers continue functioning

### 10. Network Path Handling
**Steps:**
1. Add a folder on a network share (\\server\share\folder)
2. Verify warning is shown
3. Enable watching

**Expected Results:**
- Warning about network folder is displayed before adding
- Watcher works (may be less reliable)
- Handles network disconnection gracefully

### 11. Cloud Sync Folder
**Steps:**
1. Add a folder in OneDrive/Dropbox/Google Drive
2. Verify warning is shown
3. Test auto-organize behavior

**Expected Results:**
- Warning about cloud sync is displayed
- Suggestion to disable auto-organize
- Works but may have sync conflicts

### 12. Subfolder of Watched Folder
**Steps:**
1. Add folder A to watched folders
2. Try to add folder A/SubfolderB

**Expected Results:**
- Warning displayed about subfolder relationship
- User can choose to add anyway
- Both watchers can coexist

### 13. Parent of Watched Folder
**Steps:**
1. Add folder A/SubfolderB to watched folders
2. Try to add folder A

**Expected Results:**
- Warning displayed about parent relationship
- Lists affected child folders
- User can choose to add anyway

### 14. Duplicate Folder
**Steps:**
1. Add folder A to watched folders
2. Try to add folder A again

**Expected Results:**
- Error message: "This folder is already being watched"
- Folder is not added twice

### 15. Loop Prevention
**Steps:**
1. Create watched folder A with destination in folder B
2. Create watched folder B with destination in folder A
3. Add a file to folder A

**Expected Results:**
- File is organized once, not in an infinite loop
- Recently organized files are skipped for 5 seconds

### 16. Incomplete Download Files
**Steps:**
1. Start downloading a file to watched folder (creates .part/.crdownload file)
2. Wait for download to complete

**Expected Results:**
- Incomplete file (.part, .crdownload, etc.) is ignored
- Completed file triggers organization

## Profile-Related Tests

### 17. Profile Deletion
**Steps:**
1. Create watched folder using Profile A
2. Delete Profile A

**Expected Results:**
- Watcher is stopped
- Folder status changes to Error
- Error message indicates profile was deleted
- User can reconfigure with different profile

### 18. Profile Switch
**Steps:**
1. Configure folder with Profile A
2. Open Configure dialog
3. Switch to Profile B
4. Run organization

**Expected Results:**
- Profile B's rules/categories are used
- Different organization results than Profile A

## UI/UX Tests

### 19. Loading States
**Steps:**
1. Click Organize on a folder with many files
2. Observe button state during operation

**Expected Results:**
- Button shows spinner and "Organizing..." text
- Button is disabled during operation
- Restores to normal after completion

### 20. Status Badge Tooltips
**Steps:**
1. Hover over different status badges
2. Check tooltip content

**Expected Results:**
- Watching: "Actively monitoring for file changes"
- Idle: "Not currently watching for changes"
- Error: Shows specific error message
- Organizing: "Currently organizing files"

### 21. Empty State
**Steps:**
1. Remove all watched folders
2. Observe the UI

**Expected Results:**
- Empty state illustration is shown
- "No watched folders" message displayed
- "Add Folder" button is prominent

### 22. Info Banner Dismiss
**Steps:**
1. Click the X button on info banner
2. Navigate away and return

**Expected Results:**
- Banner is hidden
- Banner stays hidden for current session

## Undo Tests

### 23. Undo Organization
**Prerequisites:** Perform an organization operation

**Steps:**
1. Click More button on folder
2. Select "Undo Last Organize"
3. Confirm undo operation

**Expected Results:**
- Files are moved back to original locations
- Copies created by Copy action are deleted
- Success message shows restore count

### 24. Undo Not Available
**Steps:**
1. Check More menu on folder that hasn't been organized
2. Or check after undo was already performed

**Expected Results:**
- "Undo Last Organize" option is not shown
- Or is disabled

## Persistence Tests

### 25. App Restart
**Steps:**
1. Add several watched folders with different settings
2. Close and reopen the app

**Expected Results:**
- All folders are restored
- Settings are preserved
- Enabled watchers restart automatically

### 26. Configuration File
**Steps:**
1. Check %AppData%\FolderFresh\watchedFolders.json
2. Verify content matches UI state

**Expected Results:**
- JSON is valid and formatted
- Contains all folder configurations
- Sensitive data is handled appropriately

## Performance Tests

### 27. Large Folder
**Steps:**
1. Add a folder with 1000+ files
2. Click Preview
3. Click Organize

**Expected Results:**
- Preview completes in reasonable time
- Organization shows progress
- UI remains responsive

### 28. Many Watchers
**Steps:**
1. Add 10+ watched folders
2. Enable all of them
3. Observe system resource usage

**Expected Results:**
- All watchers function correctly
- Memory usage is reasonable
- CPU usage is minimal when idle

## Accessibility Tests

### 29. Keyboard Navigation
**Steps:**
1. Use Tab to navigate through folder cards
2. Use Enter/Space to activate buttons
3. Use Arrow keys in menus

**Expected Results:**
- All interactive elements are focusable
- Focus order is logical
- Actions work with keyboard

### 30. Screen Reader
**Steps:**
1. Enable screen reader (Narrator)
2. Navigate through watched folders UI

**Expected Results:**
- All text is readable
- Status badges are announced
- Buttons have descriptive labels
