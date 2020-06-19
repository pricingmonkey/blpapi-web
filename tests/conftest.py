import eventlet
import pytest

from server import app as my_app, wire_up_blpapi_implementation
from bridge.routes import dev


@pytest.yield_fixture(scope="function")
def app():
    wire_up_blpapi_implementation(eventlet.import_patched("blpapi_simulator"))
    my_app.register_blueprint(dev.blueprint, url_prefix='/dev')
    my_app.all_subscriptions = {}
    client = my_app.test_client()
    client.testing = True
    ctx = my_app.app_context()
    ctx.push()
    yield client
    ctx.pop()
