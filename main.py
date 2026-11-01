"""
main.py - Start here.  Run the app with:   python main.py

Structure:
    main.py           starts the program and opens the window
      gui.py          the window: buttons, banner, alert list, pop-up form
        map_view.py   draws the coloured map and converts clicks to lat/lon
        alert_manager.py   the list of alerts, distance and left/right logic
          alert.py    one alert (type, position, description, status)
          storage.py  saves/loads alerts to data/alerts.json  (file I/O)
        route.py      the course and positions along it
          route_data.py   the waypoints, harbour and parks (2D arrays)
        user.py       a runner or volunteer with a position
        utils.py      constants, distance maths and input validation

No installing of anything else needed
"""

import sys


def main():
    """Open the main window and keep it running until the user closes it."""
    # tkinter ships with Python
    # Check here so we can show a helpful message instead of a crash.
    try:
        import tkinter as tk
    except ImportError:
        print("This app needs tkinter, which was not found.")
        print("On Ubuntu/Debian install it with:  sudo apt install python3-tk")
        sys.exit(1)

    from gui import MarathonApp

    root = tk.Tk()
    MarathonApp(root)
    root.mainloop()          # hand control to tkinter's event loop


if __name__ == "__main__":
    main()
