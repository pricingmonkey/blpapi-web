import eventlet
import pytest

from server import app as my_app, wireUpBlpapiImplementation
from routes import dev

headers=[('Content-Type', 'text/plain')]

@pytest.fixture(scope="session")
def app():
    wireUpBlpapiImplementation(eventlet.import_patched("blpapi_simulator"))
    my_app.register_blueprint(dev.blueprint, url_prefix='/dev')
    my_app.testing = True
    app = my_app.test_client()
    return app


def test_status(app):
    result = app.get("/status", headers = headers)
    assert result.status_code == 200


def test_break_requests_service(app):
    assert app.get("/latest?security=TEST&field=TEST", headers = headers).status_code == 200

    assert app.get("/dev/requests/getService/break").status_code == 200
    assert app.get("/dev/requests/getService/break").status_code == 200

    assert app.get("/status", headers = headers).status_code == 200

    assert app.get("/latest?security=TEST&field=TEST", headers = headers).status_code == 500
    assert app.get("/latest?security=TEST&field=TEST", headers=headers).status_code == 200
    assert app.get("/latest?security=TEST&field=TEST", headers=headers).status_code == 200

    assert app.get("/status", headers=headers).status_code == 200


def test_break_subscription_service(app):
    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202

    assert app.get("/dev/subscriptions/getService/break").status_code == 200
    assert app.get("/dev/subscriptions/getService/break").status_code == 200

    assert app.get("/status", headers=headers).status_code == 200
    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 500
    assert app.get("/status", headers=headers).status_code == 200
    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202
    assert app.get("/status", headers=headers).status_code == 200
