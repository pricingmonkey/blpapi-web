import eventlet

BLOOMBERG_HOST = "localhost"
BLOOMBERG_PORT = 8194

class BrokenSessionException(Exception):
    pass

class Session:
    def __init__(self):
        self.sessionImpl = None

    def isStarted(self):
        return self.sessionImpl is not None

    def start(self):
        if self.isStarted():
            return

        sessionOptions = blpapi.SessionOptions()
        sessionOptions.setServerHost(BLOOMBERG_HOST)
        sessionOptions.setServerPort(BLOOMBERG_PORT)
        sessionOptions.setAutoRestartOnDisconnection(True)

        self.sessionImpl = blpapi.Session(sessionOptions)

        if not self.sessionImpl.start():
            raise BrokenSessionException("Failed to start session on {}:{}".format(BLOOMBERG_HOST, BLOOMBERG_PORT))

        return

    def stop(self):
        try:
            if self.isStarted():
                self.sessionImpl.stop()
        finally:
            self.reset()

    def reset(self):
        self.sessionImpl = None

    def _getOrOpenService(self, serviceName):
        try:
            return self.sessionImpl.getService(serviceName), True
        except Exception as e:
            opened = self.sessionImpl.openService(serviceName)
            return self.sessionImpl.getService(serviceName), opened

    def getService(self, serviceName):
        if not self.isStarted():
            self.start()

        try:
            sessionRestarted = False
            service, opened = self._getOrOpenService(serviceName)
            if not opened:
                sessionRestarted = True
                self.sessionImpl.stop()
                self.sessionImpl.start()
                if not self.sessionImpl.openService(serviceName):
                    raise BrokenSessionException("Failed to open {}".format(serviceName))

            return service, sessionRestarted
        except Exception as e:
            raise BrokenSessionException("Failed to open {}".format(serviceName)) from e

    def sendAndWait(self, request):
        if not self.isStarted():
            self.start()

        eventQueue=blpapi.EventQueue()
        self.sessionImpl.sendRequest(request, eventQueue=eventQueue)
        responses = []
        while True:
            ev = eventQueue.tryNextEvent()
            if not ev:
                eventlet.sleep(25 / 1000)
                continue

            for msg in ev:
                if msg.messageType() == blpapi.Name("ReferenceDataResponse") or msg.messageType() == blpapi.Name("HistoricalDataResponse") or msg.messageType() == blpapi.Name("IntradayBarResponse"):
                    responses.append(msg)

            responseCompletelyReceived = ev.eventType() == blpapi.Event.RESPONSE
            if responseCompletelyReceived:
                break
        return responses

    def nextEvent(self, timeout):
        return self.sessionImpl.nextEvent(timeout)

    def subscribe(self, subscriptionList):
        return self.sessionImpl.subscribe(subscriptionList)

    def resubscribe(self, subscriptionList):
        return self.sessionImpl.resubscribe(subscriptionList)

    def unsubscribe(self, subscriptionList):
        return self.sessionImpl.unsubscribe(subscriptionList)
