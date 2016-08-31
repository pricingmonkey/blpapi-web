from distutils.core import setup
import py2exe
import os

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)

        self.version = "1.0.0"
        self.company_name = "Pricing Monkey"
        self.copyright = "Pricing Monkey"
        self.name = "Bloomberg Bridge"

old_determine_dll_type = py2exe.dllfinder.DllFinder.determine_dll_type
pack = ("msvcp140.dll", "vcruntime140.dll")
def determine_dll_type(self, imagename):
    if os.path.basename(imagename).lower() in pack:
        return "EXT"
    return old_determine_dll_type(self, imagename)
py2exe.dllfinder.DllFinder.determine_dll_type = determine_dll_type

standalone_server = Target(
    script = 'server.py',
    dest_base = 'pmbb'
)

service = Target(
    modules = ['windows-service'],
    cmdline_style='pywin32',
    dest_base = 'pmbb-service'
)

setup(
    options = {
        "py2exe": {
            "compressed": True, 
            "bundle_files": 3, 
            "includes": ["_internals"],
            "packages": ["encodings"]
        }},
        console=[standalone_server],
    service=[service]
)
