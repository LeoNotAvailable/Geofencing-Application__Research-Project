"""This module is the executable of the project. It defines and updates every element the UI has, and imports as a class al the logic they will
use."""

import tkinter as tk
import tkintermapview as tkmap
from geofencing_logic_V5 import GeofenceLogic
import threading
from time import sleep
from config_manager import load_config
from geofencing_read_bt_2 import read_port
from is_inside_area_function_2 import is_inside_area
from debug_logger_2 import log, start_log_tailer, set_bluetooth_label, set_reconnect_button

configuration= load_config()

def start_bt_thread(geofence: GeofenceLogic): # It starts the port reading as a secondary thread.
    def loop():
        read_port(callback=lambda msg: execute_action(msg, geofence))
    threading.Thread(target=loop, daemon=True).start()

def execute_action(msg, geofence: GeofenceLogic): # It actualizes the current position and checks the geofencing function if activated.
    try:
        lat = msg.get("lat")
        lon = msg.get("lon")
        state= msg.get("estado")
        if lat is not None and lon is not None:
            if not state == "SEARCHING": # Cannot give a position if there's no fix
                geofence.create_marker(lat= lat, lon= lon)
                geofence.actualize_current_position(lat= lat, lon= lon)

                if geofence.geofence_button.cget("text")== "Stop" and geofence.polygon: # If the geofencing function is activated.
                    inside = is_inside_area(lat, lon, geofence.polygon.position_list)
                    if inside:
                        log(f"[INFO] The positioning device is inside the area!")
                        logic.geofence_status.config(fg= "lightblue", bg= "green", text= "INSIDE THE AREA!")
                    else:
                        log(f"[INFO] The positioning device is NOT inside the area!")
                        logic.geofence_status.config(fg= "lightblue", bg= "darkred", text= "OUTSIDE THE AREA!")

    except Exception as e:
        log(f"[ERROR] While executing execute_action: {e}")

def on_map_click(event): # Converts the coords of the click in lat and lon. 
    lat, lon = Map.get_position(event.x, event.y)
    button = event.num  # 1=left, 2=right, 3=mid


# Defining the window
Geofence = tk.Tk()
Geofence.title("Geofencing Application - Leo Sarria")
Geofence.geometry("800x700")
Geofence.resizable(False, False)

Geofence.grid_rowconfigure(0, weight=1)
Geofence.grid_rowconfigure(1, weight=0)
Geofence.grid_columnconfigure(0, weight=0)
Geofence.grid_columnconfigure(1, weight=1)


# Frames
frame_left = tk.Frame(Geofence)
frame_left.grid(row= 0, column= 0, sticky= "nsew", padx= 5, pady= 5)
frame_right = tk.Frame(Geofence)
frame_right.grid(row= 0, column= 1, sticky= "nsew", padx= 5, pady= 5)
frame_bottom = tk.Frame(Geofence, height=110)
frame_bottom.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0,5))
frame_bottom.grid_propagate(False)  # manitains a fix height

frame_right.grid_rowconfigure(0, weight=0)
frame_right.grid_rowconfigure(1, weight=1)
frame_right.grid_columnconfigure(0, weight=1)

# Left Side
# Writting and list spots
area_name = tk.Entry(frame_left, width= 40)
area_name.grid(row= 0, column= 0, columnspan= 2, padx= 5, pady= 5, sticky= "ew")
area_points = tk.Text(frame_left, width= 40, height= 5, bg= "lightgrey")
area_points.grid(row= 1, column= 0, columnspan= 2, padx= 5, pady= 5, sticky= "nsew")
area_list= tk.Listbox(frame_left, width= 40, height= 20)
area_list.grid(row= 2, column= 0, columnspan= 2, padx= 5, pady= 5, sticky= "nsew")
area_list.config(selectmode=tk.SINGLE)

area_name.config(state= tk.DISABLED)
area_points.config(state= tk.DISABLED)
area_list.config(state= tk.NORMAL)

# Buttons
delete_button = tk.Button(frame_left, text= "Delete")
delete_button.grid(row= 3, column= 0, padx= 5, pady= 5, sticky= "ew")
save_add_button = tk.Button(frame_left, text= "Add")
save_add_button.grid(row= 3, column= 1, padx= 5, pady= 5, sticky= "ew")
edit_button = tk.Button(frame_left, text= "Edit")
edit_button.grid(row= 4, column= 0, padx= 5, pady= 5, sticky= "ew")

delete_button.config(state= tk.NORMAL)
save_add_button.config(state= tk.NORMAL)
edit_button.config(state= tk.DISABLED)
info_button = tk.Button(frame_left, text= "Info", bg= "lightyellow", border= 3)
info_button.grid(row= 4, column= 1, padx= 5, pady= 5, sticky= "ew")

lab_x= tk.Label(frame_left, text= "")
lab_x.grid(row= 5, column= 0)
lab_3= tk.Label(frame_left, text= "Logs Terminal:")
lab_3.grid(row= 6, column= 0, sticky= "s")
log_button= tk.Button(frame_left, text= "Log File")
log_button.grid(row= 6, column= 1, sticky= "s", padx= 3)



