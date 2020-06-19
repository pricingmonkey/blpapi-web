import json
import traceback
from flask import Blueprint, current_app as app, request, Response

from bridge.bloomberg.results.latest import extract_reference_security_pricing
from bridge.bloomberg.results.errors import extract_errors
from utils import handle_broken_session

from .utils import allow_cors, respond400, respond500, record_bloomberg_hits

blueprint = Blueprint('latest', __name__)


def request_latest(session, securities, fields):
    record_bloomberg_hits("latest", len(securities) * len(fields))
    try:
        ref_data_service, _ = session.get_service("//blp/refdata")
        reference_data_request = ref_data_service.createRequest("ReferenceDataRequest")

        reference_data_request.set("returnFormattedValue", True)
        for security in securities:
            reference_data_request.append("securities", security)

        for field in fields:
            reference_data_request.append("fields", field)

        responses = session.send_and_wait(reference_data_request)

        security_pricing = []
        for response in responses:
            security_pricing.extend(extract_reference_security_pricing(response))

        errors = []
        for response in responses:
            errors.extend(extract_errors(response))
        return {"response": security_pricing, "errors": errors}
    except Exception:
        raise


@blueprint.route('/', methods=['OPTIONS'])
def tell_them_when_cors_is_allowed():
    response = Response("")
    response.headers['Access-Control-Allow-Origin'] = allow_cors(request.headers.get('Origin'))
    response.headers['Access-Control-Allow-Methods'] = ", ".join(["GET", "POST", "OPTIONS"])
    return response


def handle_request(securities, fields):
    try:
        session = app.session_pool_for_requests.getSession()
    except Exception as e:
        handle_broken_session(app)
        traceback.print_exc()
        return respond500(e)

    try:
        payload = json.dumps(request_latest(session, securities, fields)).encode()
    except Exception as e:
        handle_broken_session(app)
        traceback.print_exc()
        return respond500(e)

    response = Response(
        payload,
        status=200,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allow_cors(request.headers.get('Origin'))
    return response


def parse_json_request(json_data):
    securities = [each['security'] for each in json_data]
    unflattened_fields = [each['fields'] for each in json_data]
    duplicated_fields = [y for x in unflattened_fields for y in x]
    fields = list(set(duplicated_fields))
    return securities, fields


# ?security=...&security=...&field=...&field=...
@blueprint.route('/', methods=['POST', 'GET'])
def index():
    try:
        if request.headers['content-type'] == 'application/json':
            json_data = request.get_json()
            securities, fields = parse_json_request(json_data)
        else:
            securities = request.values.getlist('security') or []
            fields = request.values.getlist('field') or []
    except Exception as e:
        traceback.print_exc()
        return respond400(e)

    return handle_request(securities, fields)
