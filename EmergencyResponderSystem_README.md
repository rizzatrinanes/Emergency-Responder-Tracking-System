# Emergency Responders Tracking System

A local web application for monitoring responder location and heart-rate
data from an ESP32 device.

The Python application runs a Flask web server and reads serial data
from an ESP32 through a CP210x USB-to-UART connection. The dashboard
uses Socket.IO to update the browser in real time and Leaflet to display
the responder's location.

## Features

-   Real-time heart-rate (BPM) monitoring
-   GPS latitude and longitude display
-   Automatic ESP32/CP210x serial-port detection
-   Hardware connection status
-   Automatic alert detection when BPM is above 120 or below 60
-   Map auto-follow for the latest responder position
-   Automatic map zoom when an alert is detected
-   Text command input for sending messages back to the ESP32
-   Local browser dashboard
-   PyInstaller build configuration

## Technologies

-   Python
-   Flask
-   Flask-SocketIO
-   PySerial
-   HTML / CSS / JavaScript
-   Leaflet.js
-   Socket.IO
-   ESP32
-   CP210x USB-to-UART

## Data Format

The application expects the ESP32 to send one line containing three
comma-separated values:

``` text
latitude,longitude,bpm
```

For example:

``` text
14.4791,121.0194,82
```

The Flask background thread reads the serial data, converts the values,
and broadcasts the result to the web dashboard.

## Alert Logic

The current application marks the responder as being in an emergency
state when:

``` text
BPM > 120
or
BPM < 60
```

When this happens, the dashboard highlights the vital-sign card and
moves the map to the latest coordinates.

## Command Dispatch

The dashboard also has a command field that sends text through the
Socket.IO connection.

The Flask application writes the command to the connected serial device
followed by a newline:

``` text
command\n
```

This is intended for the ESP32 side to receive and process.

## Project Structure

``` text
EmergencyResponderSystem/
├── app.py
├── mock_test.py
├── icon.ico
├── EmergencyResponderSystem.spec
├── Emergency_Responder_System.spec
└── templates/
    ├── index.html
    └── requirements.txt
```

The repository also contains PyInstaller build output in the original
project folder. Build folders and generated executables are better kept
out of the source repository unless they are intentionally published as
releases.

## Requirements

-   Python 3
-   ESP32 device
-   CP210x USB-to-UART driver/device
-   A browser
-   Python packages listed in `templates/requirements.txt`

## Installation

Clone the repository:

``` bash
git clone https://github.com/yourusername/EmergencyResponderSystem.git
cd EmergencyResponderSystem
```

Install the Python dependencies:

``` bash
pip install -r templates/requirements.txt
```

## Running

Start the application:

``` bash
python app.py
```

The application starts a local Flask-SocketIO server at:

``` text
http://127.0.0.1:5000
```

The browser is also opened automatically by the application.

## Hardware Connection

The application scans the available serial ports and looks for a device
whose description contains either:

``` text
CP210
```

or:

``` text
USB to UART
```

The serial connection uses:

``` text
Baud rate: 115200
```

## Simulation

`mock_test.py` contains a separate test implementation that can generate
simulated GPS and BPM data when the ESP32 is not available. It can be
used to test the dashboard and alert behavior without the hardware.

## Building the Executable

The project includes PyInstaller `.spec` files that package the Flask
templates with the application.

A build can be generated with PyInstaller using the appropriate `.spec`
file:

``` bash
pyinstaller EmergencyResponderSystem.spec
```

## Project Status

Prototype / Academic Project
