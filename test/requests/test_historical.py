import eventlet
import pytest

from server import app as my_app, wireUpBlpapiImplementation

@pytest.fixture(scope="session")
def app():
    wireUpBlpapiImplementation(eventlet.import_patched("blpapi_simulator"))
    app = my_app.test_client()
    app.testing = True 
    return app

def test_historical():
    result = app().get("/historical?security=TEST&field=TEST&startDate=20151221&endDate=20161218")
    assert result.status_code is 200
