import pythoncom
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
from server import main
import threading

class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "Pricing Monkey Bloomberg Bridge"
    _svc_display_name_ = "Pricing Monkey Bloomberg Bridge"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)
        self.flag = threading.Event()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.flag.set()

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        t = threading.Thread(target=main)
        t.start()
        self.flag.wait()
        raise SystemExit

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)

