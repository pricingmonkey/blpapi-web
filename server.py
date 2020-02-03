import eventlet

# "import encodings.idna" is a fix for "unknown encoding: idna" error
# which we saw occurring's on a user's computer and crashing the app
# in result
import logging
import argparse

import json
import traceback
import functools as fn

from flask import Flask, Response, request
from flask_socketio import SocketIO

from bloomberg.session import Session
from bloomberg.bbcomm import startBbcommIfNecessary
from bloomberg.sessionPool import SessionPool
from routes import latest, historical, intraday, subscribe, unsubscribe, dev
from routes.utils import allowCORS
from bloomberg.subscriptions import handleSubscriptions
from utils import main_is_frozen

VERSION = "3.0.2"
app = Flask(__name__)

app.url_map.strict_slashes = False

app.allSubscriptions = {}
app.bloombergHits = {}
app.sessionPoolForRequests = SessionPool(2)
app.sessionForSubscriptions = Session()

app.register_blueprint(latest.blueprint, url_prefix='/latest')
app.register_blueprint(historical.blueprint, url_prefix='/historical')
app.register_blueprint(intraday.blueprint, url_prefix='/intraday')
app.register_blueprint(subscribe.blueprint, url_prefix='/subscribe')
app.register_blueprint(unsubscribe.blueprint, url_prefix='/unsubscribe')
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

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
    status = "UP" if app.sessionPoolForRequests.isHealthy() or app.sessionForSubscriptions.isHealthy() else "DOWN"
    response = Response(
        json.dumps({
            "source": "bloomberg",
            "status": status,
            "version": VERSION,
            "metrics": {
                "subscriptions": fn.reduce(lambda xs, x: xs + len(x[1]), app.allSubscriptions.items(), 0),
                "bloombergHits": app.bloombergHits
            }
        }).encode(),
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
    import bloomberg.session
    bloomberg.session.__dict__["blpapi"] = blpapi
    subscribe.__dict__["blpapi"] = blpapi
    from bloomberg import subscriptions
    subscriptions.__dict__["blpapi"] = blpapi
    unsubscribe.__dict__["blpapi"] = blpapi
    dev.__dict__["blpapi"] = blpapi


def wireUpDevelopmentDependencies():
    global blpapi
    blpapi = eventlet.import_patched("blpapi_simulator")
    app.register_blueprint(dev.blueprint, url_prefix='/dev')


def wireUpProductionDependencies():
    global blpapi
    import blpapi

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)
    # startBbcommIfNecessary()


def main(port = 6659):
    wireUpBlpapiImplementation(blpapi)

    server = None
    try:
        try:
            app.sessionPoolForRequests.open()
            app.sessionForSubscriptions.start()
            app.allSubscriptions = {}
        except:
            traceback.print_exc()
        socketio.start_background_task(lambda: handleSubscriptions(app, socketio))
        socketio.run(app, port=port)
    except KeyboardInterrupt:
        print("Ctrl+C received, exiting...")
    finally:
        app.sessionPoolForRequests.stop()
        app.sessionForSubscriptions.stop()
        if server is not None:
            server.socket.close()


if main_is_frozen():
    wireUpProductionDependencies()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--simulator', action='store_true',
                        help='simulate Bloomberg API (instead of using real connection)')
    parser.add_argument('--log', choices=['critical', 'error', 'warn', 'info', 'debug'],
                        help='log level')
    parser.add_argument('--port', type=int, default=6659,
                        help='port number (default: 6659)')
    parser.add_argument('--no-ui', action='store_true',
                        help='hide console after starting (Windows only)')

    args = parser.parse_args()

    if args.log is not None:
        logging.basicConfig(level=getattr(logging, args.log.upper(), None))

    if args.no_ui:
        import win32gui, win32console

        window = win32console.GetConsoleWindow()
        win32gui.ShowWindow(window, 0)

    if args.simulator:
        print("Using blpapi_simulator")
        wireUpDevelopmentDependencies()
    else:
        wireUpProductionDependencies()
    main(args.port)

