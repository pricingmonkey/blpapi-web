from flask import request, Response

import hashlib, traceback

def allowCORS(host):
    HOSTS = ["http://staging.pricingmonkey.com", "http://pricingmonkey.com", "http://localhost:8080", "http://localhost:8081"]
    if host in HOSTS:
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

