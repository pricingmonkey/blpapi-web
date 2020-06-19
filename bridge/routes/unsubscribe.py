import json, sys
import traceback
from flask import Blueprint, current_app as app, request, Response

from utils import handle_broken_session

from .utils import allow_cors, respond400, respond500, record_bloomberg_hits

blueprint = Blueprint('unsubscribe', __name__)


@blueprint.route('/', methods=['OPTIONS'])
def tellThemWhenCORSIsAllowed():
    response = Response("")
    response.headers['Access-Control-Allow-Origin'] = allow_cors(request.headers.get('Origin'))
    response.headers['Access-Control-Allow-Methods'] = ", ".join(["OPTIONS", "GET", "POST", "DELETE"])
    return response


def do_unsubscribe(securities):
    try:
        _, session_restarted = app.session_for_subscriptions.get_service("//blp/mktdata")
        if session_restarted:
            app.all_subscriptions = {}
        subscription_list = blpapi.SubscriptionList()
        for security in securities:
            correlation_id = blpapi.CorrelationId(sys.intern(security))
            if security in app.all_subscriptions:
                del app.all_subscriptions[security]
            subscription_list.add(security, correlationId=correlation_id)

        record_bloomberg_hits("unsubscribe", subscription_list.size())
        app.session_for_subscriptions.unsubscribe(subscription_list)
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


@blueprint.route('/', methods=['DELETE'])
def unsubscribe_all():
    try:
        if not app.session_for_subscriptions.is_started():
            app.session_for_subscriptions.start()
            app.all_subscriptions = {}
    except Exception as e:
        handle_broken_session(app)
        traceback.print_exc()
        return respond500(e)

    return do_unsubscribe(list(app.all_subscriptions.keys()))


@blueprint.route('/', methods=['GET', 'POST'])
def unsubscribe():
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
            securities = [each['security'] for each in jsonData]
        else:
            securities = request.values.getlist('security') or []
    except Exception as e:
        traceback.print_exc()
        return respond400(e)

    return do_unsubscribe(securities)
