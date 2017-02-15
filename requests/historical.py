import json
from flask import Blueprint, current_app as app, request, Response

from bloomberg.utils import openBloombergSession, openBloombergService, sendAndWait
from bloomberg.extract import extractHistoricalSecurityPricing, extractErrors
from utils import handleBrokenSession

from .utils import allowCORS, generateEtag, respond400, respond500

blueprint = Blueprint('historical', __name__)

def requestHistorical(session, securities, fields, startDate, endDate):
    try:
        refDataService, _ = openBloombergService(session, "//blp/refdata")
        request = refDataService.createRequest("HistoricalDataRequest")

        request.set("startDate", startDate)
        request.set("endDate", endDate)
        request.set("periodicitySelection", "DAILY");

        for security in securities:
            request.append("securities", security)

        for field in fields:
            request.append("fields", field)

        responses = sendAndWait(session, request)

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
        securities = request.values.getlist('security') or []
        fields = request.values.getlist('field') or []
        startDate = request.values.get('startDate')
        endDate = request.values.get('endDate')
    except Exception as e:
        if app.client is not None:
            app.client.captureException()
        return respond400(e)

    etag = generateEtag({
        "securities": securities,
        "fields": fields,
        "startDate": startDate,
        "endDate": endDate
    })
    if request.headers.get('If-None-Match') == etag:
        response = Response(
            "",
            status=304,
            mimetype='application/json')
        response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
        return response
    try:
        payload = json.dumps(requestHistorical(app.sessionForRequests, securities, fields, startDate, endDate)).encode()
    except Exception as e:
        handleBrokenSession(app, e)
        if app.client is not None:
            app.client.captureException()
        return respond500(e)

    response = Response(
        payload,
        status=200,
        mimetype='application/json')
    response.headers['Etag'] = etag
    response.headers['Cache-Control'] = "max-age=86400, must-revalidate"
    response.headers['Vary'] = "Origin"
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response

