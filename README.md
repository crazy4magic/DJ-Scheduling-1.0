import streamlit as st

@st.cache_data
def parse_schedule(text):
    import re
    from collections import defaultdict
    schedules = defaultdict(list)
    current_venue = None
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line and "-" not in line:
            current_venue = line.replace(":", "").strip()
        elif current_venue and re.match(r"\d{1,2}:\d{2}.*", line):
            match = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})\s+(.*)", line)
            if match:
                start, end, dj = match.groups()
                schedules[current_venue].append({"start": start, "end": end, "dj": dj.strip()})
    return schedules

def render_slot_card(start, end, dj):
    html = f"""
    <div style='padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin: 5px 0;'>
        <strong>{start} – {end}</strong> | {dj}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ... (other existing code)

if st.button("Submit Schedule") and user_input.strip():
    schedules = parse_schedule(user_input)

# ... (other existing code)

for venue, slots in schedules.items():
    st.subheader(venue)
    for slot in slots:
        render_slot_card(slot['start'], slot['end'], slot['dj'])

# ... (other existing code)

with st.sidebar.expander("🔄 Request a Switch", expanded=True):
    st.header("Request a Switch")
    # ... (all the existing sidebar switch-request UI code, properly indented)
    # For example:
    # selected_dj = st.selectbox("Select DJ", dj_list)
    # current_slot = st.selectbox("Current Slot", current_slots)
    # desired_slot = st.selectbox("Desired Slot", desired_slots)
    # if st.button("Check Switch"):
    #     ...
    
# DJ Schedule Manager

A Streamlit-based application for managing DJ schedules across multiple venues. This tool helps DJ crews and event organizers manage schedules, detect conflicts, and handle DJ switches efficiently.

## 🌟 Features

- **Schedule Management**
  - Simple text-based schedule input
  - Support for Korean day indicators
  - Structured display by venue and day
  - Clean, modern UI with yellow/black contrast

- **Smart Switching**
  - Request DJ slot switches
  - Automatic conflict detection
  - Travel time consideration
  - Replacement suggestions

- **Bulk Operations**
  - Remove DJ slots for specific days
  - Get replacement suggestions
  - View affected venues

## 🚀 Quick Start

1. **Installation**
   ```bash
   # Clone the repository
   git clone [repository-url]
   cd DJ-Scheduling

   # Create and activate virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   streamlit run app.py
   ```

## 📝 Usage Guide

### Input Format
```
[요일] Venue Name:
HH:MM-HH:MM DJ Name
```

Example:
```
금요일 Stay Lounge:
10:00-11:00 Anemic
11:00-12:00 Drako

토요일 Day and Night:
10:00-11:30 Illi
11:30-12:45 Caleb
```

### Korean Day Indicators
- 월 (Monday)
- 화 (Tuesday)
- 수 (Wednesday)
- 목 (Thursday)
- 금 (Friday)
- 토 (Saturday)
- 일 (Sunday)
- 주말 (Weekend)

### Features in Detail

1. **Schedule Input**
   - Paste your schedule in the text area
   - Click "Submit Schedule" to parse
   - View the structured schedule display

2. **Switch Requests**
   - Select a DJ from the dropdown
   - Choose their current slot
   - Select desired slot
   - Check if the switch is possible
   - View alternative suggestions

3. **Bulk Removal**
   - Select a DJ to remove
   - Choose a specific day
   - Remove all their slots for that day
   - Get replacement suggestions

## 🏗️ Project Structure

```
DJ Schedule Manager/
├── app.py              # Main application logic
├── utils/             # Utility functions
│   ├── schedule_parser.py  # Schedule parsing logic
│   ├── validation.py      # Validation functions
│   └── folder_enforcer.py # Folder structure validation
├── config/            # Configuration files
│   └── travel_times.py    # Travel time configurations
├── shared/            # Shared components and constants
│   ├── constants.py       # Global constants
│   └── types.py          # Type definitions
├── tests/             # Test files
├── requirements.txt   # Project dependencies
└── README.md         # Project documentation
```

## 🛠️ Development

### Prerequisites
- Python 3.8+
- pip
- virtualenv (recommended)

### Dependencies
- streamlit==1.32.0
- pandas==2.2.0
- python-dateutil==2.8.2

### Coding Standards
- Follow PEP 8 style guide
- Use type hints
- Document all functions
- Write unit tests
- Follow the project structure guidelines

### Testing
```bash
# Run tests
python -m pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Streamlit team for the amazing framework
- All contributors and users of the application
 