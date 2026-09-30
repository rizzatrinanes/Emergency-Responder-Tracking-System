import threading
import time
import serial
import serial.tools.list_ports
import os
import sys
import webbrowser
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO
import engineio.async_drivers.threading

# ---------------------------------------------------------
# FUNCTION PARA MAHANAP ANG TEMPLATES SA LOOB NG EXE
# ---------------------------------------------------------
def resource_path(relative_path):
    try:
        # Kapag naka-EXE, ang files ay nasa temporary folder (_MEIPASS)
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(__name__, template_folder=resource_path("templates"))

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# ---------------------------------------------------------
# SERIAL CONFIGURATION & AUTO-DETECTION
# ---------------------------------------------------------
BAUD_RATE = 115200
ser = None

def find_and_connect():
    """Hahanapin ang ESP32 CP2102 base sa hardware description"""
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "CP210" in p.description or "USB to UART" in p.description:
            try:
                temp_ser = serial.Serial(p.device, BAUD_RATE, timeout=1)
                return temp_ser
            except Exception:
                continue
    return None

# ---------------------------------------------------------
# SOCKET EVENT: SEND COMMAND TO OLED (Laptop -> ESP32)
# ---------------------------------------------------------
@socketio.on("send_command")
def handle_command(data):
    global ser
    message = data.get("message", "")
    if ser and ser.is_open:
        try:
            # I-send ang text sa Receiver ESP32
            ser.write(f"{message}\n".encode("utf-8"))
            print(f"Command sent to LoRa: {message}")
        except Exception as e:
            print(f"Error sending command: {e}")

# ---------------------------------------------------------
# BACKGROUND THREAD PARA SA PAGBASA NG DATA (ESP32 -> Laptop)
# ---------------------------------------------------------
def serial_reader():
    global ser
    is_connected = False 

    while True:
        # Kapag walang device o nabunot ang device
        if ser is None or not ser.is_open:
            if is_connected:
                is_connected = False
                socketio.emit("device_status", {"connected": False})
            
            ser = find_and_connect()
            if ser is None:
                time.sleep(2) 
                continue
        
        # Kapag kaka-detect lang ng device
        if not is_connected:
            is_connected = True
            socketio.emit("device_status", {"connected": True})

        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8").strip()
                parts = line.split(",")

                # Pure Monitoring: lat, lng, bpm
                if len(parts) == 3:
                    try:
                        lat = float(parts[0])
                        lng = float(parts[1])
                        bpm = int(parts[2])
                        current_time = datetime.now().strftime("%H:%M:%S")

                        # AUTOMATIC ALERT LOGIC (Pure Monitoring)
                        # Ang system mismo ang mag-dedetermine kung emergency
                        is_emergency = bpm > 120 or bpm < 60

                        data = {
                            "lat": lat,
                            "lng": lng,
                            "bpm": bpm,
                            "emergency": is_emergency, # Ipadala ito para sa red blink
                            "time": current_time,
                            "status": "connected"
                        }
                        socketio.emit("update_data", data)
                    except ValueError:
                        pass # Ignore kung may corrupt data
        except Exception:
            ser = None # Reset connection kapag nagka-error
        
        time.sleep(0.05)

# ---------------------------------------------------------
# WEB SERVER ROUTES
# ---------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    # Simulan ang background serial scanning
    thread = threading.Thread(target=serial_reader)
    thread.daemon = True
    thread.start()

    # Kusa nitong bubuksan ang browser
    webbrowser.open("http://127.0.0.1:5000")

    # allow_unsafe_werkzeug=True para sa EXE compatibility
    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=False,
        log_output=False,
        allow_unsafe_werkzeug=True
    )