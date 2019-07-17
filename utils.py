import sys, imp, os

from bloomberg.session import BrokenSessionException
from bloomberg.bbcomm import restartBbcomm


def main_is_frozen():
    return (hasattr(sys, "frozen") or # new py2exe
        hasattr(sys, "importers") # old py2exe
        or imp.is_frozen("__main__")) # tools/freeze

def get_main_dir():
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.realpath(__file__))

def handleBrokenSession(app, e):
    if isinstance(e, BrokenSessionException):
        app.sessionPoolForRequests.stop()
        app.sessionForSubscriptions.stop()
        app.allSubscriptions = {}
        restartBbcomm()
