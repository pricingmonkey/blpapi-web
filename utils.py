import imp
import os
import sys


def main_is_frozen():
    return (hasattr(sys, "frozen") or     # new py2exe
            hasattr(sys, "importers") or  # old py2exe
            imp.is_frozen("__main__"))    # tools/freeze


def get_main_dir():
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.realpath(__file__))


def handle_broken_session(app):
    app.session_pool_for_requests.stop()
    app.session_for_subscriptions.stop()
    app.all_subscriptions = {}
