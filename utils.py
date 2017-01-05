import sys, imp

class BrokenSessionException(Exception):
    pass

def main_is_frozen():
    return (hasattr(sys, "frozen") or # new py2exe
        hasattr(sys, "importers") # old py2exe
        or imp.is_frozen("__main__")) # tools/freeze

def get_main_dir():
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.realpath(__file__))

def handleBrokenSession(e):
    if isinstance(e, BrokenSessionException):
        if not app.sessionForRequests is None:
            app.sessionForRequests.stop()
            app.sessionForRequests = None
        if not app.sessionForSubscriptions is None:
            app.sessionForSubscriptions.stop()
            app.sessionForSubscriptions = None

