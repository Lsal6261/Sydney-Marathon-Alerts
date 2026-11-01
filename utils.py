"""
utils.py - Shared constants and small helper functions.

Everything in this file is "plain maths" (distance, direction) or simple
text formatting / validation. Nothing here knows about the window (GUI),
so these functions are easy to test on their own.
"""

import math


# Constants


EARTH_RADIUS_M = 6371000      # Average radius of the Earth in metres
WARNING_RADIUS_M = 1000       # Runners are warned about alerts within this distance

# The roles a person can have in the app
ROLE_RUNNER = "runner"
ROLE_VOLUNTEER = "volunteer"

# The life cycle of an alert: open -> responding -> resolved
STATUS_OPEN = "open"
STATUS_RESPONDING = "responding"
STATUS_RESOLVED = "resolved"
VALID_STATUSES = (STATUS_OPEN, STATUS_RESPONDING, STATUS_RESOLVED)

# The kinds of alert a user can raise. Keeping them in ONE dictionary means
# the label, colours and map shape are all defined in a single place.
#
# "priority" is used to order warnings: 0 is the most urgent. Medical
# emergencies come in two levels so volunteers can tell at a glance whether
# someone needs a plaster or an ambulance:
#   * minor - cuts, bruises, small falls, blisters, cramp
#   * major - cardiac arrest, runner not responsive, overheating, heavy bleeding
ALERT_TYPES = {
    "obstruction":   {"label": "Road obstruction", "colour": "#f28c28",
                      "dark": "#c2410c", "shape": "square", "priority": 2,
                      "examples": "cones, fallen barrier, blocked lane"},
    "hazard":        {"label": "Hazard / warning", "colour": "#f5d000",
                      "dark": "#a16207", "shape": "triangle", "priority": 2,
                      "examples": "wet ground, loose cable, pothole"},
    "medical_minor": {"label": "Minor medical", "colour": "#f87171",
                      "dark": "#b91c1c", "shape": "circle", "priority": 1,
                      "examples": "cuts, bruises, small falls, cramp"},
    "medical_major": {"label": "MAJOR medical emergency", "colour": "#dc2626",
                      "dark": "#7f1d1d", "shape": "circle", "priority": 0,
                      "examples": "cardiac arrest, runner not responsive, overheating"},
}

# The two medical levels, most urgent first
MEDICAL_TYPES = ("medical_major", "medical_minor")

# Older saved files used a single "medical" type. We treat those as major so
# nothing that might be serious is ever downgraded or thrown away on load.
LEGACY_ALERT_TYPES = {"medical": "medical_major"}


def is_medical(alert_type):
    """True for either level of medical emergency."""
    return alert_type in MEDICAL_TYPES


# ..........................................................................
# Distance and direction maths


def distance_m(lat1, lon1, lat2, lon2):
    """Return the distance in metres between two latitude/longitude points.

    Uses the 'haversine' formula, which accounts for the curve of the Earth.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    """Return the compass bearing from point 1 to point 2 in degrees.

    0 = North, 90 = East, 180 = South, 270 = West.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_lambda = math.radians(lon2 - lon1)

    y = math.sin(d_lambda) * math.cos(phi2)
    x = (math.cos(phi1) * math.sin(phi2)
         - math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda))
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def relative_direction(heading, target_bearing):
    """Say where a target is compared with the way a runner is facing.

    heading        - the direction the runner is running (compass degrees)
    target_bearing - the compass bearing from the runner to the target
    Returns text such as "on your right".
    """
    # Difference between the two directions, wrapped into -180 .. +180.
    # Positive means the target is clockwise of us (to the right).
    angle = (target_bearing - heading + 180) % 360 - 180

    if abs(angle) <= 20:
        return "straight ahead"
    if abs(angle) >= 160:
        return "behind you"
    if angle > 0:
        return "on your right"
    return "on your left"


def compass_name(bearing):
    """Turn a bearing in degrees into a word, e.g. 45 -> 'north-east'."""
    names = ["north", "north-east", "east", "south-east",
             "south", "south-west", "west", "north-west"]
    # Each name covers a 45 degree slice, centred on its direction.
    index = int((bearing + 22.5) // 45) % 8
    return names[index]


# ..........................................................................
# Text formatting and validation


def format_distance(metres):
    """Make a distance friendly to read: '480 m' or '1.2 km'."""
    if metres >= 1000:
        return f"{metres / 1000:.1f} km"
    rounded = int(round(metres / 10.0)) * 10      # nearest 10 m
    if rounded == 0:
        return "under 10 m"
    return f"{rounded} m"


def format_coords(lat, lon):
    """Format a position as text. 5 decimal places is about 1 metre."""
    return f"{lat:.5f}, {lon:.5f}"


def parse_coordinate(text, label, low, high):
    """Convert text typed by the user into a number inside a valid range.

    Raises ValueError with a friendly message if the text is not a number
    or is outside the map area. Callers catch this with try/except.
    """
    try:
        value = float(text.strip())
    except ValueError:
        raise ValueError(f"{label} must be a number (you typed '{text}').")

    if not low <= value <= high:
        raise ValueError(f"{label} must be inside the map area "
                         f"({low} to {high}).")
    return value
