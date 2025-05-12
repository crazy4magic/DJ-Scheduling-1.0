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

def can_move_slot(
    dj: str,
    source: Optional[Dict[str, datetime]],
    target: Dict[str, datetime],
    dj_events: Dict[str, List[Dict[str, datetime]]]
) -> Tuple[bool, str]:
    """
    Check if a DJ can move from source to target without conflicts.
    
    Args:
        dj (str): DJ name
        source (Optional[Dict[str, datetime]]): Source slot information
        target (Dict[str, datetime]): Target slot information
        dj_events (Dict[str, List[Dict[str, datetime]]]): All DJ events
        
    Returns:
        Tuple[bool, str]: (can move, reason if cannot)
        
    Example:
        >>> source = {'venue': 'A', 'start': datetime(10,0), 'end': datetime(11,0)}
        >>> target = {'venue': 'B', 'start': datetime(12,0), 'end': datetime(13,0)}
        >>> can_move_slot('DJ1', source, target, {'DJ1': [source]})
        (True, '')
    """
    events = dj_events.get(dj, [])
    # Remove source event from consideration
    remaining = [e for e in events if not (
        source and 
        e['venue'] == source['venue'] and 
        e['start'] == source['start'] and 
        e['end'] == source['end']
    )]
    
    # Check if target day matches any existing events
    if target.get('day') and any(e.get('day') != target['day'] for e in remaining):
        return False, f"Cannot switch to {target['day']} due to existing schedule on other days."
    
    # Check overlap at target
    for e in remaining:
        if not (target['end'] <= e['start'] or target['start'] >= e['end']):
            return False, f"Overlap with {dj}'s event at {e['venue']} from {e['start'].strftime('%H:%M')} to {e['end'].strftime('%H:%M')}."
    
    # Check travel buffer before/after
    for e in remaining:
        # if e ends before target starts, check buffer
        if e['end'] <= target['start']:
            buffer = TRAVEL_TIME.get((e['venue'], target['venue']), 0)
            if (target['start'] - e['end']).total_seconds()/60 < buffer:
                return False, f"Not enough travel time from {e['venue']} to {target['venue']} (needs {buffer} min)."
        # if e starts after target ends, check buffer
        if e['start'] >= target['end']:
            buffer = TRAVEL_TIME.get((target['venue'], e['venue']), 0)
            if (e['start'] - target['end']).total_seconds()/60 < buffer:
                return False, f"Not enough travel time from {target['venue']} to {e['venue']} (needs {buffer} min)."
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
        ok, _ = can_move_slot(dj, None, target, dj_events)
        if ok:
            suggestions.append(dj)
    return suggestions 