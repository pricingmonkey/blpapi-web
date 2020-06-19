import datetime
from flask import request, Response, current_app as app

import traceback


def allow_cors(host):
    if not host:
        return ""
    hosts = [
        "http://localhost:8080",
        "http://localhost:8081"
    ]
    if host.endswith("pricingmonkey.com") or host in hosts:
        return host
    else:
        return "null"


def respond400(e):
    response = Response("{0}: {1}".format(type(e).__name__, e).encode(), status=400)
    response.headers['Access-Control-Allow-Origin'] = allow_cors(request.headers.get('Origin'))
    traceback.print_exc()
    return response


def respond500(e):
    response = Response("{0}: {1}".format(type(e).__name__, e).encode(), status=500)
    response.headers['Access-Control-Allow-Origin'] = allow_cors(request.headers.get('Origin'))
    traceback.print_exc()
    return response


def record_bloomberg_hits(key, number):
    today = datetime.date.today().isoformat()
    if not today in app.bloomberg_hits:
        app.bloomberg_hits[today] = {
            "latest": 0,
            "historical": 0,
            "intraday": 0,
            "subscribe": 0,
            "resubscribe": 0,
            "unsubscribe": 0
        }
    if not key in app.bloomberg_hits[today]:
        app.bloomberg_hits[today][key] = 0
    app.bloomberg_hits[today][key] += number
