headers = [('Content-Type', 'text/plain')]


def test_historical(app):
    assert app.get("/historical?security=TEST&field=TEST&startDate=20151221&endDate=20161218",
                   headers=headers).status_code == 200


def test_break_service(app, capsys):
    assert app.get("/historical?security=TEST&field=TEST&startDate=20151221&endDate=20161218",
                   headers=headers).status_code == 200

    assert app.get("/dev/requests/getService/break").status_code == 200
    assert app.get("/dev/requests/getService/break").status_code == 200

    assert app.get("/historical?security=TEST&field=TEST&startDate=20151221&endDate=20161218",
                   headers=headers).status_code == 500
    captured = capsys.readouterr()
    assert "bridge.bloomberg.session.BrokenSessionException: Failed to open //blp/refdata" in captured.err
    assert app.get("/historical?security=TEST&field=TEST&startDate=20151221&endDate=20161218",
                   headers=headers).status_code == 200


def test_reset_session(app):
    assert app.get("/historical?security=TEST&field=TEST&startDate=20151221&endDate=20161218",
                   headers=headers).status_code == 200

    assert app.get("/dev/requests/session/reset").status_code == 200

    assert app.get("/historical?security=TEST&field=TEST&startDate=20151221&endDate=20161218",
                   headers=headers).status_code == 200


def test_break_session(app, capsys):
    assert app.get("/historical?security=TEST&field=TEST&startDate=20151221&endDate=20161218",
                   headers=headers).status_code == 200

    assert app.get("/dev/requests/sendRequest/break").status_code == 200

    assert app.get("/historical?security=TEST&field=TEST&startDate=20151221&endDate=20161218",
                   headers=headers).status_code == 500
    captured = capsys.readouterr()
    assert "service is broken" in captured.err
    assert app.get("/historical?security=TEST&field=TEST&startDate=20151221&endDate=20161218",
                   headers=headers).status_code == 200
