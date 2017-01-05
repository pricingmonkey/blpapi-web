class Event:
    TIMEOUT = "TIMEOUT"
    PARTIAL_RESPONSE = "PARTIAL_RESPONSE"
    RESPONSE = "RESPONSE"
    SUBSCRIPTION_DATA = "SUBSCRIPTION_DATA"
    SUBSCRIPTION_STATUS = "SUBSCRIPTION_STATUS"

    def __init__(self, messages, eventType):
        self.messages = messages
        self.index = 0
        self._eventType = eventType

    def eventType(self):
        return self._eventType

    def __iter__(self):
        return self

    def __next__(self):
        try:
            message = self.messages[self.index]
            self.index += 1
            return message
        except IndexError:
            raise StopIteration

    def __str__(self):
        return "Map({})".format(str(self.messages))

    def __repr__(self):
        return self.__str__()

class FiniteEventSource:
   def __init__(self, messageSource):
      self.index = 0
      self.messages = messageSource.messages()

   def nextEvent(self):
      try:
          if self.index == len(self.messages) - 1:
              return Event([self.messages[self.index]], Event.RESPONSE)
          else:
              return Event([self.messages[self.index]], Event.PARTIAL_RESPONSE)
      except IndexError:
          return None
      finally:
          self.index += 1

class InfiniteEventSource:
   def __init__(self, messageSource, eventType):
     self.messageSource = messageSource
     self.eventType = eventType

   def nextEvent(self):
      return Event(self.messageSource.messages(), self.eventType)

class QueueMessageSource:
    def __init__(self, messageQueue):
       self.messageQueue = messageQueue

    def messages(self):
       return [self.messageQueue.get()]

class EventQueue:
    def attachEventSource(self, eventSource):
        self.eventSource = eventSource

    def nextEvent(self, timeout):
        return self.eventSource.nextEvent()

