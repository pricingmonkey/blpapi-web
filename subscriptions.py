import eventlet
import traceback

from flask import current_app as app

from utils import handleBrokenSession

class SubscriptionEventHandler(object):
    def getTimeStamp(self):
        return time.strftime("%Y/%m/%d %X")

    def processSubscriptionStatus(self, event):
        timeStamp = self.getTimeStamp()
        for msg in event:
            security = msg.correlationIds()[0].value()
            if msg.messageType() == "SubscriptionFailure":
                if security in app.allSubscriptions:
                    del app.allSubscriptions[security]
                if app.client is not None:
                    app.client.captureMessage(str({"security": security, "message": str(msg)}))
        return True

    def processSubscriptionDataEvent(self, event):
        timeStamp = self.getTimeStamp()
        for msg in event:
            security = msg.correlationIds()[0].value()
            pushMessage = {
                "type": "SUBSCRIPTION_DATA",
                "security": security,
                "values": {str(each.name()): str(each.getValue()) for each in msg.asElement().elements() if each.numValues() > 0}
            }
            socketio.emit("action", pushMessage, namespace="/")
            socketio.sleep(0)
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
            if app.client is not None:
                app.client.captureException()
        return False

def handleSubscriptions():
    with app.app_context():
        eventHandler = SubscriptionEventHandler()
        while True:
            try:
                if app.sessionForSubscriptions is None:
                    app.sessionForSubscriptions = openBloombergSession()
                    app.allSubscriptions = {}

                event = app.sessionForSubscriptions.nextEvent(500)
                eventHandler.processEvent(event, app.sessionForSubscriptions)
            except Exception as e:
                traceback.print_exc()
                handleBrokenSession(e)
                if app.client is not None:
                    app.client.captureException()
                eventlet.sleep(1)
            finally:
                eventlet.sleep()

