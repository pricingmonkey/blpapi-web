def extractIntradaySecurityPricing(security, message):
    values = []
    if message.hasElement("barData"):
        barData = message.getElement("barData")
        for barTick in list(barData.getElement("barTickData").values()):
            values.append({
                "time": barTick.getElement("time").getValueAsString(),
                "open": barTick.getElement("open").getValueAsString(),
                "high": barTick.getElement("high").getValueAsString(),
                "low": barTick.getElement("low").getValueAsString(),
                "close": barTick.getElement("close").getValueAsString(),
                "numEvents": barTick.getElement("numEvents").getValueAsString(),
                "volume": barTick.getElement("volume").getValueAsString()
            })
    return {
        "security": security,
        "values": values
    }