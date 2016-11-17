# Info

This module pulls price information from external data providers (eg. Bloomberg).
Runs on Python == 3.4.

# Windows

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

If you get an error saying "Error: Microsoft Visual C++ 10.0 is required" please follow instructions from here: http://stackoverflow.com/questions/28251314/error-microsoft-visual-c-10-0-is-required-unable-to-find-vcvarsall-bat

# Run (development instructions)

## Server in terminal mode

    python .\server.py mock

## Windows service in background mode

    python .\windows-service.py --startup auto install

# Deploy

## Build into Windows executable

Make sure you have Inno Setup installed, and the path to Inno Setup
in the script below is correct.

    cp $PYTHON_HOME/lib/site-packages/blpapi/_internals.pyd .
    python setup.py py2exe
    & 'C:\Program Files (x86)\Inno Setup 5\ISCC.exe' .\pmbb.iss

The result is a setup file in "./dist" directory.

## Install manually

1. Unzip deployment package on the user's computer.
2. Go to URL and install: https://www.microsoft.com/en-us/download/details.aspx?id=48145
3. Go to a directory where deployment package was unzipped and run:

    run-service.exe --startup auto install
    run-service.exe start

* In order to debug you can run the server in terminal mode as well (make sure Windows
service is stopped, otherwise this will not work):

    run.exe

# Automatic user installation

TBD (use Inno setup and pmbb.iss file as input)

# Mac

# First time use (run once after checking out the code)

Run:

    pip install virtualenv
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements-dev.txt -r requirements.txt
