"""
DJ Schedule Manager - Main Application

A Streamlit application for managing DJ schedules across multiple venues.
Handles schedule input, parsing, validation, and switching logic.
"""

import streamlit as st
import re
from collections import defaultdict
from datetime import datetime, timedelta

from utils.schedule_parser import parse_schedule, parse_dj_events, generate_replacement_summary
from utils.validation import (
    can_move_slot, 
    suggest_replacements,
    get_venue_area,
    get_area_travel_time
)

def get_replacement_suggestions(slot, dj_events, used_djs=None, cascade_chain=None):
    """Get ordered list of replacement suggestions for a slot with cascading logic."""
    if used_djs is None:
        used_djs = set()
    if cascade_chain is None:
        cascade_chain = []
    
    suggestions = []
    
    # Debug logging removed
    
    # 1. Try pool DJs first (they don't need cascading)
    for pool_dj in DJ_POOL:
        if pool_dj not in used_djs:
            ok, reason = can_move_slot(pool_dj, None, slot, dj_events)
            # st.write(f"DEBUG: Pool DJ {pool_dj} check - OK: {ok}, Reason: {reason}")  # DEBUG removed
            if ok:
                suggestions.append((pool_dj, "DJ Pool", None, None))
    
    # 2. Try free DJs (no cascading needed)
    for dj in dj_events.keys():
        if dj not in used_djs and dj not in DJ_POOL:
            ok, reason = can_move_slot(dj, None, slot, dj_events)
            # st.write(f"DEBUG: Free DJ {dj} check - OK: {ok}, Reason: {reason}")  # DEBUG removed
            if ok:
                suggestions.append((dj, "Free", None, None))
    
    # 3. Try cascade options (recursive)
    for dj in dj_events.keys():
        if dj not in used_djs and dj not in DJ_POOL:
            # Check if this DJ has any sets that could be moved
            for e in dj_events[dj]:
                if e['day'] == slot.get('day'):
                    temp_slot = {
                        'venue': e['venue'],
                        'start': e['start'],
                        'end': e['end'],
                        'day': e['day']
                    }
                    
                    # Look for someone who could take this DJ's set
                    for potential_replacer in dj_events.keys():
                        if (potential_replacer != dj and 
                            potential_replacer not in used_djs and
                            potential_replacer not in cascade_chain):  # Prevent infinite loops
                            
                            ok, reason = can_move_slot(potential_replacer, None, temp_slot, dj_events)
                            # st.write(f"DEBUG: Cascade check for {dj} -> {potential_replacer} - OK: {ok}, Reason: {reason}")  # DEBUG removed
                            if ok:
                                # Recursively check if we can fill the replacer's slot
                                cascade_chain.append(dj)
                                cascade_suggestions = get_replacement_suggestions(
                                    temp_slot, 
                                    dj_events, 
                                    used_djs.union({dj, potential_replacer}),
                                    cascade_chain
                                )
                                cascade_chain.pop()
                                
                                if cascade_suggestions:
                                    suggestions.append((dj, "Cascade", potential_replacer, cascade_chain.copy()))
    
    # st.write("DEBUG: Final suggestions list:", suggestions)  # DEBUG removed
    return suggestions

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
DEFAULT_SCHEDULE_TEXT = """Day and Night (Friday):
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

AP Lounge (Friday):
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

AP Lounge (Saturday):
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

Owl Lounge (Friday):
22:00-00:00 Yolo
03:00-04:30 Tezz
04:30-06:00 Caleb

Owl Lounge (Saturday):
22:00-00:00 Yolo
03:00-04:30 Tezz
04:30-06:00 Caleb"""

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
st.markdown("### Step 1: Input Schedule")
st.markdown("""
Enter the schedule in the following format:
```
Venue (Day):
HH:MM-HH:MM DJ
HH:MM-HH:MM DJ
...
```

Example:
```
AP Lounge (Friday):
22:00-00:00 Caleb
00:00-02:00 Tezz
02:00-04:00 Yolo
04:00-06:00 Caleb
```
""")

user_input = st.text_area(t['input_label'], height=300, value=st.session_state['last_schedule_text'])

