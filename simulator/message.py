from .name import Name

class Map:
    class Entry:
        def __init__(self, key, value):
            self.key = key
            self.value = value

        def name(self):
            return self.key

        def numValues(self):
            if self.value is None:
                return 0
            return 1

        def getValue(self):
            return self.value

        def getValueAsString(self):
            return str(self.value)

    def __init__(self, value):
        self.value = value

    def isArray(self):
        return False

    def hasElement(self, name):
        return name in self.value

    def getElement(self, name):
        return self.value[name]

    def getElementValue(self, name):
        return self.value[name]

    def elements(self):
        return [Map.Entry(k, v) for k, v in self.value.items()]

    def __str__(self):
        return "Map({})".format(str(self.value))

    def __repr__(self):
        return self.__str__()

class List:
    def __init__(self, items):
        self.items = items

    def isArray(self):
        return True

    def values(self):
        return self.items

    def __str__(self):
        return "List({})".format(str(self.items))

    def __repr__(self):
        return self.__str__()


class Message(Map):
    def __init__(self, value, correlationId=None):
        self.value = value
        self._correlationId = correlationId

    def messageType(self):
        return Name("ReferenceDataResponse")

    def correlationIds(self):
        return [self._correlationId]

    def asElement(self):
        return Map(self.value)

    def __str__(self):
        return "Message({})".format(str(self.value))

    def __repr__(self):
        return self.__str__()


