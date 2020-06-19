headers = [('Content-Type', 'text/plain')]


def test_status(app):
    result = app.get("/status", headers=headers)
    assert result.status_code == 200


def test_break_requests_service(app, capsys):
    assert app.get("/latest?security=TEST&field=TEST", headers=headers).status_code == 200

    assert app.get("/dev/requests/getService/break").status_code == 200
    assert app.get("/dev/requests/getService/break").status_code == 200

    assert app.get("/status", headers=headers).status_code == 200

    assert app.get("/latest?security=TEST&field=TEST", headers=headers).status_code == 500
    captured = capsys.readouterr()
    assert "bridge.bloomberg.session.BrokenSessionException: Failed to open //blp/refdata" in captured.err
    assert app.get("/latest?security=TEST&field=TEST", headers=headers).status_code == 200
    assert app.get("/latest?security=TEST&field=TEST", headers=headers).status_code == 200

    assert app.get("/status", headers=headers).status_code == 200


def test_break_subscription_service(app, capsys):
    assert app.get("/subscribe?security=TEST&field=TEST", headers=headers).status_code == 202

    assert app.get("/dev/subscriptions/getService/break").status_code == 200
    assert app.get("/dev/subscriptions/getService/break").status_code == 200

    assert app.get("/status", headers=headers).status_code == 200
    assert app.get("/subscribe?security=TEST&field=TEST", headers=headers).status_code == 500
    captured = capsys.readouterr()
    assert "bridge.bloomberg.session.BrokenSessionException: Failed to open //blp/mktdata" in captured.err
    assert app.get("/status", headers=headers).status_code == 200
    assert app.get("/subscribe?security=TEST&field=TEST", headers=headers).status_code == 202
    assert app.get("/status", headers=headers).status_code == 200
