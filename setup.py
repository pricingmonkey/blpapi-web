from distutils.core import setup
import py2exe

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)

        self.version = "2.3.0-systray"
        self.company_name = "Pricing Monkey Ltd"
        self.copyright = "Pricing Monkey Ltd"
        self.name = "Web API for Bloomberg Market Data"

standalone_server = Target(
    script = 'server.py',
    icon_resources = [(1, "pricingmonkey.ico")],
    dest_base = 'run'
)

systray = Target(
    script = 'systray.py',
    icon_resources = [(1, "pricingmonkey.ico")],
    dest_base = 'run-systray'
)

service = Target(
    modules = ['windows-service'],
    cmdline_style='pywin32',
    dest_base = 'service'
)

setup(
    data_files = [('./certifi', ['./certifi/cacert.pem']), ('./', ['./pricingmonkey.ico'])],
    options = {
        "py2exe": {
            "dist_dir": "./build",
            "compressed": True, 
            "bundle_files": 3, 
            "includes": ["_internals", "urllib", "engineio.async_eventlet", "engineio.async_threading"],
            "packages": ["blpapi", "encodings", "raven", "eventlet"]
        }},
        console=[standalone_server, systray],
        service=[service]
)
