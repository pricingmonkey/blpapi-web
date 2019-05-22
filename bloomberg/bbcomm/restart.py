import datetime
import os
import sys
import traceback

from .start import startBbcomm

global BBCOMM_LAST_RESTARTED_AT
BBCOMM_LAST_RESTARTED_AT = None


def restartBbcomm():
    if not sys.platform == "win32":
        return

    global BBCOMM_LAST_RESTARTED_AT
    # debounce restarting for a few seconds, to allow bbcomm to fully initialise
    if BBCOMM_LAST_RESTARTED_AT and (datetime.datetime.now() - BBCOMM_LAST_RESTARTED_AT).total_seconds() < 10:
        return
    BBCOMM_LAST_RESTARTED_AT = datetime.datetime.now()
    try:
        os.system("taskkill /im bbcomm.exe /f")
        startBbcomm()
    except Exception:
        traceback.print_exc()
