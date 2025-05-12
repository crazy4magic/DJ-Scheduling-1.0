"""
Global constants for the DJ Schedule Manager application.
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

# UI Constants
UI = {
    'PAGE_TITLE': "DJ Schedule Manager",
    'PAGE_ICON': "🎧",
    'SLOT_BG_COLOR': "#ffd700",
    'SLOT_TEXT_COLOR': "#000000",
    'SLOT_BORDER_COLOR': "#000000",
    'SLOT_FONT_SIZE': "16px",
    'SLOT_PADDING': "10px",
    'SLOT_BORDER_RADIUS': "6px",
    'SLOT_BORDER_WIDTH': "2px",
    'SLOT_BOX_SHADOW': "2px 2px 4px rgba(0,0,0,0.1)"
}

# Time Constants
TIME = {
    'DEFAULT_TRAVEL_TIME': 15,  # minutes
    'MIN_SLOT_DURATION': 30,    # minutes
    'MAX_SLOT_DURATION': 180    # minutes
}

# Validation Constants
VALIDATION = {
    'MAX_VENUES': 10,
    'MAX_DJS': 50,
    'MAX_SLOTS_PER_DAY': 24
} 