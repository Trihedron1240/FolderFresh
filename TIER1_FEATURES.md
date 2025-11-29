# FolderFresh Tier-1 Hazel-Style Automation Features

This document describes the new Tier-1 automation actions and conditions added to FolderFresh, inspired by Hazel's powerful automation capabilities.

## New Actions

### 1. Token Rename Action

Rename files using token expansion for dynamic naming based on file metadata.

**Syntax:**
```python
TokenRenameAction("<date_modified>_<name>_backup<extension>")
```

**Available Tokens:**
- `<name>` - Filename without extension
- `<extension>` - File extension (with dot, e.g., `.pdf`)
- `<date_created>` - File creation date (YYYY-MM-DD)
- `<date_modified>` - File modification date (YYYY-MM-DD)
- `<date_created_year>`, `<date_created_month>`, `<date_created_day>` - Parts of creation date
- `<date_modified_year>`, `<date_modified_month>`, `<date_modified_day>` - Parts of modification date
- `<year>`, `<month>`, `<day>` - Current date components
- `<hour>`, `<minute>` - Current time components

**Examples:**
```
Input: "report.pdf"
Pattern: "<date_modified>_<name><extension>"
Output: "2025-11-29_report.pdf"

Input: "photo.jpg"
Pattern: "<year>/<month>/<day>_<name><extension>"
Output: "2025/11/29_photo.jpg"

Input: "document.txt"
Pattern: "[<name>]_<hour>h<minute>m<extension>"
Output: "[document]_14h30m.txt"
```

**Features:**
- Idempotent: Skips if filename already matches the pattern
- Collision avoidance: Creates numbered copies if destination exists
- Safe mode: Works in safe_mode without side effects
- Dry run: Preview the new filename without changes
- Full undo support

---

### 2. Run Command Action

Execute scripts or commands on matched files.

**Syntax:**
```python
RunCommandAction("powershell -command Get-FileHash {path}")
RunCommandAction("python script.py {name}")
RunCommandAction("cmd /c del {path}")
```

**Placeholders:**
- `{path}` - Full file path
- `{name}` - Filename

**Features:**
- Supports PowerShell, CMD, batch files, Python, executables
- Captures stdout/stderr for logging
- Timeout protection (30 seconds)
- Safe mode: Preview only, no execution
- Dry run: Show command without execution
- Full command with arguments supported

**Examples:**
```
# Encrypt file with GPG
RunCommandAction("gpg --encrypt {path}")

# Copy to remote server
RunCommandAction("xcopy {path} \\\\server\\share")

# Generate thumbnail
RunCommandAction("ffmpeg -i {path} -scale 100x100 thumb_{name}")
```

---

### 3. Archive Action (ZIP)

Compress files to ZIP archives.

**Syntax:**
```python
ArchiveAction("C:/Archives")
ArchiveAction("D:/Backups/<year>/<month>")  # With tokens
```

**Features:**
- Creates ZIP files with single file per archive
- Supports token expansion in destination path
- Collision avoidance: Creates numbered archives if needed
- Safe mode: No actual archiving
- Dry run: Preview archive path
- Undo support (stores archive location)

**Examples:**
```
Input: "document.pdf"
Destination: "D:/Archives"
Output: "D:/Archives/document.zip"

Input: "report.xlsx"
Destination: "D:/Backup/<year>/<month>"
Output: "D:/Backup/2025/11/report.zip"
```

---

### 4. Extract Action

Unzip or extract archive files to a destination.

**Syntax:**
```python
ExtractAction("C:/Extracted")
ExtractAction("D:/Restore/<date_modified>")  # With tokens
```

**Supported Formats:**
- `.zip` (native Python support)
- `.rar`, `.7z` (requires external tools or fallback)

**Features:**
- Token expansion in destination path
- Creates nested folders as needed
- Safe mode: No extraction
- Dry run: Preview extraction path
- Extraction to temporary location for undo

**Examples:**
```
Input: "archive.zip"
Destination: "C:/Extracted"
Output: "C:/Extracted/[archive contents]"

Input: "backup.zip"
Destination: "D:/Restore/<date_modified>"
Output: "D:/Restore/2025-11-29/[archive contents]"
```

---

### 5. Create Folder Action

Create folders with token expansion for dynamic folder structures.

**Syntax:**
```python
CreateFolderAction("D:/Documents/<name>")
CreateFolderAction("D:/Photos/<year>/<month>/<day>")  # Date-based structure
```

**Features:**
- Full token support (same as TokenRenameAction)
- Creates nested folders automatically
- Idempotent: Skips if folder already exists
- Safe mode: No folder creation
- Dry run: Preview folder path

**Examples:**
```
Input: "profile.jpg" (created 2025-11-29)
Pattern: "D:/Photos/<year>/<month>"
Output: "D:/Photos/2025/11/" (created)

Input: "project.docx"
Pattern: "D:/Work/<name>"
Output: "D:/Work/project/" (created)
```

---

## New Conditions

### 1. Content Contains Condition

Match files based on their content (text or binary).

**Syntax:**
```python
ContentContainsCondition("ERROR", max_bytes=256000)
```

**Supported File Types:**
- Plain text (`.txt`, `.log`, `.py`, `.js`, `.md`, etc.)
- PDF (if pdfplumber available)
- DOCX (if python-docx available)
- XLSX (if openpyxl available)
- Binary search fallback for other formats

**Features:**
- Case-insensitive matching
- Reads first N KB (default 256 KB, configurable)
- Efficient binary search for large files
- Safe for system files (no modification)

