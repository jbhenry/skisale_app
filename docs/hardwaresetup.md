# Hardware Setup & Installation

This document details the specific hardware and configurations we use at Mt. Brighton Ski Patrol's swap. Where specific commands are documented here, they are specific to running under native Windows. Other documents in this repository may show commands for a Linux, MacOS or WSL environment.

## Equipment Inventory

We currently use the following hardware to run the swap:

* One laptop as the 'server' machine. Currently a Dell laptop running Windows 10. It has a label marking it as the server. This machine can also be used as a workstation to process check-in, sales, and pickup transactions. Most admin functions will be run from this machine. 
* Workstation laptops. We currently have 4 Dell laptops running Windows 7. These machines use the web browser to connect to the application running on the server machine. 
* Printers
    * Two Pantum laser printers - for check-in and pickup receipts for vendors. Also used for printing final reports and vendor checks at the end of the swap. Network printers connected via WiFi to the router.
    * Two Rongta receipt printers - print sales receipts for customer purchases. Network printers connected via Ethernet to the router.
* Bar-code scanners. We have a selection of scanners, some of which connect via USB cable, others are wireless with a USB dongle.
* Router. The swap runs on an isolated LAN managed with our own router. This network **DOES NOT** have Internet access. Currently using a Linksys WRT54G "blue-box" router. Router SSID and password are labeled on the device. All devices connect to the network via WiFi, with the exception of the two receipt printers, which use Ethernet. 
* Square credit card readers. We have two bluetooth-connected card readers. Access to the WiFi in the lodge has at times been... challenging.
    * If we can get access to the lodge WiFi, we can use the patrol's two iPads to run the Square register app to process credit cards.
    * If we cannot get access to the lodge WiFi, we have in the past used individual's cell phones either as a hotspot for the tablets, or used the phone directly with the Square app and readers.
    * Note that credit card processing via Square is entirely separate from the main application. 

## Setup a new laptop workstation

Setup of a laptop to be used as a workstation (not server) machine is relatively simple. 

Assuming a Windows machine:
1. Make sure Windows is installed and relatively up to date. Run Windows Update if needed. 
1. Follow the naming conventions labeled on our other laptops, and create a user ID and password for the machine. Give it a machine name following the same convention. Create a label with the machine name, ID, and password.
1. Install an alternative browser if needed. Required only if the included browser does not function properly with the application. 
1. Connect to the isolated LAN environment. SSID and password are on the router.
1. Install printer drivers. Drivers are located on the server machine in C:\skisale, or can be downloaded from the manufacturers web site.
    * Rongta receipt printer driver.
    * Pantum laser printer driver.
1. Setup printers
    * Each printer has the IP address labeled on the side.
    * Two instances of the Rongta receipt printer
    * Two instances of the Pantum laser printer
    * Set the closest Rongta as the default printer. 
1. Create a shortcut on the desktop to the server URL **http://\<hostname\>:5000**, where \<hostname\> is the IP address of the server machine. 

We've only had Windows laptops so far, but a Linux, Mac, or Chromebook machine should work just as well for a workstation. The only requirements are a web browser, access to our LAN, and drivers for our printers. Setup would be very similar to above. An iPad or other tablet might also work as a workstation, with the caveat that printing might not work as designed due to lack of drivers for our printers. This has not been tested. 

## Setup a new server

Setting up a new server machine is a little more involved. The below again assumes a Windows machine is being used. Setup for Linux or Mac will be different.

1. Make sure Windows is installed correctly.
1. The next steps require Internet access. Connect to a WiFi network with Internet access. 
1. Install Python.

    Open a command prompt as administrator and type
    ```
    winget install 9NQ7512CXL7T
    ```
    This will download and install the Python install manager, and install the latest version of Python. See [Python install manager page](https://www.python.org/downloads/release/pymanager-260/) for more information.
1. Create a Python virtual environment (venv) to run the software
    ```
    cd c:\
    python -m venv skisale_app
    ```
    This will create the C:\skisale_app directory, and a several subdirectories and files under it. 
1. Download the latest version of the skisale_app application as a zip file from the [Github repository](https://github.com/jbhenry/skisale_app/releases) release page. 
1. Extract the .zip file into the C:\skisale_app directory. Do not allow it to overwrite the pyvenv.cfg file!
1. Activate the virtual environment, and install the Python package requirements. Open a command prompt and type:
    ``` 
    cd C:\skisale_app
    Scripts\activate.bat
    pip install -r requirements.txt
    ```
1. Now you can run the development server to check that everything is installed correctly. In the same command prompt type:
    ```
    python app.py
    ```
1. Connect your browser to http://localhost:5000. You should see the complete application, with a sample database of a few vendors and items. Hit CTRL-C to shut down the dev server.
1. The database is stored in a SQLite3 database in C:\skisale_app\var\app-instance\skisale.db. If you have a copy from a past swap that you want to use (to maintain the list of Vendors), you can simply replace this file and re-start the server.
1. Connect to the isolated LAN environment. SSID and password are on the router.
1. Start the production server. In a command prompt:
    ```
    cd C:\skisale_app
    Scripts\activate.bat
    python serve.py
    ```
    This will start the application running under the Waitress web server. On first run, you may be asked to allow it to access the network.
1. You should now be able to connect to the server from either the local browser, or from any of the workstation machines. 

