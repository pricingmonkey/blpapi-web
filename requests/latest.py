import json
import traceback
from flask import Blueprint, current_app as app, request, Response

from bloomberg.utils import openBloombergSession, openBloombergService, sendAndWait
from bloomberg.extract import extractReferenceSecurityPricing, extractErrors
from utils import handleBrokenSession

from .utils import allowCORS, respond400, respond500, recordBloombergHits

blueprint = Blueprint('latest', __name__)

def requestLatest(session, securities, fields):
    recordBloombergHits("latest", len(securities) * len(fields))
    try:
        refDataService, _ = openBloombergService(session, "//blp/refdata")
        request = refDataService.createRequest("ReferenceDataRequest")

        request.set("returnFormattedValue", True)
        for security in securities:
            request.append("securities", security)

        for field in fields:
            request.append("fields", field)

        responses = sendAndWait(session, request)

        securityPricing = []
        for response in responses:
            securityPricing.extend(extractReferenceSecurityPricing(response))

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

# ?security=...&security=...&field=...&field=...
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
        traceback.print_exc()
        return respond500(e)
    try:
        securities = request.values.getlist('security') or []
        fields = request.values.getlist('field') or []
    except Exception as e:
        traceback.print_exc()
        return respond400(e)

    try:
        payload = json.dumps(requestLatest(app.sessionForRequests, securities, fields)).encode()
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


