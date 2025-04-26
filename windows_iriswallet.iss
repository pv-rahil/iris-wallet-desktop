[Setup]
AppName=iriswallet
AppVersion={#AppVersion}
DefaultDirName={commonpf}\iriswallet
DefaultGroupName=iriswallet
UninstallDisplayIcon={app}\iriswallet.exe
OutputDir=".\"
OutputBaseFilename=iriswallet
Compression=lzma
SolidCompression=yes
SetupIconFile=.\src\assets\icons\iriswallet.ico
WizardImageFile=.\src\assets\icons\iriswallet_icon_svg.bmp
WizardSmallImageFile=.\src\assets\icons\iriswallet_icon_svg.bmp

[Tasks]
Name: "launchAfterInstall"; Description: "Launch application after installation"; GroupDescription: "Additional Options:"; Flags: unchecked
Name: "createDesktopShortcut"; Description: "Create desktop shortcut"; GroupDescription: "Additional Options:"; Flags: unchecked

[Files]
Source: ".\dist\iriswallet\iriswallet.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\dist\iriswallet\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\iriswallet"; Filename: "{app}\iriswallet.exe"
Name: "{commondesktop}\iriswallet"; Filename: "{app}\iriswallet.exe"

[Run]
Filename: "{app}\iriswallet.exe"; Flags: postinstall shellexec; Tasks: launchAfterInstall

[Code]
function ShouldCreateDesktopShortcut: Boolean;
begin
  Result := WizardIsTaskSelected('createDesktopShortcut');
end;
