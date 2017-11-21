try:
    import eventlet
    eventlet.monkey_patch()

    import tempfile
    import os
    import sys
    log_location = os.path.join(tempfile.gettempdir(), "pricingmonkey.log")
    sys.stdout = sys.stderr = open(log_location, "a")

    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    import time
    from server import main as start_server
except Exception as e:
    print("import error: " + str(e))
    raise Exception("import error: " + str(e))

class BloombergBridgeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "BBApi"
    _svc_display_name_ = "Web API for Bloomberg Market Data"

    def __init__(self, args):
        try:
            win32serviceutil.ServiceFramework.__init__(self,args)
            servicemanager.LogInfoMsg("Logging to: " + log_location)
            print("Initialising...")
            servicemanager.LogInfoMsg("Initialising...")
            self.hWaitStop = win32event.CreateEvent(None,0,0,None)
            self.isAlive = True
        except Exception as e:
            print("Error: " + str(e))
            servicemanager.LogErrorMsg("Error: " + str(e))

    def SvcStop(self):
        try:
            print("Stopping...")
            servicemanager.LogInfoMsg("Stopping...")
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
            self.isAlive = False
        except Exception as e:
            print("Error: " + str(e))
            servicemanager.LogErrorMsg("Error: " + str(e))

    def SvcDoRun(self):
        try:
            print("Starting...")
            servicemanager.LogInfoMsg("Starting...")
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                  servicemanager.PYS_SERVICE_STARTED,
                                  (self._svc_name_,''))
            self.main()
        except Exception as e:
            print("Error: " + str(e))
            servicemanager.LogErrorMsg("Error: " + str(e))

    def main(self):
        eventlet.spawn(start_server)
        print("Started")
        servicemanager.LogInfoMsg("Started")
        while self.isAlive:
            time.sleep(5)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(BloombergBridgeService)
