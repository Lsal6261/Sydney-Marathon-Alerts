"""
alert.py - for the Alert class

An Alert is one report from a runner or volunteer, for example
"a barrier has fallen over here" or "a runner is injured here".
"""

import uuid
from datetime import datetime

from utils import (ALERT_TYPES, LEGACY_ALERT_TYPES, STATUS_OPEN, STATUS_RESOLVED,
                   VALID_STATUSES, is_medical)


class Alert:
    """One alert on the course, with an exact position."""

    def __init__(self, alert_type, lat, lon, description, reported_by,
                 alert_id=None, created=None, status=STATUS_OPEN):
        alert_type = LEGACY_ALERT_TYPES.get(alert_type, alert_type)
        # Check the inputs so a bad alert can never be created
        if alert_type not in ALERT_TYPES:
            raise ValueError(f"Unknown alert type: {alert_type}")
        if status not in VALID_STATUSES:
            raise ValueError(f"Unknown status: {status}")

        self.alert_type = alert_type
        self.lat = float(lat)
        self.lon = float(lon)
        self.description = str(description)
        self.reported_by = str(reported_by)
        self.status = status

        # A short random id so we can find this alert again later
        self.alert_id = alert_id or uuid.uuid4().hex[:8]
        # When it was raised, stored as text like 2027-08-29T07:15:00
        self.created = created or datetime.now().isoformat(timespec="seconds")

    # ----- status -----

    def is_active(self):
        """An alert is active until a volunteer marks it resolved."""
        return self.status != STATUS_RESOLVED

    def set_status(self, new_status):
        """Change the status (open / responding / resolved)."""
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Unknown status: {new_status}")
        self.status = new_status

    # ----- what kind of alert is this? -----

    def is_medical(self):
        """True for a minor or a major medical emergency."""
        return is_medical(self.alert_type)

    def is_major_medical(self):
        """True only for the serious level (cardiac arrest, unresponsive...)."""
        return self.alert_type == "medical_major"

    def priority(self):
        """0 = most urgent (major medical), then minor medical, then the rest."""
        return ALERT_TYPES[self.alert_type]["priority"]

    # ----- text for the screen -----

    def label(self):
        """Human-friendly name of this alert's type."""
        return ALERT_TYPES[self.alert_type]["label"]

    def time_text(self):
        """Just the time of day, e.g. '07:15'."""
        try:
            return datetime.fromisoformat(self.created).strftime("%H:%M")
        except ValueError:
            return self.created      # show the raw text if it is not a date

    def details_text(self):
        """Several lines of detail for the 'selected alert' panel."""
        return (f"{self.label()} ({self.status})\n"
                f"Position: {self.lat:.5f}, {self.lon:.5f}\n"
                f"Reported by {self.reported_by} at {self.time_text()}\n"
                f"\"{self.description}\"")

    # ----- saving and loading -----

    def to_dict(self):
        """Turn the alert into a plain dictionary so it can be saved as JSON."""
        return {
            "id": self.alert_id,
            "type": self.alert_type,
            "lat": self.lat,
            "lon": self.lon,
            "description": self.description,
            "reported_by": self.reported_by,
            "created": self.created,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild an Alert from a dictionary loaded from JSON.

        Raises KeyError / ValueError / TypeError if the data is damaged;
        storage.py catches these so one bad entry can't crash the app.
        """
        return cls(alert_type=data["type"],
                   lat=data["lat"],
                   lon=data["lon"],
                   description=data["description"],
                   reported_by=data["reported_by"],
                   alert_id=data["id"],
                   created=data["created"],
                   status=data["status"])
