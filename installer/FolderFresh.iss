#define MyAppName      "FolderFresh"
#define MyAppVersion   "1.1.3"
#define MyAppPublisher "Tristan Jay Neale"
#define MyAppURL       ""
#define MyAppExeName   "FolderFresh.exe"

[Setup]
AppId={{70EC37A1-1275-482B-985A-8805CAA7CAB9}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=Output
OutputBaseFilename=Setup {#MyAppName} v{#MyAppVersion}
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog


[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked
Name: "runonstartup"; Description: "Run {#MyAppName} at Windows &startup"; GroupDescription: "Startup options:"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion


[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\folderfresh.ico"; Check: FileExists(ExpandConstant('{app}\folderfresh.ico'))
; Fallback Start Menu shortcut without icon
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Check: not FileExists(ExpandConstant('{app}\folderfresh.ico'))
; Desktop shortcut (optional task) with/without icon
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\folderfresh.ico"; Check: FileExists(ExpandConstant('{app}\folderfresh.ico'))
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Check: not FileExists(ExpandConstant('{app}\folderfresh.ico'))
; Uninstall shortcut
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; \
    ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: runonstartup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.json"


