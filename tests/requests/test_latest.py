headers=[('Content-Type', 'text/plain')]


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

