import py2exe
import os

old_determine_dll_type = py2exe.dllfinder.DllFinder.determine_dll_type
pack = ("msvcp140.dll", "vcruntime140.dll")


def determine_dll_type(self, imagename):
    if os.path.basename(imagename).lower() in pack:
        return "EXT"
    return old_determine_dll_type(self, imagename)


py2exe.dllfinder.DllFinder.determine_dll_type = determine_dll_type

import setup
