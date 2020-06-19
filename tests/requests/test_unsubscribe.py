headers = [('Content-Type', 'text/plain')]


def test_unsubscribe(app):
    result = app.get("/unsubscribe?security=TEST&field=TEST", headers=headers)
    assert result.status_code is 202
