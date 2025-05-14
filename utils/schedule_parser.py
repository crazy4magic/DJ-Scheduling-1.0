"""
Schedule parsing utilities for DJ Schedule Manager.

This module handles parsing of schedule text input, including:
- Korean day indicators
- Venue names
- Time slots
- DJ assignments

Dependencies:
- re: For regular expression matching
- collections.defaultdict: For schedule organization
- datetime: For time handling
"""

import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from shared.constants import KOREAN_DAYS

def parse_clean_text(text: str) -> str:
    """
    Remove emojis and clean text.
    
    Args:
        text (str): Input text that may contain emojis
        
    Returns:
        str: Cleaned text with emojis removed
        
    Example:
        >>> parse_clean_text("Hello 👋 World!")
        'Hello World!'
    """
    # Remove emojis
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    # Remove emojis and clean text
    text = emoji_pattern.sub('', text)
    return text.strip()

def parse_schedule(text: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Parse schedule text with support for Korean day indicators.
    
    Args:
        text (str): Raw schedule text input
        
    Returns:
        Dict[str, List[Dict[str, str]]]: Parsed schedule organized by venue
            Each venue has a list of slots with start, end, dj, and day
        
    Example:
        >>> text = "금요일 Stay Lounge:\\n10:00-11:00 Anemic"
        >>> parse_schedule(text)
        {'Stay Lounge': [{'start': '10:00', 'end': '11:00', 'dj': 'Anemic', 'day': 'Friday'}]}
    """
    schedules = defaultdict(list)
    current_venue = None
    current_day = None
    
    for line in text.strip().split("\n"):
        line = parse_clean_text(line)
        if not line:
            continue
            
        # Check for Korean day indicators
        for kr_day, en_day in KOREAN_DAYS.items():
            if kr_day in line:
                current_day = en_day
                line = line.replace(kr_day, '').strip()
                break
                
        if ":" in line and "-" not in line:
            current_venue = line.replace(":", "").strip()
        elif current_venue and re.match(r"\d{1,2}:\d{2}.*", line):
            match = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})\s+(.*)", line)
            if match:
                start, end, dj = match.groups()
                schedules[current_venue].append({
                    "start": start,
                    "end": end,
                    "dj": dj.strip(),
                    "day": current_day
                })
    
    return dict(schedules)

def parse_dj_events(schedules: Dict[str, List[Dict[str, str]]]) -> Dict[str, List[Dict[str, datetime]]]:
    """
    Convert parsed schedules into per-DJ event lists with datetime objects.
    
    Args:
        schedules (Dict[str, List[Dict[str, str]]]): Parsed schedule organized by venue
        
    Returns:
        Dict[str, List[Dict[str, datetime]]]: Events organized by DJ name
            Each DJ has a list of events with venue, start, end, and day
        
    Example:
        >>> schedules = {'Venue': [{'start': '10:00', 'end': '11:00', 'dj': 'DJ1'}]}
        >>> parse_dj_events(schedules)
        {'DJ1': [{'venue': 'Venue', 'start': datetime(1900,1,1,10,0), 'end': datetime(1900,1,1,11,0)}]}
    """
    dj_events = {}
    for venue, slots in schedules.items():
        for slot in slots:
            start_dt = datetime.strptime(slot['start'], "%H:%M")
            end_dt = datetime.strptime(slot['end'], "%H:%M")
            dj = slot['dj']
            dj_events.setdefault(dj, []).append({
                "venue": venue,
                "start": start_dt,
                "end": end_dt,
                "day": slot.get('day', 'No day specified')
            })
    return dj_events

def generate_replacement_summary(schedules: Dict[str, List[Dict[str, str]]]) -> str:
    """
    Generate a plain text summary of replacements.
    
    Args:
        schedules (Dict[str, List[Dict[str, str]]]): Parsed schedule with replacements
        
    Returns:
        str: Plain text summary of replacements
    """
    replacement_text = ""
    for venue, slots in schedules.items():
        for slot in slots:
            if slot.get("autofilled"):
                replacement_text += f"{venue} {slot['start']}–{slot['end']} → {slot['dj']}\n"
    return replacement_text.strip()