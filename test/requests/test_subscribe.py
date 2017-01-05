import eventlet
import pytest

from server import app as my_app, wireUpBlpapiImplementation

@pytest.fixture(scope="session")
def app():
    wireUpBlpapiImplementation(eventlet.import_patched("blpapi_simulator"))
    app = my_app.test_client()
    app.testing = True 
    return app

def test_subscribe():
    result = app().get("/subscribe?security=TEST&field=TEST")
    assert result.status_code is 202
