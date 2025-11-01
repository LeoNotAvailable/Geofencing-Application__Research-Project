"""This module hold all the logic that will be used for the application, from the UI module. Takes care of everything, from the areas management
to the map viewing and edditing."""

import tkinter as tk
import tkintermapview as tkmap
from tkinter import messagebox as mbox
from is_inside_area_function_2 import order_points_for_polygon
from config_manager import load_config, edit_config
from debug_logger_2 import check_log_file, log
import json, os
import time

configuration= load_config()
FILE_NAME= configuration["AREAS_FILE"]
check_log_file() # This ensures the log file exists before editing it

class GeofenceLogic: # We define everything inside a class, because it will be imported from the UI module.
    def __init__(self, area_name, area_points, area_list,
                 delete_button, save_add_button, edit_button, tk_map, geofence_button, geofence_status, reconnect_button, connection_status,
                 terminal, ui_lat, ui_lon, center_button):
        self.area_name = area_name
        self.area_points = area_points
        self.original_area_coords = None
        self.deleted_markers = []
        self.area_list = area_list
        self.delete_button = delete_button
        self.save_add_button = save_add_button
        self.edit_button = edit_button
        self.geofence_button= geofence_button
        self.areas = {}
        self.edit_name = None
        self.adding= False
        self.new_markers= []
        self.tk_map= tk_map
        self.polygon= None
        self.pos_marker= None
        self.load_areas_local()
        self.geofence_status= geofence_status # Label that shows if you're in or out the area
        self.reconnect_button= reconnect_button # Restablish the connection, just when connection_status is red. 
        self.connection_status= connection_status # Label just of colour
        self.terminal= terminal # The application built-in terminal
        self.ui_lat= ui_lat # Text boxes that shows the current position
        self.ui_lon= ui_lon # Text boxes that shows the current position
        self.center_button= center_button # Centers the position of the map to the actual position
        self.last_position_time= 0
        self.check_position_loop()

    def check_position_loop(self): # Checks if the position is being actualized
        now = time.time()
        if now - self.last_position_time > configuration["POSITION_TIMEOUT"]:
            self.clear_marker()
            self.center_button.config(state=tk.DISABLED)
            lat_text = self.ui_lat.cget("text")
            lon_text = self.ui_lon.cget("text")
            if lat_text or lon_text:
                log(f"[WARNING] The position has been lost!")
            self.ui_lat.config(text= "")
            self.ui_lon.config(text= "")
            if self.geofence_button.cget("text") == "Stop":
                self.geofence_button.config(text="Start")
                self.area_list.config(state=tk.NORMAL)
                self.edit_button.config(state=tk.NORMAL)
                self.save_add_button.config(state=tk.NORMAL)
                self.delete_button.config(state=tk.NORMAL)
                self.geofence_status.config(fg="black", bg="grey", text="Start the application")
                log("[WARNING] Geofencing stopped automatically due to position loss!")

        self.tk_map.after(1000, self.check_position_loop) # Executes itself a second after



    def load_areas_local(self): # Loads the areas JSON to a variable of the class
        if not os.path.exists(FILE_NAME):
            with open(FILE_NAME, "w") as f:
                json.dump({}, f)
            self.areas = {}
            return

        try:
            with open(FILE_NAME, "r") as f:
                data = json.load(f)
                self.areas = {name: [tuple(coord) for coord in coords] for name, coords in data.items()}
                areas= {}
                keys= self.areas.keys()
                for key in keys:
                    if len(self.areas[key]) < 3:
                        log(f"[WARNING] Invalid Area: The area {key} has less than three points. It has been removed.")
                    else:
                        areas[key]= self.areas[key]
                self.areas= areas
        except Exception as e:
            log(f"[ERROR] While loading {FILE_NAME}: {e}")
            self.areas = {}

    def save_areas_local(self): # Saves the areas in a JSON format.
        try:
            data = {name: [list(coord) for coord in coords] for name, coords in self.areas.items()}
            with open(FILE_NAME, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log(f"[ERROR] While saving information in {FILE_NAME}: {e}")

    def clean_interface(self):
        self.clear_polygon()
        self.area_name.delete(0, tk.END)
        self.area_points.config(state= tk.NORMAL)
        self.area_points.delete("1.0", tk.END) 
        self.area_points.config(state= tk.DISABLED)
        self.tk_map.delete_all_marker()

    def refresh_area_list(self): # Shows every area defined in the selectable list.
        self.area_list.delete(0, tk.END)
        for name in self.areas.keys():
            self.area_list.insert(tk.END, name)


    def string_to_coords(self, coords_raw: str): # Transforms text to the coords system used for the app; [(lat1, lon1), (lat2, lon2)...]
        result = []
        coords_raw = coords_raw.strip()

        if "{" in coords_raw:  # Initially, the appliaction showed different formats of viewing the areas as the eddition was made purely
            # by writting coords. Now, just uses one, but this is held in case an error took place.
            blocks = coords_raw.split("}")
            for block in blocks:
                block = block.strip(" {")
                if not block:
                    continue
                try:
                    lat, lon = map(float, block.split())
                    result.append((lat, lon))
                except Exception as e:
                    log(f"[ERROR] While processing coordinates information of '{block}': {e}")
        else:  # Formato 'lat,lon; lat2,lon2'
            coords = coords_raw.split(";")
            for coord in coords:
                if coord.strip():
                    try:
                        lat, lon = map(float, coord.split(","))
                        result.append((lat, lon))
                    except Exception as e:
                        log(f"[ERROR] While processing the coordinates '{coord}': {e}")

        return result


    def coords_to_user_string(self, coords: list[tuple]) -> str: # From [(lat,lon),...] to lat,lon; lat2,lon2;...
        return "; ".join(f"{lat},{lon}" for lat, lon in coords)

    def obtain_selection(self): # Returns the name of the area selected, and the index that represents it.
        selected_index= self.area_list.curselection()
        
        if not selected_index:
            return None

        name= self.area_list.get(selected_index)

        return name, selected_index
    

    def area_selected(self, event= None): # Every time an area has been selected in the list. It deletes it if the UI is in delete mode or, instead, shows it
        result= self.obtain_selection()
        if not result:
            return
        name, selected_index= result
        if self.delete_button.cget('text') == "Delete": # If the UI isn't in delete mode.
            self.area_name.config(state= tk.NORMAL)
            self.area_points.config(state= tk.NORMAL)
            self.edit_button.config(state= tk.NORMAL)

            # This shows the area information, and every point is made of in the map, as well as the area itself.
            self.clean_interface()
            self.set_polygon(name)
            self.area_name.insert(0, name)
            self.area_points.config(state= tk.NORMAL)
            for element in self.areas[name]:
                self.area_points.insert("end", str(element[0]) + ", " + str(element[1]) + f";\n")
            self.area_points.config(state= tk.DISABLED)            
            for area in self.areas[name]:
                self.tk_map.set_marker(area[0], area[1], marker_color_outside= configuration["MARKER_COLOR_OUTSIDE"], marker_color_circle= configuration["MARKER_COLOR_CIRCLE"], command= self.remove_map_marker)

            self.area_name.config(state= tk.DISABLED)
            self.area_points.config(state= tk.DISABLED)
        else: # The UI is in delete mode, so every area is selected should be removed.
            answer= mbox.askyesno("Delete Selection", f"Are you sure you want to delete -{name}-?")
            if answer:
                self.areas.pop(name)
                self.area_list.delete(selected_index)
                log(f"[INFO] The user has deleted the area {name}")
            else:
                self.area_list.selection_clear(0, tk.END)
        self.save_areas_local() # Saves the changes
        self.refresh_area_list()
        self.edit_name= None
        self.adding= False        

    def save_add_pressed(self):
        area_to_select = None # When changes are saved, it selects the area it has been working with
        
        if self.save_add_button.cget('text') == "Add":  # The button says "Add", so the UI prepares for creating a new area.
            self.adding= True
            self.area_name.config(state=tk.NORMAL)
            self.geofence_button.config(state=tk.DISABLED)


            self.clean_interface()
            self.area_list.select_clear(0, tk.END)
            self.area_name.insert(0, "New area")
            self.save_add_button.config(text="Save")
            self.delete_button.config(text="Cancel")

            self.area_list.config(state=tk.DISABLED)

        elif self.save_add_button.cget('text') == "Save": # You were creating or editing an area.
            name = self.area_name.get().strip()
            
            if not name:
                log(f"[WARNING] While saving an area: the area name cannot be empty!")
                mbox.showwarning("Invalid Name", "The area name cannot be empty!")
                return

            if self.edit_name: # If you were editing an existent area...
                base = [p for p in self.areas[self.edit_name] if p not in self.deleted_markers] # Saves the area without edits.
                final_coords = base + self.new_markers # Combines the base with the markers added to the map.
                
                if len(final_coords) < 3:
                    log(f"[WARNING] While saving an area: the area must have at least 3 points!")
                    mbox.showwarning("Invalid Area", "The area must have at least 3 points!")
                    return

                if name != self.edit_name:
                    if name in self.areas:
                        log(f"[WARNING] While saving an area: the area -{name}- already exists!")
                        mbox.showwarning("Rename Area", f"The area -{name}- already exists!")
                        return
                    #  Here, we rename it by removing the previous one and saving the new one.
                    self.areas.pop(self.edit_name, None)
                    self.areas[name] = final_coords
                    log(f"[INFO] The user has renamed the area -{self.edit_name}- to -{name}-.")
                else:
                    # Just actualize coords.
                    self.areas[name] = final_coords
                    log(f"[INFO] The user has eddited the area -{name}-.")
                area_to_select = name

                self.save_add_button.config(text="Add")
                self.delete_button.config(text="Delete")
                self.clean_interface()
                self.area_name.config(state=tk.DISABLED)
                self.area_list.config(state=tk.NORMAL)
                self.new_markers = []
                self.deleted_markers = []
                self.edit_name = None
                self.adding = False
                self.geofence_button.config(state=tk.NORMAL)
            

            else:  # We're creating a new area
                if name in self.areas:
                    log(f"[WARNING] While creating a new area: the area -{name}- already exists!")
                    mbox.showwarning("Add A New Area", f"The name '{name}' already exists. Choose another one.")
                    return 

                if len(self.new_markers) < 3:
                    log(f"[WARNING] While creating a new area: the area must have at least 3 points!")
                    mbox.showwarning("Invalid Area", "An area must have at least three valid points.")
                    return

                self.areas[name] = self.new_markers[:]
                self.area_list.insert(tk.END, name)
                self.area_list.selection_clear(0, tk.END)

                log(f"[INFO] The user has saved the new area -{name}-.")
                area_to_select = name

                # Reset de botones y campos
                self.save_add_button.config(text="Add")
                self.delete_button.config(text="Delete")
                self.clean_interface()
                self.area_name.config(state=tk.DISABLED)
                self.area_list.config(state=tk.NORMAL)
                self.area_list.selection_set(0)
                self.new_markers = []
                self.adding = False
                self.geofence_button.config(state=tk.NORMAL)

        else: # Means the button says "Delete all"
            answer= mbox.askyesno("Delete All Areas", "Are you sure you want to delete every area?\nYou won't be able to recover them.")
            if answer:
                self.area_list.delete(0, tk.END)
                log("[INFO] The user has deleted all the areas.")
                self.areas= {}
            self.geofence_button.config(state=tk.NORMAL)
            self.save_add_button.config(text= "Add")
            self.delete_button.config(text= "Delete")


        self.save_areas_local() # We save all the changes
        self.refresh_area_list()
        self.edit_name= None
        index = self.area_list.size() - 1
        self.area_list.selection_clear(0, tk.END)
        self.area_list.selection_set(index)
        if area_to_select is not None and area_to_select in self.areas: # If we have been editing or creating an area, must be selected when we end the edition.
            current_list = self.area_list.get(0, tk.END)
            index = current_list.index(area_to_select)
            self.area_list.selection_clear(0, tk.END)
            self.area_list.selection_set(index)
            self.area_selected()
        else:
            self.area_list.selection_clear(0, tk.END) # If there's no area that should be selected, we clear the selection

    def edit_pressed(self): # This button manages the edition of existen areas. Other functions know if the edition is activated by the edit_name variable
        self.edit_button.config(state=tk.DISABLED)
        self.area_name.config(state=tk.NORMAL)
        self.area_list.config(state=tk.DISABLED)
        self.save_add_button.config(text="Save")
        self.delete_button.config(text="Cancel")
        self.geofence_button.config(state=tk.DISABLED)

        self.area_points.config(state= tk.NORMAL)
        self.area_points.delete("1.0", tk.END)
        self.area_points.config(state= tk.DISABLED)


        self.edit_name = self.area_name.get().strip()
        
        if not self.edit_name or self.edit_name not in self.areas:
            log(f"[WARNING] The user has tried to edit an unvalid area!")
            mbox.showerror("Error", "You cannot edit the area, unvalid area.")
            self.edit_button.config(state=tk.NORMAL)
            self.area_name.config(state=tk.DISABLED)
            self.area_points.config(state=tk.DISABLED)
            self.area_list.config(state=tk.NORMAL)
            self.save_add_button.config(text="Add")
            self.delete_button.config(text="Delete")
            self.edit_name = None
            return

        self.original_area_coords = list(self.areas[self.edit_name])
        self.deleted_markers = []

        text = self.area_points.get("1.0", tk.END)
        coords = self.string_to_coords(text)
        string = self.coords_to_user_string(coords)
        self.area_points.delete("1.0", tk.END)
        self.area_points.config(state= tk.NORMAL)
        self.area_points.insert("1.0", string)
        self.area_points.config(state= tk.DISABLED)


    def delete_pressed(self): # The application enters in "delete mode", or cancells an action (as you've seen, every button has more than one functionality)
        if self.delete_button.cget('text') == "Delete": # If we want to delete something
            if len(self.areas)== 0:
                log(f"[WARNING] There are no areas to be removed!")
                mbox.showwarning("Delete Area", "Error: there are no areas to remove.")
            else:
                self.area_list.selection_clear(0, tk.END)
                self.delete_button.config(text= "Back")
                self.save_add_button.config(text= "Delete all")
                self.area_name.config(state= tk.NORMAL)
                self.area_points.config(state= tk.NORMAL)
                self.clean_interface()
                self.area_name.config(state= tk.DISABLED)
                self.area_list.config(state= tk.NORMAL)
                self.area_list.selection_clear(0, tk.END)
                self.edit_button.config(state= tk.DISABLED)
                self.geofence_button.config(state=tk.DISABLED)


        elif self.delete_button.cget('text') == "Cancel": # If we want to cancel an ongoing action
            answer = mbox.askyesno("Cancel Action", "Are you sure you want to cancel what you are doing?\nThe changes won't be saved.")
            if answer:
                self.clean_interface()
                # We restore the original area and select it.
                if self.edit_name and self.edit_name in self.areas:
                    self.area_name.insert(0, self.edit_name)
                    self.area_points.config(state= tk.NORMAL)
                    for element in self.areas[self.edit_name]:
                        self.area_points.insert("end", str(element[0]) + ", " + str(element[1]) + f";\n")
                    self.area_points.config(state= tk.DISABLED)
                    self.set_polygon(self.edit_name)  # We draw the area
                    for pt in self.areas[self.edit_name]:
                        self.tk_map.set_marker(pt[0], pt[1], marker_color_outside= configuration["MARKER_COLOR_OUTSIDE"], marker_color_circle= configuration["MARKER_COLOR_CIRCLE"], command=self.remove_map_marker)
                self.area_name.config(state=tk.DISABLED)
                self.area_points.config(state=tk.DISABLED)
                self.area_list.config(state=tk.NORMAL)
                self.delete_button.config(text="Delete")
                self.save_add_button.config(text="Add")
                self.area_list.selection_clear(0, tk.END)
                self.geofence_button.config(state=tk.NORMAL)

                
                # We initialize the temporal values
                self.new_markers = []
                self.deleted_markers = []
                self.edit_name = None
                self.adding = False

        else: # Means that the button says "Back" because we were already in "delete mode"
            self.delete_button.config(text= "Delete")
            self.save_add_button.config(text= "Add")
            self.area_list.selection_clear(0, tk.END)
            self.geofence_button.config(state=tk.NORMAL)
        self.edit_name= None
        self.adding= False


    def clear_polygon(self): # We remove the area
        if self.polygon:
            self.polygon.delete()
            self.polygon = None


    def set_polygon(self, name, color= "blue", out_color= "black", border_with= 2): # We put an area on the map
        self.clear_polygon()
        ordered_coords = order_points_for_polygon(self.areas[name])
        self.polygon= self.tk_map.set_polygon(
            ordered_coords, 
            name= name,
            fill_color=color, 
            outline_color=out_color, 
            border_width=border_with
            )
        
    def actualize_polygon(self, color="blue", out_color="black", border_with=2, name=""):
        if self.edit_name: # If we were editing an existent area
            # Action: orginal area - removed points + new points
            base = [p for p in self.areas[self.edit_name] if p not in self.deleted_markers]
            combined = base + self.new_markers
            if len(combined) >= 3:
                ordered = order_points_for_polygon(combined)
                self.clear_polygon()
                self.polygon = self.tk_map.set_polygon(ordered, name=self.edit_name, fill_color=color, outline_color=out_color, border_width=border_with)
            else:
                self.clear_polygon()
        else:
            # We were creating a new area
            if len(self.new_markers) >= 3:
                ordered = order_points_for_polygon(self.new_markers)
                self.clear_polygon()
                self.polygon = self.tk_map.set_polygon(ordered, name=name, fill_color=color, outline_color=out_color, border_width=border_with)
            else:
                self.clear_polygon()

                
    def clear_marker(self): # Removes the position marker
        if self.pos_marker:
            self.pos_marker.delete()
            self.pos_marker= None
    
    def remove_map_marker(self, marker): # Removes any marker on the map, it happens when you click on them
        if not self.edit_name and not self.adding:
            return

        ans = mbox.askyesno("Remove Marker", "Are you sure you want to remove this marker?")
        if ans:
            lat, lon = marker.position
            marker_coords = (lat, lon)
            
            # If it is a marker added while editing:
            if marker_coords in self.new_markers:
                self.new_markers.remove(marker_coords)
            # If it is a marker of the original area:
            elif self.edit_name and marker_coords in self.areas.get(self.edit_name, []):
                # We just add it to the removed points intead of removing it from the original area 
                if marker_coords not in self.deleted_markers:
                    self.deleted_markers.append(marker_coords)
            else:
                return

            marker.delete()
            self.actualize_polygon()


    def create_marker(self, lat, lon, text= "Current Position", text_color= configuration["MARKER_POSITION_COLOR_TEXT"], marker_color_outside= configuration["MARKER_POSITION_COLOR_OUTSIDE"], marker_color_circle= configuration["MARKER_POSITION_COLOR_CIRCLE"]):
        if lat is None or lon is None:
            self.clear_marker()
            return
        self.clear_marker()
        self.pos_marker = self.tk_map.set_marker(lat, lon, text, text_color= text_color, marker_color_outside= marker_color_outside, marker_color_circle= marker_color_circle)


    def geofencing_function(self): # Blocks every action the user can do, except canceling this function 
        if self.geofence_button.cget("text")== "Start":
            lat_text = self.ui_lat.cget("text")
            lon_text = self.ui_lon.cget("text")
            if not lat_text or not lon_text:
                log(f"[WARNING] While starting the geofencing application: cannot start without a fixed position!")
                mbox.showwarning("Start Geofencing Aplication", "You cannot start the aplication without a fixed position!")
                return
            if not self.polygon:
                log(f"[WARNING] While starting the geofencing application: cannot start without a valid area!")
                mbox.showwarning("Start Geofencing Aplication", "You cannot start the aplication without an area!")
                return
            self.geofence_button.config(text= "Stop")
            self.area_name.config(state= tk.DISABLED)
            self.area_points.config(state= tk.DISABLED)
            self.area_list.config(state= tk.DISABLED)
            self.edit_button.config(state= tk.DISABLED)
            self.save_add_button.config(state= tk.DISABLED)
            self.delete_button.config(state= tk.DISABLED)
            log(f"[INFO] Starting geofencing function...")
                    
        else:
            self.geofence_button.config(text= "Start")
            self.area_list.config(state= tk.NORMAL)
            self.edit_button.config(state= tk.NORMAL)
            self.save_add_button.config(state= tk.NORMAL)
            self.delete_button.config(state= tk.NORMAL)
            self.geofence_status.config(fg= "black", bg= "grey", text= "Start the application")
            log(f"[INFO] Stopping geofencing function...")


    def actualize_current_position(self, lat, lon): # Updates the current position
        
        if lat is not None and lon is not None:
            self.ui_lat.config(text=str(lat))
            self.ui_lon.config(text=str(lon))
            self.center_button.config(state=tk.NORMAL)
            self.create_marker(lat, lon)
            self.last_position_time = time.time()
        else:
            self.clear_marker()
            self.center_button.config(state=tk.DISABLED)
        

    def center_view(self): # Centers the view to the current position.
        try:
            lat_text = self.ui_lat.cget("text")
            lon_text = self.ui_lon.cget("text")
            lat = float(lat_text)
            lon = float(lon_text)


            self.tk_map.set_position(lat, lon)
            self.tk_map.set_zoom(configuration["ZOOM_LEVEL"])
            
        except Exception as e:
            log(f"[ERROR] Cannot center the view in the actual position: {e}")
            self.center_button.config(state= tk.DISABLED)

    def open_log_file(self): # Action activated by a UI button, opens the log file to the user.
        check_log_file()
        LOG_FILE= configuration["LOG_FILE"]
        try:
            os.startfile(LOG_FILE)
        except Exception as e:
            log(f"[ERROR] Couldn't open the log file: {e}")


    def open_instructions_file(self): # As the previous one, but with the usage guide
        file_path = configuration["INFO_FILE"]
        text= f"	---GEOFENCING APPLICATION USAGE GUIDE---\n\nBY LEO SARRIA\n\nThis application allows you to define virtual geographic areas and check, using a GPS receiver and an ESP32 STEAMakers microcontroller, whether your current position is inside or outside those areas.\n\nIn this document, you will see a simple explanation of how to use every function of this interface.\n\n\nAREAS MANAGEMENT:\n\nEach area is composed of the following elements:\n\n· Area name: Will show you the name of the area, or let you enter it when needed\n· Area points list: a non-editable textbox that shows every point an area is made of\n· Areas list: a list with every created area, it is automatically saved in the app file.\n· Delete, add and edit buttons\n\nTo add an area, you must click that button, write a name that is not repeated, and define at least three points. Then, click save. You can cancel the action.\n\nIn order to edit an area, the method is the same, but the name is set (although still editable) as well as some points. When cancelled, the area returns to its last version.\n\nTo delete areas, click the button -Delete-. Then you can click on whichever area you want to remove, and click Accept in the confirmation message. Or remove them all at once.\n\n\nMAP USAGE:\n\nThe map is interactive. When creating or editing an area, you can define points by right-clicking with the mouse, and clicking -Add Marker-. To remove one, just click on it.\nWith the mouse wheel, you can adjust the map scale, and by dragging it, you can move it.\n\nIt's important to understand that the map NEEDS AN INTERNET CONNECTION in order to work.\n\n\nBLUETOOTH AND SATELLITE CONNECTION, POSITION FIX:\n\nThe color indicator shows the state of the Bluetooth connection to the microcontroller or the satellite connection's quality:\n· Dark green: the Bluetooth connection is established and the position is clear\n· Light green: the Bluetooth connection is established and the position is unclear\n· Yellow: the Bluetooth connection is established but there's no position yet\n· Orange: there's no Bluetooth connection and it's searching actively to establish it.\n· Red: the Bluetooth connection search time has ended without success, so it stopped searching for it. you can restart the search by the -Reconnect- button.\n\nOnce there's a position fix, you will see the values in the -Current Position- part. Then you will be able to center the view on the position.\n\n\nGEOFENCING APPLICATION:\n\nTo start it, it needs a position fix and a selected area. It will check if the position is inside the area or not, and update the label consequently.\n\n\nLOG TERMINAL AND LOG FILE:\n\nThe black terminal you can see on the bottom left of the application shows every message that is saved in the log file. You can view it by clicking its respective button.\nIt is saved in the application directory.\n\n\n\nAll areas are saved automatically in a file called -areas.json- in the application folder."
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
        try:
            os.startfile(file_path)
        except Exception as e:
            log(f"[ERROR] Couldn't open the instructions file.: {e}")

        