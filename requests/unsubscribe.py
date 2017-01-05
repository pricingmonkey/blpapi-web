import json, sys
from flask import Blueprint, current_app as app, request, Response

from bloomberg.utils import openBloombergSession, openBloombergService
from utils import handleBrokenSession

from .utils import allowCORS, respond400, respond500

blueprint = Blueprint('unsubscribe', __name__)

@blueprint.route('/', methods = ['GET'])
def unsubscribe():
    try:
        if app.sessionForSubscriptions is None:
            app.sessionForSubscriptions = openBloombergSession()
            app.allSubscriptions = {}
    except Exception as e:
        handleBrokenSession(e)
        if app.client is not None:
            app.client.captureException()
        return respond500(e)
    try:
        securities = request.args.getlist('security') or []
    except Exception as e:
        if app.client is not None:
            app.client.captureException()
        return respond400(e)

    try:
        _, sessionRestarted = openBloombergService(app.sessionForSubscriptions, "//blp/mktdata")
        if sessionRestarted:
            app.allSubscriptions = {}
        subscriptionList = blpapi.SubscriptionList()
        for security in securities:
            correlationId = blpapi.CorrelationId(sys.intern(security))
            if security in app.allSubscriptions:
                del app.allSubscriptions[security]
            subscriptionList.add(security, correlationId=correlationId)

        app.sessionForSubscriptions.unsubscribe(subscriptionList)
    except Exception as e:
        handleBrokenSession(e)
        if app.client is not None:
            app.client.captureException()
        return respond500(e)

    response = Response(
        json.dumps({ "message": "OK"}).encode(),
        status=202,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response

