class SessionOptions:
    def setServerHost(self, host):
        pass

    def setServerPort(self, port):
        pass

class Request:
    def __init__(self, message):
        self.message = message

    def set(self, name, value):
        pass

    def append(self, name, value):
        pass

    def message(self):
        return self.message

class Service:
    def createRequest(self, serviceType):
        if serviceType == "ReferenceDataRequest":
            return Request(Message({
                "securityData": List([Map({
                    "security": "L Z7 Comdty",
                    "fieldData": Map({
                        "PX_LAST": "90"
                    })
                })])
            }))
        if serviceType == "HistoricalDataRequest":
            return Request(Message({
                "securityData": List([Map({
                    "security": "L Z7 Comdty",
                    "fieldData": List([
                        Map({
                            "date": "2006-01-31",
                            "PX_LAST": 90
                        }),
                        Map({
                            "date": "2006-02-01",
                            "PX_LAST": 90.05
                    })])
                })])
            }))

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
        self.responses = [Event([request.message])]

    def nextEvent(self, timeout):
        try:
            return self.responses[self.index]
        except IndexError:
            return None
        self.index += 1

