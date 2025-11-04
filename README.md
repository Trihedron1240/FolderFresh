# FolderFresh — Desktop and Folder Cleaner for Windows

FolderFresh is a small utility that automatically organises messy folders.  
It sorts files into simple categories such as Documents, Images, Videos, Audio, Archives, Code, and Other.  
Nothing is deleted, and the process can be undone.

This tool is designed to help students, general Windows users, and anyone with a cluttered Desktop or Downloads folder.

---

## Features
- Sorts files into clean category folders
- Preview mode shows exactly what will be moved before anything happens
- Undo button restores all files to their original locations
- Safe Mode copies files instead of moving them
- Works on any folder, not just Desktop
- Progress bar and status messages so the window never “freezes”
- Skips internal files of games or software to avoid breaking installations

---

## Example Result

After running FolderFresh on a messy Desktop or Downloads folder, the structure may look like:

Desktop
├─ Documents
├─ Images
├─ Videos
├─ Audio
├─ Archives
└─ Other

---

## Screenshots
Before:

![Before](screenshots/Before)

Preview:

![Preview](screenshots/Preview)

After:

![Finished](screenshots/After)

---

### Requirements
- Windows
- Python 3.10+
- pip


---

## Build the Executable (PyInstaller)

Open a PowerShell window in the project root:

```powershell
# (optional) clean previous builds
rmdir /s /q build dist

python -m pip install pyinstaller

python -m PyInstaller --onefile --windowed ^ src\FolderFresh_full_app.py

```
The executable will appear in dist/.

## **Build the Installer (Inno Setup)**

Install Inno Setup

Open installer/FolderFresh.iss

Update #define MyAppVersion when releasing a new version

Build → Compile

The installer will appear in the Output/ folder

## **Safety Notes**

Files are never deleted

Undo puts everything back where it was

Safe Mode can be used to create copies instead of moving originals

For OneDrive users: moving files out of Desktop/Documents may trigger cloud “file removed” messages. Files remain safely on the machine.

## **Build Status / Contributions**

Pull requests, issues, and suggestions are welcome.
This is a small, open project intended to help everyday users keep their machines organised.

## **AI Assistance Disclosure**

Some parts of the code were developed with the assistance of AI tools, then reviewed and tested manually.
No third-party proprietary code is included.
