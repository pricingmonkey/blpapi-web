# Info

This module pulls price information from external data providers (eg. Bloomberg).
Runs on Python >= 3.4.

# installation and deployment can only be done on windows.

# use windows powershell to run any of the following instructions.
# You need powersheel3

# install scoop (the following command can be found at scoop.sh)
1. Run: set-executionpolicy unrestricted -s cu
2. Run: iex (new-object net.webclient).downloadstring('https://get.scoop.sh')
1. Install: https://sourceforge.net/projects/pywin32/files/pywin32/Build%20220/
2. select pywin for python3.5, and download it
3. open the file, select run and click the next boxes to install.

3. Run: scoop install python
4. you may need to click an OK on a windows pop-up.

# incase you have two version of python installed see this link on how to
# switch into the one you need:
# https://github.com/lukesampson/scoop/wiki/Switching-Ruby-and-Python-Versions


# first time use:

1. Clone the bloombergBridge repo.
2. cd into bloombergBridge.
3. pip install virtualenv
3. create virtual env with: virtualenv venv
4. run: souce venv/bin/activate
5. run: pip install -r requirements.txt



go to: https://www.bloomberglabs.com/api/libraries/
download: C/C++ supported Release.
go to the downloaded file which is zipped. Extract it to C:
cd into the bloapi_cpp_... folder
add the path to an environment variable called BLPAPI_ROOT
restart PowerShell

go to the bloombergBridge directory
run pip install -r requirements.txt


!!!! NOW INSTALL VISUAL STUDIO !!!!!


# before running any of the following instructions cd into bloombergBridge


# Set up - to be run once after you first checkout the code


1. Clone the bloombergBridge repo.
2. cd into bloombergBridge.
3. create virtual env with: virtualenv venv
4. run: souce venv/Scripts/activate
5. run: pip install -i requirements.txt



2. Run: pip install -i requirements.txt
kh

# Developer installation - don't need to run this to deploy

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

