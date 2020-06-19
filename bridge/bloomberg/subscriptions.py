import traceback

from utils import handle_broken_session


def extract_field_values(message, fields):
    d = {}
    for each in message.asElement().elements():
        if each.numValues() > 0:
            try:
                field_name = str(each.name())
                if field_name in fields:
                    d[field_name] = each.getValueAsString()
            except Exception:
                traceback.print_exc()
    return d


class SubscriptionEventHandler(object):
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio

    def process_subscription_status(self, event):
        for msg in event:
            security = msg.correlationIds()[0].value()
            if msg.messageType() == "SubscriptionFailure":
                if security in self.app.all_subscriptions:
                    del self.app.all_subscriptions[security]
                print("SubscriptionFailure: " + str({'security': security, 'description': str(msg)}))
        return True

    def process_subscription_data_event(self, event):
        messages = []
        for msg in event:
            security = msg.correlationIds()[0].value()
            fields = self.app.all_subscriptions[security]
            messages.append({
                "type": "SUBSCRIPTION_DATA",
                "security": security,
                "values": extract_field_values(msg, fields)
            })
            if len(messages) > 10:
                self.socketio.emit("action", messages, namespace="/")
                self.socketio.sleep(5 / 1000)
                messages = []
        if len(messages):
            self.socketio.emit("action", messages, namespace="/")
            self.socketio.sleep(5 / 1000)
        return True

    def process_event(self, event):
        try:
            if event.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
                return self.process_subscription_data_event(event)
            elif event.eventType() == blpapi.Event.SUBSCRIPTION_STATUS:
                return self.process_subscription_status(event)
            else:
                return True
        except blpapi.Exception as e:
            traceback.print_exc()
        return False


def handle_subscriptions(app, socketio):
    event_handler = SubscriptionEventHandler(app, socketio)
    while True:
        try:
            if not app.session_for_subscriptions.is_started():
                app.session_for_subscriptions.start()
                app.all_subscriptions = {}

            event = app.session_for_subscriptions.nextEvent(50)
            event_handler.process_event(event)
        except Exception:
            traceback.print_exc()
            handle_broken_session(app)
            socketio.sleep(1)
        finally:
            socketio.sleep()

