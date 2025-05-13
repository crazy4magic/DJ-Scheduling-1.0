"""
DJ Schedule Manager - Main Application

A Streamlit application for managing DJ schedules across multiple venues.
Handles schedule input, parsing, validation, and switching logic.
"""

import streamlit as st
import re
from collections import defaultdict
from datetime import datetime, timedelta

from utils.schedule_parser import parse_schedule, parse_dj_events
from utils.validation import can_move_slot, suggest_replacements

# Persist parsed schedule and last submitted text across reruns
if 'schedules' not in st.session_state:
    st.session_state['schedules'] = None
if 'last_schedule_text' not in st.session_state:
    st.session_state['last_schedule_text'] = ''

# Korean day mapping
KOREAN_DAYS = {
    '월': 'Monday',
    '화': 'Tuesday',
    '수': 'Wednesday',
    '목': 'Thursday',
    '금': 'Friday',
    '토': 'Saturday',
    '일': 'Sunday',
    '주말': 'Weekend'
}

def clean_text(text):
    """Remove emojis and clean text."""
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

def parse_schedule(schedule_text):
    """Parse the schedule text into a structured format."""
    # Split into lines and remove empty lines
    lines = [line.strip() for line in schedule_text.split('\n') if line.strip()]
    
    # Initialize schedule dictionary
    schedules = defaultdict(list)
    current_venue = None
    current_day = None
    
    for line in lines:
        # Check if line contains a day indicator and venue
        match_header = re.match(r'^(.+?)\s*\((.*?)\)\s*:', line)
        if match_header:
            current_venue, day_label = match_header.groups()
            current_venue = current_venue.strip()
            current_day = day_label.strip().capitalize()

            # Translate Korean day if applicable
            for kr_day, en_day in KOREAN_DAYS.items():
                if current_day.startswith(kr_day):
                    current_day = en_day
                    break
            continue
        
        # Parse time slot with DJ name
        if current_venue and '-' in line:
            match = re.match(r'(\d{1,2}:\d{2})-(\d{1,2}:\d{2})\s+(.*)', line)
            if match:
                start, end, dj = match.groups()
                schedules[current_venue].append({
                    'start': start,
                    'end': end,
                    'dj': dj.strip().title(),
                    'day': current_day
                })
    
    return dict(schedules)

st.set_page_config(
    page_title="아 타임 개 꼬이네",
    page_icon="🎧",
    layout="wide"
)

st.title("아 타임 개 꼬이네")

# Step 1: Input area with example format
example_schedule = """금요일 Stay Lounge:
10:00-11:00 Anemic
11:00-12:00 Drako

토요일 Day and Night:
10:00-11:30 Illi
11:30-12:45 Caleb"""

st.markdown("""
### 📝 Instructions
Paste your schedule below using the following format:
```
[요일] Venue Name:
HH:MM-HH:MM DJ Name
```

You can use Korean day indicators:
- 월 (Monday)
- 화 (Tuesday)
- 수 (Wednesday)
- 목 (Thursday)
- 금 (Friday)
- 토 (Saturday)
- 일 (Sunday)
- 주말 (Weekend)
""")

st.text_area("Example format:", example_schedule, height=150, disabled=True)

# Step 1: Input area
user_input = st.text_area("Paste today's schedule here:", height=300, value=st.session_state['last_schedule_text'])

# When the user submits, parse and save to session state
if st.button("Submit Schedule") and user_input.strip():
    st.session_state['schedules'] = parse_schedule(user_input)
    st.session_state['last_schedule_text'] = user_input

