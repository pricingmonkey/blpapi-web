import sys


def startBbcomm():
    if not sys.platform == "win32":
        return

    CREATE_NEW_CONSOLE = 0x00000010

    try:
        info = subprocess.STARTUPINFO()
        info.dwFlags = 1
        info.wShowWindow = 0
        subprocess.Popen(["c:/blp/api/bbcomm.exe"],
                        creationflags=CREATE_NEW_CONSOLE,
                        startupinfo=info)
    except FileNotFoundError:
        try:
            info = subprocess.STARTUPINFO()
            info.dwFlags = 1
            info.wShowWindow = 0
            subprocess.Popen(["c:/blp/dapi/bbcomm.exe"],
                            creationflags=CREATE_NEW_CONSOLE,
                            startupinfo=info)
        except FileNotFoundError:
            pass
