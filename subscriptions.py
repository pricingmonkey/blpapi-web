import eventlet
import traceback
import time

from bloomberg.utils import openBloombergSession
from utils import handleBrokenSession

def extractFieldValues(message):
    d = {}
    for each in message.asElement().elements():
        if each.numValues() > 0:
            try:
                d[str(each.name())] = each.getValueAsString()
            except Exception as e:
                if self.app.client is not None:
                    self.app.client.captureException()
    return d

class SubscriptionEventHandler(object):
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio

    def getTimeStamp(self):
        return time.strftime("%Y/%m/%d %X")

    def processSubscriptionStatus(self, event):
        timeStamp = self.getTimeStamp()
        for msg in event:
            security = msg.correlationIds()[0].value()
            if msg.messageType() == "SubscriptionFailure":
                if security in self.app.allSubscriptions:
                    del self.app.allSubscriptions[security]
                if self.app.client is not None:
                    self.app.client.captureMessage(str({"security": security, "message": str(msg)}))
        return True

    def processSubscriptionDataEvent(self, event):
        timeStamp = self.getTimeStamp()
        for msg in event:
            security = msg.correlationIds()[0].value()
            pushMessage = {
                "type": "SUBSCRIPTION_DATA",
                "security": security,
                "values": extractFieldValues(msg)
            }
            self.app.latestSubscriptionValues[security] = extractFieldValues(msg)
            self.socketio.emit("action", pushMessage, namespace="/")
            self.socketio.sleep(0)
        return True

    def processEvent(self, event, session):
        try:
            if event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
                return self.processSubscriptionDataEvent(event)
            elif event.eventType() == blpapi.Event.SUBSCRIPTION_STATUS:
                return self.processSubscriptionStatus(event)
            else:
                return True
        except blpapi.Exception as e:
            traceback.print_exc()
            if self.app.client is not None:
                self.app.client.captureException()
        return False

def handleSubscriptions(app, socketio):
    eventHandler = SubscriptionEventHandler(app, socketio)
    while True:
        try:
            if app.sessionForSubscriptions is None:
                app.sessionForSubscriptions = openBloombergSession()
                app.allSubscriptions = {}

            event = app.sessionForSubscriptions.nextEvent(500)
            eventHandler.processEvent(event, app.sessionForSubscriptions)
        except Exception as e:
            traceback.print_exc()
            handleBrokenSession(app, e)
            if app.client is not None:
                app.client.captureException()
            eventlet.sleep(1)
        finally:
            eventlet.sleep()

