# FolderFresh Rule Engine Documentation

This document explains how the FolderFresh rule engine works, including all available conditions, actions, and tokens you can use to organize your files.

---

## Table of Contents

1. [How Rules Work](#how-rules-work)
2. [Organization Modes](#organization-modes)
3. [Conditions](#conditions)
4. [Pattern Matching](#pattern-matching)
5. [Actions](#actions)
6. [Tokens](#tokens)
7. [Examples](#examples)

---

## How Rules Work

Rules are the core of FolderFresh's organization system. Each rule consists of:

1. **Conditions** - Criteria that files must match
2. **Match Type** - Whether ALL conditions must match, or just ANY one
3. **Actions** - What to do with files that match

When you organize a folder, FolderFresh checks each file against your rules in order. When a file matches a rule's conditions, the rule's actions are executed. By default, once a file matches a rule, no further rules are checked for that file (unless you use the "Continue" action).

### Rule Processing Order

1. Rules are checked from top to bottom in your rules list
2. The first matching rule wins (unless "Continue" action is used)
3. Files that don't match any rules can be organized by categories (depending on your organization mode)

---

## Organization Modes

FolderFresh offers three organization modes (configurable in Settings):

### Rules First, Then Categories (Recommended)

Files are first checked against your rules. Any files that don't match a rule are then organized using your category definitions. This gives you precise control over specific files while still auto-organizing everything else.

### Categories Only

Simple mode that ignores rules entirely. All files are organized solely based on their category (determined by file extension). Good for basic organization without complex rules.

### Rules Only

Advanced mode where only files matching a rule are organized. Files that don't match any rule are left untouched. Use this when you want complete manual control.

---

## Conditions

Conditions determine which files a rule applies to. Each condition has three parts:

1. **Attribute** - What property of the file to check
2. **Operator** - How to compare the value
3. **Value** - The value to compare against

### Attributes

| Attribute | Description | Example Values |
|-----------|-------------|----------------|
| **Name** | File name without extension | `report`, `photo_001` |
| **Extension** | File extension (with dot) | `.pdf`, `.jpg`, `.docx` |
| **Full Name** | Complete file name with extension | `report.pdf`, `photo.jpg` |
| **Kind** | General file type category | `Image`, `Document`, `Video` |
| **Folder** | Name of the containing folder | `Downloads`, `Screenshots` |
| **Folder Path** | Full path to the containing folder | `C:\Users\Name\Downloads` |
| **Size** | File size | `100MB`, `1GB`, `500KB` |
| **Date Created** | When the file was created | A date or relative time |
| **Date Modified** | When the file was last changed | A date or relative time |
| **Date Accessed** | When the file was last opened | A date or relative time |

### Operators

Different attributes support different operators:

#### Text Operators (Name, Extension, Full Name, Folder, Folder Path)

| Operator | Description | Example |
|----------|-------------|---------|
| **is** | Exact match | Extension is `.pdf` |
| **is not** | Does not match exactly | Extension is not `.tmp` |
| **contains** | Contains the text anywhere | Name contains `report` |
| **does not contain** | Does not contain the text | Name does not contain `backup` |
| **starts with** | Begins with the text | Name starts with `IMG_` |
| **ends with** | Ends with the text | Name ends with `_final` |
| **matches pattern** | Matches a wildcard pattern | Name matches pattern `*_v[0-9]*` |

#### Kind Operators

| Operator | Description |
|----------|-------------|
| **is** | File is of this kind |
| **is not** | File is not of this kind |

Available kinds: Document, Image, Audio, Video, Archive, PDF, Executable, Code, Text, Spreadsheet, Presentation, Other

#### Size Operators

| Operator | Description | Example |
|----------|-------------|---------|
| **is greater than** | File is larger than | Size is greater than 100MB |
| **is less than** | File is smaller than | Size is less than 1KB |

Size units: B (bytes), KB (kilobytes), MB (megabytes), GB (gigabytes)

#### Date Operators

| Operator | Description | Example |
|----------|-------------|---------|
| **is** | On this exact date | Date modified is 2024-01-15 |
| **is before** | Before this date | Date created is before 2023-01-01 |
| **is after** | After this date | Date modified is after 2024-06-01 |
| **is in the last** | Within the last X time units | Date modified is in the last 7 days |

Time units for "is in the last": days, weeks, months, years

### Match Type

When a rule has multiple conditions, you can choose:

- **All** - Every condition must be true (AND logic)
- **Any** - At least one condition must be true (OR logic)

---

## Pattern Matching

The "matches pattern" operator allows you to use wildcard patterns to match file names, extensions, folders, and paths. This is more flexible than simple "contains" or "starts with" comparisons.

### Wildcard Characters

| Character | Meaning | Example |
|-----------|---------|---------|
| `*` | Matches any number of characters (including zero) | `IMG_*` matches `IMG_001`, `IMG_vacation`, `IMG_` |
| `?` | Matches exactly one character | `file_?.txt` matches `file_1.txt`, `file_A.txt` but not `file_12.txt` |

### Pattern Examples

| Pattern | Matches | Does Not Match |
|---------|---------|----------------|
| `*report*` | `annual_report`, `report_2024`, `my_report_final` | `reprt` (missing 'o') |
| `IMG_????` | `IMG_0001`, `IMG_abcd` | `IMG_1`, `IMG_12345` |
| `backup_*_final` | `backup_jan_final`, `backup_2024_final` | `backup_final`, `backup_jan` |
| `*.bak` | `file.bak`, `document.bak` | `file.backup` |
| `test_v?.*` | `test_v1.txt`, `test_v2.pdf` | `test_v10.txt` |
| `*_[0-9]*` | `file_1`, `doc_9_final` | (see note below) |

### Important Notes

1. **Case insensitive** - Patterns ignore uppercase/lowercase differences. `*.PDF` matches `file.pdf`.

2. **Matches entire value** - The pattern must match the complete attribute value, not just part of it. Use `*` at the start/end to match partial strings.

3. **No regex support** - FolderFresh uses glob-style wildcards, not full regular expressions. Character classes like `[0-9]` or `[a-z]` are treated as literal text.

4. **Special characters** - Characters like `.`, `(`, `)`, `[`, `]` are matched literally (no need to escape them).

### Common Use Cases

**Match files with version numbers:**
- Pattern: `*_v?` or `*_v??`
- Matches: `document_v1`, `report_v12`

**Match dated files:**
- Pattern: `*_????-??-??*`
- Matches: `backup_2024-03-15`, `log_2024-01-01_errors`

**Match files with specific prefixes and suffixes:**
- Pattern: `IMG_*_edited`
- Matches: `IMG_vacation_edited`, `IMG_001_edited`

**Match numbered sequences:**
- Pattern: `photo_???`
- Matches: `photo_001`, `photo_999`
- Does not match: `photo_1`, `photo_1234`

**Match any file in a specific format:**
- Pattern: `*-*-*`
- Matches: `2024-03-15`, `john-doe-resume`

---

## Actions

Actions define what happens to files that match a rule. A rule can have multiple actions that execute in order.

| Action | Description | Value |
|--------|-------------|-------|
| **Move to folder** | Move the file to a specific folder | Folder path (absolute or relative) |
| **Copy to folder** | Copy the file to a folder (keeps original) | Folder path |
| **Move to category folder** | Move to the category's configured destination | (no value needed) |
| **Sort into subfolder** | Create/use a subfolder with a dynamic name | Subfolder pattern (supports tokens) |
| **Rename** | Rename the file using a pattern | New name pattern (supports tokens) |
| **Delete** | Move the file to the Recycle Bin | (no value needed) |
| **Ignore** | Skip this file completely | (no value needed) |
| **Continue** | Keep checking more rules after this one | (no value needed) |

### Action Notes

- **Relative paths** in Move/Copy actions are relative to the folder being organized
- **Absolute paths** (like `C:\Archives`) can be used to move files anywhere
- **Delete** sends files to the Recycle Bin (can be recovered) unless disabled in Settings
- **Ignore** prevents the file from being organized by categories too
- **Continue** allows multiple rules to apply to the same file

---

## Tokens

Tokens are placeholders that get replaced with actual values when actions run. Use them in Rename and Sort into subfolder actions to create dynamic names.

### File Name Tokens

| Token | Description | Example Output |
|-------|-------------|----------------|
| `{Name}` | File name without extension | `report` |
| `{Extension}` | File extension without dot | `pdf` |
| `{ext}` | Same as Extension | `pdf` |

### Category and Kind Tokens

| Token | Description | Example Output |
|-------|-------------|----------------|
| `{Category}` | User-defined category name | `Documents` |
| `{Kind}` | Built-in file type | `Image` |

### Modified Date Tokens

Based on when the file was last modified:

| Token | Description | Example Output |
|-------|-------------|----------------|
| `{Date}` | Full date (YYYY-MM-DD) | `2024-03-15` |
| `{Year}` | Year (4 digits) | `2024` |
| `{Month}` | Month (2 digits) | `03` |
| `{Day}` | Day (2 digits) | `15` |
| `{date:FORMAT}` | Custom date format | See below |

### Created Date Tokens

Based on when the file was created:

| Token | Description | Example Output |
|-------|-------------|----------------|
| `{CreatedYear}` | Year file was created | `2023` |
| `{CreatedMonth}` | Month file was created | `11` |
| `{CreatedDay}` | Day file was created | `28` |
| `{created:FORMAT}` | Custom created date format | See below |

### Today's Date Tokens

Based on when you run the organization:

| Token | Description | Example Output |
|-------|-------------|----------------|
| `{Today}` | Today's date (YYYY-MM-DD) | `2024-03-20` |
| `{today:FORMAT}` | Custom today format | See below |

### Custom Date Formats

The `{date:FORMAT}`, `{created:FORMAT}`, and `{today:FORMAT}` tokens let you specify any date format:

| Format Code | Meaning | Example |
|-------------|---------|---------|
| `yyyy` | 4-digit year | 2024 |
| `yy` | 2-digit year | 24 |
| `MM` | 2-digit month | 03 |
| `MMM` | Short month name | Mar |
| `MMMM` | Full month name | March |
| `dd` | 2-digit day | 15 |
| `ddd` | Short day name | Fri |
| `dddd` | Full day name | Friday |

**Examples:**
- `{date:yyyy-MM}` produces `2024-03`
- `{date:MMMM yyyy}` produces `March 2024`
- `{created:yyyy}` produces the year the file was created

### Token Case Sensitivity

Tokens are case-insensitive. `{Name}`, `{name}`, and `{NAME}` all work the same.

---

## Examples

### Example 1: Organize Screenshots by Month

**Goal:** Move screenshots to folders organized by year and month.

**Conditions:**
- Name starts with `Screenshot`
- Kind is Image

**Match Type:** All

**Action:**
- Sort into subfolder: `Screenshots/{date:yyyy}/{date:MM}`

**Result:** `Screenshot_2024-03-15.png` moves to `Screenshots/2024/03/`

---

### Example 2: Archive Old Documents

**Goal:** Move documents older than 1 year to an archive folder.

**Conditions:**
- Kind is Document
- Date modified is in the last 365 days (use "is not" or "is before")

Alternative approach using "is before":
- Kind is Document
- Date modified is before [one year ago date]

**Action:**
- Move to folder: `Archive/Documents`

---

### Example 3: Rename Downloaded Files

**Goal:** Add the download date to file names.

**Conditions:**
- Folder is `Downloads`

**Action:**
- Rename: `{Date}_{Name}.{Extension}`

**Result:** `report.pdf` becomes `2024-03-15_report.pdf`

---

### Example 4: Sort by Category

**Goal:** Organize files into folders matching your custom categories.

**Conditions:**
- (none - matches all files)

**Action:**
- Sort into subfolder: `{Category}`

**Result:** Files go into folders like `Documents/`, `Images/`, `Music/`, etc. based on your category definitions.

---

### Example 5: Clean Up Temporary Files

**Goal:** Delete temporary files that are more than 7 days old.

**Conditions:**
- Extension is `.tmp`
- Date modified is in the last 7 days (set to NOT match, or use "is before")

Alternative:
- Extension is `.tmp`
- Date accessed is before [7 days ago date]

**Action:**
- Delete

---

### Example 6: Ignore System Files

**Goal:** Prevent certain files from being organized.

**Conditions:**
- Name starts with `.`

OR

- Extension is `.ini`
- Extension is `.db`

**Match Type:** Any

**Action:**
- Ignore

---

### Example 7: Multi-Action Rule

**Goal:** Rename a file AND move it to a specific folder.

**Conditions:**
- Extension is `.pdf`
- Name contains `invoice`

**Actions (in order):**
1. Rename: `{Year}-{Month}_{Name}.{Extension}`
2. Move to folder: `Finances/Invoices`

**Result:** `invoice_acme.pdf` becomes `2024-03_invoice_acme.pdf` in the `Finances/Invoices` folder.

---

### Example 8: Exclude Folders from Organization

**Goal:** Don't organize files from specific folders.

**Conditions:**
- Folder is `Work Projects`

OR

- Folder Path contains `\DoNotOrganize\`

**Match Type:** Any

**Action:**
- Ignore

---

## Tips

1. **Order matters** - Put more specific rules before general ones
2. **Test first** - Use the preview (AFTER panel) before clicking "Organize Now"
3. **Use Ignore wisely** - Protect important files from accidental organization
4. **Combine with Categories** - Let rules handle special cases, categories handle the rest
5. **Relative paths** - Use relative paths in actions to keep rules portable
6. **Undo is available** - You can undo the last organization if something goes wrong

---

## Conflict Resolution

When a file would be moved to a location where a file with the same name already exists, FolderFresh will automatically rename the new file by adding a number (e.g., `report (1).pdf`).
