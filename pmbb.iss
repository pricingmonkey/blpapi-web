[Setup]
AppName=Pricing Monkey
AppVersion=1.0
AppPublisher=Pricing Monkey
DefaultDirName={pf}\Pricing Monkey
UninstallDisplayIcon={app}\uninstall.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.\dist
OutputBaseFilename=pricing-monkey-setup
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

[Run]
Filename: {tmp}\vc_redist.x64.exe; Parameters: "/q /passive /Q:a /c:""msiexec /q /i vcredist.msi"" "; StatusMsg: Installing VC++ 20015 Redistributables...

[Run]
Filename: "{app}\run-service.exe"; WorkingDir: "{app}"; Parameters: "--startup auto install"; Flags: runhidden
Filename: "{app}\run-service.exe"; WorkingDir: "{app}"; Parameters: "restart"; Flags: runhidden