**Examples:**
```python
# Match log files with errors
ContentContainsCondition("ERROR")

# Match documents with specific keywords
ContentContainsCondition("CONFIDENTIAL")

# Search with custom byte limit (1 MB)
ContentContainsCondition("password", max_bytes=1048576)
```

---

### 2. Date Pattern Condition

Match files by their creation or modification date using wildcard patterns.

**Syntax:**
```python
DatePatternCondition("modified", "2025-*")           # All of 2025
DatePatternCondition("created", "2025-11-*")         # November 2025
DatePatternCondition("modified", "*-12-25")          # All Christmas files
DatePatternCondition("created", "2025-01-15")        # Exact date
```

**Date Types:**
- `"created"` - File creation date
- `"modified"` - Last modification date

**Pattern Matching:**
Uses wildcard patterns (fnmatch):
- `*` - Match any characters
- `?` - Match single character
- `[abc]` - Match any of a, b, c

**Examples:**
```python
# Match files created in 2025
DatePatternCondition("created", "2025-*")

# Match files modified in Q4
DatePatternCondition("modified", "2025-10-*")
DatePatternCondition("modified", "2025-11-*")
DatePatternCondition("modified", "2025-12-*")

# Match files from specific day of month
DatePatternCondition("created", "*-*-15")  # 15th of any month
```

---

## Integration with Existing Features

All Tier-1 actions and conditions integrate seamlessly with FolderFresh's existing systems:

### Safe Mode
- All actions respect the `safe_mode` config
- In safe mode, file operations are previewed but not executed
- Archive/Extract operations skip execution
- Commands are not run

### Dry Run
- All actions can run in dry_run mode
- Returns descriptive preview of what would happen
- No filesystem changes
- Useful for preview before actual execution

### Undo Support
- All actions store metadata for undo operations
- Archive action stores zip file location
- Extract action stores extraction destination
- Token rename stores old and new names
- Undo manager can reverse all operations

### Idempotency
- Token rename skips if pattern matches current name
- Create folder skips if folder exists
- All operations check before executing
- Safe for multiple runs on same files

### Preview Integration
- All actions work with FolderFresh's preview system
- Preview shows what would happen without changes
- Matches dry_run behavior for consistency

### Watcher Integration
- Actions trigger on file creation/modification
- Tokens use file timestamps for dynamic naming
- Collision avoidance prevents duplicates
- Full undo support for watcher-triggered actions

---

## Usage Examples

### Organize photos by date
```python
rule = Rule(
    name="Organize Photos",
    conditions=[ExtensionIsCondition(".jpg")],
    actions=[
        CreateFolderAction("D:/Photos/<year>/<month>/<day>"),
        MoveAction("D:/Photos/<year>/<month>/<day>")
    ]
)
```

### Archive old documents
```python
rule = Rule(
    name="Archive Old Documents",
    conditions=[
        ExtensionIsCondition(".pdf"),
        FileAgeGreaterThanCondition(365*24*60*60)  # Older than 1 year
    ],
    actions=[
        ArchiveAction("D:/Archive/<year>"),
        DeleteFileAction()  # After archiving
    ]
)
```

### Process files by content
```python
rule = Rule(
    name="Process Error Logs",
    conditions=[
        ExtensionIsCondition(".log"),
        ContentContainsCondition("ERROR")
    ],
    actions=[
        TokenRenameAction("<date_modified>_ERROR_<name><extension>"),
        MoveAction("D:/Errors/<month>")
    ]
)
```

### Extract and organize archives
```python
rule = Rule(
    name="Extract and Organize",
    conditions=[ExtensionIsCondition(".zip")],
    actions=[
        CreateFolderAction("D:/Extracted/<name>"),
        ExtractAction("D:/Extracted/<name>"),
        DeleteFileAction()  # Remove original zip
    ]
)
```

### Execute commands on matched files
```python
rule = Rule(
    name="Virus Scan",
    conditions=[ExtensionIsCondition(".exe")],
    actions=[
        RunCommandAction("C:/Program Files/ClamAV/clamscan.exe {path}")
    ]
)
```

---

## Testing

All Tier-1 features have comprehensive test coverage:

- **27 new unit tests** covering all actions and conditions
- **Idempotency tests** ensuring safe repeated execution
- **Safe mode tests** verifying preview behavior
- **Dry run tests** confirming no filesystem changes
- **Collision avoidance tests** ensuring unique naming
- **Integration tests** with RuleExecutor and preview system

Run tests with:
```bash
pytest tests/test_tier1_actions.py -v
```

---

## Performance Considerations

### Content Matching
- Searches first 256 KB by default (configurable)
- Binary search for unsupported formats
- Cached for repeated evaluations

### Token Expansion
- Computed only when needed
- File timestamps cached per file
- O(1) token replacement

### Archive Operations
- ZIP uses Python standard library (fast)
- RAR/7z require external tools
- Large files processed efficiently

---

## Future Enhancements

Potential future additions to Tier-1 features:

- **CloudFlare/FTP Upload Action** - Upload processed files
- **Image Metadata Condition** - Match by EXIF data
- **Compression Level Options** - Control ZIP compression
- **Batch Operations** - Process multiple files atomically
- **Custom Script Conditions** - Run Python/shell for matching
- **Email Notification Action** - Alert on rule execution

---

## Compatibility

- Windows 10+ (tested)
- Python 3.10+
- FolderFresh 1.5.0+
- Safe for coexistence with existing rules
- Backward compatible (old rules still work)

---

## Support

For issues or feature requests, please file an issue with:
1. FolderFresh version
2. Action/condition used
3. Steps to reproduce
4. Expected vs actual behavior
