# Info

This module pulls price information from external data providers (eg. Bloomberg).
Runs on Python >= 3.4.

# Set up

1. Install: https://sourceforge.net/projects/pywin32/files/pywin32/Build%20220/
2. Run:

    virtualenv -p python3 ./venv
    source ./venv/bin/activate
    pip install -i requirements.txt

# Run tests

    pytest

# Run

Run server (only on Windows with Bloomberg connection):

    python server.py

Run mock server:

    python server.py mock

# Developer installation

    python .\windows-service.py --startup auto install

# Deployment

    cp $PYTHON_HOME/lib/site-packages/blpapi/_internals.pyd .
    python setup.py py2exe

Contents of build\exe.win-amd64-3.4 needs to be zipped.

# User installation

1. Install: https://www.microsoft.com/en-us/download/details.aspx?id=48145
2. Run

    pmbb-service.exe --startup auto install
    pmbb-service.exe start

