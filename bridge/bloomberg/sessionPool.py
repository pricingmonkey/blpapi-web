from bridge.bloomberg.session import Session


class SessionPool:
    def __init__(self, poolSize):
        self.sessions = list(map(lambda s: Session(), [None] * poolSize))
        self.currentIndex = 0

    def __poolSize(self):
        return len(self.sessions)

    def getSession(self):
        nextIndex = (self.currentIndex + 1) % self.__poolSize()
        session = self.sessions[self.currentIndex]
        if not session.is_started():
            session.start()
        self.currentIndex = nextIndex
        return session

    def isHealthy(self):
        return all(map(lambda session: session.is_started(), self.sessions))

    def open(self):
        for session in self.sessions:
            session.start()

    def stop(self):
        for session in self.sessions:
            session.stop()

    def reset(self):
        for session in self.sessions:
            session.reset()
