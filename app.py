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
from utils.validation import (
    can_move_slot, 
    suggest_replacements,
    get_venue_area,
    get_area_travel_time
)

# Language strings
LANG = {
    'ko': {
        'title': '아 타임 개 꼬이네',
        'instructions': '### 📝 사용법\n\n1. 아래 기본 스케줄을 복사하세요.\n2. 복사한 내용을 위 스케줄 입력창에 붙여넣고 "스케줄 제출" 버튼을 누르세요.\n3. 좌측 사이드바에서 대타를 요청하거나 DJ가 빠지는 상황을 설정할 수 있습니다.\n4. 대타가 가능한 경우 가능한 DJ 리스트가 표시됩니다.\n\n스케줄 형식:\n```\n[요일] Venue Name:\nHH:MM-HH:MM DJ Name\n```\n\n요일 예시:\n- 월 (Monday)\n- 화 (Tuesday)\n- 수 (Wednesday)\n- 목 (Thursday)\n- 금 (Friday)\n- 토 (Saturday)\n- 일 (Sunday)\n- 주말 (Weekend)',
        'default_schedule': '#### 📋 기본 스케줄',
        'copy_schedule': '📄 스케줄 복사',
        'input_label': '오늘의 스케줄을 여기에 붙여넣으세요:',
        'submit': '스케줄 제출',
        'switch_header': '대타 대타',
        'select_dj': 'DJ 선택',
        'current_slot': '현재 슬롯',
        'desired_slot': '원하는 슬롯',
        'check_switch': '대타 가능한지 확인',
        'switch_possible': '✅ 대타 가능!',
        'other_djs': '이 슬롯에 가능한 다른 DJ들:',
        'cannot_switch': '❌ 대타 불가:',
        'remove_header': '아 왜 빠져서 우리 고생시키는데',
        'select_day': '요일 선택',
        'remove_dj': '빠지겠단다 ㅠ_ㅠ',
        'no_slots': '이 요일에 제거할 슬롯이 없습니다.',
        'please_paste': '스케줄을 붙여넣고 제출 버튼을 클릭하세요.'
    },
    'en': {
        'title': 'DJ Schedule Manager',
        'instructions': '### 📝 Instructions\nPaste your schedule below using the following format:\n```\n[Day] Venue Name:\nHH:MM-HH:MM DJ Name\n```\n\nYou can use Korean day indicators:\n- 월 (Monday)\n- 화 (Tuesday)\n- 수 (Wednesday)\n- 목 (Thursday)\n- 금 (Friday)\n- 토 (Saturday)\n- 일 (Sunday)\n- 주말 (Weekend)',
        'default_schedule': '#### 📋 Default Schedule',
        'copy_schedule': '📄 Copy schedule',
        'input_label': 'Paste today\'s schedule here:',
        'submit': 'Submit Schedule',
        'switch_header': 'Switch Slots',
        'select_dj': 'Select DJ',
        'current_slot': 'Current Slot',
        'desired_slot': 'Desired Slot',
        'check_switch': 'Check Switch',
        'switch_possible': '✅ Switch possible!',
        'other_djs': 'Other DJs available for this slot:',
        'cannot_switch': '❌ Cannot switch:',
        'remove_header': 'Remove DJ for Day',
        'select_day': 'Select Day',
        'remove_dj': 'Remove DJ',
        'no_slots': 'No slots to remove for this day.',
        'please_paste': 'Please paste a schedule and click Submit Schedule.'
    }
}

# Persist parsed schedule and last submitted text across reruns
if 'schedules' not in st.session_state:
    st.session_state['schedules'] = None
if 'last_schedule_text' not in st.session_state:
    st.session_state['last_schedule_text'] = ''
if 'language' not in st.session_state:
    st.session_state['language'] = 'ko'

# Pool of DJs who are available but not currently scheduled
DJ_POOL = ["Xiid"]

# Full default schedule for preview/copy
DEFAULT_SCHEDULE_TEXT = """

Day and Night (Friday):
22:00-23:30 Illi
23:30-00:45 Caleb
00:45-02:00 Yolo
02:00-03:15 Giri
03:15-04:30 Ellia
04:30-06:00 Big ma

Code Lounge (Friday):
22:00-00:00 Rude
00:00-01:00 Illi
01:00-02:00 Freekey
02:00-03:00 Caleb
03:00-04:00 Emess
04:00-05:00 Yolo
05:00-06:00 AP
06:00-07:00 Rude

Stay Lounge (Friday):
22:00-23:00 Anemic
23:00-00:00 Drako
00:00-01:00 AP
01:00-02:00 Tezz
02:00-03:00 Emess
03:00-04:00 Caleb
04:00-05:00 Pluma

Day and Night (Saturday):
22:00-23:30 Illi
23:30-00:45 Caleb
00:45-02:00 Yolo
02:00-03:15 Drako
03:15-04:30 Giri
04:30-05:45 Ellia
05:45-07:00 Big ma

Code Lounge (Saturday):
22:00-00:00 Rude
00:00-01:00 Tezz
01:00-02:00 Freekey
02:00-03:00 Caleb
03:00-04:00 Emess
04:00-05:00 Yolo
05:00-06:00 AP
06:00-07:00 Rude

Stay Lounge (Saturday):
22:00-23:00 Anemic
23:00-00:00 Drako
00:00-01:00 AP
01:00-02:00 Tezz
02:00-03:00 Emess
03:00-04:00 Caleb
04:00-05:00 Pluma

Pose Lounge (Friday):
10:30-00:00 Jamie

Badass (Friday):
00:00-01:00 Jamie

Dive (Friday):
01:30-03:00 Jamie

Dive (Saturday):
00:00-01:30 Jamie

Pose Lounge (Saturday):
01:30-03:00 Jamie

Badass (Saturday):
03:00-04:00 Jamie
"""

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
            current_day = day_label.strip().lower().capitalize()

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

