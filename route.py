"""
route.py - made for the Route class: knows how long the course is and where a
person is when they are a certain fraction of the way along it
"""

from route_data import ROUTE_WAYPOINTS
from utils import bearing_deg, distance_m


class Route:
    """The marathon course, made of straight lines between waypoints."""

    def __init__(self, waypoints=None):
        # Use the real course unless a different list is given (handy for tests)
        self.waypoints = waypoints if waypoints is not None else ROUTE_WAYPOINTS

        # cumulative_m[i] = how many metres it is from the start to waypoint i
        self.cumulative_m = [0.0]
        for i in range(1, len(self.waypoints)):
            _, lat1, lon1 = self.waypoints[i - 1]
            _, lat2, lon2 = self.waypoints[i]
            leg = distance_m(lat1, lon1, lat2, lon2)
            self.cumulative_m.append(self.cumulative_m[-1] + leg)

        self.total_m = self.cumulative_m[-1]

    def position_at_fraction(self, fraction):
        """Return (lat, lon, heading) for a point part-way along the course.

        fraction is 0.0 at the start and 1.0 at the finish. The heading is
        the compass direction of the straight section the person is on.
        """
        fraction = max(0.0, min(1.0, fraction))      # keep it between 0 and 1
        target = fraction * self.total_m

        for i in range(1, len(self.waypoints)):
            if target <= self.cumulative_m[i]:
                _, lat1, lon1 = self.waypoints[i - 1]
                _, lat2, lon2 = self.waypoints[i]
                leg_length = self.cumulative_m[i] - self.cumulative_m[i - 1]

                # How far along this one straight section (0 to 1)?
                t = (target - self.cumulative_m[i - 1]) / leg_length if leg_length else 0
                lat = lat1 + t * (lat2 - lat1)
                lon = lon1 + t * (lon2 - lon1)
                return lat, lon, bearing_deg(lat1, lon1, lat2, lon2)

        # Safety net: we only get here if the fraction was rounded past the end
        _, lat1, lon1 = self.waypoints[-2]
        _, lat2, lon2 = self.waypoints[-1]
        return lat2, lon2, bearing_deg(lat1, lon1, lat2, lon2)

    def nearest_waypoint_name(self, lat, lon):
        """Return the name of the waypoint closest to a position."""
        best_name = ""
        best_distance = None
        for name, wp_lat, wp_lon in self.waypoints:
            d = distance_m(lat, lon, wp_lat, wp_lon)
            if best_distance is None or d < best_distance:
                best_distance = d
                best_name = name
        return best_name
