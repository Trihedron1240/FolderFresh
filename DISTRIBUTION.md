# Distribution

FolderFresh is distributed from GitHub Releases first. Future distribution
channels should use the same release artifacts and checksums so users can verify
what they install.

## Install Options

### GitHub Releases

Download the latest installer from the
[FolderFresh Releases](https://github.com/Trihedron1240/FolderFresh/releases)
page.

Release artifacts use predictable names:

```text
FolderFresh-Setup-x.y.z.exe
FolderFresh-Setup-x.y.z.exe.sha256
FolderFresh-ReleaseNotes-x.y.z.md
```

The installer is built as a self-contained Windows x64 package. Users do not
need to install the .NET runtime separately.

### WinGet

WinGet distribution is planned after a release installer URL, SHA256 checksum,
and silent install/uninstall validation are available.

The intended package identity is:

```text
PackageIdentifier: Trihedron1240.FolderFresh
PackageName: FolderFresh
Publisher: Trihedron1240
License: GPL-3.0
InstallerType: inno
```

### Microsoft Store

Microsoft Store distribution is planned as later work. GitHub Releases remain
the primary public install source until Store packaging, identity, and update
behavior are ready.

## Checksums

Every release should include a SHA256 checksum next to the installer.

To verify a downloaded installer in PowerShell:

```powershell
Get-FileHash .\FolderFresh-Setup-x.y.z.exe -Algorithm SHA256
Get-Content .\FolderFresh-Setup-x.y.z.exe.sha256
```

The hash printed by `Get-FileHash` should match the hash in the `.sha256` file.

## Unsigned Binary Notice

FolderFresh release installers may be unsigned. Windows SmartScreen can warn on
unsigned or newly published installers even when the file is clean. This warning
does not prove the installer is unsafe, but users should only download
FolderFresh from the official GitHub repository and should verify the SHA256
checksum before installing.

## Silent Install And Uninstall

FolderFresh uses an Inno Setup installer. Release validation checks the silent
install and uninstall paths used by package managers:

```powershell
.\FolderFresh-Setup-x.y.z.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

Silent uninstall is handled by the `unins*.exe` file created in the install
directory:

```powershell
.\unins000.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

Uninstall removes the installed application files. FolderFresh user data in
`%APPDATA%\FolderFresh` is preserved unless the user removes it manually.
