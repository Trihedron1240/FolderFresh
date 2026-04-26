# Security Policy

FolderFresh watches folders and can move, copy, rename, and delete files. Security
and recovery issues are treated as product-critical.

## Supported Versions

I prepare security fixes for the latest stable `3.x` release line.

## Reporting A Vulnerability

Please do not open a public issue for vulnerabilities that could expose user data,
cause file loss, bypass safety checks, or abuse watched-folder automation.

Report privately through GitHub Security Advisories when available, or contact me
through my GitHub profile, `Trihedron1240`.

Helpful reports include:

- FolderFresh version and installation source.
- Windows version and architecture.
- Exact rule, category, profile, or watched-folder setup involved.
- Whether Preview, Undo, Recycle Bin, or snapshots were enabled.
- Steps to reproduce using temporary test folders where possible.

## Safety Principles

- FolderFresh should make file changes previewable whenever possible.
- Delete actions should use the Recycle Bin by default.
- New installs should ask for confirmation before organizing files.
- Release artifacts should include checksums.
