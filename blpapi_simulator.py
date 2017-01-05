from simulator.session import Session, Event
from simulator.event import EventQueue
from simulator.name import Name
from simulator.message import Message
from simulator.sessionoptions import SessionOptions
from simulator.subscriptionlist import SubscriptionList

class CorrelationId():
    def __init__(self, string):
        self._value = string

    def value(self):
        return self._value

class Exception(BaseException):
    pass
