# FolderFresh — Desktop and Folder Cleaner for Windows

Website: https://trihedron1240.github.io/FolderFresh/  
Support (optional): https://trihedron.itch.io/folderfresh-1-click-desktop-folder-cleaner-windows

FolderFresh is a lightweight utility that organises messy folders by sorting files into simple, predictable categories.  
It is designed for Windows users who want a quick, safe way to clean their Desktop, Downloads, or project folders without risk.  
Nothing is deleted, and all actions can be undone.

This tool is intended for students, general Windows users, and anyone who prefers a clean, organised workspace.

---

## Features

- Sorts files into category folders such as Documents, Images, Videos, Audio, Archives, Code, and Other.
- Preview mode shows exactly what will be moved before anything happens.
- Undo restores every moved file back to its original location.
- Safe Mode copies files instead of moving them.
- Works on any folder (Desktop, Downloads, project folders, external drives, etc.).
- Progress bar and status messages to prevent the interface from freezing.
- Smart Sorting for recognising screenshots, assignments, invoices, photos, and other common patterns.
- Auto-tidy mode automatically organises new files as they appear.
- File age filter to only move older files.
- Ignore list for file types you do not want to touch.
- Duplicate finder with quick hashing.
- “Clean Desktop” one-click shortcut.

---

## Example Output Structure


Desktop
├─ Documents

├─ Images

├─ Videos

├─ Audio

├─ Archives

└─ Other


---

## Screenshots

**Before:**  
![Before](screenshots/Before.png)

**Preview:**  
![Preview](screenshots/Preview.png)

**After:**  
![Finished](screenshots/After.png)

---

## Requirements

- Windows  
- Python 3.10+  
- pip  

---

## Build script
make sure to update version number in the .iss file

```powershell
Write-Host "Building FolderFresh..."


Write-Host "Cleaning previous build folders..."
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist")  { Remove-Item "dist"  -Recurse -Force }

Write-Host "Checking PyInstaller installation..."
pip show pyinstaller > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not found. Installing..."
    python -m pip install pyinstaller
}

Write-Host "Building FolderFresh.exe..."
python -m PyInstaller --onefile --windowed --name FolderFresh main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller build failed."
    exit 1
}

Write-Host "Executable created: dist/FolderFresh.exe"

$issPath = "installer/FolderFresh.iss"
Write-Host "Reading version from $issPath..."

$versionLine = Get-Content $issPath | Select-String '#define MyAppVersion'
$version = ($versionLine -split '"')[1]

Write-Host "Version detected: $version"

Write-Host "Building installer..."

$ISCC = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (!(Test-Path $ISCC)) {
    $ISCC = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
}

if (!(Test-Path $ISCC)) {
    Write-Host "Error: Inno Setup Compiler (ISCC.exe) was not found."
    exit 1
}

& "$ISCC" "installer/FolderFresh.iss"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Installer build failed."
    exit 1
}

Write-Host "Build complete. Installer located in Output/ folder."

```

## **Safety Notes**

Files are never deleted.

Undo restores all moved files.

Safe Mode can duplicate files instead of moving them.

OneDrive users may receive cloud messages when files move out of synced folders; files remain safely stored locally.

## **Build Status / Contributions**

Pull requests, issues, and suggestions are welcome.
This is an open project intended to help everyday users keep their machines organised.

## **AI Assistance Disclosure**

Some parts of the code were developed with the assistance of AI tools, then reviewed and tested manually.
No third-party proprietary code is included.
