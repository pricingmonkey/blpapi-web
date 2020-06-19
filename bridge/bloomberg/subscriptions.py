import traceback

from utils import handleBrokenSession

def extractFieldValues(message, fields):
    d = {}
    for each in message.asElement().elements():
        if each.numValues() > 0:
            try:
                fieldName = str(each.name())
                if fieldName in fields:
                    d[fieldName] = each.getValueAsString()
            except Exception as e:
                traceback.print_exc()
    return d

class SubscriptionEventHandler(object):
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio

    def processSubscriptionStatus(self, event):
        for msg in event:
            security = msg.correlationIds()[0].value()
            if msg.messageType() == "SubscriptionFailure":
                if security in self.app.allSubscriptions:
                    del self.app.allSubscriptions[security]
                print("SubscriptionFailure: " + str({ 'security': security, 'description': str(msg) }))
        return True

    def processSubscriptionDataEvent(self, event):
        messages = []
        for msg in event:
            security = msg.correlationIds()[0].value()
            fields = self.app.allSubscriptions[security]
            messages.append({
                "type": "SUBSCRIPTION_DATA",
                "security": security,
                "values": extractFieldValues(msg, fields)
            })
            if len(messages) > 10:
                self.socketio.emit("action", messages, namespace="/")
                self.socketio.sleep(5 / 1000)
                messages = []
        if len(messages):
            self.socketio.emit("action", messages, namespace="/")
            self.socketio.sleep(5 / 1000)
        return True

    def processEvent(self, event):
        try:
            if event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
                return self.processSubscriptionDataEvent(event)
            elif event.eventType() == blpapi.Event.SUBSCRIPTION_STATUS:
                return self.processSubscriptionStatus(event)
            else:
                return True
        except blpapi.Exception as e:
            traceback.print_exc()
        return False

def handleSubscriptions(app, socketio):
    eventHandler = SubscriptionEventHandler(app, socketio)
    while True:
        try:
            if not app.sessionForSubscriptions.isStarted():
                app.sessionForSubscriptions.start()
                app.allSubscriptions = {}

            event = app.sessionForSubscriptions.nextEvent(50)
            eventHandler.processEvent(event)
        except Exception as e:
            traceback.print_exc()
            handleBrokenSession(app)
            socketio.sleep(1)
        finally:
            socketio.sleep()
