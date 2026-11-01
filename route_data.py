"""
route_data.py - The map "data": course waypoints, harbour, parks, labels.

IMPORTANT: these coordinates are APPROXIMATE and simplified. They are based
loosely on the published Sydney Marathon course (start in North Sydney, over
the Harbour Bridge, through the CBD, out along Anzac Parade, a lap of
Centennial Park, then back through Hyde Park and the Domain to finish at the
Opera House). They are NOT the official course line.

These include multi-dimensional arrays: each ROW
describes one thing, and each COLUMN holds one kind of value
"""

MARATHON_KM = 42.195

# The edges of the area drawn on the map (latitude is negative in Sydney,
# so "top" (north) is the number closest to zero).
LAT_TOP = -33.832
LAT_BOTTOM = -33.918
LON_LEFT = 151.185
LON_RIGHT = 151.250

# 2D array of the course.  Each row is:  [name, latitude, longitude]
ROUTE_WAYPOINTS = [
    ["Start - Miller St, North Sydney", -33.8395, 151.2078],
    ["Pacific Highway",                 -33.8440, 151.2085],
    ["Milsons Point",                   -33.8470, 151.2105],
    ["Harbour Bridge (north)",          -33.8488, 151.2107],
    ["Harbour Bridge (south)",          -33.8553, 151.2098],
    ["The Rocks",                       -33.8590, 151.2070],
    ["Millers Point",                   -33.8595, 151.2030],
    ["Pyrmont",                         -33.8690, 151.1965],
    ["Pyrmont Bridge",                  -33.8715, 151.2020],
    ["Town Hall",                       -33.8732, 151.2069],
    ["Hyde Park (south)",               -33.8768, 151.2118],
    ["Taylor Square",                   -33.8803, 151.2160],
    ["Moore Park",                      -33.8895, 151.2235],
    ["Anzac Parade",                    -33.9020, 151.2275],
    ["Kingsford (turnaround)",          -33.9125, 151.2310],
    ["Anzac Parade (return)",           -33.9020, 151.2284],
    ["Moore Park (return)",             -33.8902, 151.2244],
    ["Centennial Park (north)",         -33.8935, 151.2335],
    ["Centennial Park (east)",          -33.8975, 151.2420],
    ["Centennial Park (south)",         -33.9030, 151.2370],
    ["Centennial Park (west)",          -33.8995, 151.2315],
    ["Surry Hills",                     -33.8830, 151.2125],
    ["Hyde Park (north)",               -33.8745, 151.2112],
    ["The Domain",                      -33.8705, 151.2170],
    ["Mrs Macquarie's Road",            -33.8660, 151.2198],
    ["Mrs Macquarie's Chair",           -33.8606, 151.2228],
    ["Mrs Macquarie's Road (return)",   -33.8666, 151.2196],
    ["Botanic Garden",                  -33.8664, 151.2158],
    ["Circular Quay",                   -33.8630, 151.2132],
    ["Bennelong Point",                 -33.8595, 151.2145],
    ["FINISH - Opera House",            -33.8578, 151.2147],
]

# Outline of Sydney Harbour (the blue water), as [latitude, longitude] pairs.
# It is drawn as one filled polygon on top of the land.
HARBOUR_POLYGON = [
    [-33.8480, 151.1500], [-33.8470, 151.1950], [-33.8465, 151.2040],
    [-33.8445, 151.2075], [-33.8480, 151.2102], [-33.8455, 151.2145],
    [-33.8420, 151.2200], [-33.8400, 151.2300], [-33.8400, 151.3000],
    [-33.8700, 151.3000], [-33.8670, 151.2300], [-33.8650, 151.2260],
    [-33.8588, 151.2230], [-33.8628, 151.2205], [-33.8648, 151.2172],
    [-33.8605, 151.2152], [-33.8568, 151.2151], [-33.8590, 151.2138],
    [-33.8612, 151.2130], [-33.8622, 151.2105], [-33.8600, 151.2085],
    [-33.8553, 151.2090], [-33.8565, 151.2045], [-33.8575, 151.2020],
    [-33.8610, 151.2000], [-33.8618, 151.1970], [-33.8590, 151.1900],
    [-33.8600, 151.1500],
]

# Green areas.  Each row is: [name, top lat, bottom lat, left lon, right lon]
PARKS = [
    ["St Leonards Park",       -33.8350, -33.8400, 151.2060, 151.2110],
    ["Hyde Park",              -33.8722, -33.8775, 151.2095, 151.2128],
    ["The Domain",             -33.8600, -33.8735, 151.2140, 151.2225],
    ["Moore Park",             -33.8880, -33.8980, 151.2190, 151.2285],
    ["Centennial Park",        -33.8920, -33.9050, 151.2290, 151.2445],
]

# Text labels drawn on the map.  Each row is: [text, lat, lon, anchor]
# The anchor says which side of the point the text sits on:
# "w" = text runs to the right of the point, "e" = to the left, "center".
LANDMARKS = [
    ["North Sydney",          -33.8365, 151.2120, "w"],
    ["Harbour Bridge",        -33.8521, 151.2120, "w"],
    ["Opera House",           -33.8550, 151.2162, "w"],
    ["Sydney Harbour",        -33.8440, 151.2300, "center"],
    ["Pyrmont",               -33.8665, 151.1925, "center"],
    ["CBD",                   -33.8695, 151.2050, "center"],
    ["Hyde Park",             -33.8790, 151.2095, "e"],
    ["Moore Park",            -33.8935, 151.2205, "e"],
    ["Centennial\nPark",      -33.8990, 151.2368, "center"],
    ["Kingsford",             -33.9125, 151.2335, "w"],
    ["Mrs Macquarie's Chair", -33.8588, 151.2240, "w"],
    ["The Domain",            -33.8718, 151.2200, "w"],
]
