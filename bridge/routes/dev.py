import json
from flask import Blueprint, current_app as app, request, Response

blueprint = Blueprint('dev', __name__)


def raise_(ex):
    raise ex


class BrokenSession:
    def __init__(self, ignore):
        pass

    def start(self):
        return False

    def stop(self):
        raise Exception("broken")

    def getService(self, serviceName):
        raise Exception("broken")

    def openService(self, serviceName):
        raise Exception("broken")

    def nextEvent(self, param):
        raise Exception("broken")


class DisconnectedSession:
    def __init__(self, parentSession):
        self.parentSession = parentSession

    def start(self):
        self.parentSession = blpapi.Session()
        return True

    def stop(self):
        raise Exception("disconnected")

    def getService(self, serviceName):
        raise Exception("disconnected")

    def openService(self, serviceName):
        raise Exception("disconnected")

    def nextEvent(self, param):
        raise Exception("disconnected")


@blueprint.route('/requests/session/reset', methods=['GET'])
def reset_session_for_requests():
    app.session_pool_for_requests.reset()
    return Response("OK", status=200)


@blueprint.route('/subscriptions/session/reset', methods=['GET'])
def reset_session_for_subscriptions():
    app.session_for_subscriptions.reset()
    return Response("OK", status=200)


OriginalSession = [None]


@blueprint.route('/session/stop', methods=['GET'])
def stop_session_for_subscriptions():
    OriginalSession[0] = blpapi.Session
    blpapi.Session = BrokenSession
    app.session_pool_for_requests.reset()
    app.session_for_subscriptions.reset()
    return Response("OK", status=200)


@blueprint.route('/session/start', methods=['GET'])
def start_session_for_requests():
    if OriginalSession[0]:
        blpapi.Session = OriginalSession[0]
        app.session_pool_for_requests.reset()
        app.session_for_subscriptions.reset()
    return Response("OK", status=200)


@blueprint.route('/session/disconnect', methods=['GET'])
def disconnect_session():
    app.session_pool_for_requests.sessions[0].session_impl = DisconnectedSession(app.session_pool_for_requests.sessions[0])
    app.session_pool_for_requests.sessions[1].session_impl = DisconnectedSession(app.session_pool_for_requests.sessions[1])
    app.session_for_subscriptions.session_impl = DisconnectedSession(app.session_for_subscriptions)
    return Response("OK", status=200)


def function_one_time_broken(original):
    hit = [False]

    def function(*args, **kwargs):
        if hit[0]:
            return original(*args, **kwargs)
        else:
            hit[0] = True
            raise_(Exception("service is broken"))

    return function


@blueprint.route('/requests/sendRequest/break', methods=['GET'])
def break_send_request_for_requests():
    session_pool = app.session_pool_for_requests
    session = session_pool.sessions[session_pool.currentIndex]
    session.start()
    session.session_impl.sendRequest = function_one_time_broken(session.session_impl.sendRequest)

    return Response("OK", status=200)


@blueprint.route('/subscriptions/nextEvent/break', methods=['GET'])
def break_next_event_for_subscriptions():
    app.session_for_subscriptions.session_impl.nextEvent = function_one_time_broken(
        app.session_for_subscriptions.session_impl.nextEvent)

    return Response("OK", status=200)


@blueprint.route('/requests/getService/break', methods=['GET'])
def break_get_service_for_requests():
    session_pool = app.session_pool_for_requests
    session = session_pool.sessions[session_pool.currentIndex]
    session.start()
    session.session_impl.getService = function_one_time_broken(session.session_impl.getService)

    return Response("OK", status=200)


@blueprint.route('/subscriptions/getService/break', methods=['GET'])
def break_get_service_for_subscriptions():
    app.session_for_subscriptions.session_impl.getService = function_one_time_broken(
        app.session_for_subscriptions.session_impl.getService)

    return Response("OK", status=200)