# Right Side
# Map
Map = tkmap.TkinterMapView(frame_right)
Map.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
Map.set_position(41, 2)


# Positioning info and controls
frame_positioning= tk.Frame(frame_right)
frame_positioning.grid(row= 0, column= 0, sticky= "ew", padx= 5, pady= 5)


lab_0= tk.Label(frame_positioning, text= "Current Position (°): ")
lab_0.grid(row= 0, column= 0, padx= 4)
lab_1= tk.Label(frame_positioning, text= "lat: ")
lab_1.grid(row= 0, column= 1, padx= 4)
lab_2= tk.Label(frame_positioning, text= "lon: ")
lab_2.grid(row= 0, column= 3, padx= 4)
ui_lat= tk.Label(frame_positioning, width= 10, anchor="w") # Text box with lat for entering value
ui_lat.grid(row= 0, column= 2)
ui_lon= tk.Label(frame_positioning, width= 10, anchor="w") # Text box with lon for entering value
ui_lon.grid(row= 0, column= 4)
center_button= tk.Button(frame_positioning, text= "Center View")
center_button.grid(row= 0, column= 5, padx= 6, sticky= "e")




# Bottom Side
#Terminal (logs)
terminal = tk.Text(frame_bottom, height=5, width=50, state=tk.DISABLED, bg="black", font=("Courier", 8))
terminal.grid(row=0, column=0, sticky="we", padx=10)
terminal_scroll = tk.Scrollbar(frame_bottom, orient="vertical", command=terminal.yview)
terminal_scroll.grid(row=0, column=1, sticky="ns")
terminal.config(yscrollcommand=terminal_scroll.set)

# Connection and Geofencing elements
others_frame= tk.Frame(frame_bottom)
others_frame.grid(row= 0, column= 1, padx= 10)

lab_4= tk.Label(others_frame, text= "Bluetooth and Satellite Connection: ")
lab_4.grid(row= 0, column= 0, padx= 2)
connection_status= tk.Label(others_frame, text= "                   ", bg= "grey")  # Shows by the colour the bluetooth connection (green, yellow or red), gray is default for errors 
connection_status.grid(row= 0, column= 1)
reconnect_button= tk.Button(others_frame, text= "Reconnect")
reconnect_button.grid(row= 0, column= 2)
reconnect_button.config(state= tk.DISABLED)

lab_5= tk.Label(others_frame, text= "Geofencing Applicaction:  ")
lab_5.grid(row= 1, column= 0, padx= 5)
geofence_button = tk.Button(others_frame, text= "Start")
geofence_button.grid(row= 1, column= 1, pady= 5)
geofence_status= tk.Label(others_frame, text="Start the application", fg= "black", bg= "lightgrey", width= 16)
geofence_status.grid(row= 1, column= 2, sticky= "ew")


# Import the logic class
logic= GeofenceLogic(area_name= area_name, area_points= area_points, area_list= area_list, delete_button= delete_button,
                     save_add_button= save_add_button, edit_button= edit_button, tk_map= Map, geofence_button= geofence_button,
                     geofence_status= geofence_status, reconnect_button= reconnect_button, connection_status= connection_status,
                     terminal= terminal, ui_lat= ui_lat, ui_lon= ui_lon, center_button= center_button)


set_bluetooth_label(logic.connection_status)
set_reconnect_button(reconnect_button)

def reconnect_bluetooth():
    logic.reconnect_button.config(state= tk.DISABLED)
    Geofence.after(3000, lambda: start_bt_thread(logic))

def add_marker_event(coords):
    if logic.edit_name or logic.adding:
        __ = Map.set_marker(coords[0], coords[1], text="", marker_color_outside= configuration["MARKER_COLOR_OUTSIDE"], marker_color_circle= configuration["MARKER_COLOR_CIRCLE"], command= logic.remove_map_marker) # We create markers that'll remove when clicked
        logic.new_markers.append(coords)
        logic.actualize_polygon()
    else:
        logic.new_markers= []

Map.add_right_click_menu_command(label="Add Marker",
                                        command=add_marker_event,
                                        pass_coords=True) # Adds the command to a contextual menu

# Here, we define every command the buttons will execute
area_list.bind("<<ListboxSelect>>", logic.area_selected) # If the area list is clicked on, selecting an area
delete_button.config(command=logic.delete_pressed)
save_add_button.config(command=logic.save_add_pressed)
edit_button.config(command=logic.edit_pressed)
geofence_button.config(command=logic.geofencing_function)
center_button.config(command= logic.center_view)
reconnect_button.config(command= reconnect_bluetooth)
log_button.config(command= logic.open_log_file)
info_button.config(command= logic.open_instructions_file)



Map.bind("<Button>", on_map_click)

logic.refresh_area_list()

start_log_tailer(Geofence, terminal) # Starts the built-in terminal logic
sleep(0.1)

log("\n\n[INFO] Application Started!\n")


# start_bt_thread(logic) --> Sometimes didn't open the principal window, so this fixes it.
Geofence.after(3000, lambda: start_bt_thread(logic))

Geofence.mainloop()