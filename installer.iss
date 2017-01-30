[Setup]
AppName=Web API for Bloomberg Market Data
AppVersion=2.3-systray
AppPublisher=Pricing Monkey Ltd.
DefaultDirName={pf}\Pricing Monkey
DefaultGroupName=Pricing Monkey
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

[Files]
Source: "build/*.*"; DestDir: "{app}"; Flags: recursesubdirs

[Files]
Source: "ext/vc_redist.x64.exe"; DestDir: {tmp}; Flags: deleteafterinstall

[Icons]
Name: "{userstartup}\Web API for Bloomberg Market Data"; Filename: "{app}\run-systray.exe"; IconFilename: "{app}\pricingmonkey.ico"; Comment: "Web API for Bloomberg Market Data"
Name: "{group}\Web API for Bloomberg Market Data"; Filename: "{app}\run-systray.exe"; IconFilename: "{app}\pricingmonkey.ico"; Comment: "Web API for Bloomberg Market Data"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"

[Run]
Filename: {tmp}\vc_redist.x64.exe; Parameters: "/install /quiet /norestart"; StatusMsg: Installing VC++ 20015 Redistributables...
Filename: "sc"; Parameters: "stop BBApi"; Flags: shellexec runhidden
Filename: "sc"; Parameters: "delete BBApi"; Flags: shellexec runhidden
Filename: "sc"; Parameters: "delete ""Pricing Monkey Bloomberg Bridge"""; Flags: shellexec runhidden; StatusMsg: Finishing installation. Please wait, this might take few minutes..
Filename: "{app}\run-systray.exe"; Flags: shellexec runhidden runminimized; StatusMsg: Finishing installation. Please wait, this might take few minutes..

[UninstallRun]
Filename: "sc"; Parameters: "stop BBApi"; Flags: shellexec runhidden
Filename: "sc"; Parameters: "delete BBApi"; Flags: shellexec runhidden
