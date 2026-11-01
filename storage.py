"""
storage.py - Saving and loading alerts from a file (file I/O).

Alerts are stored as JSON in data/alerts.json. Because every user in our
simulation reads and writes the same file, that file is how alerts are
"shared" between users.

Error handling: loading never crashes the app. A missing file gives an empty
list, a corrupted file is set aside, and a damaged entry is skipped.
Saving raises OSError on failure so the caller can tell the user.
"""

import json
import os
import shutil

from alert import Alert

# Build file paths relative to this file so the app works from any folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.json")
DEMO_FILE = os.path.join(DATA_DIR, "demo_alerts.json")


def ensure_data_file(path=ALERTS_FILE, demo_path=DEMO_FILE):
    """On the very first run, copy the demo alerts so the map isn't empty."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path) and os.path.exists(demo_path):
            shutil.copyfile(demo_path, path)
    except OSError as error:
        print(f"Could not create the alerts file: {error}")


def reset_to_demo(path=ALERTS_FILE, demo_path=DEMO_FILE):
    """Replace all saved alerts with the demo alerts (raises OSError on failure)."""
    shutil.copyfile(demo_path, path)


def load_alerts(path=ALERTS_FILE):
    """Read the alerts file and return a list of Alert objects."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            raw_entries = json.load(file)
    except FileNotFoundError:
        return []                                  # no file yet: no alerts
    except json.JSONDecodeError:
        # The file is damaged. Keep a copy for inspection and start fresh.
        print(f"{path} is corrupted - moving it aside and starting empty.")
        try:
            os.replace(path, path + ".corrupt")
        except OSError:
            pass
        return []
    except OSError as error:
        print(f"Could not read {path}: {error}")
        return []

    if not isinstance(raw_entries, list):          # valid JSON, wrong shape
        print(f"{path} does not contain a list of alerts - ignoring it.")
        return []

    alerts = []
    for entry in raw_entries:
        try:
            alerts.append(Alert.from_dict(entry))
        except (KeyError, ValueError, TypeError) as error:
            print(f"Skipping a damaged alert in the file ({error!r}).")
    return alerts


def save_alerts(alerts, path=ALERTS_FILE):
    """Write the list of Alert objects to the file. Raises OSError on failure.

    We write to a temporary file first and then swap it in, so a crash half
    way through can never leave a half-written alerts file behind.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump([alert.to_dict() for alert in alerts], file, indent=2)
    os.replace(temp_path, path)
