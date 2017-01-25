import json
from flask import Blueprint, current_app as app, request, Response

blueprint = Blueprint('dev', __name__)

def raise_(ex):
    raise ex

@blueprint.route('/requests/session/reset', methods = ['GET'])
def resetSessionForRequests():
    app.sessionForRequests = None
    return Response("OK", status=200)

@blueprint.route('/subscriptions/session/reset', methods = ['GET'])
def resetSessionForSubscriptions():
    app.sessionForSubscriptions = None
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
    app.sessionForRequests.sendRequest = functionOneTimeBroken(app.sessionForRequests.sendRequest)

    return Response("OK", status=200)

@blueprint.route('/subscriptions/nextEvent/break', methods = ['GET'])
def breakNextEventForSubscriptions():
    app.sessionForSubscriptions.nextEvent = functionOneTimeBroken(app.sessionForSubscriptions.nextEvent)

    return Response("OK", status=200)

@blueprint.route('/requests/getService/break', methods = ['GET'])
def breakGetServiceForRequests():
    app.sessionForRequests.getService = functionOneTimeBroken(app.sessionForRequests.getService)

    return Response("OK", status=200)

@blueprint.route('/subscriptions/getService/break', methods = ['GET'])
def breakGetServiceForSubscriptions():
    app.sessionForSubscriptions.getService = functionOneTimeBroken(app.sessionForSubscriptions.getService)

    return Response("OK", status=200)
