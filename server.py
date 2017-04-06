import eventlet

# "import encodings.idna" is a fix for "unknown encoding: idna" error
# which we saw occurring's on a user's computer and crashing the app
# in result
import encodings.idna
import logging
import argparse

import time, random
import json
import traceback
import sys
import subprocess
import psutil
import npyscreen

from flask import Flask, Response, request
from flask_socketio import emit, SocketIO

from bloomberg.utils import openBloombergSession, startBbcommIfNecessary
from requests import latest, historical, intraday, subscribe, unsubscribe, dev
from requests.utils import allowCORS
from subscriptions import handleSubscriptions
from utils import get_main_dir, main_is_frozen

app = Flask(__name__)
app.url_map.strict_slashes = False
app.allSubscriptions = {}
app.latestSubscriptionValues = {}
app.client = None
app.sessionForRequests = None
app.sessionForSubscriptions = None

app.register_blueprint(latest.blueprint, url_prefix='/latest')
app.register_blueprint(historical.blueprint, url_prefix='/historical')
app.register_blueprint(intraday.blueprint, url_prefix='/intraday')
app.register_blueprint(subscribe.blueprint, url_prefix='/subscribe')
app.register_blueprint(unsubscribe.blueprint, url_prefix='/unsubscribe')
socketio = SocketIO(app, async_mode="eventlet")

@app.route('/status', methods = ['OPTIONS'])
@app.route('/subscriptions', methods = ['OPTIONS'])
@app.route('/latest', methods = ['OPTIONS'])
@app.route('/historical', methods = ['OPTIONS'])
@app.route('/intraday', methods = ['OPTIONS'])
@app.route('/subscribe', methods = ['OPTIONS'])
@app.route('/unsubscribe', methods = ['OPTIONS'])
def tellThemWhenCORSIsAllowed():
    response = Response("")
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    response.headers['Access-Control-Allow-Methods'] = ", ".join(["GET", "OPTIONS"])
    return response

@app.route('/status', methods = ['GET'])
def status():
    status = "UP" if app.sessionForRequests or app.sessionForSubscriptions else "DOWN"
    response = Response(
        json.dumps({ "status": status, "version": "2.3.2"}).encode(),
        status=200,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response

@app.route('/subscriptions', methods = ['GET'])
def subscriptions():
    response = Response(
        json.dumps(app.allSubscriptions).encode(),
        status=200,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response

def wireUpBlpapiImplementation(blpapi):
    import bloomberg.utils
    bloomberg.utils.__dict__["blpapi"] = blpapi
    subscribe.__dict__["blpapi"] = blpapi
    import subscriptions
    subscriptions.__dict__["blpapi"] = blpapi
    unsubscribe.__dict__["blpapi"] = blpapi
    dev.__dict__["blpapi"] = blpapi

def wireUpDevelopmentDependencies():
    global blpapi
    global client
    blpapi = eventlet.import_patched("blpapi_simulator")
    client = None
    app.register_blueprint(dev.blueprint, url_prefix='/dev')

def wireUpProductionDependencies():
    global blpapi
    global client
    import blpapi

    from raven.transport.eventlet import EventletHTTPTransport
    from raven import Client
    client = Client(
        "https://ec16b2b639e642e49c59e922d2c7dc9b:2dd38313e1d44fd2bc2adb5a510639fc@sentry.io/100358?ca_certs={}/certifi/cacert.pem".format(get_main_dir()),
        transport=EventletHTTPTransport,
        enable_breadcrumbs=False
    )

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)
    startBbcommIfNecessary(client)

class TestApp(npyscreen.NPSAppManaged):
    def while_waiting(self):
        self.grid.values = []
        for security, fields in app.allSubscriptions.items():
            for field in fields:
                self.grid.values.append([security, field, (app.latestSubscriptionValues.get(security) or {}).get(field)])
        if self.grid.edit_cell and len(self.grid.values) != 0:
            row, col = self.grid.edit_cell
            self.security.value = self.grid.values[row][0]
            self.security.display()
            self.field.value = self.grid.values[row][1]
            self.field.display()
            self.value.value = self.grid.values[row][2] or "None"
            self.value.display()
        eventlet.sleep()

    def onStart(self):
        self.keypress_timeout_default = 1
        F = self.addForm("MAIN", npyscreen.ActionForm, name = "Subscriptions")

        self.security = F.add(npyscreen.TitleFixedText, name = "Security", relx = 5, rely = 2)
        self.field = F.add(npyscreen.TitleFixedText, name = "Field", relx = 5, rely = 4)
        self.value = F.add(npyscreen.TitleText, name = "Value", relx = 5, rely = 6)
        self.grid = F.add(npyscreen.GridColTitles, relx = 5, rely = 10, col_titles = ['Security', 'Fields', 'Values'])

        F.edit()

def main(port = 6659):
    wireUpBlpapiImplementation(blpapi)

    app.client = client
    server = None
    try:
        try:
            app.sessionForRequests = openBloombergSession()
            app.sessionForSubscriptions = openBloombergSession()
            app.allSubscriptions = {}
        except:
            traceback.print_exc()
            if client is not None:
                client.captureException()
        pool = eventlet.GreenPool()
        pool.spawn(lambda: handleSubscriptions(app, socketio))
        my_logger = logging.getLogger('my-logger')
        my_logger.setLevel(logging.ERROR)
        pool.spawn(lambda: socketio.run(app, port = port, log = my_logger))
        pool.spawn(lambda: TestApp().run())
        pool.waitall()
    except KeyboardInterrupt:
        print("Ctrl+C received, exiting...")
    finally:
        if app.sessionForRequests is not None:
            app.sessionForRequests.stop()
        if app.sessionForSubscriptions is not None:
            app.sessionForSubscriptions.stop()
        if server is not None:
            server.socket.close()

if main_is_frozen():
    wireUpProductionDependencies()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--simulator', action='store_true',
                        help='simulate Bloomberg API (instead of using real connection)')
    parser.add_argument('--log', choices=['critical', 'error', 'warn', 'info', 'debug'],
                        help='log level')
    parser.add_argument('--port', type=int, default=6659,
                        help='port number (default: 6659)')

    args = parser.parse_args()

    if args.log is not None:
        logging.basicConfig(level=getattr(logging, args.log.upper(), None))

    if args.simulator:
        print("Using blpapi_simulator")
        wireUpDevelopmentDependencies()
    else:
        wireUpProductionDependencies()
    main(args.port)

