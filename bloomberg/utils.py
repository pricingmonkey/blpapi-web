BLOOMBERG_HOST = "localhost"
BLOOMBERG_PORT = 8194

def openBloombergSession():
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost(BLOOMBERG_HOST)
    sessionOptions.setServerPort(BLOOMBERG_PORT)
    sessionOptions.setAutoRestartOnDisconnection(True)

    session = blpapi.Session(sessionOptions)

    if not session.start():
        raise Exception("Failed to start session on {}:{}".format(BLOOMBERG_HOST, BLOOMBERG_PORT))

    return session

def openBloombergService(session, serviceName):
    sessionRestarted = False
    if not session.openService(serviceName):
        sessionRestarted = True
        session.stop()
        session.start()
        if not session.openService(serviceName):
            raise BrokenSessionException("Failed to open {}".format(serviceName))

    return session.getService(serviceName), sessionRestarted

def sendAndWait(session, request):
    eventQueue=blpapi.EventQueue()
    session.sendRequest(request, eventQueue=eventQueue)
    responses = []
    while(True):
        ev = eventQueue.nextEvent(100)
        if ev.eventType() == blpapi.Event.TIMEOUT:
            continue

        for msg in ev:
            if msg.messageType() == blpapi.Name("ReferenceDataResponse") or msg.messageType() == blpapi.Name("HistoricalDataResponse"):
                responses.append(msg)
        responseCompletelyReceived = ev.eventType() == blpapi.Event.RESPONSE
        if responseCompletelyReceived:
            break
    return responses


