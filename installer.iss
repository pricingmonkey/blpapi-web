#define AppName "Pricing Monkey Web API for Bloomberg Market Data"
#define ShortAppName "Pricing Monkey"
#define AppVersion "2.7.1"
[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Pricing Monkey Ltd
AppPublisherURL=https://pricingmonkey.com
LicenseFile=.\FULL_LICENSE
DefaultDirName={autopf}\{#ShortAppName}
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
Filename: {tmp}\vc_redist_2010.x64.exe; Parameters: "/q /norestart"; StatusMsg: Installing Microsoft Visual C++ 2010 Redistributables...
Filename: {tmp}\vc_redist_2015.x64.exe; Parameters: "/install /quiet /norestart"; StatusMsg: Installing Microsoft Visual C++ 2015 Redistributables...

[Run]
Filename: "{app}\bbapi.exe"; WorkingDir: "{app}"; Flags: nowait runhidden; StatusMsg: Finishing installation. Please wait, this might take a few minutes...
Filename: "sc"; Parameters: "stop BBApi"; Flags: shellexec runhidden; StatusMsg: Finishing installation. Please wait, this might take a few minutes...
Filename: "sc"; Parameters: "delete BBApi"; Flags: shellexec runhidden; StatusMsg: Finishing installation. Please wait, this might take a few minutes...
Filename: "sc"; Parameters: "delete ""Pricing Monkey Bloomberg Bridge"""; Flags: shellexec runhidden; StatusMsg: Finishing installation. Please wait, this might take a few minutes..

[Registry]
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#ShortAppName}"; ValueData: "'"{app}\bbapi.exe"' --no-ui";

[UninstallRun]
Filename: "taskkill"; Parameters: "/im bbapi.exe /f"; Flags: shellexec runhidden
