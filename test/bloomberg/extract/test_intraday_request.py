from bloomberg.results.intraday import extractIntradaySecurityPricing
from blpapi_simulator.simulator.message import Message, Map, List, Element

def test_simple():
    message = Message({
        "barData":
            Map({
                "barTickData": List([
                    Map({
                        "time": Element(6), 
                        "open": Element(5),
                        "high": Element(4), 
                        "low": Element(3), 
                        "close": Element(2), 
                        "volume": Element(100), 
                        "numEvents": Element(10)
                    })
                ])
            })
    })
    response = extractIntradaySecurityPricing("L Z7 Comdty", message)
    assert response["security"] == "L Z7 Comdty"
    assert response["values"][0]["high"] == "4"
    assert response["values"][0]["low"] == "3"

