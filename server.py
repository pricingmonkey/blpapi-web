import eventlet
eventlet.monkey_patch()

import time
import imp, os, sys
import threading
import hashlib
from urllib.parse import parse_qs, urlparse
import json
import traceback

from flask import Flask, Response, request
from flask_socketio import emit, SocketIO

app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet")

class BrokenSessionException(Exception):
    pass

def main_is_frozen():
    return (hasattr(sys, "frozen") or # new py2exe
        hasattr(sys, "importers") # old py2exe
        or imp.is_frozen("__main__")) # tools/freeze

def get_main_dir():
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.realpath(__file__))

BLOOMBERG_HOST = "localhost"
BLOOMBERG_PORT = 8194

subscriptions = {}

class SubscriptionEventHandler(object):
    def getTimeStamp(self):
        return time.strftime("%Y/%m/%d %X")

    def processSubscriptionStatus(self, event):
        timeStamp = self.getTimeStamp()
        for msg in event:
            topic = msg.correlationIds()[0].value()
            print("(SUBSCRIPTION_STATUS) %s: %s - %s" % (timeStamp, topic, msg.messageType()))

    def processSubscriptionDataEvent(self, event):
        timeStamp = self.getTimeStamp()
        for msg in event:
            correlationId = msg.correlationIds()[0].value()
            pushMessage = {
                "type": "SUBSCRIPTION_DATA",
                "security": subscriptions[correlationId]["security"],
                "values": {str(each.name()): str(each.getValue()) for each in msg.asElement().elements() if each.numValues() > 0}
            }
            socketio.emit("action", pushMessage, namespace="/")
            socketio.sleep(0)

    def processMiscEvents(self, event):
        timeStamp = self.getTimeStamp()
        for msg in event:
            print("(MISC_EVENT) %s: %s" % (timeStamp, msg.messageType()))

    def processEvent(self, event, session):
        try:
            if event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
                return self.processSubscriptionDataEvent(event)
            elif event.eventType() == blpapi.Event.SUBSCRIPTION_STATUS:
                return self.processSubscriptionStatus(event)
            else:
                return self.processMiscEvents(event)
        except blpapi.Exception as e:
            traceback.print_exc()
            if client is not None:
                client.captureException()
        return False

def openBloombergSession(isAsync = False):
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost(BLOOMBERG_HOST)
    sessionOptions.setServerPort(BLOOMBERG_PORT)
    sessionOptions.setAutoRestartOnDisconnection(True)

    if isAsync:
        session = blpapi.Session(sessionOptions, SubscriptionEventHandler().processEvent)
    else:
        session = blpapi.Session(sessionOptions)

    if not session.start():
        raise Exception("Failed to start session on {}:{}".format(BLOOMBERG_HOST, BLOOMBERG_PORT))

    return session

def openBloombergService(session, serviceName):
    if not session.openService(serviceName):
        session.stop()
        session.start()
        if not session.openService(serviceName):
            raise BrokenSessionException("Failed to open {}".format(serviceName))

    return session.getService(serviceName)

def sendAndWait(session, request):
    session.sendRequest(request)
    responses = []
    while(True):
        # timeout to give a chance to Ctrl+C handling:
        ev = session.nextEvent(100)
        for msg in ev:
            if msg.messageType() == blpapi.Name("ReferenceDataResponse") or msg.messageType() == blpapi.Name("HistoricalDataResponse"):
                responses.append(msg)
        responseCompletelyReceived = ev.eventType() == blpapi.Event.RESPONSE
        if responseCompletelyReceived:
            break
    return responses

def extractReferenceSecurityPricing(message):
    result = []
    if message.hasElement("securityData"):
        for securityInformation in list(message.getElement("securityData").values()):
            fields = []
            for field in securityInformation.getElement("fieldData").elements():
                fields.append({
                    "name": str(field.name()),
                    "value": field.getValue()
                })
            result.append({
                "security": securityInformation.getElementValue("security"),
                "fields": fields
            })
    return result

def extractHistoricalSecurityPricing(message):
    resultsForDate = {}
    if message.hasElement("securityData"):
        securityInformation = message.getElement("securityData")
        security = securityInformation.getElementValue("security")
        for fieldsOnDate in list(securityInformation.getElement("fieldData").values()):
            fields = []
            for fieldElement in fieldsOnDate.elements():
                if str(fieldElement.name()) == "date":
                    date = fieldElement.getValueAsString()
                elif str(fieldElement.name()) == "relativeDate":
                    pass
                else: # assume it's the {fieldName -> fieldValue}
                    fields.append({
                        "name": str(fieldElement.name()),
                        "value": fieldElement.getValue()
                    })
            if not date in resultsForDate:
                resultsForDate[date] = {}
            if not security in resultsForDate[date]:
                resultsForDate[date][security] = []
            for field in fields:
                resultsForDate[date][security].append(field)

    result = []
    for date, securities in resultsForDate.items():
        valuesForSecurities = []
        for security, fields in securities.items():
            valuesForSecurities.append({
                "security": security,
                "fields": fields
            })
        result.append({
            "date": date,
            "values": valuesForSecurities
        })
    return sorted(result, key=lambda each: each["date"])

