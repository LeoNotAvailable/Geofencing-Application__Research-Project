"""This module manages all the log messages as well as the logging file. Also, updates the built-in terminal with the log messages and
defines how the Bluetooth and satellite connection state is set."""

from datetime import datetime
import os
from config_manager import load_config, edit_config
import time
import threading
import tkinter as tk


configuration = load_config()
LOG_FILE = configuration["LOG_FILE"]


# All these are global variables that will be accessible in the principal thread, but editable outside in this module.
_ui_log_callback = None
_bluetooth_label = None
_reconnect_button = None




def set_ui_log_callback(callback_func):
    global _ui_log_callback
    _ui_log_callback = callback_func

def set_bluetooth_label(label):
    global _bluetooth_label
    _bluetooth_label = label

def set_reconnect_button(button):
    global _reconnect_button
    _reconnect_button = button



def check_log_file(): # Just creates a log file in case it isn't present. All the "extra" documents should be created whenever they miss.
    date = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as file:
            file.write("===== STARTING OF THE LOG FILE =====\n\n")
            header = f"===== LOG {date} ====="
            file.write(f"____________________________________________\n\n\n{header}\n\n")
            edit_config("LAST_DATE", date)
            file.flush()
            

def log(message): # Writes a string with the message, including the exact time it was emmited. Also updates the date of the log file if it's necessary.
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        if configuration.get("LAST_DATE") != date: # If the last saved date isn't the same as today, updates it and writes it in the log file.
            configuration["LAST_DATE"]= date # This function relies on the config file, so if it is deleted, the date will be writen again.
            edit_config("LAST_DATE", date)
            header = f"===== LOG {date} ====="
            file.write(f"____________________________________________\n\n\n{header}\n\n")
            file.flush()
        final_message= f"[{time}] --> {message}\n" # Writes the message
        file.write(final_message)
        file.flush()
    
    if _ui_log_callback is not None:
        _ui_log_callback(final_message)


# Log tailer, for the build in terminal. The terminal works printing wathever change is made in the log file.

def start_log_tailer(root, text_widget):
    log_file = configuration["LOG_FILE"]

    if not os.path.exists(log_file):
        open(log_file, 'w').close() # We create the file if it doesn't exists.
    last_size = os.path.getsize(log_file) # We'll know when there's an update when the file size changes, so we get the initial measure to compare.

    def tail_loop():
        nonlocal last_size # It isn't a local or global variable, we just use it here
        while True:
            try:
                current_size = os.path.getsize(log_file)
                if current_size < last_size: # This should never happen, the last size cannot be bigger than the new!
                    last_size = 0 # We just fix it here

                if current_size > last_size: # There has been an update
                    with open(log_file, "r", encoding="utf-8") as f:
                        f.seek(last_size) # We just see from the last position we defined
                        new_lines = f.read() # We save that info in this variable
                        last_size = f.tell() # We update the last position we checked

                    if new_lines:
                        root.after(0, lambda lines=new_lines: _update_terminal(lines, text_widget))
                time.sleep(0.5)  # The log will be checked every half second
            except:
                time.sleep(2)

    threading.Thread(target=tail_loop, daemon=True, name="LogTailer").start()
    # By using a thread, we're defining a secondary thread named LogTailer that will run this. If we just executed the function,
    # the while True loop will freeze the GUI, as the code would wait to the function to finish, but it would never happen.

def _update_terminal(text, text_widget):
    type_logs = {
        "[INFO]": "yellow",
        "[BLUETOOTH]": "lightblue",
        "[ERROR]": "red",
        "[WARNING]": "lightgreen"
    }

    text_widget.config(state=tk.NORMAL)

    for line in text.splitlines(True):  # Don't delete the '\n'
        color = "white" # If the code don't find the correct color, instead of breaking, defines the default as white.
        for type_log, c in type_logs.items():
            if type_log in line:
                color = c
                break 

        if color not in text_widget.tag_names(): # In case the color variable isn't defined in the terminal
            text_widget.tag_config(color, foreground=color)

        text_widget.insert(tk.END, line, color) # We print the line at the end of the terminal with its respective color.

    text_widget.see(tk.END) # It scrolls to the end at the moment
    text_widget.config(state=tk.DISABLED)


def actualize_bluetooth_state(state): # This actualizes a label that, by its background color, indicates the Bluetooth and satellite connection state.
    states_colors = {
        "FIXED": "darkgreen",
        "UNSURE": "lightgreen",
        "SEARCHING": "yellow",
        "CONNECTING": "orange",
        "DISCONNECTED": "red"
    }
    color = states_colors.get(state, "grey") # Once given a state, it sets its color by the dictionary defined previously. If it doesn't find it, just sets gray as the color.
    if _bluetooth_label is not None:
        _bluetooth_label.after(0, lambda: _bluetooth_label.config(bg=color)) # We update the Bluetooth state indicator
    else:
        log(f"[ERROR] No Bluetooth label set, state: {state}")

    if _reconnect_button is not None:
        def update_button(): # If the Bluetooth searching function isn't running and there's no connection, the reconnect button is enabled.
            if state == "DISCONNECTED":
                _reconnect_button.config(state=tk.NORMAL)
            else:
                _reconnect_button.config(state=tk.DISABLED)
        _reconnect_button.after(0, update_button)

