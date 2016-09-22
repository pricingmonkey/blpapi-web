import imp, os, sys
from http.server import BaseHTTPRequestHandler,HTTPServer
import threading
import hashlib
from urllib.parse import parse_qs,urlparse
import json
import traceback

def main_is_frozen():
   return (hasattr(sys, "frozen") or # new py2exe
           hasattr(sys, "importers") # old py2exe
           or imp.is_frozen("__main__")) # tools/freeze

def get_main_dir():
   if main_is_frozen():
       return os.path.dirname(sys.executable)
   return os.path.dirname(os.path.realpath(__file__))

from raven.transport.threaded_requests import ThreadedRequestsHTTPTransport
from raven import Client
client = Client("https://ec16b2b639e642e49c59e922d2c7dc9b:2dd38313e1d44fd2bc2adb5a510639fc@sentry.io/100358?ca_certs={}/certifi/cacert.pem".format(get_main_dir()))

BLOOMBERG_HOST = "localhost"
BLOOMBERG_PORT = 8194

def openBloombergSession():
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost(BLOOMBERG_HOST)
    sessionOptions.setServerPort(BLOOMBERG_PORT)

    session = blpapi.Session(sessionOptions)

    if not session.start():
        raise Exception("Failed to start session on {}:{}".format(BLOOMBERG_HOST, BLOOMBERG_PORT))

    return session

def openBloombergService(session, serviceName):
    if not session.openService(serviceName):
        raise Exception("Failed to open {}".format(serviceName))

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
    print("extractHistoricalSecurityPricing input: {}".format(message))

    resultsForDate = {}
    if message.hasElement("securityData"): 
        for securityInformation in list(message.getElement("securityData").values()):
            security = securityInformation.getElementValue("security")
            for fieldsOnDate in securityInformation.getElement("fieldData").values():
                fields = []
                for fieldElement in fieldsOnDate.elements():
                    if str(fieldElement.name()) == "date":
                        date = fieldElement.getValue()
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

    print("extractHistoricalSecurityPricing preprocessed: {}".format(resultsForDate))

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
    print("extractHistoricalSecurityPricing output: {}".format(result))
    return sorted(result, key=lambda each: each["date"])

def extractError(errorElement):
    category = errorElement.getElementValue("category")
    subcategory = errorElement.getElementValue("subcategory")
    message = errorElement.getElementValue("message")
    return "{}/{} {}".format(category, subcategory, message)

def extractErrors(message):
    result = []
    print("extractErrors input: {}".format(message))
    if message.hasElement("responseError"): 
        result.append(extractError(message.getElement("responseError")))
    if message.hasElement("securityData"): 
        for securityInformation in list(message.getElement("securityData").values()):
            if securityInformation.hasElement("fieldExceptions"):
                for fieldException in list(securityInformation.getElement("fieldExceptions").values()):
                    error = extractError(fieldException.getElement("errorInfo"))
                    result.append("{}: {}".format(error, fieldException.getElementValue("fieldId")))
            if securityInformation.hasElement("securityError"):
                error = extractError(securityInformation.getElement("securityError"))
                result.append("{}: {}".format(error, securityInformation.getElementValue("security")))
    print("extractErrors output: {}".format(result))
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
    HOSTS = ["http://pricingmonkey.com", "http://localhost:8080"]
    if host in HOSTS:
        return host
    else:
        return "null"

def generateEtag(obj):
    sha1 = hashlib.sha1()
    sha1.update("{}".format(obj).encode())
    return '"{}"'.format(sha1.hexdigest())

class handler(BaseHTTPRequestHandler):
    session = None
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", allowCORS(self.headers.get('Origin')))
        self.end_headers()
        self.wfile.write("".encode())

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        # /latest?field=...&field=...&security=...&security=...
        if self.path.startswith("/latest"):
            try:
                securities = query.get('security') or []
                fields = query.get('field') or []
            except Exception as e:
                client.captureException()
                self.send_response(400)
                self.send_header("Access-Control-Allow-Origin", allowCORS(self.headers.get('Origin')))
                self.end_headers()
                self.wfile.write("{0}".format(e).encode())
                raise

            try:
                response = requestLatest(self.session, securities, fields)
            except Exception as e:
                client.captureException()
                self.send_response(500)
                self.send_header("Access-Control-Allow-Origin", allowCORS(self.headers.get('Origin')))
                self.end_headers()
                self.wfile.write("{0}".format(e).encode())
                raise

            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", allowCORS(self.headers.get('Origin')))
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        # /historical?fields=[...]&securities=[...]
        elif self.path.startswith("/historical"):
            try:
                securities = query.get('security') or []
                fields = query.get('field') or []
                startDate = query.get('startDate')
                if startDate is not None:
                    startDate = startDate[0]
                endDate = query.get('endDate')
                if endDate is not None:
                    endDate = endDate[0]
            except Exception as e:
                client.captureException()
                self.send_response(400)
                self.send_header("Access-Control-Allow-Origin", allowCORS(self.headers.get('Origin')))
                self.end_headers()
                self.wfile.write("{0}".format(e).encode())
                raise

            etag = generateEtag({
                "securities": securities,
                "fields": fields,
                "startDate": startDate,
                "endDate": endDate
            })
            if self.headers.get('If-None-Match') == etag:
                self.send_response(304)
                self.send_header("Access-Control-Allow-Origin", allowCORS(self.headers.get('Origin')))
                self.end_headers()
                return

            try:
                response = requestHistorical(self.session, securities, fields, startDate, endDate)
            except Exception as e:
                client.captureException()
                self.send_response(500)
                self.send_header("Access-Control-Allow-Origin", allowCORS(self.headers.get('Origin')))
                self.end_headers()
                self.wfile.write("{0}".format(e).encode())
                raise

            self.send_response(200)
            self.send_header('Etag', etag)
            self.send_header('Cache-Control', "max-age=86400, must-revalidate")
            self.send_header("Vary", "Origin")
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", allowCORS(self.headers.get('Origin')))
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header("Access-Control-Allow-Origin", allowCORS(self.headers.get('Origin')))
            self.end_headers()

def main():
    session = None
    try:
        PORT_NUMBER = 6659
        handler.session = openBloombergSession()
        server = HTTPServer(('localhost', PORT_NUMBER), handler)
        print("Server started on port {}".format(PORT_NUMBER))

        server.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down the web server')
    finally:
        if session is not None:
            session.stop()
        server.socket.close()

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "mock":
        print("Using blpapi_mock")
        import blpapi_mock as blpapi
    else:
        import blpapi
    main()

