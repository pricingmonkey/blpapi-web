import random, time
from datetime import datetime, timedelta

from .message import Message, Map, List
from .utils import merge_dicts, randomFieldValue, isValidSecurity

class Request:
    def __init__(self, serviceType):
        self.params = {}
        self.serviceType = serviceType

    def set(self, name, value):
        self.params[name] = value

    def append(self, name, value):
        if not name in self.params:
            self.params[name] = []
        self.params[name].append(value)

    def __isWeekday(self, date):
        return date.isoweekday() <= 5

    def messages(self):
        if self.serviceType == "ReferenceDataRequest":
            time.sleep(random.randint(2, 6) / 10)
            validSecurities, invalidSecurities = [], []

            for s in self.params["securities"]:
                if isValidSecurity(s):
                    validSecurities.append(s)
                else:
                    invalidSecurities.append(s)
            return [Message({
                "securityData": List([Map({
                    "security": security,
                    "fieldData": Map({
                        field: randomFieldValue(field, security)
                    for field in self.params["fields"]})
                }) for security in validSecurities] + [
                    Map({
                        "security": security,
                        "fieldData": Map({}),
                        "fieldExceptions": List([Map({
                                "errorInfo": Map({
                                    "category": "INCORRECT SECURITY",
                                    "subcategory": "SUBCAT",
                                    "message": "MSG"
                                }),
                                "fieldId": "FIELD_ID",
                                "message": "MESSAGE"
                        })])
                }) for security in invalidSecurities]
            )})]
        if self.serviceType == "HistoricalDataRequest":
            time.sleep(random.randint(4, 8) / 10)
            startDate = datetime.strptime(self.params["startDate"], "%Y%m%d").date()
            endDate = datetime.strptime(self.params["endDate"], "%Y%m%d").date()
            return [Message({
                "securityData": Map({
                    "security": security,
                    "fieldData": List([
                        Map(merge_dicts(
                            { "date": date},
                            { field: randomFieldValue(field, security) for field in self.params["fields"] }
                        )) for date in [startDate + timedelta(days=i) for i in range((endDate - startDate).days + 1)] if self.__isWeekday(date)])
                    })
                }) for security in self.params["securities"]]


