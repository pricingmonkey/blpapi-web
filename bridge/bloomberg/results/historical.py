def extract_historical_security_pricing(message):
    results_for_date = {}
    if message.hasElement("securityData"):
        security_information = message.getElement("securityData")
        security = security_information.getElementValue("security")
        for fields_on_date in list(security_information.getElement("fieldData").values()):
            fields = []
            for fieldElement in fields_on_date.elements():
                if str(fieldElement.name()) == "date":
                    date = fieldElement.getValueAsString()
                elif str(fieldElement.name()) == "relativeDate":
                    pass
                else:  # assume it's the {fieldName -> fieldValue}
                    fields.append({
                        "name": str(fieldElement.name()),
                        "value": fieldElement.getValue()
                    })
            if not date in results_for_date:
                results_for_date[date] = {}
            if not security in results_for_date[date]:
                results_for_date[date][security] = []
            for field in fields:
                results_for_date[date][security].append(field)

    result = []
    for date, securities in results_for_date.items():
        values_for_securities = []
        for security, fields in securities.items():
            values_for_securities.append({
                "security": security,
                "fields": fields
            })
        result.append({
            "date": date,
            "values": values_for_securities
        })
    return sorted(result, key=lambda each: each["date"])
