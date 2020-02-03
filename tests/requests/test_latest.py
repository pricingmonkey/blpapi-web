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


def test_latest(app):
    result = app.get("/latest?security=TEST&field=TEST", headers = headers)
    assert result.status_code == 200


def test_break_service(app):
    assert app.get("/latest?security=TEST&field=TEST", headers = headers).status_code == 200

    assert app.get("/dev/requests/getService/break").status_code == 200
    assert app.get("/dev/requests/getService/break").status_code == 200

    assert app.get("/latest?security=TEST&field=TEST", headers = headers).status_code == 500
    assert app.get("/latest?security=TEST&field=TEST", headers = headers).status_code == 200


def test_reset_session(app):
    assert app.get("/latest?security=TEST&field=TEST", headers = headers).status_code == 200

    assert app.get("/dev/requests/session/reset").status_code == 200

    assert app.get("/latest?security=TEST&field=TEST", headers = headers).status_code == 200


def test_break_session(app):
    assert app.get("/latest?security=TEST&field=TEST", headers = headers).status_code == 200

    assert app.get("/dev/requests/sendRequest/break").status_code == 200

    assert app.get("/latest?security=TEST&field=TEST", headers = headers).status_code == 500
    assert app.get("/latest?security=TEST&field=TEST", headers = headers).status_code == 200

