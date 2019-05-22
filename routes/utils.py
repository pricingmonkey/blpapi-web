import datetime
from flask import request, Response, current_app as app

import hashlib, traceback


def allowCORS(host):
    if not host:
        return ""
    HOSTS = [
        "http://localhost:8080",
        "http://localhost:8081"
    ]
    if host.endswith("pricingmonkey.com") or host in HOSTS: 
        return host
    else:
        return "null"

def generateEtag(obj):
    sha1 = hashlib.sha1()
    sha1.update("{}".format(obj).encode())
    return '"{}"'.format(sha1.hexdigest())

def respond400(e):
    response = Response("{0}: {1}".format(type(e).__name__, e).encode(), status=400)
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    traceback.print_exc()
    return response

def respond500(e):
    response = Response("{0}: {1}".format(type(e).__name__, e).encode(), status=500)
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    traceback.print_exc()
    return response

def recordBloombergHits(key, number):
    today = datetime.date.today().isoformat()
    if not today in app.bloombergHits:
        app.bloombergHits[today] = {
            "latest": 0,
            "historical": 0,
            "intraday": 0,
            "subscribe": 0,
            "resubscribe": 0,
            "unsubscribe": 0
        }
    if not key in app.bloombergHits[today]:
        app.bloombergHits[today][key] = 0
    app.bloombergHits[today][key] += number
