import random
import time
from datetime import datetime, timedelta
import threading

def merge_dicts(d1, d2):
    out = d1.copy()
    out.update(d2)
    return out

def randomFieldValue(field, security = "RXH7 COMDTY"):
    if field == "FUT_CTD_CPN":
        return "1.000"
    elif field == "FUT_CTD_MTY":
        return "08/15/2025"
    elif field == "FUT_CTD_FREQ":
        return "A"
    elif field == "FUT_DLV_DT_LAST":
        return "12/12/2016"
    elif field == "FUT_CNVS_FACTOR":
        return ".669312"
    elif len(security) < 12:
        return str(99 + (0.05 * random.random()))
    else:
        return str(0.14 + (0.05 * random.random()))

class SessionOptions:
    def setServerHost(self, host):
        pass

    def setServerPort(self, port):
        pass

    def setAutoRestartOnDisconnection(self, enabled):
        pass

class Request:
    def __init__(self, serviceType):
        self.params = {}
        self.serviceType = serviceType

    def set(self, name, value):
        self.params[name] = value

    def append(self, name, value):
        if not name in self.params:
            self.params[name] = []
        self.params[name].append(value)

    def __isWeekday(self, date):
        return date.isoweekday() <= 5

    def messages(self):
        if self.serviceType == "ReferenceDataRequest":
            time.sleep(random.randint(2, 6) / 10)
            correctSecurities, incorrectSecurities = [], []

            for s in self.params["securities"]:
                if s.endswith("ERR"):
                    incorrectSecurities.append(s)
                else:
                    correctSecurities.append(s)
            return [Message({
                "securityData": List([Map({
                    "security": security,
                    "fieldData": Map({
                        field: randomFieldValue(field, security)
                    for field in self.params["fields"]})
                }) for security in correctSecurities] + [
                    Map({
                        "security": security,
                        "fieldData": Map({}),
                        "fieldExceptions": List([Map({
                                "errorInfo": Map({
                                    "category": "CAT",
                                    "subcategory": "SUBCAT",
                                    "message": "MSG"
                                }),
                                "fieldId": "FIELD_ID",
                                "message": "MESSAGE"
                        })])
                }) for security in incorrectSecurities]
            )})]
        if self.serviceType == "HistoricalDataRequest":
            time.sleep(random.randint(4, 8) / 10)
            startDate = datetime.strptime(self.params["startDate"], "%Y%m%d").date()
            endDate = datetime.strptime(self.params["endDate"], "%Y%m%d").date()
            return [Message({
                "securityData": Map({
                    "security": security,
                    "fieldData": List([
                        Map(merge_dicts(
                            { "date": date},
                            { field: randomFieldValue(field, security) for field in self.params["fields"] }
                        )) for date in [startDate + timedelta(days=i) for i in range((endDate - startDate).days + 1)] if self.__isWeekday(date)])
                    })
                }) for security in self.params["securities"]]

class Service:
    def createRequest(self, serviceType):
        return Request(serviceType)

def Name(name):
    return name

class Event:
    RESPONSE = "RESPONSE"
    SUBSCRIPTION_DATA = "SUBSCRIPTION_DATA"
    SUBSCRIPTION_STATUS = "SUBSCRIPTION_STATUS"

    def __init__(self, messages, eventType=RESPONSE):
        self.messages = messages
        self.index = 0
        self._eventType = eventType

    def eventType(self):
        return self._eventType

    def __iter__(self):
        return self

    def __next__(self):
        try:
            message = self.messages[self.index]
            self.index += 1
            return message
        except IndexError:
            raise StopIteration

    def __str__(self):
        return "Map({})".format(str(self.messages))

    def __repr__(self):
        return self.__str__()

class List:
    def __init__(self, items):
        self.items = items

    def isArray(self):
        return True

    def values(self):
        return self.items

    def __str__(self):
        return "List({})".format(str(self.items))

    def __repr__(self):
        return self.__str__()

class Map:
    class Entry:
        def __init__(self, key, value):
            self.key = key
            self.value = value

        def name(self):
            return self.key

        def getValue(self):
            return self.value

        def getValueAsString(self):
            return str(self.value)

    def __init__(self, value):
        self.value = value

    def isArray(self):
        return False

    def hasElement(self, name):
        return name in self.value

    def getElement(self, name):
        return self.value[name]

    def getElementValue(self, name):
        return self.value[name]

    def elements(self):
        return [Map.Entry(k, v) for k, v in self.value.items()]

    def __str__(self):
        return "Map({})".format(str(self.value))

    def __repr__(self):
        return self.__str__()

class Message(Map):
    def __init__(self, value, correlationId=None):
        self.value = value
        self._correlationId = correlationId

    def messageType(self):
        return Name("ReferenceDataResponse")

    def correlationIds(self):
        return [self._correlationId]

    def asElement(self):
        return Map(self.value)

    def __str__(self):
        return "Message({})".format(str(self.value))

    def __repr__(self):
        return self.__str__()

class Session:
    def __init__(self, sessionOptions, processEvent=None):
        self.responses = []
        self.index = 0
        self.processEvent = processEvent

    def start(self):
        return True

    def stop(self):
        pass

    def openService(self, serviceName):
        return True

    def getService(self, serviceName):
        return Service()

    def sendRequest(self, request):
        self.responses = [Event(request.messages())]

    def subscribe(self, subscriptionList):
        def tick():
           while True:
              time.sleep(0.3 + 0.5 * random.random())
              self.processEvent(Event([subscriptionList.messages()], Event.SUBSCRIPTION_DATA), self)
        threading.Thread(target=tick).start()

    def nextEvent(self, timeout):
        try:
            return self.responses[self.index]
        except IndexError:
            return None
        self.index += 1

class SubscriptionList:
    def add(self, topic, fields, extra, correlationId):
        self.fields = fields
        self.correlationId = correlationId

    def messages(self):
        return Message(
            {field: randomFieldValue(field) for field in self.fields},
            self.correlationId)

class CorrelationId():
    def __init__(self, string):
        self._value = hash(string)

    def value(self):
        return self._value

class Exception(BaseException):
    pass
