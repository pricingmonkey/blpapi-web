headers=[('Content-Type', 'text/plain')]


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

