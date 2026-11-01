"""
test_logic.py - Automatic checks for the non-GUI parts of the project.

Run them from the project folder with:   python -m unittest discover -s tests
"""

import json
import os
import sys
import tempfile
import unittest

# Let the tests import the project files that live one folder up
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import storage
from alert import Alert
from alert_manager import AlertManager
from route import Route
from user import User
from utils import (ROLE_RUNNER, ROLE_VOLUNTEER, STATUS_RESPONDING,
                   bearing_deg, compass_name, distance_m, format_distance,
                   parse_coordinate, relative_direction)


class TestMaths(unittest.TestCase):
    def test_distance_zero_and_known_value(self):
        self.assertEqual(distance_m(-33.86, 151.21, -33.86, 151.21), 0)
        # 0.001 degrees of latitude is about 111 metres
        self.assertAlmostEqual(distance_m(-33.860, 151.2, -33.861, 151.2), 111, delta=2)

    def test_bearing_and_directions(self):
        self.assertAlmostEqual(bearing_deg(-33.9, 151.2, -33.8, 151.2), 0, delta=1)    # north
        self.assertAlmostEqual(bearing_deg(-33.9, 151.2, -33.9, 151.3), 90, delta=1)   # east
        self.assertEqual(compass_name(45), "north-east")
        self.assertEqual(relative_direction(0, 90), "on your right")
        self.assertEqual(relative_direction(0, 270), "on your left")
        self.assertEqual(relative_direction(0, 5), "straight ahead")
        self.assertEqual(relative_direction(0, 180), "behind you")
        self.assertEqual(relative_direction(350, 10), "straight ahead")   # wraps past 360

    def test_format_distance(self):
        self.assertEqual(format_distance(483), "480 m")
        self.assertEqual(format_distance(1234), "1.2 km")
        self.assertEqual(format_distance(3), "under 10 m")

    def test_parse_coordinate_errors(self):
        self.assertEqual(parse_coordinate(" -33.86 ", "Latitude", -34, -33), -33.86)
        with self.assertRaises(ValueError):
            parse_coordinate("abc", "Latitude", -34, -33)
        with self.assertRaises(ValueError):
            parse_coordinate("10", "Latitude", -34, -33)


class TestRoute(unittest.TestCase):
    def test_start_and_finish(self):
        route = Route()
        lat, lon, _ = route.position_at_fraction(0)
        self.assertEqual((lat, lon), tuple(route.waypoints[0][1:]))
        lat, lon, _ = route.position_at_fraction(1)
        self.assertAlmostEqual(lat, route.waypoints[-1][1])
        self.assertGreater(route.total_m, 10000)

    def test_nearest_waypoint(self):
        route = Route()
        self.assertEqual(route.nearest_waypoint_name(-33.8578, 151.2147),
                         "FINISH - Opera House")


class TestAlertAndStorage(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "alerts.json")

    def tearDown(self):
        self.folder.cleanup()

    def test_alert_round_trip(self):
        original = Alert("hazard", -33.86, 151.21, "Loose barrier", "Runner 1")
        copy = Alert.from_dict(original.to_dict())
        self.assertEqual(copy.to_dict(), original.to_dict())

    def test_bad_alert_type_rejected(self):
        with self.assertRaises(ValueError):
            Alert("banana", 0, 0, "x", "y")

    def test_save_then_load(self):
        storage.save_alerts([Alert("medical_major", -33.86, 151.21, "Down", "R1")], self.path)
        loaded = storage.load_alerts(self.path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].alert_type, "medical_major")

    def test_old_medical_type_is_upgraded_to_major(self):
        # Files saved by the previous version used a single "medical" type
        old = Alert("medical", -33.86, 151.21, "Collapsed", "R1")
        self.assertEqual(old.alert_type, "medical_major")
        self.assertTrue(old.is_medical())
        self.assertTrue(old.is_major_medical())

    def test_medical_levels(self):
        minor = Alert("medical_minor", -33.86, 151.21, "Grazed knee", "R1")
        major = Alert("medical_major", -33.86, 151.21, "Not breathing", "R1")
        self.assertTrue(minor.is_medical() and not minor.is_major_medical())
        self.assertTrue(major.is_medical() and major.is_major_medical())
        self.assertLess(major.priority(), minor.priority())
        self.assertFalse(Alert("hazard", -33.86, 151.21, "x", "y").is_medical())

    def test_missing_file_gives_empty_list(self):
        self.assertEqual(storage.load_alerts(self.path), [])

    def test_corrupted_file_is_set_aside(self):
        with open(self.path, "w") as file:
            file.write("{ this is not json")
        self.assertEqual(storage.load_alerts(self.path), [])
        self.assertTrue(os.path.exists(self.path + ".corrupt"))

    def test_damaged_entry_is_skipped(self):
        good = Alert("hazard", -33.86, 151.21, "ok", "R1").to_dict()
        with open(self.path, "w") as file:
            json.dump([good, {"type": "hazard"}, "nonsense"], file)
        self.assertEqual(len(storage.load_alerts(self.path)), 1)


