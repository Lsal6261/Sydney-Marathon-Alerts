# Sydney Marathon Alerts

I made this Python app that lets runners and volunteers at the Sydney
Marathon raise alerts on a coloured map, such as a fallen barrier, a blocked road,
an injured runner, so that other people know what is coming up and volunteers
can find anyone who needs help.


> **Simulation:** this is a single-computer prototype. There is no live
> server. You switch between a **Runner** and a **Volunteer** inside the
> app, and alerts are "shared" through a saved file (`data/alerts.json`).
> The map and route are **simplified and approximate**, based loosely on the
> published course, and are not the official course line.

## Features

- Coloured map of the course: harbour, parks, route, kilometre markers,
  landmarks, start (North Sydney) and finish (Opera House).
- **Click the map** to pick an exact point and see its latitude/longitude.
- **Raise an alert** (road obstruction, hazard, or medical emergency) at your
  own position or at any point you clicked. Medical emergencies have two
  levels: **minor** (cuts, bruises, small falls, cramp) and **major**
  (cardiac arrest, runner not responsive, overheating). Major ones are drawn
  bigger on the map and always come first in the volunteer's warning banner.
- **Runner warnings:** alerts within 1 km that are ahead of you are shown in a
  banner with a direction and distance, e.g.
  *"WARNING: Road obstruction on your right in 500 m"*.
- **Volunteer view:** open medical emergencies (both levels) are flagged, with
  distance and compass direction, major before minor. Volunteers can press **I'm responding** and **Mark
  resolved**.
- Alerts are saved between runs and reloaded every 2 seconds, so you can run
  the app **twice** and watch alerts from one window appear in the other.

## How to run

You need Python 3.8.

Run by using:
```
python main.py
```

`tkinter` (the window toolkit) comes with Python on Windows and macOS. On
Ubuntu/Debian install it with `sudo apt install python3-tk`.

### Try it out using these instructions

1. Run the app. Five demo alerts are loaded on the first run.
2. Drag the **position slider** to move the runner along the course and watch
   the warning banner change.
3. Click an empty spot on the map, press **Raise alert at selected point**,
   fill in the form and send it.
4. Switch to **Volunteer** (top right), select the major medical alert and
   press **I'm responding**, then **Mark resolved**.
5. **Reset demo alerts** puts everything back to the starting set.

## Project structure

```
main.py            Entry point: opens the window
gui.py             Window, buttons, banner, alert list and the pop-up form
map_view.py        Draws the map and converts clicks to latitude/longitude
alert_manager.py   List of alerts, distance and left/right logic, warnings
alert.py           Alert class (one report)
user.py            User class (runner or volunteer with a position)
route.py           Route class (the course and positions along it)
route_data.py      Waypoints, harbour outline, parks and labels
storage.py         Saving and loading alerts as JSON
utils.py           Constants, distance/bearing maths, input validation
data/              demo_alerts.json (shipped) and alerts.json (created at run time)
tests/             Automatic tests for the non-GUI code
```


## How the "500 m on your right" message works

1. `utils.distance_m` uses the haversine formula to get the distance in
   metres between the runner and the alert.
2. `utils.bearing_deg` gives the compass direction from the runner to the alert.
3. `utils.relative_direction` compares that with the direction the runner is
   facing (taken from the current section of the route) to decide
   left / right / ahead / behind.

## Tests

```
python -m unittest discover -s tests
```

## Limitations and ideas for the future of the project!

- No real-time networking (alerts are shared through one file; if two windows
  save at the same moment, the last save wins) - would be great to have an online network here
- Positions are simulated with a slider instead of GPS.
- The route is approximate and the drawn course is shorter than 42.195 km;
  the kilometre display is scaled to the full marathon distance.

- Ideas: Multiple maps to choose from (Boston Marathon, other marathons around the world), real GPS input (ran out of time and not sure how to do this), a small server for true multi-user use, users can upload photos on alerts.
