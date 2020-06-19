import json
import sys
import traceback

from flask import Blueprint, current_app as app, request, Response

from utils import handle_broken_session
from .utils import allow_cors, respond400, respond500, record_bloomberg_hits

blueprint = Blueprint('subscribe', __name__)


@blueprint.route('/', methods=['OPTIONS'])
def tell_them_when_cors_is_allowed():
    response = Response("")
    response.headers['Access-Control-Allow-Origin'] = allow_cors(request.headers.get('Origin'))
    response.headers['Access-Control-Allow-Methods'] = ", ".join(["GET", "POST", "OPTIONS"])
    return response


def do_subscribe(correlationId, security, fields, interval):
    subscription_list = blpapi.SubscriptionList()
    app.all_subscriptions[security] = list(fields)

    subscription_list.add(security, app.all_subscriptions[security], "interval=" + interval, correlationId)

    record_bloomberg_hits("subscribe", len(fields))
    app.session_for_subscriptions.subscribe(subscription_list)


def do_resubscribe(correlationId, security, fields, interval):
    subscription_list = blpapi.SubscriptionList()
    app.all_subscriptions[security] += fields
    app.all_subscriptions[security] = list(set(app.all_subscriptions[security]))

    subscription_list.add(security, app.all_subscriptions[security], "interval=" + interval, correlationId)

    try:
        record_bloomberg_hits("resubscribe", len(fields))
        app.session_for_subscriptions.resubscribe(subscription_list)
    except Exception as e:
        traceback.print_exc()
        record_bloomberg_hits("unsubscribe", subscription_list.size() * 3)
        app.session_for_subscriptions.unsubscribe(subscription_list)
        record_bloomberg_hits("subscribe", subscription_list.size() * 3)
        app.session_for_subscriptions.subscribe(subscription_list)


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    try:
        if not app.session_for_subscriptions.is_started():
            app.session_for_subscriptions.start()
            app.all_subscriptions = {}
    except Exception as e:
        handle_broken_session(app)
        traceback.print_exc()
        return respond500(e)
    try:
        if request.headers['content-type'] == 'application/json':
            jsonData = request.get_json()
            securities, fields, interval = parse_json_request(jsonData)
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
        _, session_restarted = app.session_for_subscriptions.get_service("//blp/mktdata")
        if session_restarted:
            app.all_subscriptions = {}

        for security in securities:
            correlation_id = blpapi.CorrelationId(sys.intern(security))

            if not security in app.all_subscriptions:
                try:
                    do_subscribe(correlation_id, security, fields, interval)
                except blpapi.DuplicateCorrelationIdException as e:
                    do_resubscribe(correlation_id, security, fields, interval)
            else:
                do_resubscribe(correlation_id, security, fields, interval)
    except Exception as e:
        handle_broken_session(app)
        traceback.print_exc()
        return respond500(e)

    response = Response(
        json.dumps({"message": "OK"}).encode(),
        status=202,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allow_cors(request.headers.get('Origin'))
    return response


def parse_json_request(json_data):
    securities = [each['security'] for each in json_data['list']]
    unflattened_fields = [each['fields'] for each in json_data['list']]
    duplicated_fields = [y for x in unflattened_fields for y in x]
    fields = list(set(duplicated_fields))
    interval = json_data['interval']
    return securities, fields, interval