class TestAlertManager(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.manager = AlertManager(os.path.join(self.folder.name, "alerts.json"))
        # A runner facing north at a fixed spot
        self.runner = User("Runner 1", ROLE_RUNNER, -33.8800, 151.2000, heading=0)

    def tearDown(self):
        self.folder.cleanup()

    def test_obstruction_on_the_right_about_500m(self):
        # About 500 m due east of the runner, so it should be on their right
        self.manager.raise_alert("obstruction", -33.8800, 151.2054, "Cones", "Runner 2")
        warnings = self.manager.warnings_for(self.runner)
        self.assertEqual(len(warnings), 1)
        alert, dist, where = warnings[0]
        self.assertEqual(where, "on your right")
        self.assertAlmostEqual(dist, 500, delta=15)
        self.assertIn("Road obstruction on your right in 500 m",
                      self.manager.warning_text(self.runner, alert, dist, where))

    def test_far_and_behind_alerts_are_not_warnings(self):
        self.manager.raise_alert("hazard", -33.8800, 151.2300, "Far away", "Runner 2")
        self.manager.raise_alert("hazard", -33.8840, 151.2000, "Behind", "Runner 2")
        self.assertEqual(self.manager.warnings_for(self.runner), [])

    def test_volunteer_only_sees_open_medical(self):
        volunteer = User("Volunteer Sam", ROLE_VOLUNTEER, -33.88, 151.20)
        self.manager.raise_alert("hazard", -33.88, 151.201, "Barrier", "Runner 2")
        medical = self.manager.raise_alert("medical_minor", -33.89, 151.201, "Hurt", "Runner 2")
        self.assertEqual(len(self.manager.warnings_for(volunteer)), 1)
        self.manager.change_status(medical.alert_id, STATUS_RESPONDING)
        self.assertEqual(self.manager.warnings_for(volunteer), [])

    def test_major_medical_comes_before_closer_minor(self):
        volunteer = User("Volunteer Sam", ROLE_VOLUNTEER, -33.88, 151.20)
        # The minor one is about 100 m away, the major one about 1 km away
        self.manager.raise_alert("medical_minor", -33.881, 151.20, "Blister", "Runner 2")
        self.manager.raise_alert("medical_major", -33.89, 151.20, "Collapsed", "Runner 3")
        warnings = self.manager.warnings_for(volunteer)
        self.assertEqual([w[0].alert_type for w in warnings],
                         ["medical_major", "medical_minor"])
        alert, dist, where = warnings[0]
        text = self.manager.warning_text(volunteer, alert, dist, where)
        self.assertIn("!!! MAJOR MEDICAL EMERGENCY", text)

    def test_resolved_alerts_disappear_and_persist(self):
        alert = self.manager.raise_alert("hazard", -33.88, 151.20, "Gone soon", "R2")
        self.assertTrue(self.manager.change_status(alert.alert_id, "resolved"))
        self.assertEqual(self.manager.get_active_alerts(), [])
        self.manager.reload()                       # re-read from the file
        self.assertEqual(self.manager.get_active_alerts(), [])
        self.assertFalse(self.manager.change_status("nope", "resolved"))


if __name__ == "__main__":
    unittest.main()
