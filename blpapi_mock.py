import random
from datetime import datetime, timedelta

def merge_dicts(d1, d2):
    out = d1.copy()
    out.update(d2)
    return out

class SessionOptions:
    def setServerHost(self, host):
        pass

    def setServerPort(self, port):
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

    def message(self):
        if self.serviceType == "ReferenceDataRequest":
            return Message({
                "securityData": List([Map({
                    "security": security,
                    "fieldData": Map({
                        field:  str(90 + (0.5 - random.random()))
                    for field in self.params["fields"]})
                }) for security in self.params["securities"]])
            })
        if self.serviceType == "HistoricalDataRequest":
            return Message({
                "securityData": List([Map({
                    "security": security,
                    "fieldData": List([
                        Map(merge_dicts(
                            { "date": (datetime.strptime("20160917", "%Y%m%d") + timedelta(days=i)).strftime("%Y-%m-%d")},
                            { field: str(90 + (0.5 - random.random())) for field in self.params["fields"] }
                        )) for i in range(365)])
                    }) for security in self.params["securities"]])
                })

class Service:
    def createRequest(self, serviceType):
        return Request(serviceType)

def Name(name):
    return name

class Event:
    RESPONSE = "RESPONSE"
    def __init__(self, messages):
        self.messages = messages
        self.index = 0

    def eventType(self):
        return Event.RESPONSE

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

    def __init__(self, value):
        self.value = value

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
    def __init__(self, value):
        self.value = value

    def messageType(self):
        return Name("ReferenceDataResponse")

    def __str__(self):
        return "Message({})".format(str(self.value))

    def __repr__(self):
        return self.__str__()

class Session:
    def __init__(self, sessionOptions):
        self.responses = []
        self.index = 0

    def start(self):
        return True

    def stop(self):
        pass

    def openService(self, serviceName):
        return True

    def getService(self, serviceName):
        return Service()

    def sendRequest(self, request):
        self.responses = [Event([request.message()])]

    def nextEvent(self, timeout):
        try:
            return self.responses[self.index]
        except IndexError:
            return None
        self.index += 1

