import sys
import traceback

from .start import startBbcomm

def startBbcommIfNecessary():
    if not sys.platform == "win32":
        return

    try:
        bbcomm = next((proc for proc in psutil.process_iter() if proc.name() == "bbcomm.exe"), None)

        if not bbcomm:
            startBbcomm()
    except Exception:
        traceback.print_exc()
