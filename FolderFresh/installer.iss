; Inno Setup Script for FolderFresh
; Download Inno Setup from https://jrsoftware.org/isinfo.php

#define MyAppName "FolderFresh"
#define MyAppVersion "3.0.1-beta"
#define MyAppPublisher "FolderFresh"
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
; Output settings - installer will be created here
OutputDir=installer_output
OutputBaseFilename=FolderFresh-Setup-{#MyAppVersion}
; App icon for installer
SetupIconFile=bin\Release\net9.0-windows10.0.22621\icon.ico
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

[Code]
// Uninstall old Python FolderFresh before installing new version
procedure RemoveOldFolderFresh;
var
  UninstallPath: String;
  ResultCode: Integer;
begin
  // Method 1: Try to run uninstaller from registry (if old version had an installer)
  // Check HKLM (all users)
  if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\FolderFresh_is1',
     'UninstallString', UninstallPath) then
  begin
    Log('Found old FolderFresh (HKLM), running uninstaller: ' + UninstallPath);
    Exec('cmd.exe', '/c ' + UninstallPath + ' /SILENT', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;

  // Check HKCU (current user)
  if RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\FolderFresh_is1',
     'UninstallString', UninstallPath) then
  begin
    Log('Found old FolderFresh (HKCU), running uninstaller: ' + UninstallPath);
    Exec('cmd.exe', '/c ' + UninstallPath + ' /SILENT', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;

  // Method 2: Delete known old installation folders (adjust paths as needed)
  if DirExists(ExpandConstant('{localappdata}\FolderFresh')) then
  begin
    Log('Removing old FolderFresh from LocalAppData');
    DelTree(ExpandConstant('{localappdata}\FolderFresh'), True, True, True);
  end;

  if DirExists(ExpandConstant('{autopf}\FolderFresh')) then
  begin
    Log('Removing old FolderFresh from Program Files');
    DelTree(ExpandConstant('{autopf}\FolderFresh'), True, True, True);
  end;

  // Method 3: Remove old Start Menu shortcuts (use userprograms instead of group)
  if DirExists(ExpandConstant('{userprograms}\FolderFresh')) then
  begin
    Log('Removing old Start Menu folder');
    DelTree(ExpandConstant('{userprograms}\FolderFresh'), True, True, True);
  end;

  // Also check common programs (all users)
  if DirExists(ExpandConstant('{commonprograms}\FolderFresh')) then
  begin
    Log('Removing old Start Menu folder (common)');
    DelTree(ExpandConstant('{commonprograms}\FolderFresh'), True, True, True);
  end;

  // Remove old desktop shortcut if it exists
  if FileExists(ExpandConstant('{autodesktop}\FolderFresh.lnk')) then
  begin
    DeleteFile(ExpandConstant('{autodesktop}\FolderFresh.lnk'));
  end;
end;

function IsDotNet9Installed: Boolean;
var
  Output: AnsiString;
  ResultCode: Integer;
begin
  Result := False;
  // Check if dotnet command exists and has .NET 9 runtime
  if Exec('cmd.exe', '/c dotnet --list-runtimes | findstr "Microsoft.WindowsDesktop.App 9."', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    Result := (ResultCode = 0);
  end;
end;

function InitializeSetup: Boolean;
var
  ErrorCode: Integer;
begin
  Result := True;
  RemoveOldFolderFresh;

  // Check for .NET 9 Desktop Runtime
  if not IsDotNet9Installed then
  begin
    if MsgBox('FolderFresh requires .NET 9 Desktop Runtime which is not installed.' + #13#10 + #13#10 +
              'Would you like to download it now?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      ShellExec('open', 'https://dotnet.microsoft.com/en-us/download/dotnet/9.0', '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
    end;
    Result := False;
  end;
end;

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Include all files from the build folder (framework-dependent)
Source: "bin\Release\net9.0-windows10.0.22621\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent shellexec
