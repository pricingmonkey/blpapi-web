from bloomberg.extract import extractReferenceSecurityPricing, extractErrors
from blpapi_simulator.simulator.message import Message, Map, List

def test_simple():
    message = Message({
        "securityData": List([Map({
            "security": "L Z7 Comdty",
            "fieldData": Map({
                "PX_LAST": "90.00"
            })
        })])
    })
    response = extractReferenceSecurityPricing(message)
    assert len(response) == 1
    assert response[0]["security"] == "L Z7 Comdty"
    fields = response[0]["fields"]
    assert len(fields) == 1
    assert fields[0]["name"] == "PX_LAST"
    assert fields[0]["value"] == "90.00"

def test_multiple_securities_and_fields():
    message = Message({
        "securityData": List([Map({
            "security": "L Z7 Comdty",
            "fieldData": Map({
                "PX_LAST": "90.00",
                "ASK": "90.00",
                "BID": "90.00"
            })
            }), Map({
            "security": "L Z6 Comdty",
            "fieldData": Map({
                "PX_LAST": "90.00",
                "ASK": "90.00"
            })
        })])
    })
    response = extractReferenceSecurityPricing(message)
    assert len(response) == 2
    fields = response[0]["fields"]
    assert len(response[0]["fields"]) == 3
    assert len(response[1]["fields"]) == 2

def test_response_error():
    message = Message({
        "responseError": Map({
            "category": "CATEGORY",
            "subcategory": "SUBCATEGORY",
            "message": "MESSAGE"
        })
    })
    response = extractReferenceSecurityPricing(message)
    errors = extractErrors(message)
    assert len(response) == 0
    assert len(errors) == 1
    assert errors[0] == "CATEGORY/SUBCATEGORY MESSAGE"

def test_response_error_no_subcategory():
    message = Message({
        "responseError": Map({
            "category": "CATEGORY",
            "message": "MESSAGE"
        })
    })
    response = extractReferenceSecurityPricing(message)
    errors = extractErrors(message)
    assert len(response) == 0
    assert len(errors) == 1
    assert errors[0] == "CATEGORY/None MESSAGE"
