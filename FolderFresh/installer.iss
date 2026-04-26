; Inno Setup Script for FolderFresh
; Download Inno Setup from https://jrsoftware.org/isinfo.php

#define MyAppName "FolderFresh"
#define MyAppVersion "3.0.3"
#define MyAppPublisher "Trihedron1240"
#define MyAppExeName "FolderFresh.exe"
#define MyAppId "{{B8F2E4A1-5C3D-4E6F-9A8B-7C0D1E2F3A4B}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
UsePreviousTasks=no
; Output settings - installer will be created here
OutputDir=installer_output
OutputBaseFilename=FolderFresh-Setup-{#MyAppVersion}
; App icon for installer
SetupIconFile=bin\Release\net9.0-windows10.0.22621\win-x64\publish\icon.ico
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Windows version requirement
MinVersion=10.0.17763
; Modern installer look
WizardStyle=modern
; Privileges - install for current user by default
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Uninstall settings
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Include self-contained publish output so users do not need to install .NET separately.
Source: "bin\Release\net9.0-windows10.0.22621\win-x64\publish\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec
