import traceback
import eventlet

BLOOMBERG_HOST = "localhost"
BLOOMBERG_PORT = 8194


class BrokenSessionException(Exception):
    pass


class Session:
    def __init__(self):
        self.session_impl = None

    def is_started(self):
        return self.session_impl is not None

    def is_healthy(self):
        return self.is_started()

    def start(self):
        if self.is_started():
            return

        session_options = blpapi.SessionOptions()
        session_options.setServerHost(BLOOMBERG_HOST)
        session_options.setServerPort(BLOOMBERG_PORT)
        session_options.setAutoRestartOnDisconnection(True)

        self.session_impl = blpapi.Session(session_options)

        if not self.session_impl.start():
            raise BrokenSessionException("Failed to start session on {}:{}".format(BLOOMBERG_HOST, BLOOMBERG_PORT))

        return

    def stop(self):
        try:
            if self.is_started():
                self.session_impl.stop()
        except:
            traceback.print_exc()
            pass
        finally:
            self.reset()

    def reset(self):
        self.session_impl = None

    def _get_or_open_service(self, serviceName):
        try:
            return self.session_impl.getService(serviceName), True
        except Exception as e:
            opened = self.session_impl.openService(serviceName)
            return self.session_impl.getService(serviceName), opened

    def get_service(self, serviceName):
        if not self.is_started():
            self.start()

        try:
            sessionRestarted = False
            service, opened = self._get_or_open_service(serviceName)
            if not opened:
                sessionRestarted = True
                self.session_impl.stop()
                self.session_impl.start()
                if not self.session_impl.openService(serviceName):
                    raise BrokenSessionException("Failed to open {}".format(serviceName))

            return service, sessionRestarted
        except Exception as e:
            raise BrokenSessionException("Failed to open {}".format(serviceName)) from e

    def send_and_wait(self, request):
        if not self.is_started():
            self.start()

        event_queue = blpapi.EventQueue()
        self.session_impl.sendRequest(request, eventQueue=event_queue)
        responses = []
        while True:
            ev = event_queue.tryNextEvent()
            if not ev:
                eventlet.sleep(25 / 1000)
                continue

            for msg in ev:
                if msg.messageType() == blpapi.Name("ReferenceDataResponse") \
                        or msg.messageType() == blpapi.Name("HistoricalDataResponse") \
                        or msg.messageType() == blpapi.Name("IntradayBarResponse"):
                    responses.append(msg)

            response_completely_received = ev.eventType() == blpapi.Event.RESPONSE
            if response_completely_received:
                break
        return responses

    def nextEvent(self, timeout):
        return self.session_impl.nextEvent(timeout)

    def subscribe(self, subscriptionList):
        return self.session_impl.subscribe(subscriptionList)

    def resubscribe(self, subscriptionList):
        return self.session_impl.resubscribe(subscriptionList)

    def unsubscribe(self, subscriptionList):
        return self.session_impl.unsubscribe(subscriptionList)
