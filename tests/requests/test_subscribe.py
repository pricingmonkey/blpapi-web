import eventlet
import pytest

from server import app as my_app, wireUpBlpapiImplementation
from routes import dev

headers=[('Content-Type', 'text/plain')]

@pytest.fixture(scope="session")
def app():
    wireUpBlpapiImplementation(eventlet.import_patched("blpapi_simulator"))
    my_app.register_blueprint(dev.blueprint, url_prefix='/dev')
    app = my_app.test_client()
    app.testing = True
    return app


def test_subscribe(app):
    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202


def test_break_service(app):
    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202

    assert app.get("/dev/subscriptions/getService/break").status_code == 200
    assert app.get("/dev/subscriptions/getService/break").status_code == 200

    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 500
    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202


def test_reset_session(app):
    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202

    assert app.get("/dev/subscriptions/session/reset").status_code == 200

    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202

