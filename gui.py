"""
gui.py - The main window of the app (tkinter).

Two classes live here:
  * AlertDialog    - the small pop-up form for raising a new alert
  * MarathonApp    - the main window: map on the left, controls on the right

The window only handles buttons and text. The real work is done by the other
files: AlertManager (alerts), Route (course), User (position), MapView (drawing).
"""

import tkinter as tk
from tkinter import messagebox, ttk

import storage
from alert_manager import AlertManager
from map_view import MapView
from route import Route
from route_data import LAT_BOTTOM, LAT_TOP, LON_LEFT, LON_RIGHT, MARATHON_KM
from user import User
from utils import (ALERT_TYPES, ROLE_RUNNER, ROLE_VOLUNTEER, STATUS_RESOLVED,
                   STATUS_RESPONDING, WARNING_RADIUS_M, format_coords,
                   format_distance, parse_coordinate)

MAP_WIDTH = 400
MAP_HEIGHT = 640
WINDOW_WIDTH = 760            # the main window is locked to this size on opening
WINDOW_HEIGHT = 700           
PANEL_TEXT_WIDTH = 310        # width (pixels) at which side-panel text wraps
REFRESH_MS = 2000             # reload the shared alerts file every 2 seconds
OK_COLOUR = "#2f855a"         # green banner when everything is clear
BOLD = ("TkDefaultFont", 10, "bold")


