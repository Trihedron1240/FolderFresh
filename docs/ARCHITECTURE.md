# Architecture Notes

## Current Shape

FolderFresh is a Windows 10/11 x64 desktop app built with C#, .NET 9, WinUI 3,
and Windows App SDK.

The app is intentionally Windows-first:

- `FolderFresh` contains the WinUI app, models, components, and services.
- `FolderFresh.Tests` links pure model and service files directly for fast,
  UI-independent xUnit coverage.
- `docs` contains the GitHub Pages site and public project docs.
- `starter-packs` contains importable `.folderfresh` profile packs.

## Core Product Flow

1. Users define profiles containing rules, categories, and settings.
2. Users organize a folder manually or configure watched folders.
3. Rule evaluation runs before category fallback when enabled.
4. Preview shows expected outcomes before manual organization.
5. Execution records undo state for move, copy, and rename operations.
6. Delete actions use the Recycle Bin by default.

## Rule Engine Scope

Supported condition attributes are name, extension, full name, kind, folder,
folder path, size, created date, modified date, and accessed date.

FolderFresh does not inspect document contents in the current release. Rules use
file names, metadata, paths, dates, sizes, and file types.

## Safety Defaults

New installs default to confirmation before organizing and do not include
subfolders unless the user opts in. Hidden and system files are ignored by
default, and delete actions move files to the Recycle Bin by default.
