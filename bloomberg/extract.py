def extractReferenceSecurityPricing(message):
    result = []
    if message.hasElement("securityData"):
        for securityInformation in list(message.getElement("securityData").values()):
            fields = []
            for field in securityInformation.getElement("fieldData").elements():
                fields.append({
                    "name": str(field.name()),
                    "value": field.getValue()
                })
            result.append({
                "security": securityInformation.getElementValue("security"),
                "fields": fields
            })
    return result

def extractHistoricalSecurityPricing(message):
    resultsForDate = {}
    if message.hasElement("securityData"):
        securityInformation = message.getElement("securityData")
        security = securityInformation.getElementValue("security")
        for fieldsOnDate in list(securityInformation.getElement("fieldData").values()):
            fields = []
            for fieldElement in fieldsOnDate.elements():
                if str(fieldElement.name()) == "date":
                    date = fieldElement.getValueAsString()
                elif str(fieldElement.name()) == "relativeDate":
                    pass
                else: # assume it's the {fieldName -> fieldValue}
                    fields.append({
                        "name": str(fieldElement.name()),
                        "value": fieldElement.getValue()
                    })
            if not date in resultsForDate:
                resultsForDate[date] = {}
            if not security in resultsForDate[date]:
                resultsForDate[date][security] = []
            for field in fields:
                resultsForDate[date][security].append(field)

    result = []
    for date, securities in resultsForDate.items():
        valuesForSecurities = []
        for security, fields in securities.items():
            valuesForSecurities.append({
                "security": security,
                "fields": fields
            })
        result.append({
            "date": date,
            "values": valuesForSecurities
        })
    return sorted(result, key=lambda each: each["date"])

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

def extractError(errorElement):
    category = errorElement.getElementValue("category")
    if errorElement.hasElement("subcategory"):
        subcategory = errorElement.getElementValue("subcategory")
    else:
        subcategory = None
    message = errorElement.getElementValue("message")
    return "{}/{} {}".format(category, subcategory, message)

def extractErrors(message):
    result = []
    if message.hasElement("responseError"):
        result.append(extractError(message.getElement("responseError")))
    if message.hasElement("securityData"):
        if message.getElement("securityData").isArray():
           securityData = list(message.getElement("securityData").values())
        else:
           securityData = list([message.getElement("securityData")])
        for securityInformation in securityData:
            if securityInformation.hasElement("fieldExceptions"):
                for fieldException in list(securityInformation.getElement("fieldExceptions").values()):
                    error = extractError(fieldException.getElement("errorInfo"))
                    result.append("{}: {}/{}".format(
                        error,
                        securityInformation.getElementValue("security"),
                        fieldException.getElementValue("fieldId")
                    ))
            if securityInformation.hasElement("securityError"):
                error = extractError(securityInformation.getElement("securityError"))
                result.append("{}: {}".format(error, securityInformation.getElementValue("security")))
    return result

