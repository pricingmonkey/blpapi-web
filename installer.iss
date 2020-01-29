#define AppName "Pricing Monkey Web API for Bloomberg Market Data"
#define ShortAppName "Pricing Monkey"
#define AppVersion "3.0.1"
[Setup]
; AppId can never change, as it unique identifies the installer!
AppId=Web API for Bloomberg Market Data
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Pricing Monkey Ltd
AppPublisherURL=https://pricingmonkey.com
LicenseFile=.\FULL_LICENSE
DefaultDirName={autopf}\{#ShortAppName}
DefaultGroupName={#ShortAppName}
UninstallDisplayIcon={app}\uninstall.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.\dist
OutputBaseFilename=bloomberg-web-api-setup
; "ArchitecturesAllowed=x64" specifies that Setup cannot run on
; anything but x64.
ArchitecturesAllowed=x64
; "ArchitecturesInstallIn64BitMode=x64" requests that the install be
; done in "64-bit mode" on x64, meaning it should use the native
; 64-bit Program Files directory and the 64-bit view of the registry.
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequiredOverridesAllowed=commandline dialog
WizardStyle=modern

[Messages]
SetupWindowTitle = Setup - {#ShortAppName} v{#AppVersion}

[Files]
Source: "build/*.*"; DestDir: "{app}"; Flags: recursesubdirs

[Files]
Source: "ext/vc_redist_2010.x64.exe"; DestDir: {tmp}; Flags: deleteafterinstall
Source: "ext/vc_redist_2015.x64.exe"; DestDir: {tmp}; Flags: deleteafterinstall

[Run]
Filename: {tmp}\vc_redist_2010.x64.exe; Parameters: "/q /norestart"; StatusMsg: Installing Microsoft Visual C++ 2010 Redistributables...; Check: IsAdmin;
Filename: {tmp}\vc_redist_2015.x64.exe; Parameters: "/install /quiet /norestart"; StatusMsg: Installing Microsoft Visual C++ 2015 Redistributables...; Check: IsAdmin;

[Code]
function CreateBatch(): boolean;
var
  fileName : string;
  lines : TArrayOfString;
begin
  Result := true;
  fileName := ExpandConstant('{app}\Restart Pricing Monkey.bat');
  SetArrayLength(lines, 2);
  lines[0] := 'taskkill /im bbapi.exe /f';
  lines[1] := ExpandConstant('bbapi.exe --no-ui');
  Result := SaveStringsToFile(filename, lines, true);
  exit;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if  CurStep=ssPostInstall then
    begin
         CreateBatch();
    end
end;

[Icons]
Name: "{autostartmenu}\{#ShortAppName}\Restart {#ShortAppName}"; Filename: "{app}\Restart Pricing Monkey.bat"; WorkingDir: "{app}"
Name: "{autostartmenu}\{#ShortAppName}\Uninstall {#ShortAppName}"; Filename: "{app}\unins000.exe"; WorkingDir: "{app}"


[Run]
Filename: "sc"; Parameters: "stop BBApi"; Flags: shellexec runhidden waituntilterminated; StatusMsg: Finishing installation. Please wait, this might take a few minutes...
Filename: "sc"; Parameters: "delete BBApi"; Flags: shellexec runhidden waituntilterminated; StatusMsg: Finishing installation. Please wait, this might take a few minutes...
Filename: "{app}\bbapi.exe"; WorkingDir: "{app}"; Flags: nowait runhidden runasoriginaluser; StatusMsg: Finishing installation. Please wait, this might take a few minutes...

[Registry]
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#ShortAppName}"; ValueData: """{app}\bbapi.exe"" --no-ui"; Flags: uninsdeletekey;

[UninstallDelete]
Type: files; Name: "{app}\Restart Pricing Monkey.bat";

[UninstallRun]
Filename: "taskkill"; Parameters: "/im bbapi.exe /f"; Flags: shellexec runhidden waituntilterminated
Filename: "timeout"; Parameters: "/t 2 /nobreak"; Flags: shellexec runhidden waituntilterminated
