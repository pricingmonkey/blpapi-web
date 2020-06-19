def extract_reference_security_pricing(message):
    result = []
    if message.hasElement("securityData"):
        for security_information in list(message.getElement("securityData").values()):
            fields = []
            for field in security_information.getElement("fieldData").elements():
                fields.append({
                    "name": str(field.name()),
                    "value": field.getValue()
                })
            result.append({
                "security": security_information.getElementValue("security"),
                "fields": fields
            })
    return result
