"""
user.py - The User class: a runner or a volunteer with a position.
"""

from utils import ROLE_VOLUNTEER


class User:
    """The person using the app (we simulate one person at a time)."""

    def __init__(self, name, role, lat=0.0, lon=0.0, heading=0.0):
        self.name = name
        self.role = role          # "runner" or "volunteer"
        self.lat = lat
        self.lon = lon
        self.heading = heading    # direction of travel, compass degrees

    def is_volunteer(self):
        """True if this user is a volunteer (they can respond to alerts)."""
        return self.role == ROLE_VOLUNTEER

    def move_along_route(self, route, fraction):
        """Place the user part-way along the course (0.0 = start, 1.0 = finish)."""
        self.lat, self.lon, self.heading = route.position_at_fraction(fraction)
