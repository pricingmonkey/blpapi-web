import json, sys
import traceback
from flask import Blueprint, current_app as app, request, Response

from bloomberg.utils import openBloombergSession, openBloombergService
from utils import handleBrokenSession

from .utils import allowCORS, respond400, respond500

blueprint = Blueprint('subscribe', __name__)

@blueprint.route('/', methods = ['OPTIONS'])
def tellThemWhenCORSIsAllowed():
    response = Response("")
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    response.headers['Access-Control-Allow-Methods'] = ", ".join(["GET", "POST", "OPTIONS"])
    return response

@blueprint.route('/', methods = ['GET', 'POST'])
def index():
    try:
        if app.sessionForSubscriptions is None:
            app.sessionForSubscriptions = openBloombergSession()
            app.allSubscriptions = {}
    except Exception as e:
        handleBrokenSession(app, e)
        traceback.print_exc()
        return respond500(e)
    try:
        securities = request.values.getlist('security') or []
        fields = request.values.getlist('field') or []
        interval = request.values.get('interval') or "2.0"
    except Exception as e:
        traceback.print_exc()
        return respond400(e)

    try:
        _, sessionRestarted = openBloombergService(app.sessionForSubscriptions, "//blp/mktdata")
        if sessionRestarted:
            app.allSubscriptions = {}
        subscriptionList = blpapi.SubscriptionList()
        resubscriptionList = blpapi.SubscriptionList()
        for security in securities:
            correlationId = blpapi.CorrelationId(sys.intern(security))
            if not security in app.allSubscriptions:
                app.allSubscriptions[security] = list(fields)
                subscriptionList.add(security, app.allSubscriptions[security], "interval=" + interval, correlationId)
            else:
                app.allSubscriptions[security] += fields
                app.allSubscriptions[security] = list(set(app.allSubscriptions[security]))
                resubscriptionList.add(security, app.allSubscriptions[security], "interval=" + interval, correlationId)

        if subscriptionList.size() != 0:
            app.sessionForSubscriptions.subscribe(subscriptionList)

        if resubscriptionList.size() != 0:
            try:
                app.sessionForSubscriptions.resubscribe(resubscriptionList)
            except Exception as e:
                traceback.print_exc()
                app.sessionForSubscriptions.unsubscribe(resubscriptionList)
                app.sessionForSubscriptions.subscribe(resubscriptionList)
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


