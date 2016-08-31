from distutils.core import setup
import py2exe

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)

        self.version = "1.0.0"
        self.company_name = "Pricing Monkey"
        self.copyright = "Pricing Monkey"
        self.name = "Bloomberg Bridge"

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