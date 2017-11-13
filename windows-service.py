import eventlet
eventlet.monkey_patch()

import tempfile
import os
import sys
import win32serviceutil
import win32service
import win32event
import servicemanager
import time
from server import main as start_server

class BloombergBridgeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "BBApi"
    _svc_display_name_ = "Web API for Bloomberg Market Data"

    def __init__(self,args):
        print("Initialising...")
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        self.isAlive = True

    def SvcStop(self):
        servicemanager.LogInfoMsg("Stopping...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.isAlive = False

    def SvcDoRun(self):
        print("Starting...")
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        print("Started")
        sys.stdout = sys.stderr = open(os.path.join(tempfile.gettempdir(), "pricingmonkey.log"), "w")
        eventlet.spawn(start_server)
        while self.isAlive:
            time.sleep(5)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(BloombergBridgeService)
