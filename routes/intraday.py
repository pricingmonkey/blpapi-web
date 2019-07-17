import dateutil.parser
import json
import traceback
from flask import Blueprint, current_app as app, request, Response

from bloomberg.results.errors import extractErrors
from bloomberg.results.intraday import extractIntradaySecurityPricing
from utils import handleBrokenSession

from .utils import allowCORS, respond400, respond500, recordBloombergHits

blueprint = Blueprint('intraday', __name__)

def requestIntraday(session, securities, eventTypes, startDateTime, endDateTime, interval = 5):
    recordBloombergHits("intraday", len(securities) * len(eventTypes))
    try:
        refDataService, _ = session.getService("//blp/refdata")
        securityPricing = []
        errors = []
        for security in securities:
            for eventType in eventTypes:
                request = refDataService.createRequest("IntradayBarRequest")

                request.set("startDateTime", startDateTime)
                request.set("endDateTime", endDateTime)
                request.set("security", security)
                request.set("eventType", eventType)
                request.set("interval", interval)

                responses = session.sendAndWait(request)

                for response in responses:
                    securityPricing.append(extractIntradaySecurityPricing(security, response))

                for response in responses:
                    errors.extend(extractErrors(response))

        return { "response": securityPricing, "errors": errors }
    except Exception as e:
        raise


def parseJsonRequest(jsonData):
    securities = [each['security'] for each in jsonData['list']]

    unflattenedEventTypes = [each['eventType'] for each in jsonData['list']]
    duplicatedEventTypes = [y for x in unflattenedEventTypes for y in x]
    eventTypes = list(set(duplicatedEventTypes))

    startDateTime = dateutil.parser.parse(jsonData['startDateTime'])
    endDateTime = dateutil.parser.parse(jsonData['endDateTime'])
    interval = jsonData['interval']

    return securities, eventTypes, startDateTime, endDateTime, interval

# ?eventType=[...]&security=[...]
@blueprint.route('/', methods = ['GET'])
def index():
    try:
        session = app.sessionPoolForRequests.getSession()
    except Exception as e:
        handleBrokenSession(app, e)
        traceback.print_exc()
        return respond500(e)
    try:
        if request.headers['content-type'] == 'application/json':
            jsonData = request.get_json()
            securities, eventTypes, startDateTime, endDateTime, interval = parseJsonRequest(jsonData)
        else:
            securities = request.values.getlist('security') or []
            eventTypes = request.values.getlist('eventType') or []
            startDateTime = request.values.get('startDateTime')
            endDateTime = request.values.get('endDateTime')
            interval = request.values.get('interval')

    except Exception as e:
        traceback.print_exc()
        return respond400(e)

    try:
        payload = json.dumps(requestIntraday(session, securities, eventTypes, startDateTime, endDateTime, interval)).encode()
    except Exception as e:
        handleBrokenSession(app, e)
        traceback.print_exc()
        return respond500(e)

    response = Response(
        payload,
        status=200,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response
