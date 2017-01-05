import time, random
from eventlet.green import threading
from eventlet import queue

from .event import Event, EventQueue
from .event import FiniteEventSource, InfiniteEventSource, QueueMessageSource
from .service import Service
from .utils import isValidSecurity

class Session:
    def __init__(self, sessionOptions, processEvent=None):
        self.responses = []
        self.eventQueue = None
        self.processEvent = processEvent
        self.subscriptions = []
        self.messageQueue = queue.Queue(100)
        def produce():
           while True:
              if len(self.subscriptions) == 0:
                 time.sleep(2)
              numOfTopics = len(self.subscriptions)
              for each in self.subscriptions:
                 for message in each.messages():
                    self.messageQueue.put(message)
                    time.sleep((2 + 0.25 * random.random()) / (numOfTopics or 1))
        threading.Thread(target=produce).start()
        if self.processEvent is not None:
            def consume():
               while True:
                  message = self.messageQueue.get()
                  self.processEvent(Event([message], Event.SUBSCRIPTION_DATA), self)
            threading.Thread(target=consume).start()

    def start(self):
        return True

    def stop(self):
        pass

    def openService(self, serviceName):
        return True

    def getService(self, serviceName):
        return Service()

    def sendRequest(self, request, eventQueue=EventQueue()):
        self.eventQueue = eventQueue
        self.eventQueue.attachEventSource(FiniteEventSource(request))

    def subscribe(self, subscriptionList):
        if self.eventQueue is None:
            self.eventQueue = EventQueue()
            self.eventQueue.attachEventSource(InfiniteEventSource(QueueMessageSource(self.messageQueue), Event.SUBSCRIPTION_DATA))
        for subscription in subscriptionList:
            if isValidSecurity(subscription.topicOrSecurity):
                self.subscriptions.append(subscription)

    def resubscribe(self, subscriptionList):
        for subscription in subscriptionList:
            element = next([each for each in self.subscriptions if each.topicOrSecurity == subscrption.topicOrSecurity], None)
            if not element:
                raise Error("subscrption does not exist")

    def unsubscribe(self, subscriptionList):
        for subscription in subscriptionList:
            self.subscriptions = [each for each in self.subscriptions if each.topicOrSecurity == subscription.topicOrSecurity]

    def nextEvent(self, timeout):
        if self.eventQueue is None:
            time.sleep(timeout / 1000)
            return Event([], Event.TIMEOUT)
        return self.eventQueue.nextEvent(timeout)

