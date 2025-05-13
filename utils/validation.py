"""
Validation utilities for DJ Schedule Manager.

This module handles schedule validation, including:
- Conflict detection
- Travel time validation
- Schedule feasibility checks

Dependencies:
- datetime: For time handling
- config.travel_times: For travel time data
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional

from config.travel_times import TRAVEL_TIME

# Venue area grouping
CLUB_AREAS = {
    "Day and Night": "Itaewon",
    "Code Lounge": "Apgujeong",
    "A.P. Lounge": "Apgujeong"
}

# Travel time between areas in minutes
AREA_TRAVEL_TIME = {
    ("Itaewon", "Apgujeong"): 30,
    ("Apgujeong", "Itaewon"): 30,
    ("Itaewon", "Itaewon"): 5,
    ("Apgujeong", "Apgujeong"): 5
}

def get_venue_area(venue: str) -> str:
    """
    Get the area a venue is located in.
    
    Args:
        venue (str): Venue name
        
    Returns:
        str: Area name (e.g. "Itaewon", "Apgujeong")
    """
    return CLUB_AREAS.get(venue, "Unknown")

def get_area_travel_time(from_venue: str, to_venue: str) -> int:
    """
    Calculate travel time between venues based on their areas.
    
    Args:
        from_venue (str): Starting venue
        to_venue (str): Destination venue
        
    Returns:
        int: Travel time in minutes
    """
    from_area = get_venue_area(from_venue)
    to_area = get_venue_area(to_venue)
    
    # First check if we have a direct venue-to-venue time
    direct_time = TRAVEL_TIME.get((from_venue, to_venue))
    if direct_time is not None:
        return direct_time
        
    # Otherwise use area-based travel time
    return AREA_TRAVEL_TIME.get((from_area, to_area), 30)  # Default to 30 min if unknown

def can_move_slot(
    dj: str,
    source: Optional[Dict[str, datetime]],
    target: Dict[str, datetime],
    dj_events: Dict[str, List[Dict[str, datetime]]],
    day: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Check if a DJ can move from source to target without conflicts.
    
    Args:
        dj (str): DJ name
        source (Optional[Dict[str, datetime]]): Source slot information
        target (Dict[str, datetime]): Target slot information
        dj_events (Dict[str, List[Dict[str, datetime]]]): All DJ events
        day (Optional[str]): Specific day to check conflicts for
        
    Returns:
        Tuple[bool, str]: (can move, reason if cannot)
    """
    events = dj_events.get(dj, [])
    
    # Filter events by day if specified
    if day:
        events = [e for e in events if e.get('day') == day]
    
    # Remove source event from consideration
    remaining = [e for e in events if not (
        source and 
        e['venue'] == source['venue'] and 
        e['start'] == source['start'] and 
        e['end'] == source['end']
    )]
    
    # Check overlap at target
    for e in remaining:
        if not (target['end'] <= e['start'] or target['start'] >= e['end']):
            return False, f"Overlap with {dj}'s event at {e['venue']} from {e['start'].strftime('%H:%M')} to {e['end'].strftime('%H:%M')}."
    
    # Check travel buffer and back-to-back sets
    for e in remaining:
        # Check for back-to-back sets (within 1 minute)
        if abs((target['start'] - e['end']).total_seconds()) < 60:
            return False, f"Would be double-booked back-to-back with set at {e['venue']} ending at {e['end'].strftime('%H:%M')}"
        if abs((e['start'] - target['end']).total_seconds()) < 60:
            return False, f"Would be double-booked back-to-back with set at {e['venue']} starting at {e['start'].strftime('%H:%M')}"
            
        # Check travel buffer before/after using area-based travel times
        if e['end'] <= target['start']:
            buffer = get_area_travel_time(e['venue'], target['venue'])
            if (target['start'] - e['end']).total_seconds()/60 < buffer:
                return False, f"Not enough travel time from {e['venue']} ({get_venue_area(e['venue'])}) to {target['venue']} ({get_venue_area(target['venue'])}) (needs {buffer} min)."
        if e['start'] >= target['end']:
            buffer = get_area_travel_time(target['venue'], e['venue'])
            if (e['start'] - target['end']).total_seconds()/60 < buffer:
                return False, f"Not enough travel time from {target['venue']} ({get_venue_area(target['venue'])}) to {e['venue']} ({get_venue_area(e['venue'])}) (needs {buffer} min)."
    return True, ""

def suggest_replacements(
    target: Dict[str, datetime],
    dj_events: Dict[str, List[Dict[str, datetime]]]
) -> List[str]:
    """
    Suggest DJs who can fill a target slot.
    
    Args:
        target (Dict[str, datetime]): Target slot information
        dj_events (Dict[str, List[Dict[str, datetime]]]): All DJ events
        
    Returns:
        List[str]: List of available DJs
        
    Example:
        >>> target = {'venue': 'A', 'start': datetime(10,0), 'end': datetime(11,0)}
        >>> suggest_replacements(target, {'DJ1': []})
        ['DJ1']
    """
    suggestions = []
    for dj, events in dj_events.items():
        # Only check conflicts for the specific day if provided
        ok, _ = can_move_slot(dj, None, target, dj_events, day=target.get('day'))
        if ok:
            suggestions.append(dj)
    return suggestions 