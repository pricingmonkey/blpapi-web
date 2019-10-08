# Info

This module pulls price information from external data providers (eg. Bloomberg).
Windows: Runs on Python == 3.4.
MacOS: Runs on Python == 3.7.

# Windows (see the end of doc for mac instructions)

Use Windows Power Shell 3 to run any of the following instructions.

# Set up your machine

1. Open Power Shell.
2. Run:

        set-executionpolicy unrestricted -s cu

3. Install scoop:

        iex (new-object net.webclient).downloadstring('https://get.scoop.sh')

4. Install latest version of Python 3.4 from https://www.python.org/downloads/.
5. Go to https://sourceforge.net/projects/pywin32/files/pywin32/Build%20220/,
download pywin for python 3.4 and install it.
6. Configure PATH to include your main Python 3.4 directory and scripts
directory (eg. C:\Python3.4 and C:\Python34\Scripts).
7. Go to https://www.bloomberglabs.com/api/libraries/ and download C/C++ supported
release.
8. Go to the downloaded file which is zipped. Extract it directly to C:/
9. Add environment variable BLPAPI_ROOT to point to directory containing previously
extracted Bloomberg C++ API.
10. Install Visual Studio Community version from
https://www.visualstudio.com/en-us/downloads/download-visual-studio-vs.aspx
11. Restart all open PowerShell terminals.

# First time use (run once after checking out the code)

Run:

    pip install virtualenv
    virtualenv venv
    venv/Scripts/activate
    pip install -r requirements-dev.txt -r requirements.txt -r requirements-deploy.txt
    cp venv\Lib\site-packages\blpapi\_internals.pyd .

If you get an error saying "Error: Microsoft Visual C++ 10.0 is required" please follow instructions from here:
(preferrably) https://stackoverflow.com/a/35958285/6306919
or here:
(in case previous solution doesn't work) http://stackoverflow.com/questions/28251314/error-microsoft-visual-c-10-0-is-required-unable-to-find-vcvarsall-bat

# Run (development instructions)

## Server in terminal mode

    python .\server.py --simulator

## Windows service in background mode

    python .\windows-service.py --startup auto install

# Deploy

## Build Windows installer

Before proceeding you will need to apply a patch presented below to
your py2exe module (you should find it in %PYTHON_HOME%/Lib/site-packages/py2exe):

    diff --git a/hooks.py b/hooks-patched.py
    --- a/hooks.py
    +++ b/hooks-patched.py
    @@ -291,14 +291,14 @@ def hook_six(finder, module):
                     self.__finder.safe_import_hook(renamed, caller=self)
                     mod = self.__finder.modules[renamed]
                     # add the module again with the renamed name:
    -                self.__finder._add_module("six.moves." + name, mod)
    +                self.__finder._add_module("six.moves.py2exe." + name, mod)
                     return mod
                 else:
                     raise AttributeError(name)

         m = SixImporter(finder,
    -                    None, "six.moves", finder._optimize)
    -    finder._add_module("six.moves", m)
    +                    None, "six.moves.py2exe", finder._optimize)
    +    finder._add_module("six.moves.py2exe", m)

Make sure you have Inno Setup installed, and the path to Inno Setup
in the script below is correct.

    cp $PYTHON_HOME/lib/site-packages/blpapi/_internals.pyd .
    python setup.py py2exe
    & 'C:\Program Files\Microsoft SDKs\Windows\v7.1\Bin\signtool.exe' sign /f <CERTIFICATE_LOCATION> /n "<COMPANY_NAME>" /p <PASSWORD> /a .\build\run.exe
    & 'C:\Program Files\Microsoft SDKs\Windows\v7.1\Bin\signtool.exe' sign /f <CERTIFICATE_LOCATION> /n "<COMPANY_NAME>" /p <PASSWORD> /a .\build\run-service.exe
    & 'C:\Program Files (x86)\Inno Setup 5\ISCC.exe' .\installer.iss
    & 'C:\Program Files\Microsoft SDKs\Windows\v7.1\Bin\signtool.exe' sign /f <CERTIFICATE_LOCATION> /n "<COMPANY_NAME>" /p <PASSWORD> /a .\dist\bloomberg-web-api-setup.exe

The result is a setup file in "./dist" directory.

Before publishing the installer submit it to Norton Symantec for whitelisting: https://submit.symantec.com/whitelist/

## Install manually

1. Unzip deployment package on the user's computer.
2. Go to URL and install: https://www.microsoft.com/en-us/download/details.aspx?id=48145
3. Go to a directory where deployment package was unzipped and run:

        run-service.exe --startup auto install
        run-service.exe start

* In order to debug you can run the server in terminal mode as well (make sure Windows
service is stopped, otherwise this will not work):

        run.exe

# Mac

# First time use (run once after checking out the code)

Run:

    pip install virtualenv
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements-dev.txt -r requirements.txt

## To run Server from terminal

    python server.py --simulator

## To build MacOS app

1. Go to https://www.bloomberglabs.com/api/libraries/ and download C/C++ supported
release for MacOS.
2. Go to the downloaded file which is zipped. Extract it to selected directory.
3. Add environment variable BLPAPI_ROOT to point to directory containing previously
extracted Bloomberg C++ API.

Run:

    pip install git+https://github.com/msitt/blpapi-python
    cp ./venv/lib/python3.7/site-packages/blpapi/_internals.cpython-37m-darwin.so .
    python setup.py py2app

You can make sure executable works by running dist/BBAPI.app/Contents/MacOS/BBAPI. At the
minimum - even where there is no connectivity to Bloomberg Terminal - you should see no other
errors than **bloomberg.session.BrokenSessionException: Failed to start session on localhost:8194**.

Caveat:
  - Error "Mismatch between C++ and Python SDK libraries." means that a version
    of blpapi-python and ext/libblpapi3_64.so do not match. Resolving this can
    be quite tricky, but you can access wider range of blpapi-python at
    **pip install git+https://github.com/msitt/blpapi-python#vX.Y.Z** and blpapi-cpp
    at **https://bloomberg.bintray.com/BLPAPI-Experimental-Generic/**
    