# When the user submits, parse and save to session state
if st.button(t['submit']) and user_input.strip():
    with st.spinner("Parsing schedule..."):
        st.session_state['schedules'] = parse_schedule(user_input)
    st.session_state['last_schedule_text'] = user_input
    
    # Display parsed schedule in text format
    st.markdown("### Parsed Schedule")
    schedules = st.session_state['schedules']
    schedule_text = ""
    for venue, slots in schedules.items():
        schedule_text += f"\n{venue}:\n"
        # Group slots by day
        slots_by_day = defaultdict(list)
        for slot in slots:
            day = slot.get('day', 'No day specified')
            slots_by_day[day].append(slot)
        
        # Display slots by day
        for day, day_slots in slots_by_day.items():
            schedule_text += f"\n{day}:\n"
            for slot in sorted(day_slots, key=lambda x: x['start']):
                schedule_text += f"{slot['start']}–{slot['end']} {slot['dj']}\n"
    
    st.text_area("Schedule Summary", schedule_text.strip(), height=300)
    st.success("✅ Schedule parsed successfully!")

# If a schedule is stored in session state, display and enable sidebar
if st.session_state['schedules']:
    schedules = st.session_state['schedules']
    st.success("✅ Schedule parsed successfully!")
    
    # Display schedule cards and sidebar UI as before
    for venue, slots in schedules.items():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### 📍 {venue}")
        with col2:
            # Create copy text for this venue
            venue_text = f"{venue}:\n"
            slots_by_day = defaultdict(list)
            for slot in slots:
                day = slot.get('day', 'No day specified')
                slots_by_day[day].append(slot)
            for day, day_slots in slots_by_day.items():
                venue_text += f"\n{day}:\n"
                for slot in sorted(day_slots, key=lambda x: x['start']):
                    venue_text += f"{slot['start']}–{slot['end']} {slot['dj']}\n"
            
            if st.button("📋 Copy", key=f"copy_{venue}"):
                st.code(venue_text.strip())
                st.success("Copied!")
        
        slots_by_day = defaultdict(list)
        for slot in slots:
            day = slot.get('day', 'No day specified')
            slots_by_day[day].append(slot)
        for day, day_slots in slots_by_day.items():
            st.markdown(f"**{day}**")
            for slot in day_slots:
                # Different styling for autofilled slots
                if slot.get('autofilled'):
                    st.markdown(f"- {slot['start']}–{slot['end']} 🎧 {slot['dj']} (Auto-filled)")
                else:
                    st.markdown(f"- {slot['start']}–{slot['end']} 🎧 {slot['dj']}")
    
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
            # Example: 'Day and Night (Saturday) 23:30-00:30' or 'AP Lounge 10:00-11:00'
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

    # Day selection for targeted removal
    day_selection = st.sidebar.multiselect(t['select_day'], ["Friday", "Saturday"], default=["Friday"])
    remove_clicked = st.sidebar.button(t['remove_dj'])

    if remove_clicked:
        removed = []
        for venue, slots in schedules.items():
            for slot in slots.copy():
                if slot['dj'] == dj_to_remove and slot.get('day') in day_selection:
                    removed.append((venue, slot))
                    slots.remove(slot)
        if removed:
            # Get replacement suggestions for each removed slot
            replacement_ui = {}
            for venue, slot in removed:
                slot_key = f"{venue}_{slot['start']}_{slot['end']}"
                suggestions = get_replacement_suggestions({
                    'venue': venue,
                    'start': datetime.strptime(slot['start'], "%H:%M"),
                    'end': datetime.strptime(slot['end'], "%H:%M"),
                    'day': slot.get('day')
                }, dj_events)
                # Always track each slot, even if no suggestions
                replacement_ui[slot_key] = {
                    'slot': slot,
                    'suggestions': suggestions,
                    'selected': suggestions[0] if suggestions else None
                }

            # Display replacement UI in main area
            st.markdown(f"### {dj_to_remove} is unavailable")
            
            # Track selected replacements
            selected_replacements = {}

            # Move replacement selection to sidebar
            st.sidebar.markdown("### Select Replacements")
            for slot_key, data in replacement_ui.items():
                slot = data['slot']
                suggestions = data['suggestions']

                st.sidebar.markdown(f"**{slot['venue']} ({slot.get('day', 'No day')}) {slot['start']}–{slot['end']}**")
                if suggestions:
                    # Create dropdown options with cascade information
                    options = []
                    for dj, source_type, cascade_dj, cascade_chain in suggestions:
                        if cascade_chain and len(cascade_chain) > 1:
                            label = f"{dj} (via cascade: {' → '.join(cascade_chain)})"
                        elif cascade_dj:
                            label = f"{dj} (moved from {cascade_dj})"
                        elif source_type == "DJ Pool":
                            label = f"{dj} (from DJ Pool)"
                        else:
                            label = f"{dj} (Free)"
                        options.append((label, (dj, source_type, cascade_dj, cascade_chain)))

                    selected = st.sidebar.selectbox(
                        "Replacement",
                        options=options,
                        format_func=lambda x: x[0],
                        key=f"replace_{slot_key}"
                    )
                    selected_replacements[slot_key] = selected[1]
                else:
                    st.sidebar.markdown("❗ No available replacements for this slot.")

            # Add confirm/cancel buttons
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("✅ Confirm & Apply", key="confirm_replacements"):
                    # Apply the selected replacements
                    for slot_key, (dj, source_type, cascade_dj, cascade_chain) in selected_replacements.items():
                        venue, start, end = slot_key.split('_')
                        # Find the slot in the schedule
                        for slot in schedules[venue]:
                            if (slot['start'] == start and
                                slot['end'] == end):
                                slot['dj'] = dj
                                slot['autofilled'] = True

                                # Handle cascade if needed
                                if cascade_chain:
                                    # Apply the entire cascade chain
                                    for i in range(len(cascade_chain) - 1):
                                        current_dj = cascade_chain[i]
                                        next_dj = cascade_chain[i + 1]
                                        # Find and update the cascade DJ's slot
                                        for other_venue, other_slots in schedules.items():
                                            for other_slot in other_slots:
                                                if (other_slot['dj'] == current_dj):
                                                    other_slot['dj'] = next_dj
                                                    other_slot['autofilled'] = True

                    # Rebuild events
                    dj_events = parse_dj_events(schedules)
                    st.success("✅ Replacements applied successfully!")

                    # Generate and display summary
                    st.markdown("### Changes Summary")
                    summary = []
                    for slot_key, (dj, source_type, cascade_dj, cascade_chain) in selected_replacements.items():
                        venue, start, end = slot_key.split('_')
                        slot = next(s for s in removed if s[0] == venue and s[1]['start'] == start and s[1]['end'] == end)[1]
                        summary.append(format_slot_summary(slot, dj, source_type, cascade_dj, cascade_chain))

                    summary_text = "\n".join(summary)
                    st.code(summary_text)

            with col2:
                if st.button("❌ Cancel", key="cancel_replacements"):
                    # Restore the original slots
                    for venue, slot in removed:
                        schedules[venue].append(slot)
                    st.info("❌ Changes cancelled. Original schedule restored.")
                    # Rebuild events
                    dj_events = parse_dj_events(schedules)
        else:
            st.info(t['no_slots'])

    # --- Single Slot Removal ---
    st.sidebar.markdown("---")
    st.sidebar.header("🕳 특정 슬롯 빠지기 (Single Slot Removal)")

    dj_for_single_removal = st.sidebar.selectbox("DJ 선택 (1개 슬롯만 제거)", dj_list, key="single_remove_dj")
    single_slot_options = []

    if dj_for_single_removal in dj_events:
        for e in dj_events[dj_for_single_removal]:
            label = f"{e['day']} - {e['venue']} {e['start'].strftime('%H:%M')}–{e['end'].strftime('%H:%M')}"
            single_slot_options.append((label, e))

    if single_slot_options:
        selected_event = st.sidebar.selectbox(
            "슬롯 선택", single_slot_options, format_func=lambda x: x[0], key="single_slot_select"
        )[1]

        if st.sidebar.button("이 슬롯만 빠지기"):
            removed = False
            for venue, slots in schedules.items():
                for slot in slots.copy():
                    if (
                        slot['dj'] == dj_for_single_removal and
                        slot['start'] == selected_event['start'].strftime('%H:%M') and
                        slot['end'] == selected_event['end'].strftime('%H:%M')
                    ):
                        slots.remove(slot)
                        removed = True
                if removed:
                    st.sidebar.success(f"{dj_for_single_removal} removed from {selected_event['venue']} on {selected_event['start'].strftime('%H:%M')}–{selected_event['end'].strftime('%H:%M')}")
                else:
                    st.sidebar.warning("No matching slot found.")
else:
    st.info(t['please_paste'])

def format_slot_summary(slot, new_dj, source_type, cascade_dj=None, cascade_chain=None):
    """Format a slot change for the summary text."""
    venue = slot['venue']
    time = f"{slot['start']}–{slot['end']}"
    day = slot.get('day', '')
    
    if cascade_chain and len(cascade_chain) > 1:
        chain_str = " → ".join(cascade_chain)
        return f"{venue} ({day}) {time}: {new_dj} (via cascade: {chain_str})"
    elif cascade_dj:
        return f"{venue} ({day}) {time}: {new_dj} (moved from {cascade_dj})"
    elif source_type == "DJ Pool":
        return f"{venue} ({day}) {time}: {new_dj} (from DJ Pool)"
    else:
        return f"{venue} ({day}) {time}: {new_dj}"
    