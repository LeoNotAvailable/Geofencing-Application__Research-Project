# Geofencing-Application__Research-Project
This repository contains the final version of my geofencing application, developed in Python for a pre-universitary Research Project. Works with an ESP32 STEAMakers via bluetooth, the Arduino code is also uploaded here.

The geofencing term refers to a geographic delimitation, when a program tells if you're inside or outside an area. It have multiple uses, especially in percision agriculture and animal care, location-based advertising, control of the position of a specific person, anti-theft systems...


This is a code divided in six modules, that tries to understand how to create an application with a user interface, while receiving information and having different processes running simultaneously. With this project I've worked:
- Managing Bluetooth connection (errors of format of the information, reconnection, timeouts...)
- Modularizing a code in order of making it as most escalable as possible, working with classes
- Creating a strong enogh log system that allows to check the progress of the project, and integrating a terminal in the UI that shows those messages
- Managing areas with its proper structure, while showing them to the user in an understendable format. Editing those areas with a map instead than by commands or text.
- Implementing the geofencing function


The application is structured in six Python modules, each with a specific responsibility. This modular design allows the code to be scalable, maintainable, and easy to debug.

**geofencing_ui_V5.py**
This is the main executable file. It creates the complete graphical user interface (GUI) using tkinter, sets up all buttons, labels, map view, and log terminal, and connects them to the logic layer. It also starts the Bluetooth reading thread and the log tailer.

**geofencing_logic_V5.py**
Contains the core logic class (GeofenceLogic) that handles everything the user interacts with: managing areas (create, edit, delete), updating the map, controlling the geofencing state, handling position updates, and responding to button actions. It also loads and saves area data to areas.json.

**is_inside_area_function_2.py**
Implements the geofencing algorithm. It uses the shapely library to determine whether the current GPS position is inside a defined polygonal area. It also includes a helper function to order points correctly for polygon creation.

**geofencing_read_bt_2.py**
Manages the Bluetooth communication with the ESP32. It continuously reads the serial port, parses incoming JSON messages with GPS data, handles connection timeouts, and attempts automatic reconnection. All received data is passed to the logic layer via a callback.

**debug_logger_2.py**
Provides a complete logging system. It writes all important events to a log file (debug.log) with timestamps, updates the built-in terminal in real time with colored messages, and controls the Bluetooth status indicator (green, yellow, red, etc.) based on connection state.

**config_manager.py**
Handles the configuration file (config.json). It loads settings (like COM port, timeouts, colors), creates a default config if missing, and allows other modules to safely read or modify configuration values at runtime.



The libraries I've used in this project, that are present in different modules, are:

- tkinter
- tkintermapview
- threading
- time
- datetime
- json
- os
- serial
- shapely.geometry
- math

The hardware that I've been using in this project is:
- ESP32 STEAMakers microcontroller
- GPS Moudle NEO-7M
- Active antenna
- LCD Display i2c

Also, we've used an rtl-sdr V3, and some passive antennas, although there're not present in the final application.


How to set the project for it to work:

1. Connect the GPS's TXD pin with the RXD pin of the microcontroller (D5 in this case), as well as the ground an VCC pins. Connect also the LCD display.
<img width="246" height="231" alt="Connexion" src="https://github.com/user-attachments/assets/137679cd-6812-433a-a864-16f6d91a7561" />
2. Upload the arduino code (ESP32_main.ino) to the microcontroller
3. Load the python code to a code environment, with the libraries uploaded.
4. Execute geofencing_ui.py, this is the only code that must be executed. The other five modules should be in the same directory, but all the other elements will be created automatically. Those elements are: config.json, areas.json, debug.log and instructions.txt.


Some images of the project:
Initial version of the project:
<img width="747" height="592" alt="Initial version" src="https://github.com/user-attachments/assets/7b5c0857-f08b-4253-a5f2-8bba0e2376b7" />

Some of the elements involved in the area editing:
<img width="1198" height="381" alt="Edit areas functionalities" src="https://github.com/user-attachments/assets/2e1bca3b-d0df-4194-8b22-ac05bf90d3f6" />

The final version of the application, functional and intuitive:
<img width="898" height="820" alt="Final application" src="https://github.com/user-attachments/assets/0522e5ae-d46e-45bf-b227-1b18b297db2e" />


In order of viewing some of the project materials, you can visit this [drive folder](https://drive.google.com/drive/folders/1t67lw22AGPEhrx539AiQmShMc4wpZvie?usp=sharing).



This project is licensed under the MIT License, so you can download, edit, publish and use this code. Can be used for comertial purpouses as well, as long as you indicate the author.
