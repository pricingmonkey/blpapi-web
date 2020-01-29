'''
 py2app/py2exe build script

 Usage (Mac OS X):
     python setup.py py2app

 Usage (Windows):
     python setup.py py2exe
 '''
import sys

if sys.platform == 'win32':
    import py2exe
    from distutils.core import setup

    class Target:
        def __init__(self, **kw):
            self.__dict__.update(kw)

            self.version = '3.0.1'
            self.company_name = 'Pricing Monkey Ltd'
            self.copyright = 'Pricing Monkey Ltd'
            self.name = 'Web API for Bloomberg Market Data'

    standalone_server = Target(
        script = 'server.py',
        dest_base = 'bbapi',
        description = 'Web API for Bloomberg Market Data',
        icon_resources = [(1, 'icon.ico')]
    )

    setup(
        data_files = [('.', ['./ext/blpapi3_64.dll'])],
        options = {
            'py2exe': {
                'dist_dir': './build',
                'compressed': True, 
                'bundle_files': 3, 
                'includes': ['_internals', 'urllib', 'engineio.async_eventlet', 'engineio.async_threading'],
                'packages': ['blpapi', 'encodings', 'eventlet']
            }},
            console=[standalone_server]
    )
elif sys.platform == 'darwin':
    from setuptools import setup

    APP = ['server.py']
    DATA_FILES = [('.', ['./ext/libblpapi3_64.so'])]
    OPTIONS = {
        'argv_emulation': False,
        'iconfile': 'icon.icns',
        'includes': ['_internals', 'urllib', 'engineio.async_drivers.threading', 'engineio.async_drivers.eventlet'],
        'packages': ['blpapi', 'encodings', 'eventlet', 'dns', 'jinja2']
    }

    setup(
        app=APP,
        name='BBAPI',
        data_files=DATA_FILES,
        options={'py2app': OPTIONS},
        setup_requires=['py2app'],
    )
else:
    raise ('platform unsupported: ' + sys.platform)
