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

from bridge.bloomberg.session import Session
from bridge.bloomberg.sessionPool import SessionPool
from bridge.routes import latest, historical, intraday, subscribe, unsubscribe, dev
from bridge.routes.utils import allow_cors
from bridge.bloomberg.subscriptions import handle_subscriptions
from utils import main_is_frozen

VERSION = "3.0.2"
app = Flask(__name__)

app.url_map.strict_slashes = False

app.source = "bloomberg"
app.all_subscriptions = {}
app.bloomberg_hits = {}
app.session_pool_for_requests = SessionPool(2)
app.session_for_subscriptions = Session()

app.register_blueprint(latest.blueprint, url_prefix='/latest')
app.register_blueprint(historical.blueprint, url_prefix='/historical')
app.register_blueprint(intraday.blueprint, url_prefix='/intraday')
app.register_blueprint(subscribe.blueprint, url_prefix='/subscribe')
app.register_blueprint(unsubscribe.blueprint, url_prefix='/unsubscribe')
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")


@app.route('/status', methods=['OPTIONS'])
@app.route('/subscriptions', methods=['OPTIONS'])
@app.route('/latest', methods=['OPTIONS'])
@app.route('/historical', methods=['OPTIONS'])
@app.route('/intraday', methods=['OPTIONS'])
@app.route('/subscribe', methods=['OPTIONS'])
@app.route('/unsubscribe', methods=['OPTIONS'])
def tell_them_when_cors_is_allowed():
    response = Response("")
    response.headers['Access-Control-Allow-Origin'] = allow_cors(request.headers.get('Origin'))
    response.headers['Access-Control-Allow-Methods'] = ", ".join(["GET", "OPTIONS"])
    return response


@app.route('/status', methods=['GET'])
def status():
    if app.session_pool_for_requests.isHealthy() or app.session_for_subscriptions.is_healthy():
        _status = "UP"
    else:
        _status = "DOWN"
    response = Response(
        json.dumps({
            "source": app.source,
            "status": _status,
            "version": VERSION,
            "metrics": {
                "subscriptions": fn.reduce(lambda xs, x: xs + len(x[1]), app.all_subscriptions.items(), 0),
                "bloombergHits": app.bloomberg_hits
            }
        }).encode(),
        status=200,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allow_cors(request.headers.get('Origin'))
    return response


@app.route('/subscriptions', methods=['GET'])
def subscriptions():
    response = Response(
        json.dumps(app.all_subscriptions).encode(),
        status=200,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allow_cors(request.headers.get('Origin'))
    return response


def wire_up_blpapi_implementation(blpapi_impl):
    import bridge.bloomberg.session
    bridge.bloomberg.session.__dict__["blpapi"] = blpapi_impl
    subscribe.__dict__["blpapi"] = blpapi_impl
    from bridge.bloomberg import subscriptions
    subscriptions.__dict__["blpapi"] = blpapi_impl
    unsubscribe.__dict__["blpapi"] = blpapi_impl
    dev.__dict__["blpapi"] = blpapi_impl


def wire_up_development_dependencies():
    global blpapi
    blpapi = eventlet.import_patched("blpapi_simulator")
    app.register_blueprint(dev.blueprint, url_prefix='/dev')


def wire_up_production_dependencies():
    global blpapi
    import blpapi

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)


def main(port=6659):
    wire_up_blpapi_implementation(blpapi)

    server = None
    try:
        try:
            app.session_pool_for_requests.open()
            app.session_for_subscriptions.start()
            app.all_subscriptions = {}
        except:
            traceback.print_exc()
        socketio.start_background_task(lambda: handle_subscriptions(app, socketio))
        socketio.run(app, port=port)
    except KeyboardInterrupt:
        print("Ctrl+C received, exiting...")
    finally:
        app.session_pool_for_requests.stop()
        app.session_for_subscriptions.stop()
        if server is not None:
            server.socket.close()


if main_is_frozen():
    wire_up_production_dependencies()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--source',
                        help='impersonate different market data source')
    parser.add_argument('--simulator', action='store_true',
                        help='simulate Bloomberg API (instead of using real connection)')
    parser.add_argument('--log', choices=['critical', 'error', 'warn', 'info', 'debug'],
                        help='log level')
    parser.add_argument('--port', type=int, default=6659,
                        help='port number (default: 6659)')
    parser.add_argument('--no-ui', action='store_true',
                        help='hide console after starting (Windows only)')

    args = parser.parse_args()

    if args.source is not None:
        app.source = args.source

    if args.log is not None:
        logging.basicConfig(level=getattr(logging, args.log.upper(), None))

    if args.no_ui:
        import win32gui, win32console

        window = win32console.GetConsoleWindow()
        win32gui.ShowWindow(window, 0)

    if args.simulator:
        print("Using blpapi_simulator")
        wire_up_development_dependencies()
    else:
        wire_up_production_dependencies()
    main(args.port)
