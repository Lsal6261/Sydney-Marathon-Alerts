"""
alert_manager.py - made for the AlertManager class

Cotains a list of alerts and answers questions such as "which alerts are
close to this user?" It does the saving through storage.py, and it contains
the logic behind messages like "Road obstruction on your right in 500 m".
"""

from alert import Alert
from storage import ALERTS_FILE, load_alerts, save_alerts
from utils import (ALERT_TYPES, STATUS_OPEN, WARNING_RADIUS_M, bearing_deg,
                   compass_name, distance_m, format_distance, relative_direction)


class AlertManager:
    """Keeps track of every alert on the course."""

    def __init__(self, path=ALERTS_FILE):
        self.path = path
        self.alerts = load_alerts(path)

    # ----- loading, saving and changing alerts -----

    def reload(self):
        """Re-read the file so we see alerts raised by other users."""
        self.alerts = load_alerts(self.path)

    def save(self):
        """Write all alerts to the file (raises OSError if that fails)."""
        save_alerts(self.alerts, self.path)

    def raise_alert(self, alert_type, lat, lon, description, reported_by):
        """Create a new alert, save it and return it."""
        self.reload()                      # start from the latest shared data
        alert = Alert(alert_type, lat, lon, description, reported_by)
        self.alerts.append(alert)
        self.save()
        return alert

    def change_status(self, alert_id, new_status):
        """Set an alert's status and save. Returns False if it wasn't found."""
        self.reload()
        alert = self.find(alert_id)
        if alert is None:
            return False
        alert.set_status(new_status)
        self.save()
        return True

    # ----- looking things up -----

    def find(self, alert_id):
        """Return the alert with this id, or None."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                return alert
        return None

    def get_active_alerts(self):
        """All alerts that have not been resolved."""
        return [alert for alert in self.alerts if alert.is_active()]

    # ----- distance and direction from a user -----

    def where_text(self, user, alert):
        """Return (distance in metres, text describing the direction).

        A runner hears "on your left / on your right / straight ahead" (based
        on the way they are running). A volunteer, who is standing still,
        hears a compass direction such as "to the north-east".
        """
        dist = distance_m(user.lat, user.lon, alert.lat, alert.lon)
        if dist < 15:
            return dist, "right here"

        bearing = bearing_deg(user.lat, user.lon, alert.lat, alert.lon)
        if user.is_volunteer():
            return dist, "to the " + compass_name(bearing)
        return dist, relative_direction(user.heading, bearing)

    def alerts_for_user(self, user):
        """Every active alert as (alert, distance, where_text), nearest first."""
        rows = []
        for alert in self.get_active_alerts():
            dist, where = self.where_text(user, alert)
            rows.append((alert, dist, where))
        rows.sort(key=lambda row: row[1])          # sort by distance
        return rows

    def warnings_for(self, user):
        """The alerts this user should be actively warned about.

        Runners: anything within the warning radius that is not behind them
        (and that they did not raise themselves).
        Volunteers: every medical emergency (minor or major) nobody is
        responding to yet. Major emergencies are listed before minor ones,
        even if a minor one is closer.
        """
        warnings = []
        for alert, dist, where in self.alerts_for_user(user):
            if user.is_volunteer():
                if alert.is_medical() and alert.status == STATUS_OPEN:
                    warnings.append((alert, dist, where))
            else:
                near = dist <= WARNING_RADIUS_M
                ahead = where != "behind you"
                not_mine = alert.reported_by != user.name
                if near and ahead and not_mine:
                    warnings.append((alert, dist, where))
        # Most urgent level first, then nearest first within a level
        warnings.sort(key=lambda row: (row[0].priority(), row[1]))
        return warnings

    def warning_text(self, user, alert, dist, where):
        """The message shown to the user, e.g.
        'WARNING: Road obstruction on your right in 500 m'."""
        label = ALERT_TYPES[alert.alert_type]["label"]
        if user.is_volunteer():
            first_line = f"{label.upper()} - {format_distance(dist)} {where}"
            if alert.is_major_medical():
                first_line = "!!! " + first_line + " !!!"
        elif where == "right here":
            first_line = f"WARNING: {label} right here"
        else:
            first_line = f"WARNING: {label} {where} in {format_distance(dist)}"
        return f"{first_line}\n\"{alert.description}\""
