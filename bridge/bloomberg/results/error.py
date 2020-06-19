def extract_error(error_element):
    category = error_element.getElementValue("category")
    if error_element.hasElement("subcategory"):
        subcategory = error_element.getElementValue("subcategory")
    else:
        subcategory = None
    message = error_element.getElementValue("message")
    return "{}/{} {}".format(category, subcategory, message)
