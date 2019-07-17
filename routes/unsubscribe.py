import json, sys
import traceback
from flask import Blueprint, current_app as app, request, Response

from utils import handleBrokenSession

from .utils import allowCORS, respond400, respond500, recordBloombergHits

blueprint = Blueprint('unsubscribe', __name__)

@blueprint.route('/', methods = ['OPTIONS'])
def tellThemWhenCORSIsAllowed():
    response = Response("")
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    response.headers['Access-Control-Allow-Methods'] = ", ".join(["OPTIONS", "GET", "POST", "DELETE"])
    return response

def doUnsubscribe(securities):
    try:
        _, sessionRestarted = app.sessionForSubscriptions.getService("//blp/mktdata")
        if sessionRestarted:
            app.allSubscriptions = {}
        subscriptionList = blpapi.SubscriptionList()
        for security in securities:
            correlationId = blpapi.CorrelationId(sys.intern(security))
            if security in app.allSubscriptions:
                del app.allSubscriptions[security]
            subscriptionList.add(security, correlationId=correlationId)

        recordBloombergHits("unsubscribe", subscriptionList.size())
        app.sessionForSubscriptions.unsubscribe(subscriptionList)
    except Exception as e:
        handleBrokenSession(app, e)
        traceback.print_exc()
        return respond500(e)

    response = Response(
        json.dumps({ "message": "OK"}).encode(),
        status=202,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response

@blueprint.route('/', methods = ['DELETE'])
def unsubscribeAll():
    try:
        if not app.sessionForSubscriptions.isStarted():
            app.sessionForSubscriptions.start()
            app.allSubscriptions = {}
    except Exception as e:
        handleBrokenSession(app, e)
        traceback.print_exc()
        return respond500(e)

    return doUnsubscribe(list(app.allSubscriptions.keys()))

@blueprint.route('/', methods = ['GET', 'POST'])
def unsubscribe():
    try:
        if not app.sessionForSubscriptions.isStarted():
            app.sessionForSubscriptions.start()
            app.allSubscriptions = {}
    except Exception as e:
        handleBrokenSession(app, e)
        traceback.print_exc()
        return respond500(e)

    try:
        securities = request.values.getlist('security') or []
    except Exception as e:
        traceback.print_exc()
        return respond400(e)

    return doUnsubscribe(securities)
