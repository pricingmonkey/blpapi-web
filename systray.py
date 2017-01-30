import os
import sys
import win32api
import win32con
import win32gui_struct
try:
    import winxpgui as win32gui
except ImportError:
    import win32gui

import traceback
import itertools, glob
import threading
import inspect, ctypes
        
from utils import get_main_dir, main_is_frozen
from server import main as start_server

import sys
sys.stdout = sys.stderr = None

class ServerSysTray(object):
    FIRST_ID = 1023
    QUIT = 'QUIT'
    
    def __init__(self,
                 icon,
                 hover_text,
                 menu_options,
                 on_quit=None,
                 default_menu_index=None,
                 window_class_name=None,):
        self.icon = icon
        self.hover_text = hover_text
        self.change_menu_options(menu_options)
        self.on_quit = on_quit
        
        self.default_menu_index = (default_menu_index or 0)
        self.window_class_name = window_class_name or "Tray Program"
        
        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
                       win32con.WM_DESTROY: self.destroy,
                       win32con.WM_COMMAND: self.command,
                       win32con.WM_USER+20 : self.notify,}

        # Register the Window class.
        window_class = win32gui.WNDCLASS()
        hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
        window_class.lpszClassName = self.window_class_name
        window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        window_class.hbrBackground = win32con.COLOR_WINDOW
        window_class.lpfnWndProc = message_map # could also specify a wndproc.
        classAtom = win32gui.RegisterClass(window_class)

        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(classAtom,
                                          self.window_class_name,
                                          style,
                                          0,
                                          0,
                                          win32con.CW_USEDEFAULT,
                                          win32con.CW_USEDEFAULT,
                                          0,
                                          0,
                                          hinst,
                                          None)
        win32gui.UpdateWindow(self.hwnd)
        self.notify_id = None
        self.refresh_icon()

    def change_menu_options(self, menu_options):
        menu_options = menu_options + (('Quit', self.QUIT), )

        self._next_action_id = self.FIRST_ID
        self.menu_actions_by_id = set()
        self.menu_options = self._add_ids_to_menu_options(list(menu_options))
        self.menu_actions_by_id = dict(self.menu_actions_by_id)
        del self._next_action_id

    def _add_ids_to_menu_options(self, menu_options):
        result = []
        for menu_option in menu_options:
            option_text, option_action = menu_option
            if callable(option_action) or option_action is None or option_action == self.QUIT:
                self.menu_actions_by_id.add((self._next_action_id, option_action))
                result.append(menu_option + (self._next_action_id,))
            else:
                print('Unknown item', option_text, option_action)
            self._next_action_id += 1
        return result
        
    def refresh_icon(self):
        # Try and find a custom icon
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(self.icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst,
                                       self.icon,
                                       win32con.IMAGE_ICON,
                                       0,
                                       0,
                                       icon_flags)
        else:
            print("Can't find icon file - using default.")
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if self.notify_id: message = win32gui.NIM_MODIFY
        else: message = win32gui.NIM_ADD
        self.notify_id = (self.hwnd,
                          0,
                          win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                          win32con.WM_USER+20,
                          hicon,
                          self.hover_text)
        win32gui.Shell_NotifyIcon(message, self.notify_id)

    def restart(self, hwnd, msg, wparam, lparam):
        self.refresh_icon()

    def destroy(self, hwnd, msg, wparam, lparam):
        if self.on_quit:
            try:
                self.on_quit(self)
            except:
                traceback.print_exc()
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0) # Terminate the app.

    def notify(self, hwnd, msg, wparam, lparam):
        if lparam==win32con.WM_RBUTTONUP:
            self.show_menu()
        elif lparam==win32con.WM_LBUTTONUP:
            self.show_menu()
        return True
        
    def show_menu(self):
        self.menu = win32gui.CreatePopupMenu()
        self.create_menu(self.menu, self.menu_options)
        
        pos = win32gui.GetCursorPos()
        # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(self.menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                self.hwnd,
                                None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
    
    def create_menu(self, menu, menu_options):
        for option_text, option_action, option_id in menu_options[::-1]:
            item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                            wID=option_id,
                                                            fState=0 if option_action else 3)
            win32gui.InsertMenuItem(menu, 0, 1, item)

    def command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        self.execute_menu_option(id)
        
    def execute_menu_option(self, id):
        menu_action = self.menu_actions_by_id[id]
        if menu_action == self.QUIT:
            win32gui.DestroyWindow(self.hwnd)
        else:
            try:
                menu_action(self)
            except:
                traceback.print_exc()
            
def non_string_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return not isinstance(obj, str)

if __name__ == '__main__':
    from raven.transport.threaded import ThreadedHTTPTransport
    from raven import Client
    client = Client(
        "https://ec16b2b639e642e49c59e922d2c7dc9b:2dd38313e1d44fd2bc2adb5a510639fc@sentry.io/100358?ca_certs={}/certifi/cacert.pem".format(get_main_dir()),
        transport=ThreadedHTTPTransport,
        enable_breadcrumbs=False
    )
    try:
        hover_text = "Web API for Bloomberg Market Data"

        def _async_raise(tid, exctype):
            '''Raises an exception in the threads with id tid'''
            if not inspect.isclass(exctype):
                raise TypeError("Only types can be raised (not instances)")
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid,
                                                          ctypes.py_object(exctype))
            if res == 0:
                raise ValueError("invalid thread id")
            elif res != 1:
                # "if it returns a number greater than one, you're in trouble,
                # and you should call it again with exc=NULL to revert the effect"
                ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
                raise SystemError("PyThreadState_SetAsyncExc failed")

        server = [None]

        def menu_options(is_running):
            if is_running:
                return (("Web API is running...", None), ("Stop", start_stop), )
            else:
                return (("Web API is stopped.", None), ("Start", start_stop), )

        def run_server(systray):
            def func():
                try:
                    systray.change_menu_options(menu_options(is_running = True))
                    start_server()
                finally:
                    systray.change_menu_options(menu_options(is_running = False))
            return func

        def start(systray):
            server[0] = threading.Thread(target=run_server(systray))
            server[0].start()

        def stop():
            if server[0] and server[0].is_alive():
                _async_raise(server[0].ident, KeyboardInterrupt)

        def quit(self):
            stop()

        def start_stop(self):
            if server[0] and server[0].is_alive():
                stop()
            else:
                start(self)

        systray = ServerSysTray(
                "pricingmonkey.ico",
                hover_text,
                menu_options(is_running = False),
                on_quit=quit,
                default_menu_index=1)
        start(systray)
        
        win32gui.PumpMessages()
    except:
        client.captureException()
        traceback.print_exc()
