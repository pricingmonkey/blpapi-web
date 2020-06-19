import dateutil.parser
import json
import traceback
from flask import Blueprint, current_app as app, request, Response

from bridge.bloomberg.results.errors import extract_errors
from bridge.bloomberg.results.intraday import extract_intraday_security_pricing
from utils import handle_broken_session

from .utils import allow_cors, respond400, respond500, record_bloomberg_hits

blueprint = Blueprint('intraday', __name__)


def request_intraday(session, securities, event_types, start_date_time, end_date_time, interval=5):
    record_bloomberg_hits("intraday", len(securities) * len(event_types))
    try:
        ref_data_service, _ = session.get_service("//blp/refdata")
        security_pricing = []
        errors = []
        for security in securities:
            for eventType in event_types:
                intraday_bar_request = ref_data_service.createRequest("IntradayBarRequest")

                intraday_bar_request.set("startDateTime", start_date_time)
                intraday_bar_request.set("endDateTime", end_date_time)
                intraday_bar_request.set("security", security)
                intraday_bar_request.set("eventType", eventType)
                intraday_bar_request.set("interval", interval)

                responses = session.send_and_wait(intraday_bar_request)

                for response in responses:
                    security_pricing.append(extract_intraday_security_pricing(security, response))

                for response in responses:
                    errors.extend(extract_errors(response))

        return {"response": security_pricing, "errors": errors}
    except Exception:
        raise


def parse_json_request(json_data):
    securities = [each['security'] for each in json_data['list']]

    unflattened_event_types = [each['eventType'] for each in json_data['list']]
    duplicated_event_types = [y for x in unflattened_event_types for y in x]
    event_types = list(set(duplicated_event_types))

    start_date_time = dateutil.parser.parse(json_data['startDateTime'])
    end_date_time = dateutil.parser.parse(json_data['endDateTime'])
    interval = json_data['interval']

    return securities, event_types, start_date_time, end_date_time, interval


# ?eventType=[...]&security=[...]
@blueprint.route('/', methods=['GET', 'POST'])
def index():
    try:
        session = app.session_pool_for_requests.getSession()
    except Exception as e:
        handle_broken_session(app)
        traceback.print_exc()
        return respond500(e)
    try:
        if request.headers['content-type'] == 'application/json':
            json_data = request.get_json()
            securities, event_types, start_date_time, end_date_time, interval = parse_json_request(json_data)
        else:
            securities = request.values.getlist('security') or []
            event_types = request.values.getlist('eventType') or []
            start_date_time = request.values.get('startDateTime')
            end_date_time = request.values.get('endDateTime')
            interval = request.values.get('interval')

    except Exception as e:
        traceback.print_exc()
        return respond400(e)

    try:
        intraday_response = request_intraday(session, securities, event_types, start_date_time, end_date_time, interval)
        payload = json.dumps(intraday_response).encode()
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
