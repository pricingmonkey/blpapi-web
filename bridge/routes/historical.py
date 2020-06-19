import json
import traceback
from flask import Blueprint, current_app as app, request, Response

from bridge.bloomberg.results.errors import extractErrors
from bridge.bloomberg.results.historical import extractHistoricalSecurityPricing
from utils import handleBrokenSession

from .utils import allowCORS, respond400, respond500, recordBloombergHits

blueprint = Blueprint('historical', __name__)

def requestHistorical(session, securities, fields, startDate, endDate):
    recordBloombergHits("historical", len(securities) * len(fields))
    try:
        refDataService, _ = session.getService("//blp/refdata")
        request = refDataService.createRequest("HistoricalDataRequest")

        request.set("startDate", startDate)
        request.set("endDate", endDate)
        request.set("periodicitySelection", "DAILY");

        for security in securities:
            request.append("securities", security)

        for field in fields:
            request.append("fields", field)

        responses = session.sendAndWait(request)

        securityPricing = []
        for response in responses:
            securityPricing.extend(extractHistoricalSecurityPricing(response))

        errors = []
        for response in responses:
            errors.extend(extractErrors(response))

        return { "response": securityPricing, "errors": errors }
    except Exception as e:
        raise

@blueprint.route('/', methods = ['OPTIONS'])
def tellThemWhenCORSIsAllowed():
    response = Response("")
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    response.headers['Access-Control-Allow-Methods'] = ", ".join(["GET", "POST", "OPTIONS"])
    return response

# ?security=...&security=...&field=...&field=...&startDate=...&endDate=...
@blueprint.route('/', methods = ['GET', 'POST'])
def index():
    session = app.sessionPoolForRequests.getSession()
    try:
        session.start()
    except Exception as e:
        handleBrokenSession(app)
        traceback.print_exc()
        return respond500(e)
    try:
        if request.headers['content-type'] == 'application/json':
            jsonData = request.get_json()
            securities, fields, startDate, endDate = parseJsonRequest(jsonData)
        else:
            securities = request.values.getlist('security') or []
            fields = request.values.getlist('field') or []
            startDate = request.values.get('startDate')
            endDate = request.values.get('endDate')
    except Exception as e:
        traceback.print_exc()
        return respond400(e)

    try:
        payload = json.dumps(requestHistorical(session, securities, fields, startDate, endDate)).encode()
    except Exception as e:
        handleBrokenSession(app)
        traceback.print_exc()
        return respond500(e)

    response = Response(
        payload,
        status=200,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response


def parseJsonRequest(jsonData):
    securities = [each['security'] for each in jsonData['list']]
    unflattenedFields = [each['fields'] for each in jsonData['list']]
    duplicatedFields = [y for x in unflattenedFields for y in x]
    fields = list(set(duplicatedFields))
    startDate = jsonData['startDate']
    endDate = jsonData['endDate']
    return securities, fields, startDate, endDate
