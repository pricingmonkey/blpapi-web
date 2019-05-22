from bloomberg.results.error import extractError


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