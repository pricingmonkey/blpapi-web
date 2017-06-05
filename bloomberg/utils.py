import os
import psutil
import subprocess
import traceback
import datetime

BLOOMBERG_HOST = "localhost"
BLOOMBERG_PORT = 8194

class BrokenSessionException(Exception):
    pass

def openBloombergSession():
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost(BLOOMBERG_HOST)
    sessionOptions.setServerPort(BLOOMBERG_PORT)
    sessionOptions.setAutoRestartOnDisconnection(True)

    session = blpapi.Session(sessionOptions)

    if not session.start():
        raise BrokenSessionException("Failed to start session on {}:{}".format(BLOOMBERG_HOST, BLOOMBERG_PORT))

    return session

def openBloombergService(session, serviceName):
    try:
        sessionRestarted = False
        if not session.openService(serviceName):
            sessionRestarted = True
            session.stop()
            session.start()
            if not session.openService(serviceName):
                raise BrokenSessionException("Failed to open {}".format(serviceName))

        return session.getService(serviceName), sessionRestarted
    except Exception as e:
        raise BrokenSessionException("Failed to open {}".format(serviceName)) from e

def sendAndWait(session, request):
    eventQueue=blpapi.EventQueue()
    session.sendRequest(request, eventQueue=eventQueue)
    responses = []
    while(True):
        ev = eventQueue.nextEvent(100)
        if ev.eventType() == blpapi.Event.TIMEOUT:
            continue

        for msg in ev:
            if msg.messageType() == blpapi.Name("ReferenceDataResponse") or msg.messageType() == blpapi.Name("HistoricalDataResponse") or msg.messageType() == blpapi.Name("IntradayBarResponse"):
                responses.append(msg)
        responseCompletelyReceived = ev.eventType() == blpapi.Event.RESPONSE
        if responseCompletelyReceived:
            break
    return responses

BBCOMM_LAST_RESTARTED_AT = None
def restartBbcomm(raven):
    # debounce restarting for a few seconds, to allow bbcomm to fully initialise
    if BBCOMM_LAST_RESTARTED_AT and (datetime.datetime.now() - BBCOMM_LAST_RESTARTED_AT).total_seconds() < 10:
        return
    BBCOMM_LAST_RESTARTED_AT = datetime.datetime.now()
    try:
        os.system("taskkill /im bbcomm.exe /f")
        startBbcomm()
    except Exception:
        if raven is not None:
            raven.captureException()
        else:
            traceback.print_exc()

def startBbcomm():
    CREATE_NEW_CONSOLE = 0x00000010

    try:
        info = subprocess.STARTUPINFO()
        info.dwFlags = 1
        info.wShowWindow = 0
        subprocess.Popen(["c:/blp/api/bbcomm.exe"],
                        creationflags=CREATE_NEW_CONSOLE,
                        startupinfo=info)
    except FileNotFoundError:
        try:
            info = subprocess.STARTUPINFO()
            info.dwFlags = 1
            info.wShowWindow = 0
            subprocess.Popen(["c:/blp/dapi/bbcomm.exe"],
                            creationflags=CREATE_NEW_CONSOLE,
                            startupinfo=info)
        except FileNotFoundError:
            pass

def startBbcommIfNecessary(raven):
    try:
        bbcomm = next((proc for proc in psutil.process_iter() if proc.name() == "bbcomm.exe"), None)

        if not bbcomm:
            startBbcomm()
    except Exception:
        if raven is not None:
            raven.captureException()
        else:
            traceback.print_exc()
