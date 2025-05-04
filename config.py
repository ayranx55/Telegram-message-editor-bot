import os

# Telegram Bot Token (get from BotFather)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Channel ID to monitor (including the @ symbol if it's a public channel)
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# Set this to True if the bot should be added as an admin to the channel
# Set to False if the bot is the owner of the channel
IS_ADMIN = False  # Try with False to see if it helps with permissions

# Source timezone - UTC+14:00
SOURCE_TIMEZONE = "Etc/GMT-14"  # Note: pytz uses opposite sign convention

# Target timezone - GMT+5:30 (IST)
TARGET_TIMEZONE = "Asia/Kolkata"  # Indian Standard Time (GMT+5:30)

# Text filters: pairs of (pattern, replacement)
TEXT_FILTERS = [
    # Example filters (customize as needed)
    (r"(?i)\b(urgent)\b", "URGENT"),  # Convert "urgent" to "URGENT"
    (r"(?i)\b(important)\b", "IMPORTANT"),  # Convert "important" to "IMPORTANT"
    (r"@Gazew_07", "@BILLIONAIREBOSS101"),  # Specific username replacement
    (r"🚧", "🚀"),  # Replace construction emoji with rocket emoji (no word boundary for emojis)
    # Add more patterns here
]

# Time pattern regex to match UTC+14:00 timestamps
# This pattern is more aggressive in finding timestamp-like patterns
# Customize this pattern based on the specific timestamp format in your channel
TIME_PATTERN = r"(\d{1,2}[/.:-]\d{1,2}[/.:-]\d{2,4}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?)"
# Alternative timestamp patterns to try if none of the standard formats match
ADDITIONAL_TIME_PATTERNS = [
    r"(\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?)",  # Just time like 12:30 PM
    r"(\d{1,2}[/.:-]\d{1,2}[/.:-]\d{2,4})"  # Just date like 01/15/2023
]

# Message types to process (set to True to enable processing)
PROCESS_TEXT = True
PROCESS_CAPTIONS = True  # For media messages with captions

# If set to True, the bot will reply with the corrected text
# when it cannot edit the message directly (useful as a fallback)
REPLY_ON_EDIT_FAILURE = True