def extractError(errorElement):
    category = errorElement.getElementValue("category")
    subcategory = errorElement.getElementValue("subcategory")
    message = errorElement.getElementValue("message")
    return "{}/{} {}".format(category, subcategory, message)

def extractErrors(message):
    result = []
    if message.hasElement("responseError"):
        result.append(extractError(message.getElement("responseError")))
    if message.hasElement("securityData"):
        if message.getElement("securityData").isArray():
           securityData = list(message.getElement("securityData").values())
        else:
           securityData = list([message.getElement("securityData")])
        for securityInformation in securityData:
            if securityInformation.hasElement("fieldExceptions"):
                for fieldException in list(securityInformation.getElement("fieldExceptions").values()):
                    error = extractError(fieldException.getElement("errorInfo"))
                    result.append("{}: {}".format(error, fieldException.getElementValue("fieldId")))
            if securityInformation.hasElement("securityError"):
                error = extractError(securityInformation.getElement("securityError"))
                result.append("{}: {}".format(error, securityInformation.getElementValue("security")))
    return result

def requestLatest(session, securities, fields):
    try:
        refDataService = openBloombergService(session, "//blp/refdata")
        request = refDataService.createRequest("ReferenceDataRequest")

        request.set("returnFormattedValue", True)
        for security in securities:
            request.append("securities", security)

        for field in fields:
            request.append("fields", field)

        responses = sendAndWait(session, request)

        securityPricing = []
        for response in responses:
            securityPricing.extend(extractReferenceSecurityPricing(response))

        errors = []
        for response in responses:
            errors.extend(extractErrors(response))
        return { "response": securityPricing, "errors": errors }
    except Exception as e:
        raise

def requestHistorical(session, securities, fields, startDate, endDate):
    try:
        refDataService = openBloombergService(session, "//blp/refdata")
        request = refDataService.createRequest("HistoricalDataRequest")

        request.set("startDate", startDate)
        request.set("endDate", endDate)
        request.set("periodicitySelection", "DAILY");

        for security in securities:
            request.append("securities", security)

        for field in fields:
            request.append("fields", field)

        responses = sendAndWait(session, request)

        securityPricing = []
        for response in responses:
            securityPricing.extend(extractHistoricalSecurityPricing(response))

        errors = []
        for response in responses:
            errors.extend(extractErrors(response))

        return { "response": securityPricing, "errors": errors }
    except Exception as e:
        raise

def allowCORS(host):
    HOSTS = ["http://staging.pricingmonkey.com", "http://pricingmonkey.com", "http://localhost:8080"]
    if host in HOSTS:
        return host
    else:
        return "null"

def generateEtag(obj):
    sha1 = hashlib.sha1()
    sha1.update("{}".format(obj).encode())
    return '"{}"'.format(sha1.hexdigest())

@app.route('/latest', methods = ['OPTIONS'])
@app.route('/historical', methods = ['OPTIONS'])
@app.route('/subscribe', methods = ['OPTIONS'])
def tellThemWhenCORSIsAllowed():
    response = Response("")
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response

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

def handleBrokenSession(e):
    if isinstance(e, BrokenSessionException):
        if not app.sessionSync is None:
            app.sessionSync.stop()
            app.sessionSync = None
        if not app.sessionAsync is None:
            app.sessionAsync.stop()
            app.sessionAsync = None