# Language selector in sidebar
lang = st.sidebar.radio("Language / 언어", ["한국어", "English"], index=0 if st.session_state['language'] == 'ko' else 1)
st.session_state['language'] = 'ko' if lang == "한국어" else 'en'
t = LANG[st.session_state['language']]

st.title(t['title'])

st.markdown(t['instructions'])

# Move clipboard copy button here between instructions and schedule heading
import streamlit.components.v1 as components
components.html(f"""
    <script>
    function copySchedule() {{
        navigator.clipboard.writeText(`{DEFAULT_SCHEDULE_TEXT}`);
        const msg = document.getElementById("copy-confirm");
        msg.style.display = "block";
        setTimeout(() => msg.style.display = "none", 2000);
    }}
    </script>
    <button onclick="copySchedule()" style="
        background-color: #FFD700;
        color: black;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 16px;
        border-radius: 6px;
        border: none;
        cursor: pointer;
        margin-bottom: 10px;
    ">📋 기본 스케줄 복사</button>
    <div id="copy-confirm" style="margin-bottom: 20px; color: green; display: none;">✅ 복사 완료!</div>
""", height=80)

st.markdown(t['default_schedule'])
st.code(DEFAULT_SCHEDULE_TEXT, language="markdown")

# Step 1: Input area
user_input = st.text_area(t['input_label'], height=300, value=st.session_state['last_schedule_text'])

# When the user submits, parse and save to session state
if st.button(t['submit']) and user_input.strip():
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
    st.sidebar.header(t['switch_header'])
    
    # Include both scheduled DJs and DJ Pool applicants
    dj_list = sorted(set(dj_events.keys()).union(DJ_POOL))
    selected_dj = st.sidebar.selectbox(t['select_dj'], dj_list)
    
    # Build source slot options
    source_options = []
    if selected_dj in dj_events:  # Only show slots for scheduled DJs
        for e in dj_events[selected_dj]:
            day_str = f" ({e['day']})" if e.get('day') else ""
            source_options.append(f"{e['venue']}{day_str} {e['start'].strftime('%H:%M')}-{e['end'].strftime('%H:%M')}")
    else:  # For DJ Pool applicants, show a placeholder
        source_options = ["No scheduled slots"]
    
    selected_source = st.sidebar.selectbox(t['current_slot'], source_options)
    
    # Build target slot options from all empty slots
    target_options = []
    # Flatten all possible slots
    for venue, slots in schedules.items():
        for slot in slots:
            day_str = f" ({slot['day']})" if slot.get('day') else ""
            target_options.append(f"{venue}{day_str} {slot['start']}-{slot['end']}")
    selected_target = st.sidebar.selectbox(t['desired_slot'], target_options)

    if st.sidebar.button(t['check_switch']):
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
            st.sidebar.success(t['switch_possible'])

            # Suggest other DJs who could also fill the target slot
            suggestions = suggest_replacements(target_event, dj_events)
            suggestions = [dj for dj in suggestions if dj != selected_dj]
            if suggestions:
                st.sidebar.info(t['other_djs'])
                for dj in suggestions:
                    # Get the DJ's current venue and area
                    current_venue = next((e['venue'] for e in dj_events[dj] if e['start'] <= target_event['start'] <= e['end']), None)
                    current_area = get_venue_area(current_venue) if current_venue else "No current set"
                    target_area = get_venue_area(target_event['venue'])
                    
                    # Show DJ with their current location and travel info
                    if current_venue:
                        travel_time = get_area_travel_time(current_venue, target_event['venue'])
                        st.sidebar.write(f"- {dj} (Currently at {current_venue} in {current_area} → {target_event['venue']} in {target_area}, {travel_time}min travel)")
                    else:
                        st.sidebar.write(f"- {dj} (Free → {target_event['venue']} in {target_area})")
        else:
            st.sidebar.error(f"{t['cannot_switch']} {reason}")
            # Suggest replacements
            suggestions = suggest_replacements(target_event, dj_events)
            if suggestions:
                st.sidebar.info(t['other_djs'])
                for dj in suggestions:
                    st.sidebar.write(f"- {dj}")
            else:
                st.sidebar.write("No available replacements found.")

    # --- Bulk Remove DJ for a Day ---
    st.sidebar.markdown("---")
    st.sidebar.header(t['remove_header'])
    dj_to_remove = st.sidebar.selectbox(t['select_dj'], list(dj_events.keys()))
    day_options = sorted({slot['day'] for slots in schedules.values() for slot in slots if slot.get('day')})
    day_to_remove = st.sidebar.selectbox(t['select_day'], day_options)
    remove_clicked = st.sidebar.button(t['remove_dj'])

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
            st.sidebar.info(t['no_slots'])
else:
    st.info(t['please_paste'])