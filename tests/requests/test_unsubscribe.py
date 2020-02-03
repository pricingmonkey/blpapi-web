import eventlet
import pytest

from server import app as my_app, wireUpBlpapiImplementation

@pytest.fixture(scope="session")
def app():
    wireUpBlpapiImplementation(eventlet.import_patched("blpapi_simulator"))
    app = my_app.test_client()
    app.testing = True 
    return app

headers=[('Content-Type', 'text/plain')]


def test_unsubscribe(app):
    result = app.get("/unsubscribe?security=TEST&field=TEST", headers = headers)
    assert result.status_code is 202
