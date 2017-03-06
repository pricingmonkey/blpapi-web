import dateutil.parser
import json
from flask import Blueprint, current_app as app, request, Response

from bloomberg.utils import openBloombergSession, openBloombergService, sendAndWait
from bloomberg.extract import extractIntradaySecurityPricing, extractErrors
from utils import handleBrokenSession

from .utils import allowCORS, generateEtag, respond400, respond500

blueprint = Blueprint('intraday', __name__)

def requestIntraday(session, securities, eventTypes, startDateTime, endDateTime):
    try:
        refDataService, _ = openBloombergService(session, "//blp/refdata")
        securityPricing = []
        errors = []
        for security in securities:
            for eventType in eventTypes:
                request = refDataService.createRequest("IntradayBarRequest")

                request.set("startDateTime", startDateTime)
                request.set("endDateTime", endDateTime)
                request.set("security", security)
                request.set("eventType", eventType)
                request.set("interval", 5)

                responses = sendAndWait(session, request)

                for response in responses:
                    securityPricing.append(extractIntradaySecurityPricing(security, response))

                for response in responses:
                    errors.extend(extractErrors(response))

        return { "response": securityPricing, "errors": errors }
    except Exception as e:
        raise


# ?eventType=[...]&security=[...]
@blueprint.route('/', methods = ['GET'])
def index():
    try:
        if app.sessionForRequests is None:
            app.sessionForRequests = openBloombergSession()
        if app.sessionForSubscriptions is None:
            app.sessionForSubscriptions = openBloombergSession()
            app.allSubscriptions = {}
    except Exception as e:
        handleBrokenSession(app, e)
        if app.client is not None:
            app.client.captureException()
        return respond500(e)
    try:
        securities = request.args.getlist('security') or []
        eventTypes = request.args.getlist('eventType') or []
        startDateTime = dateutil.parser.parse(request.args.get('startDateTime'))
        endDateTime = dateutil.parser.parse(request.args.get('endDateTime'))
    except Exception as e:
        if app.client is not None:
            app.client.captureException()
        return respond400(e)

    try:
        payload = json.dumps(requestIntraday(app.sessionForRequests, securities, eventTypes, startDateTime, endDateTime)).encode()
    except Exception as e:
        handleBrokenSession(app, e)
        if app.client is not None:
            app.client.captureException()
        return respond500(e)

    response = Response(
        payload,
        status=200,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response


