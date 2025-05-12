"""
Type definitions for the DJ Schedule Manager application.
"""

from typing import TypedDict, List, Optional
from datetime import datetime

class TimeSlot(TypedDict):
    """Represents a single time slot in the schedule."""
    start: str
    end: str
    dj: str
    day: Optional[str]

class VenueSchedule(TypedDict):
    """Represents a venue's schedule."""
    venue: str
    slots: List[TimeSlot]

class DJEvent(TypedDict):
    """Represents a DJ's event."""
    venue: str
    start: datetime
    end: datetime
    day: Optional[str]

class TravelTime(TypedDict):
    """Represents travel time between venues."""
    from_venue: str
    to_venue: str
    minutes: int

class SwitchRequest(TypedDict):
    """Represents a DJ switch request."""
    dj: str
    current_slot: DJEvent
    desired_slot: DJEvent 