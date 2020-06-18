headers=[('Content-Type', 'text/plain')]


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
