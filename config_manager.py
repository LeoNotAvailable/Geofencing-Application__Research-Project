"""This module manages the configuration file and its default version in case it is corrupted or deleted."""

import json
import os
from datetime import datetime

CONFIG_FILE = "config.json"

default_config = {
    "COM_PORT": "COM6",
    "BAUDRATE": 115200,
    "AREAS_FILE": "areas.json",
    "LOG_FILE": "debug.log",
    "INFO_FILE": "instructions.txt,",
    "LAST_DATE": datetime.now().strftime("%Y-%m-%d"),
    "BT_TIMEOUT": 5,
    "BT_CONNECTING_CYCLES": 5,
    "POSITION_TIMEOUT": 5, # Time since the last position fix to remove the current position
    "ZOOM_LEVEL": 15, 
    "MARKER_COLOR_OUTSIDE": "grey",
    "MARKER_COLOR_CIRCLE": "white",
    "MARKER_POSITION_COLOR_OUTSIDE": "red",
    "MARKER_POSITION_COLOR_CIRCLE": "orange",
    "MARKER_POSITION_COLOR_TEXT": "darkred",
}

def load_config(): # Returns the actual configuration. In case it doesn't exsist, it creates it and returns the default values.
    if not os.path.exists(CONFIG_FILE):
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] While loading the configuration : {e}")
        return default_config

def save_config(config): # Saves the configuration in the config file.
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def edit_config(key, value): # Edits a specific characteristic of the configuration.
    config= load_config()
    config[key]= value
    save_config(config)
