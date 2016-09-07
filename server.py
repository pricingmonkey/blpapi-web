from http.server import BaseHTTPRequestHandler,HTTPServer
from urllib.parse import parse_qs,urlparse
import json
import blpapi
import traceback

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
        ev = session.nextEvent(500)
        for msg in ev:
            print("Message type: {}".format(msg.messageType()))
            if msg.messageType() == blpapi.Name("ReferenceDataResponse"):
                responses.append(msg)
        responseCompletelyReceived = ev.eventType() == blpapi.Event.RESPONSE
        if responseCompletelyReceived:
            break
    return responses

def extractReferenceSecurityPricing(message):
    result = []
    print("extractReferenceSecurityPricing input: {}".format(message))
    for securityInformation in list(message.getElement("securityData").values()):
        fields = {}
        for field in securityInformation.getElement("fieldData").elements():
            fields[str(field.name())] = field.getValue()
        result.append({
            "security": securityInformation.getElementValue("security"),
            "fields": fields
        })
    print("extractReferenceSecurityPricing output: {}".format(result))
    return result

def extractHistoricalSecurityPricing(message):
    result = []
    print("extractHistoricalSecurityPricing input: {}".format(message))
    for securityInformation in list(message.getElement("securityData").values()):
        results = []
        for field in securityInformation.getElement("fieldData").values():
            fieldName = None
            singleResult = {}
            for fieldElement in field.elements():
                if str(fieldElement.name()) == "date":
                    singleResult["date"].append(fieldElement.getValue())
                elif str(fieldElement.name()) == "relativeDate":
                    singleResult["relativeDate"].append(fieldElement.getValue())
                else: # assume it's the {fieldName -> fieldValue}
                    fieldName = str(fieldElement.name())
                    singleResult["value"].append(fieldElement.value())
            if not fieldName in results:
                results[fieldName] = []
            results[fieldName].append(singleResult)
        result.append({
            "security": securityInformation.getElementValue("security"),
            "values": results
        })
    print("extractHistoricalSecurityPricing output: {}".format(result))
    return result

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
    for securityInformation in list(message.getElement("securityData").values()):
        for fieldException in list(securityInformation.getElement("fieldException").values()):
            error = extractError(fieldException.getElement("errorInfo"))
            result.append("{}: {}".format(error, fieldException.getElementValue("fieldId")))
        if securityInformation.hasElement("securityError"):
            result.append(extractError(securityInformation.getElement("securityError")))
    print("extractErrors output: {}".format(result))
    return result

def requestLatest(securities, fields):
    session = None
    try:
        session = openBloombergSession()
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
    finally:
        if session is not None:
            session.stop()

def requestHistorical(securities, fields, startDate, endDate):
    session = None
    try:
        session = openBloombergSession()
        refDataService = openBloombergService(session, "//blp/refdata")
        request = refDataService.createRequest("HistoricalDataRequest")

        request.set("returnFormattedValue", True)
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
    finally:
        if session is not None:
            session.stop()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        # /latest?field=...&field=...&security=...&security=...
        if self.path.startswith("/latest"):
            try:
                securities = query.get('security') or []
                fields = query.get('field') or []
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write("{0}".format(e).encode())
                raise

            try:
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = requestLatest(securities, fields)
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write("{0}".format(e).encode())
                raise

        # /historical?fields=[...]&securities=[...]
        elif self.path.startswith("/historical"):
            try:
                securities = query.get('security') or []
                fields = query.get('field') or []
                startDate = query.get('startDate')
                endDate = query.get('endDate')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write("{0}".format(e).encode())
                raise

            session = None
            try:
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = requestHistorical(securities, fields, startDate, endDate)
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write("{0}".format(e).encode())
        else:
            self.send_response(404)
            self.end_headers()

def main():
    try:
        PORT_NUMBER = 6659
        server = HTTPServer(('localhost', PORT_NUMBER), handler)
        print("Server started on port {}".format(PORT_NUMBER))

        server.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down the web server')
    finally:
        server.socket.close()

if __name__ == "__main__":
    main()

