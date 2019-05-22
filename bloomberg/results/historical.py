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