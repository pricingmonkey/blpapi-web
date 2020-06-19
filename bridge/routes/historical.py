import json
import traceback
from flask import Blueprint, current_app as app, request, Response

from bridge.bloomberg.results.errors import extract_errors
from bridge.bloomberg.results.historical import extract_historical_security_pricing
from utils import handle_broken_session

from .utils import allow_cors, respond400, respond500, record_bloomberg_hits

blueprint = Blueprint('historical', __name__)


def request_historical(session, securities, fields, start_date, end_date):
    record_bloomberg_hits("historical", len(securities) * len(fields))
    try:
        ref_data_service, _ = session.get_service("//blp/refdata")
        historical_data_request = ref_data_service.createRequest("HistoricalDataRequest")

        historical_data_request.set("startDate", start_date)
        historical_data_request.set("endDate", end_date)
        historical_data_request.set("periodicitySelection", "DAILY")

        for security in securities:
            historical_data_request.append("securities", security)

        for field in fields:
            historical_data_request.append("fields", field)

        responses = session.send_and_wait(historical_data_request)

        security_pricing = []
        for response in responses:
            security_pricing.extend(extract_historical_security_pricing(response))

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


# ?security=...&security=...&field=...&field=...&startDate=...&endDate=...
@blueprint.route('/', methods=['GET', 'POST'])
def index():
    session = app.session_pool_for_requests.getSession()
    try:
        session.start()
    except Exception as e:
        handle_broken_session(app)
        traceback.print_exc()
        return respond500(e)
    try:
        if request.headers['content-type'] == 'application/json':
            json_data = request.get_json()
            securities, fields, start_date, end_date = parse_json_request(json_data)
        else:
            securities = request.values.getlist('security') or []
            fields = request.values.getlist('field') or []
            start_date = request.values.get('startDate')
            end_date = request.values.get('endDate')
    except Exception as e:
        traceback.print_exc()
        return respond400(e)

    try:
        payload = json.dumps(request_historical(session, securities, fields, start_date, end_date)).encode()
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
    securities = [each['security'] for each in json_data['list']]
    unflattened_fields = [each['fields'] for each in json_data['list']]
    duplicated_fields = [y for x in unflattened_fields for y in x]
    fields = list(set(duplicated_fields))
    start_date = json_data['startDate']
    end_date = json_data['endDate']
    return securities, fields, start_date, end_date
