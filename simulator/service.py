from .request import Request

class Service:
    def createRequest(self, serviceType):
        return Request(serviceType)

