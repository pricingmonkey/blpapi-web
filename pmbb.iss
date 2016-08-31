[Setup]
AppName=Pricing Monkey
AppVersion=1.0
AppPublisher=Pricing Monkey
DefaultDirName={pf}\Pricing Monkey
UninstallDisplayIcon={app}\uninstall.exe
Compression=lzma2
SolidCompression=yes
OutputDir=./dist
OutputBaseFilename=pricing-monkey-setup
; "ArchitecturesAllowed=x64" specifies that Setup cannot run on
; anything but x64.
ArchitecturesAllowed=x64
; "ArchitecturesInstallIn64BitMode=x64" requests that the install be
; done in "64-bit mode" on x64, meaning it should use the native
; 64-bit Program Files directory and the 64-bit view of the registry.
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist/blpapi3_64.dll"; DestDir: "{app}"; DestName: "blpapi3_64.dll"
Source: "dist/library.zip"; DestDir: "{app}"; DestName: "library.zip"
Source: "dist/perfmon.pyd"; DestDir: "{app}"; DestName: "perfmon.pyd"
Source: "dist/run-service.exe"; DestDir: "{app}"; DestName: "run-service.exe"
Source: "dist/run.exe"; DestDir: "{app}"; DestName: "run.exe"
Source: "dist/pyexpat.pyd"; DestDir: "{app}"; DestName: "pyexpat.pyd"
Source: "dist/python34.dll"; DestDir: "{app}"; DestName: "python34.dll"
Source: "dist/pywintypes34.dll"; DestDir: "{app}"; DestName: "pywintypes34.dll"
Source: "dist/select.pyd"; DestDir: "{app}"; DestName: "select.pyd"
Source: "dist/servicemanager.pyd"; DestDir: "{app}"; DestName: "servicemanager.pyd"
Source: "dist/unicodedata.pyd"; DestDir: "{app}"; DestName: "unicodedata.pyd"
Source: "dist/win32api.pyd"; DestDir: "{app}"; DestName: "win32api.pyd"
Source: "dist/win32event.pyd"; DestDir: "{app}"; DestName: "win32event.pyd"
Source: "dist/win32evtlog.pyd"; DestDir: "{app}"; DestName: "win32evtlog.pyd"
Source: "dist/win32service.pyd"; DestDir: "{app}"; DestName: "win32service.pyd"
Source: "dist/_bz2.pyd"; DestDir: "{app}"; DestName: "_bz2.pyd"
Source: "dist/_ctypes.pyd"; DestDir: "{app}"; DestName: "_ctypes.pyd"
Source: "dist/_hashlib.pyd"; DestDir: "{app}"; DestName: "_hashlib.pyd"
Source: "dist/_internals.pyd"; DestDir: "{app}"; DestName: "_internals.pyd"
Source: "dist/_lzma.pyd"; DestDir: "{app}"; DestName: "_lzma.pyd"
Source: "dist/_socket.pyd"; DestDir: "{app}"; DestName: "_socket.pyd"
Source: "dist/_ssl.pyd"; DestDir: "{app}"; DestName: "_ssl.pyd"
Source: "dist/_win32sysloader.pyd"; DestDir: "{app}"; DestName: "_win32sysloader.pyd"

[Files]
Source: "ext/vc_redist.x64.exe"; DestDir: {tmp}; Flags: deleteafterinstall

[Run]
Filename: {tmp}\vc_redist.x64.exe; Parameters: "/q /passive /Q:a /c:""msiexec /q /i vcredist.msi"" "; StatusMsg: Installing VC++ 20015 Redistributables...

[Run]
Filename: "{app}\run-service.exe"; WorkingDir: "{app}"; Parameters: "--startup auto install"; Flags: runhidden
Filename: "{app}\run-service.exe"; WorkingDir: "{app}"; Parameters: "start"; Flags: runhidden
