import json, sys
import traceback
from flask import Blueprint, current_app as app, request, Response

from utils import handleBrokenSession

from .utils import allowCORS, respond400, respond500, recordBloombergHits

blueprint = Blueprint('subscribe', __name__)

@blueprint.route('/', methods = ['OPTIONS'])
def tellThemWhenCORSIsAllowed():
    response = Response("")
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    response.headers['Access-Control-Allow-Methods'] = ", ".join(["GET", "POST", "OPTIONS"])
    return response

def doSubscribe(correlationId, security, fields, interval):
    subscriptionList = blpapi.SubscriptionList()
    app.allSubscriptions[security] = list(fields)

    subscriptionList.add(security, app.allSubscriptions[security], "interval=" + interval, correlationId)

    recordBloombergHits("subscribe", len(fields))
    app.sessionForSubscriptions.subscribe(subscriptionList)

def doResubscribe(correlationId, security, fields, interval):
    subscriptionList = blpapi.SubscriptionList()
    app.allSubscriptions[security] = list(fields)
    app.allSubscriptions[security] += fields
    app.allSubscriptions[security] = list(set(app.allSubscriptions[security]))

    subscriptionList.add(security, app.allSubscriptions[security], "interval=" + interval, correlationId)

    try:
        recordBloombergHits("resubscribe", len(fields))
        app.sessionForSubscriptions.resubscribe(subscriptionList)
    except Exception as e:
        traceback.print_exc()
        recordBloombergHits("unsubscribe", subscriptionList.size() * 3)
        app.sessionForSubscriptions.unsubscribe(subscriptionList)
        recordBloombergHits("subscribe", subscriptionList.size() * 3)
        app.sessionForSubscriptions.subscribe(subscriptionList)

@blueprint.route('/', methods = ['GET', 'POST'])
def index():
    try:
        if not app.sessionForSubscriptions.isStarted():
            app.sessionForSubscriptions.start()
            app.allSubscriptions = {}
    except Exception as e:
        handleBrokenSession(app, e)
        traceback.print_exc()
        return respond500(e)
    try:
        if request.headers['content-type'] == 'application/json':
            jsonData = request.get_json()
            securities, fields, interval = parseJsonRequest(jsonData)
        else:
            securities = request.values.getlist('security') or []
            fields = request.values.getlist('field') or []
            interval = request.values.get('interval')
    except Exception as e:
        traceback.print_exc()
        return respond400(e)

    if not interval:
        interval = "2.0"

    try:
        _, sessionRestarted = app.sessionForSubscriptions.getService("//blp/mktdata")
        if sessionRestarted:
            app.allSubscriptions = {}

        for security in securities:
            correlationId = blpapi.CorrelationId(sys.intern(security))

            if not security in app.allSubscriptions:
                try:
                    doSubscribe(correlationId, security, fields, interval)
                except blpapi.DuplicateCorrelationIdException as e:
                    doResubscribe(correlationId, security, fields, interval)
            else:
                doResubscribe(correlationId, security, fields, interval)
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


def parseJsonRequest(jsonData):
    securities = [each['security'] for each in jsonData['list']]
    unflattenedFields = [each['fields'] for each in jsonData['list']]
    duplicatedFields = [y for x in unflattenedFields for y in x]
    fields = list(set(duplicatedFields))
    interval = jsonData['interval']
    return securities, fields, interval


