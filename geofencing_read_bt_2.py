"""This module takes care of all the Bluetooth connection logic, reading the port, managing reconnections and showing errors."""

import serial
import json
import time
from config_manager import load_config
from debug_logger_2 import log, actualize_bluetooth_state


configuration= load_config()

PORT = configuration["COM_PORT"]
BAUD = configuration["BAUDRATE"]


def read_port(port=PORT, baud=BAUD, callback=None):
    m= 0
    ser = None
    last= 0
    while True:
        if ser: # If there's a serial connection... the first iteration won't be.
            m= 0
            line = ser.readline().decode(errors="ignore").strip() # We get the last line
            if line: # If there's a new message
                last = time.time() # In order of managing the timeout
                try:
                    msg = json.loads(line)
                    print(f"[BLUETOOTH] Received the message {msg}") # This should not be log as it is in the normal functioning of the application,
                        # because the log file would be overloaded. Just for viewing, IT COULD BE REMOVED.
                    actualize_bluetooth_state(msg["estado"]) # This will indicate the satellite connection state.
                    if callback:
                        callback(msg)
                except json.JSONDecodeError:
                    log(f"[ERROR] [BLUETOOTH] While decoding this json message: {line}")

            # This part is important, because if the microcontroler restarts, the connection will still be defined although it's not longer being used.
            if time.time() - last > configuration["BT_TIMEOUT"]: # If there has been no message for the timeout time established...
                log("[BLUETOOTH] TIMEOUT: >5 s without messages --> Port closed") # The port closes
                actualize_bluetooth_state("CONNECTING")
                ser.close()
                ser= None
                last = time.time()
                time.sleep(0.2)
        else:  # If there's no serial connection...
            if m <= configuration["BT_CONNECTING_CYCLES"]: # The code will try to connect during the cycles given by default
                try:
                    if m == 0: # This is the first iteration of searching a connection
                        log(f"[BLUETOOTH] Starting connection to PORT {port}...")
                        actualize_bluetooth_state("CONNECTING")
                    else: # The code has been trying to connect for "m" turns.
                        log(f"[BLUETOOTH] Trying to reconnect to PORT {port}...") 
                        actualize_bluetooth_state("CONNECTING")
                    time.sleep(0.1)
                    ser= serial.Serial(port, baud, timeout=2) # This make take some seconds, if it cannot connect, it sends an error, so takes the execution to the except section instead of continuing.
                    log(f"[BLUETOOTH] Connected to {port}") # The connection has been established.
                    actualize_bluetooth_state("SEARCHING")
                    last = time.time()
                except Exception as e:
                    log(f"[ERROR] While trying to connect to the bluetooth device: {e}") # This usualy means that there's no connection established and the max time has been spend.
                    actualize_bluetooth_state("CONNECTING")
                    time.sleep(1)
                    m+= 1
            else: # Once the "m" turns has been spend, stops searching connection. Can be reactivated with the Reconnect button.
                log(f"[WARNING] Couldn't establish connection to PORT {port}. The time finished.")
                actualize_bluetooth_state("DISCONNECTED")
                return # Stops the loop