@app.route('/subscribe', methods = ['GET'])
def subscribe():
    try:
        if app.sessionSync is None:
            app.sessionSync = openBloombergSession()
        if app.sessionAsync is None:
            app.sessionAsync = openBloombergSession(isAsync=True)
    except Exception as e:
        handleBrokenSession(e)
        if client is not None:
            client.captureException()
        return respond500(e)
    try:
        securities = request.args.getlist('security') or []
        fields = request.args.getlist('field') or []
        interval = request.args.get('interval') or "2.0"
    except Exception as e:
        if client is not None:
            client.captureException()
        return respond400(e)

    try:
        service = '//blp/mktdata'
        openBloombergService(app.sessionAsync, service)
        subscriptionList = blpapi.SubscriptionList()
        for security in securities:
            topic = service
            if not security.startswith("/"):
                topic += "/"
            topic += security
            correlationId = blpapi.CorrelationId(security)
            subscriptions[correlationId.value()] = { "security": security, "fields": fields }
            subscriptionList.add(topic, fields, "interval=" + interval, correlationId)

        app.sessionAsync.subscribe(subscriptionList)
        payload = json.dumps(requestLatest(app.sessionSync, securities, fields)).encode()
    except Exception as e:
        handleBrokenSession(e)
        if client is not None:
            client.captureException()
        return respond500(e)

    response = Response(
        payload,
        status=200,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response

# /latest?field=...&field=...&security=...&security=...
@app.route('/latest', methods = ['GET'])
def latest():
    try:
        if app.sessionSync is None:
            app.sessionSync = openBloombergSession()
        if app.sessionAsync is None:
            app.sessionAsync = openBloombergSession(isAsync=True)
    except Exception as e:
        handleBrokenSession(e)
        if client is not None:
            client.captureException()
        return respond500(e)
    try:
        securities = request.args.getlist('security') or []
        fields = request.args.getlist('field') or []
    except Exception as e:
        if client is not None:
            client.captureException()
        return respond400(e)

    try:
        payload = json.dumps(requestLatest(app.sessionSync, securities, fields)).encode()
    except Exception as e:
        handleBrokenSession(e)
        if client is not None:
            client.captureException()
        return respond500(e)

    response = Response(
        payload,
        status=200,
        mimetype='application/json')
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response

# /historical?fields=[...]&securities=[...]
@app.route('/historical', methods = ['GET'])
def historical():
    try:
        if app.sessionSync is None:
            app.sessionSync = openBloombergSession()
        if app.sessionAsync is None:
            app.sessionAsync = openBloombergSession(isAsync=True)
    except Exception as e:
        handleBrokenSession(e)
        if client is not None:
            client.captureException()
        return respond500(e)
    try:
        securities = request.args.getlist('security') or []
        fields = request.args.getlist('field') or []
        startDate = request.args.get('startDate')
        endDate = request.args.get('endDate')
    except Exception as e:
        if client is not None:
            client.captureException()
        return respond400(e)

    etag = generateEtag({
        "securities": securities,
        "fields": fields,
        "startDate": startDate,
        "endDate": endDate
    })
    if request.headers.get('If-None-Match') == etag:
        response = Response(
            "",
            status=304,
            mimetype='application/json')
        response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
        return response
    try:
        payload = json.dumps(requestHistorical(app.sessionSync, securities, fields, startDate, endDate)).encode()
    except Exception as e:
        handleBrokenSession(e)
        if client is not None:
            client.captureException()
        return respond500(e)

    response = Response(
        payload,
        status=200,
        mimetype='application/json')
    response.headers['Etag'] = etag
    response.headers['Cache-Control'] = "max-age=86400, must-revalidate"
    response.headers['Vary'] = "Origin"
    response.headers['Access-Control-Allow-Origin'] = allowCORS(request.headers.get('Origin'))
    return response

def wireUpProductionDependencies():
    global blpapi
    global client
    import blpapi

    from raven.transport.threaded_requests import ThreadedRequestsHTTPTransport
    from raven import Client
    client = Client("https://ec16b2b639e642e49c59e922d2c7dc9b:2dd38313e1d44fd2bc2adb5a510639fc@sentry.io/100358?ca_certs={}/certifi/cacert.pem".format(get_main_dir()))

def main():
    app.sessionSync = None
    app.sessionAsync = None
    server = None
    try:
        if len(sys.argv) >= 3 and sys.argv[2].isdigit():
            PORT_NUMBER = sys.argv[2]
        else:
            PORT_NUMBER = 6659
        try:
            app.sessionSync = openBloombergSession()
            app.sessionAsync = openBloombergSession(isAsync=True)
        except:
            if client is not None:
                client.captureException()
            pass
        socketio.run(app, port = PORT_NUMBER)
    except KeyboardInterrupt:
        print("Ctrl+C received, exiting...")
    finally:
        if app.sessionSync is not None:
            app.sessionSync.stop()
        if app.sessionAsync is not None:
            app.sessionAsync.stop()
        if server is not None:
            server.socket.close()

if main_is_frozen():
    wireUpProductionDependencies()

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "simulator":
        print("Using blpapi_simulator")
        import blpapi_simulator as blpapi
        client = None
    else:
        wireUpProductionDependencies()
    main()