# If a schedule is stored in session state, display and enable sidebar
if st.session_state['schedules']:
    schedules = st.session_state['schedules']
    st.success("✅ Schedule parsed successfully!")
    
    # Display schedule cards and sidebar UI as before
    for venue, slots in schedules.items():
        st.markdown(f"### 📍 {venue}")
        slots_by_day = defaultdict(list)
        for slot in slots:
            day = slot.get('day', 'No day specified')
            slots_by_day[day].append(slot)
        for day, day_slots in slots_by_day.items():
            st.markdown(f"**{day}**")
            for slot in day_slots:
                st.markdown(f"""
                <div style='padding: 10px; background-color: #ffd700; color: #000000; border: 2px solid #000000; border-radius: 6px; margin: 5px 0; font-weight: bold; font-size: 16px; box-shadow: 2px 2px 4px rgba(0,0,0,0.1);'>
                    🕒 {slot['start']} – {slot['end']} | 🎧 {slot['dj']}
                </div>
                """, unsafe_allow_html=True)
    
    # Sidebar UI for switch requests
    dj_events = parse_dj_events(schedules)
    st.sidebar.header("대타 대타")
    dj_list = list(dj_events.keys())
    selected_dj = st.sidebar.selectbox("Select DJ", dj_list)
    
    # Build source slot options
    source_options = []
    for e in dj_events[selected_dj]:
        day_str = f" ({e['day']})" if e.get('day') else ""
        source_options.append(f"{e['venue']}{day_str} {e['start'].strftime('%H:%M')}-{e['end'].strftime('%H:%M')}")
    selected_source = st.sidebar.selectbox("Current Slot", source_options)
    
    # Build target slot options from all empty slots
    target_options = []
    # Flatten all possible slots
    for venue, slots in schedules.items():
        for slot in slots:
            day_str = f" ({slot['day']})" if slot.get('day') else ""
            target_options.append(f"{venue}{day_str} {slot['start']}-{slot['end']}")
    selected_target = st.sidebar.selectbox("Desired Slot", target_options)

    if st.sidebar.button("Check Switch"):
        # Parse selected source and target into dict structures
        def parse_choice(choice_str):
            # Regex to extract: venue (optional day) start-end
            # Example: 'Day and Night (Saturday) 23:30-00:30' or 'Stay Lounge 10:00-11:00'
            match = re.match(r"^(.*?)(?: \((.*?)\))? (\d{1,2}:\d{2})-(\d{1,2}:\d{2})$", choice_str)
            if not match:
                raise ValueError(f"Could not parse slot string: {choice_str}")
            venue, day, start_str, end_str = match.groups()
            return {
                "venue": venue.strip(),
                "start": datetime.strptime(start_str, "%H:%M"),
                "end": datetime.strptime(end_str, "%H:%M"),
                "day": day
            }
        
        source_event = parse_choice(selected_source)
        target_event = parse_choice(selected_target)

        ok, reason = can_move_slot(selected_dj, source_event, target_event, dj_events)
        if ok:
            st.sidebar.success("✅ Switch possible!")
        else:
            st.sidebar.error(f"❌ Cannot switch: {reason}")
            # Suggest replacements
            suggestions = suggest_replacements(target_event, dj_events)
            if suggestions:
                st.sidebar.info("Available DJs for this slot:")
                for dj in suggestions:
                    st.sidebar.write(f"- {dj}")
            else:
                st.sidebar.write("No available replacements found.")

    # --- Bulk Remove DJ for a Day ---
    st.sidebar.markdown("---")
    st.sidebar.header("아 왜 빠져서 우리 고생시키는데")
    dj_to_remove = st.sidebar.selectbox("Select DJ to remove", list(dj_events.keys()))
    day_options = sorted({slot['day'] for slots in schedules.values() for slot in slots if slot.get('day')})
    day_to_remove = st.sidebar.selectbox("Select Day", day_options)
    remove_clicked = st.sidebar.button("Remove DJ for Day")

    if remove_clicked:
        removed = []
        for venue, slots in schedules.items():
            for slot in slots.copy():
                if slot['dj'] == dj_to_remove and slot.get('day') == day_to_remove:
                    removed.append((venue, slot))
                    slots.remove(slot)
        if removed:
            st.sidebar.success(f"Removed {len(removed)} slots for {dj_to_remove} on {day_to_remove}:")
            # Rebuild events for fresh suggestions
            dj_events = parse_dj_events(schedules)
            # Suggest replacements
            for venue, slot in removed:
                st.sidebar.write(f"- {slot['start']}–{slot['end']} @ {venue}")
                # Convert time strings to datetime objects
                target_slot = {
                    "venue": venue,
                    "start": datetime.strptime(slot['start'], "%H:%M"),
                    "end": datetime.strptime(slot['end'], "%H:%M"),
                    "day": slot.get('day')
                }
                sugg = suggest_replacements(target_slot, dj_events)
                if sugg:
                    st.sidebar.write("  • Replacements:", ", ".join(sugg))
                else:
                    st.sidebar.write("  • No replacements found.")
        else:
            st.sidebar.info(f"No slots for {dj_to_remove} on {day_to_remove} to remove.")
else:
    st.info("Please paste a schedule and click Submit Schedule.")