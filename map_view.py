"""
map_view.py - Draws the coloured map using a tkinter Canvas

The key idea is converting between two coordinate systems:
  * latitude / longitude  (where things really are)
  * pixels on the screen  (where we draw them)
to_pixel() goes one way and to_latlon() goes back, which is how a mouse
click on the map becomes an exact latitude and longitude.
"""

import math
import tkinter as tk

from route_data import (HARBOUR_POLYGON, LANDMARKS, LAT_BOTTOM, LAT_TOP,
                        LON_LEFT, LON_RIGHT, MARATHON_KM, PARKS)
from utils import (ALERT_TYPES, EARTH_RADIUS_M, STATUS_RESPONDING,
                   WARNING_RADIUS_M)

# These are the colours I used on the map
LAND = "#efeadd"
WATER = "#8fc3e8"
PARK = "#b7dfa6"
ROUTE = "#2b6cb0"
RUNNER_COLOUR = "#ff1493"       # pink used for the "YOU" marker 
VOLUNTEER_COLOUR = "#15803d"


class MapView:
    """A canvas that draws the course, alerts and the user."""

    def __init__(self, parent, route, width, height, on_click):
        self.route = route
        self.on_click = on_click          # function to call when the map is clicked
        self.alerts = []                  # alerts currently drawn (for click detection)

        self.canvas = tk.Canvas(parent, width=width, height=height, bg=LAND,
                                highlightthickness=1, cursor="crosshair")
        self.canvas.bind("<Button-1>", self.handle_click)

        # --- work out how to convert lat/lon to pixels ---
        # One degree of longitude is shorter than one degree of latitude
        # (the further from the equator, the more so), so we shrink it by cos(lat).
        self.cos_lat = math.cos(math.radians((LAT_TOP + LAT_BOTTOM) / 2))
        lon_span = (LON_RIGHT - LON_LEFT) * self.cos_lat
        lat_span = LAT_TOP - LAT_BOTTOM
        self.scale = min(width / lon_span, height / lat_span)    # pixels per degree
        self.x_offset = (width - lon_span * self.scale) / 2      # centre the map
        self.y_offset = (height - lat_span * self.scale) / 2
        # Real-world metres covered by one pixel (1 degree of latitude in metres / scale)
        self.metres_per_pixel = math.radians(1) * EARTH_RADIUS_M / self.scale

        self.draw_static_map()            # land, water, route: drawn only once

    # ----- converting between coordinates -----

    def to_pixel(self, lat, lon):
        """Latitude/longitude -> (x, y) pixels on the canvas."""
        x = self.x_offset + (lon - LON_LEFT) * self.cos_lat * self.scale
        y = self.y_offset + (LAT_TOP - lat) * self.scale     # y grows downwards
        return x, y

    def to_latlon(self, x, y):
        """(x, y) pixels on the canvas -> latitude/longitude."""
        lon = LON_LEFT + (x - self.x_offset) / (self.cos_lat * self.scale)
        lat = LAT_TOP - (y - self.y_offset) / self.scale
        return lat, lon

    # ----- the parts of the map that never change -----

    def draw_static_map(self):
        """Draw land, parks, harbour, route, kilometre markers and labels."""
        c = self.canvas

        # Parks first, then the water on top (so the water can cover park edges)
        for name, top, bottom, left, right in PARKS:
            x1, y1 = self.to_pixel(top, left)
            x2, y2 = self.to_pixel(bottom, right)
            c.create_rectangle(x1, y1, x2, y2, fill=PARK, outline="")

        harbour = []
        for lat, lon in HARBOUR_POLYGON:
            harbour.extend(self.to_pixel(lat, lon))
        c.create_polygon(harbour, fill=WATER, outline="#6fa8d6")

        # The route: a white line underneath and a blue line on top looks like a road
        line = []
        for name, lat, lon in self.route.waypoints:
            line.extend(self.to_pixel(lat, lon))
        c.create_line(line, fill="white", width=8, capstyle="round", joinstyle="round")
        c.create_line(line, fill=ROUTE, width=4, capstyle="round", joinstyle="round")

        # Kilometre markers every 5 km (scaled so 42.195 km = the whole drawn route)
        km = 5
        while km < MARATHON_KM:
            lat, lon, _ = self.route.position_at_fraction(km / MARATHON_KM)
            x, y = self.to_pixel(lat, lon)
            c.create_oval(x - 8, y - 8, x + 8, y + 8, fill="white", outline=ROUTE)
            c.create_text(x, y, text=str(km), font=("TkDefaultFont", 7, "bold"))
            km += 5

        # Text labels for landmarks
        for text, lat, lon, anchor in LANDMARKS:
            x, y = self.to_pixel(lat, lon)
            style = "italic" if text == "Sydney Harbour" else "normal"
            c.create_text(x, y, text=text, anchor=anchor, fill="#374151",
                          font=("TkDefaultFont", 8, style))

        # Start and finish markers
        _, start_lat, start_lon = self.route.waypoints[0]
        _, end_lat, end_lon = self.route.waypoints[-1]
        sx, sy = self.to_pixel(start_lat, start_lon)
        ex, ey = self.to_pixel(end_lat, end_lon)
        c.create_oval(sx - 7, sy - 7, sx + 7, sy + 7, fill="#16a34a", outline="white", width=2)
        c.create_text(sx + 12, sy, text="START", anchor="w", fill="#166534",
                      font=("TkDefaultFont", 8, "bold"))
        c.create_rectangle(ex - 6, ey - 6, ex + 6, ey + 6, fill="black", outline="white", width=2)
        c.create_text(ex + 12, ey + 6, text="FINISH", anchor="w", fill="black",
                      font=("TkDefaultFont", 8, "bold"))

    # ----- the parts that change (redrawn on every update) -----

    def redraw(self, alerts, user, selected_point, selected_alert_id):
        """Delete the moving items and draw them again in their new positions."""
        self.canvas.delete("dynamic")
        self.alerts = alerts
        self.draw_alerts(alerts, selected_alert_id)
        self.draw_selected_point(selected_point)
        self.draw_user(user)

    def draw_alerts(self, alerts, selected_alert_id):
        """Draw one marker per active alert. The shape depends on the type."""
        c = self.canvas
        for alert in alerts:
            info = ALERT_TYPES[alert.alert_type]
            x, y = self.to_pixel(alert.lat, alert.lon)

            if alert.alert_id == selected_alert_id:       # highlight the chosen alert
                c.create_oval(x - 17, y - 17, x + 17, y + 17, outline="black",
                              width=2, dash=(3, 2), tags="dynamic")
            if alert.status == STATUS_RESPONDING:         # green ring = help is coming
                c.create_oval(x - 14, y - 14, x + 14, y + 14, outline="#16a34a",
                              width=3, tags="dynamic")

            shape = info["shape"]
            if shape == "square":
                c.create_rectangle(x - 8, y - 8, x + 8, y + 8, fill=info["colour"],
                                   outline="black", tags="dynamic")
                symbol = "!"
            elif shape == "triangle":
                c.create_polygon(x, y - 10, x + 10, y + 8, x - 10, y + 8,
                                 fill=info["colour"], outline="black", tags="dynamic")
                symbol = "!"
            elif alert.alert_type == "medical_major":
                # A bigger circle with a second dark ring so it stands out
                c.create_oval(x - 12, y - 12, x + 12, y + 12, fill=info["colour"],
                              outline=info["dark"], width=3, tags="dynamic")
                symbol = "+"
            else:                                         # minor medical
                c.create_oval(x - 8, y - 8, x + 8, y + 8, fill=info["colour"],
                              outline="black", tags="dynamic")
                symbol = "+"
            c.create_text(x, y + 1, text=symbol, fill="black" if shape != "circle" else "white",
                          font=("TkDefaultFont", 10, "bold"), tags="dynamic")

    def draw_selected_point(self, point):
        """Draw a crosshair where the user last clicked on the map."""
        if point is None:
            return
        x, y = self.to_pixel(point[0], point[1])
        c = self.canvas
        c.create_oval(x - 9, y - 9, x + 9, y + 9, outline="#7c3aed", width=2, tags="dynamic")
        c.create_line(x - 14, y, x + 14, y, fill="#7c3aed", width=2, tags="dynamic")
        c.create_line(x, y - 14, x, y + 14, fill="#7c3aed", width=2, tags="dynamic")

    def draw_user(self, user):
        """Draw the user, plus a dashed circle showing the warning distance."""
        c = self.canvas
        x, y = self.to_pixel(user.lat, user.lon)
        colour = VOLUNTEER_COLOUR if user.is_volunteer() else RUNNER_COLOUR

        r = WARNING_RADIUS_M / self.metres_per_pixel      # warning radius in pixels
        c.create_oval(x - r, y - r, x + r, y + r, outline=colour, dash=(4, 4),
                      tags="dynamic")

        if user.is_volunteer():
            c.create_polygon(x, y - 10, x + 10, y, x, y + 10, x - 10, y,
                             fill=colour, outline="white", width=2, tags="dynamic")
        else:
            # An arrow showing which way the runner is facing
            tip_x = x + 22 * math.sin(math.radians(user.heading))
            tip_y = y - 22 * math.cos(math.radians(user.heading))
            c.create_line(x, y, tip_x, tip_y, fill=colour, width=3, arrow="last",
                          tags="dynamic")
            c.create_oval(x - 7, y - 7, x + 7, y + 7, fill=colour, outline="white",
                          width=2, tags="dynamic")
        c.create_text(x + 12, y - 12, text="YOU", anchor="w", fill=colour,
                      font=("TkDefaultFont", 8, "bold"), tags="dynamic")

    # ----- mouse clicks -----

    def alert_at_pixel(self, x, y):
        """Return the id of the alert drawn at (x, y), or None if there isn't one."""
        for alert in self.alerts:
            ax, ay = self.to_pixel(alert.lat, alert.lon)
            if abs(ax - x) <= 12 and abs(ay - y) <= 12:
                return alert.alert_id
        return None

    def handle_click(self, event):
        """Convert the click to coordinates and tell the main window."""
        lat, lon = self.to_latlon(event.x, event.y)
        self.on_click(lat, lon, self.alert_at_pixel(event.x, event.y))
