"""This module just defines the geofencing function and helps with the creation of the areas."""

from shapely.geometry import Point, Polygon
import math

def order_points_for_polygon(points):
    if len(points) < 3:
        return points
    
    center_lat = sum(p[0] for p in points) / len(points)
    center_lon = sum(p[1] for p in points) / len(points)
    
    def angle_from_center(point):
        lat, lon = point
        return math.atan2(lat - center_lat, lon - center_lon)
    
    return sorted(points, key=angle_from_center)



def is_inside_area(lat, lon, area_coords): # Area coords has the format [(lat1, lon1), (lat2, lon2), ...] at least 3 tuples. This is the geofencing function
    ordered_coords = order_points_for_polygon(area_coords)
    punto = Point(lon, lat)  # Shapely uses (lon, lat), not (lat, lon)
    poligono_coords = [(lon_, lat_) for lat_, lon_ in ordered_coords] # Another time, as Shapely uses (lon, lat), all the structure changes
    poligono = Polygon(poligono_coords)
    return poligono.contains(punto)