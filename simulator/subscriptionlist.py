import random

from .message import Message
from .utils import randomFieldValue

class SubscriptionList:
    class Subscription:
        def __init__(self, topicOrSecurity, fields, options, correlationId):
            self.fields = fields
            self.correlationId = correlationId
            self.topicOrSecurity = topicOrSecurity

        def messages(self):
            def generateFields(security, fields):
                contents = {}
                contents.update({field: randomFieldValue(field, security) for field in fields})
                contents.update({"EXTRA_FIELD_%d" % (i): randomFieldValue(None, security) for i in range(200)})
                if random.random() < 0.1:
                    del contents["ASK"]
                    del contents["BID"]
                return contents
            return [
                Message(
                    generateFields(self.topicOrSecurity, self.fields),
                    self.correlationId)
            ]

    def __init__(self):
        self.all = []

    def __iter__(self):
        return iter(self.all)

    def add(self, topicOrSecurity, fields=None, options=None, correlationId=None):
        self.all.append(self.Subscription(topicOrSecurity, fields, options, correlationId));

    def size(self):
        return len(self.all)


