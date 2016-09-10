from server import extractHistoricalSecurityPricing
from blpapi_mock import *

def test_simple():
    message = Message({
        "securityData": List([Map({
            "security": "L Z7 Comdty",
            "fieldData": List([
                Map({
                    "date": "2006-01-31",
                    "PX_LAST": 90
                }),
                Map({
                    "date": "2006-02-01",
                    "PX_LAST": 90.05
                })
            ])
        })])
    })
    response = extractHistoricalSecurityPricing(message)
    assert len(response) == 2
    assert response[0]["date"] == "2006-01-31"
    assert response[1]["date"] == "2006-02-01"

