import sys
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
from server import main as start_server
import threading

class BloombergBridgeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "Pricing Monkey Bloomberg Bridge"
    _svc_display_name_ = "Pricing Monkey Bloomberg Bridge"

    def __init__(self,args):
        print("init")
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)
        self.flag = threading.Event()

    def SvcStop(self):
        servicemanager.LogInfoMsg("Stopping")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.flag.set()

    def SvcDoRun(self):
        print("run")
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        print("main")
        sys.stdout = sys.stderr = open("c:\Windows\Logs\pricing-monkey.log", "a")
        t = threading.Thread(target=start_server)
        t.start()
        self.flag.wait()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(BloombergBridgeService)
