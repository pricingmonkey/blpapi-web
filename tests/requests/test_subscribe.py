from flask import current_app

headers=[('Content-Type', 'text/plain')]


def test_subscribe(app):
    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202
    assert current_app.allSubscriptions == { 'TEST': ['TEST'] }


def test_break_service(app, capsys):
    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202
    assert current_app.allSubscriptions == {'TEST': ['TEST']}

    assert app.get("/dev/subscriptions/getService/break").status_code == 200
    assert app.get("/dev/subscriptions/getService/break").status_code == 200

    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 500
    captured = capsys.readouterr()
    assert "bridge.bloomberg.session.BrokenSessionException: Failed to open //blp/mktdata" in captured.err

    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202
    assert current_app.allSubscriptions == {'TEST': ['TEST']}


def test_reset_session(app):
    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202
    assert current_app.allSubscriptions == {'TEST': ['TEST']}

    assert app.get("/dev/subscriptions/session/reset").status_code == 200

    assert app.get("/subscribe?security=TEST&field=TEST", headers = headers).status_code == 202
    assert current_app.allSubscriptions == {'TEST': ['TEST']}

