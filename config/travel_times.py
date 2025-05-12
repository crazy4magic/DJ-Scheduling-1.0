"""
Travel time configuration for DJ Schedule Manager.

This module contains the travel time matrix between venues.
All times are in minutes.
"""

# Travel buffer between venues (in minutes)
TRAVEL_TIME = {
    ("Code Lounge", "Day and Night"): 10,
    ("Code Lounge", "Stay Lounge"): 15,
    ("Day and Night", "Stay Lounge"): 20,
}

# Make matrix symmetric
for (a, b), t in list(TRAVEL_TIME.items()):
    TRAVEL_TIME[(b, a)] = t 