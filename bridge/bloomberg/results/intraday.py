def extract_intraday_security_pricing(security, message):
    values = []
    if message.hasElement("barData"):
        bar_data = message.getElement("barData")
        for bar_tick in list(bar_data.getElement("barTickData").values()):
            values.append({
                "time": bar_tick.getElement("time").getValueAsString(),
                "open": bar_tick.getElement("open").getValueAsString(),
                "high": bar_tick.getElement("high").getValueAsString(),
                "low": bar_tick.getElement("low").getValueAsString(),
                "close": bar_tick.getElement("close").getValueAsString(),
                "numEvents": bar_tick.getElement("numEvents").getValueAsString(),
                "volume": bar_tick.getElement("volume").getValueAsString()
            })
    return {
        "security": security,
        "values": values
    }
