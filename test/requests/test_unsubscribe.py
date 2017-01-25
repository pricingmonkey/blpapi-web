import eventlet
import pytest

from server import app as my_app, wireUpBlpapiImplementation

@pytest.fixture(scope="session")
def app():
    wireUpBlpapiImplementation(eventlet.import_patched("blpapi_simulator"))
    app = my_app.test_client()
    app.testing = True 
    return app

def test_unsubscribe():
    result = app().get("/unsubscribe?security=TEST&field=TEST")
    assert result.status_code is 202