class AlertDialog(tk.Toplevel):
    """A pop-up form where the user describes the alert they want to raise."""

    def __init__(self, parent, lat, lon, on_submit):
        super().__init__(parent)
        self.title("Raise an alert")
        self.resizable(False, False)
        self.transient(parent)       # keep the pop-up on top of the main window
        self.grab_set()              # block the main window until this one closes
        self.on_submit = on_submit   # function to call with the finished form

        # tkinter "variables" hold whatever the user types or selects
        self.type_var = tk.StringVar(value="hazard")
        self.lat_var = tk.StringVar(value=f"{lat:.5f}")
        self.lon_var = tk.StringVar(value=f"{lon:.5f}")
        self.desc_var = tk.StringVar()

        form = ttk.Frame(self, padding=12)
        form.pack()

        ttk.Label(form, text="What are you reporting?", font=BOLD).grid(
            row=0, column=0, columnspan=2, sticky="w")
        row = 1
        for key, info in ALERT_TYPES.items():
            ttk.Radiobutton(form, text=info["label"], value=key,
                            variable=self.type_var).grid(
                row=row, column=0, columnspan=2, sticky="w")
            # A grey hint under each choice, e.g. "cuts, bruises, small falls"
            ttk.Label(form, text="e.g. " + info["examples"], foreground="#6b7280",
                      font=("TkDefaultFont", 8)).grid(
                row=row + 1, column=0, columnspan=2, sticky="w", padx=(22, 0))
            row += 2

        ttk.Label(form, text="Latitude").grid(row=row, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(form, textvariable=self.lat_var, width=14).grid(row=row, column=1, sticky="w", pady=(8, 0))
        ttk.Label(form, text="Longitude").grid(row=row + 1, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.lon_var, width=14).grid(row=row + 1, column=1, sticky="w")
        ttk.Label(form, text="Description").grid(row=row + 2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(form, textvariable=self.desc_var, width=38).grid(
            row=row + 3, column=0, columnspan=2, sticky="we")

        buttons = ttk.Frame(form)
        buttons.grid(row=row + 4, column=0, columnspan=2, pady=(12, 0), sticky="e")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        ttk.Button(buttons, text="Send alert", command=self.submit).pack(side="left")

    def submit(self):
        """Check what the user typed. If it is fine, pass it on and close."""
        try:
            lat = parse_coordinate(self.lat_var.get(), "Latitude", LAT_BOTTOM, LAT_TOP)
            lon = parse_coordinate(self.lon_var.get(), "Longitude", LON_LEFT, LON_RIGHT)
        except ValueError as error:        # bad number or outside the map
            messagebox.showerror("Check the location", str(error), parent=self)
            return

        description = self.desc_var.get().strip()
        if description == "":
            messagebox.showerror("Missing description",
                                 "Please add a short description so others know "
                                 "what to expect.", parent=self)
            return

        self.on_submit(self.type_var.get(), lat, lon, description)
        self.destroy()


class MarathonApp:
    """The main window."""

    def __init__(self, root):
        self.root = root
        root.title("Sydney Marathon - Live Alerts (simulation)")

        storage.ensure_data_file()            # first run: copy in the demo alerts
        self.route = Route()
        self.manager = AlertManager()
        self.user = User("Runner 101", ROLE_RUNNER)

        # Things the window needs to remember between updates
        self.course_km = 0.0                  # how far along the course the user is
        self.selected_point = None            # (lat, lon) the user clicked on the map
        self.selected_alert_id = None         # the alert chosen in the list or map
        self.notified_ids = set()             # alerts we have already warned about
        self.list_texts = []                  # current rows of the list box
        self.listed_ids = []                  # alert ids matching those rows

        self.role_var = tk.StringVar(value=ROLE_RUNNER)
        self.build_layout()
        self.lock_window_size()
        self.move_user(0.0)
        self.refresh_all()
        self.auto_refresh()

    # ...................................................................
    # Building the window


    def build_layout(self):
        """Create all the widgets: a top bar, the map and the side panel."""
        top = ttk.Frame(self.root, padding=(10, 6))
        top.pack(fill="x")
        ttk.Label(top, text="Sydney Marathon Alerts",
                  font=("TkDefaultFont", 14, "bold")).pack(side="left")
        ttk.Radiobutton(top, text="Volunteer", value=ROLE_VOLUNTEER,
                        variable=self.role_var, command=self.on_role_change).pack(side="right")
        ttk.Radiobutton(top, text="Runner", value=ROLE_RUNNER,
                        variable=self.role_var, command=self.on_role_change).pack(side="right")
        ttk.Label(top, text="I am a:").pack(side="right", padx=(0, 6))

        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True)
        self.map_view = MapView(body, self.route, MAP_WIDTH, MAP_HEIGHT, self.on_map_click)
        self.map_view.canvas.pack(side="left", padx=10, pady=(0, 10))

        side = ttk.Frame(body)
        side.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=(0, 10))
        self.build_side_panel(side)

    def lock_window_size(self):
        """Give the window one fixed size and stop it changing afterwards.

        Without this, tkinter re-fits the window every time a label's text
        changes (the banner, the position text, the alert details), which
        made the window jump about while the slider was dragged.
        """
        self.root.update_idletasks()                 # finish laying out widgets
        width = max(WINDOW_WIDTH, self.root.winfo_reqwidth())
        height = max(WINDOW_HEIGHT, self.root.winfo_reqheight())
        self.root.geometry(f"{width}x{height}")      # an explicit size stops auto-fitting
        self.root.minsize(width, height)
        self.root.maxsize(width, height)
        self.root.resizable(False, False)

    def build_side_panel(self, side):
        """The controls on the right-hand side."""
        # --- where am I? (the slider moves the simulated user along the course) ---
        ttk.Label(side, text="Your position on the course", font=BOLD).pack(anchor="w")
        self.km_label = ttk.Label(side, text="")
        self.km_label.pack(anchor="w")
        self.slider = ttk.Scale(side, from_=0, to=MARATHON_KM, orient="horizontal",
                                command=self.on_slider)
        self.slider.pack(fill="x")
        self.position_label = ttk.Label(side, text="", wraplength=PANEL_TEXT_WIDTH)
        self.position_label.pack(anchor="w", pady=(0, 8))

        # --- the warning banner (a plain tk.Label so we can colour it) ---
        self.banner = tk.Label(side, text="", font=("TkDefaultFont", 11, "bold"),
                               fg="white", bg=OK_COLOUR, wraplength=PANEL_TEXT_WIDTH,
                               justify="left", anchor="nw", padx=8, pady=8, height=5)
        self.banner.pack(fill="x", pady=(0, 8))

        # --- raising alerts ---
        ttk.Button(side, text="Raise alert at my position",
                   command=self.raise_at_my_position).pack(fill="x")
        self.point_button = ttk.Button(side, text="Raise alert at selected point",
                                       command=self.raise_at_selected_point,
                                       state="disabled")
        self.point_button.pack(fill="x", pady=(4, 0))
        self.point_label = ttk.Label(side, text="Click the map to pick a point.",
                                     wraplength=PANEL_TEXT_WIDTH)
        self.point_label.pack(anchor="w", pady=(2, 8))

        # --- list of active alerts ---
        ttk.Label(side, text="Active alerts (nearest first)", font=BOLD).pack(anchor="w")
        list_frame = ttk.Frame(side)
        list_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.listbox = tk.Listbox(list_frame, height=7, exportselection=False,
                                  yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_list_select)

        self.detail_label = ttk.Label(side, text="", wraplength=PANEL_TEXT_WIDTH,
                                      justify="left")
        self.detail_label.pack(anchor="w", pady=6)

        # --- volunteer-only buttons ---
        volunteer_row = ttk.Frame(side)
        volunteer_row.pack(fill="x")
        self.respond_button = ttk.Button(volunteer_row, text="I'm responding",
                                         command=lambda: self.change_status(STATUS_RESPONDING),
                                         state="disabled")
        self.respond_button.pack(side="left", expand=True, fill="x")
        self.resolve_button = ttk.Button(volunteer_row, text="Mark resolved",
                                         command=lambda: self.change_status(STATUS_RESOLVED),
                                         state="disabled")
        self.resolve_button.pack(side="left", expand=True, fill="x")

        ttk.Button(side, text="Reset demo alerts", command=self.reset_demo).pack(
            fill="x", pady=(8, 0))
        
    # ...................................................................
    # Reacting to the user


    def on_role_change(self):
        """Switch between runner and volunteer (this is how we simulate 2 users)."""
        if self.role_var.get() == ROLE_VOLUNTEER:
            self.user = User("Volunteer Sam", ROLE_VOLUNTEER)
            state = "normal"
        else:
            self.user = User("Runner 101", ROLE_RUNNER)
            state = "disabled"
        # Only volunteers may respond to or resolve alerts
        self.respond_button.config(state=state)
        self.resolve_button.config(state=state)

        self.notified_ids = set()
        self.move_user(self.course_km)
        self.refresh_all()

    def on_slider(self, value):
        """The position slider was dragged. (tkinter passes the value as text.)"""
        self.move_user(float(value))
        self.refresh_all()

    def move_user(self, km):
        """Put the user at this many km along the course and update the labels."""
        self.course_km = km
        self.user.move_along_route(self.route, km / MARATHON_KM)
        self.km_label.config(text=f"{km:.1f} km of {MARATHON_KM} km")
        near = self.route.nearest_waypoint_name(self.user.lat, self.user.lon)
        self.position_label.config(
            text=f"{format_coords(self.user.lat, self.user.lon)}\nNear: {near}")

    def on_map_click(self, lat, lon, alert_id):
        """The map was clicked: either an alert marker or an empty spot."""
        if alert_id is not None:
            self.selected_alert_id = alert_id
            self.selected_point = None
            self.point_button.config(state="disabled")
            self.point_label.config(text="Click the map to pick a point.")
        else:
            self.selected_point = (lat, lon)
            self.selected_alert_id = None
            self.point_button.config(state="normal")
            self.point_label.config(text=f"Selected point: {format_coords(lat, lon)}")
        self.refresh_all()

    def on_list_select(self, event):
        """An alert was chosen in the list box."""
        chosen = self.listbox.curselection()
        if chosen:
            self.selected_alert_id = self.listed_ids[chosen[0]]
            self.refresh_all()


    # ...................................................................

    # Raising and updating alerts
  

    def raise_at_my_position(self):
        """Open the form using the user's own position."""
        AlertDialog(self.root, self.user.lat, self.user.lon, self.submit_alert)

    def raise_at_selected_point(self):
        """Open the form using the point clicked on the map."""
        if self.selected_point is not None:
            lat, lon = self.selected_point
            AlertDialog(self.root, lat, lon, self.submit_alert)

    def submit_alert(self, alert_type, lat, lon, description):
        """Called by the form when the user presses 'Send alert'."""
        try:
            alert = self.manager.raise_alert(alert_type, lat, lon, description,
                                             self.user.name)
        except OSError as error:           # e.g. the disk is full or read-only
            messagebox.showerror("Could not save", f"Your alert was not saved:\n{error}")
            return
        self.selected_point = None
        self.point_button.config(state="disabled")
        self.point_label.config(text="Alert sent! Click the map to pick a point.")
        self.selected_alert_id = alert.alert_id
        self.refresh_all()

    def change_status(self, new_status):
        """Volunteer pressed 'I'm responding' or 'Mark resolved'."""
        if self.selected_alert_id is None:
            messagebox.showinfo("Select an alert",
                                "Choose an alert from the list or the map first.")
            return
        try:
            self.manager.change_status(self.selected_alert_id, new_status)
        except OSError as error:
            messagebox.showerror("Could not save", f"The change was not saved:\n{error}")
            return
        self.refresh_all()

    def reset_demo(self):
        """Throw away all alerts and go back to the demo set."""
        if not messagebox.askyesno("Reset demo alerts",
                                   "Replace all current alerts with the demo alerts?"):
            return
        try:
            storage.reset_to_demo()
        except OSError as error:
            messagebox.showerror("Could not reset", str(error))
            return
        self.manager.reload()
        self.selected_alert_id = None
        self.refresh_all()

    # ...................................................................

    # Refreshing what is on screen
  

    def auto_refresh(self):
        """Every few seconds re-read the shared file (so other users' alerts appear)."""
        self.manager.reload()
        self.refresh_all()
        self.root.after(REFRESH_MS, self.auto_refresh)

    def refresh_all(self):
        """Update the list, banner, details and map."""
        self.update_list()
        self.update_banner()
        self.update_detail()
        self.map_view.redraw(self.manager.get_active_alerts(), self.user,
                             self.selected_point, self.selected_alert_id)

    def update_list(self):
        """Fill the list box with active alerts, nearest first."""
        rows = self.manager.alerts_for_user(self.user)
        texts = []
        for alert, dist, where in rows:
            suffix = "" if alert.status == "open" else f"  [{alert.status}]"
            texts.append(f"{alert.label()} - {format_distance(dist)} {where}{suffix}")

        if texts != self.list_texts:          # only rebuild if something changed
            self.listbox.delete(0, "end")
            for index, (alert, dist, where) in enumerate(rows):
                self.listbox.insert("end", texts[index])
                self.listbox.itemconfig(index, fg=ALERT_TYPES[alert.alert_type]["dark"])
            self.list_texts = texts

        self.listed_ids = [alert.alert_id for alert, dist, where in rows]

        # Keep the selected alert highlighted (or forget it if it was resolved)
        self.listbox.selection_clear(0, "end")
        if self.selected_alert_id in self.listed_ids:
            self.listbox.selection_set(self.listed_ids.index(self.selected_alert_id))
        else:
            self.selected_alert_id = None

    def update_banner(self):
        """Show the most urgent warning, and beep if a new one has appeared."""
        warnings = self.manager.warnings_for(self.user)

        if not warnings:
            if self.user.is_volunteer():
                text = "No medical emergencies waiting for a volunteer."
            else:
                text = (f"All clear - no alerts ahead within "
                        f"{format_distance(WARNING_RADIUS_M)}.")
            colour = OK_COLOUR
        else:
            alert, dist, where = warnings[0]               # the closest one
            text = self.manager.warning_text(self.user, alert, dist, where)
            if len(warnings) > 1:
                text += f"\n(+{len(warnings) - 1} more nearby)"
            colour = ALERT_TYPES[alert.alert_type]["dark"]

        # Beep only for alerts we have not warned about yet
        current_ids = {alert.alert_id for alert, dist, where in warnings}
        if current_ids - self.notified_ids:
            self.root.bell()
        self.notified_ids = current_ids

        self.banner.config(text=text, bg=colour)

    def update_detail(self):
        """Show the full details of the selected alert."""
        alert = self.manager.find(self.selected_alert_id)
        if alert is None:
            self.detail_label.config(text="Select an alert (list or map) to see details.")
            return
        near = self.route.nearest_waypoint_name(alert.lat, alert.lon)
        self.detail_label.config(text=f"{alert.details_text()}\nNear: {near}")
