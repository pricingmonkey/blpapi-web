def extractError(errorElement):
    category = errorElement.getElementValue("category")
    if errorElement.hasElement("subcategory"):
        subcategory = errorElement.getElementValue("subcategory")
    else:
        subcategory = None
    message = errorElement.getElementValue("message")
    return "{}/{} {}".format(category, subcategory, message)