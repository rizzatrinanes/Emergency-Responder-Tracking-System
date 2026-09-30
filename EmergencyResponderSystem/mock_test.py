import threading
import time
import random
import serial
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- CONFIGURATION ---
SERIAL_PORT = 'COM3' 
BAUD_RATE = 115200

# Try to connect to serial, if fails, we use simulation
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    IS_SIMULATED = False
    print(f"✅ Connected to ESP32 on {SERIAL_PORT}")
except:
    IS_SIMULATED = True
    ser = None
    print("⚠️ ESP32 Not Found. Entering SIMULATION MODE...")

def data_reader():
    """
    Handles both Real Serial and Simulated Data.
    """
    # Default coordinates (Parañaque area)
    lat, lng = 14.4791, 121.0194
    
    while True:
        if not IS_SIMULATED and ser and ser.in_waiting > 0:
            # --- REAL MODE ---
            try:
                line = ser.readline().decode('utf-8').strip()
                parts = line.split(',')
                if len(parts) == 3:
                    lat, lng, bpm = float(parts[0]), float(parts[1]), int(parts[2])
                    broadcast_data(lat, lng, bpm, "REAL")
            except: pass
        
        else:
            # --- SIMULATION MODE ---
            # Randomly pick BPM to test your 120 threshold
            # 70% chance normal, 30% chance critical (para ma-test ang beep)
            if random.random() > 0.7:
                bpm = random.randint(121, 145) # Trigger High Alert
            elif random.random() < 0.1:
                bpm = random.randint(30, 39)   # Trigger Low Alert
            else:
                bpm = random.randint(70, 95)   # Normal
            
            lat += random.uniform(-0.0001, 0.0001)
            lng += random.uniform(-0.0001, 0.0001)
            
            broadcast_data(lat, lng, bpm, "MOCK")
            time.sleep(2) # Send data every 2 seconds

def broadcast_data(lat, lng, bpm, source):
    current_time = datetime.now().strftime("%H:%M:%S")
    status = "🚨 ALERT" if (bpm > 120 or bpm < 40) else "OK"
    
    data = {
        'lat': lat, 
        'lng': lng, 
        'bpm': bpm,
        'time': current_time
    }
    
    socketio.emit('update_data', data)
    print(f"📡 [{source}] {current_time} | BPM: {bpm} ({status}) | Lat: {lat:.5f}")

@socketio.on('send_command')
def handle_command(data):
    message = data.get('message', '')
    print(f"\n[DISPATCH] >>> {message}")
    if ser and ser.is_open:
        ser.write((message + '\n').encode('utf-8'))

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    thread = threading.Thread(target=data_reader, daemon=True)
    thread.start()
    
    print("\n🚀 Dashboard: http://127.0.0.1:5000")
    socketio.run(app, host='127.0.0.1', port=5000, debug=False)