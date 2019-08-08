import json
from flask import Blueprint, current_app as app, request, Response

blueprint = Blueprint('dev', __name__)

def raise_(ex):
    raise ex

class BrokenSession:
    def __init__(self, ignore):
        pass

    def start(self):
        return False

    def stop(self):
        raise Exception("broken")

@blueprint.route('/requests/session/reset', methods = ['GET'])
def resetSessionForRequests():
    app.sessionPoolForRequests.reset()
    return Response("OK", status=200)

@blueprint.route('/subscriptions/session/reset', methods = ['GET'])
def resetSessionForSubscriptions():
    app.sessionForSubscriptions.reset()
    return Response("OK", status=200)

OriginalSession = [None]
@blueprint.route('/session/stop', methods = ['GET'])
def stopSessionForSubscriptions():
    OriginalSession[0] = blpapi.Session
    blpapi.Session = BrokenSession
    app.sessionPoolForRequests.reset()
    app.sessionForSubscriptions.reset()
    return Response("OK", status=200)

@blueprint.route('/session/start', methods = ['GET'])
def startSessionForRequests():
    if OriginalSession[0]:
        blpapi.Session = OriginalSession[0]
        app.sessionPoolForRequests.reset()
        app.sessionForSubscriptions.reset()
    return Response("OK", status=200)

def functionOneTimeBroken(original):
    hit = [False]
    def function(*args, **kwargs):
        if hit[0]: 
            return original(*args, **kwargs)
        else:
            hit[0] = True
            raise_(Exception("service is broken"))
    return function

@blueprint.route('/requests/sendRequest/break', methods = ['GET'])
def breakSendRequestForRequests():
    sessionPool = app.sessionPoolForRequests
    session = sessionPool.sessions[sessionPool.currentIndex]
    session.start()
    session.sessionImpl.sendRequest = functionOneTimeBroken(session.sessionImpl.sendRequest)

    return Response("OK", status=200)

@blueprint.route('/subscriptions/nextEvent/break', methods = ['GET'])
def breakNextEventForSubscriptions():
    app.sessionForSubscriptions.sessionImpl.nextEvent = functionOneTimeBroken(app.sessionForSubscriptions.sessionImpl.nextEvent)

    return Response("OK", status=200)

@blueprint.route('/requests/getService/break', methods = ['GET'])
def breakGetServiceForRequests():
    sessionPool = app.sessionPoolForRequests
    session = sessionPool.sessions[sessionPool.currentIndex]
    session.start()
    session.sessionImpl.getService = functionOneTimeBroken(session.sessionImpl.getService)

    return Response("OK", status=200)

@blueprint.route('/subscriptions/getService/break', methods = ['GET'])
def breakGetServiceForSubscriptions():
    app.sessionForSubscriptions.sessionImpl.getService = functionOneTimeBroken(app.sessionForSubscriptions.sessionImpl.getService)

    return Response("OK", status=200)
