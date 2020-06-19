from bridge.bloomberg.results.error import extract_error


def extract_errors(message):
    result = []
    if message.hasElement("responseError"):
        result.append(extract_error(message.getElement("responseError")))
    if message.hasElement("securityData"):
        if message.getElement("securityData").isArray():
            security_data = list(message.getElement("securityData").values())
        else:
            security_data = list([message.getElement("securityData")])
        for security_information in security_data:
            if security_information.hasElement("fieldExceptions"):
                for field_exception in list(security_information.getElement("fieldExceptions").values()):
                    error = extract_error(field_exception.getElement("errorInfo"))
                    result.append("{}: {}/{}".format(
                        error,
                        security_information.getElementValue("security"),
                        field_exception.getElementValue("fieldId")
                    ))
            if security_information.hasElement("securityError"):
                error = extract_error(security_information.getElement("securityError"))
                result.append("{}: {}".format(error, security_information.getElementValue("security")))
    return result
