import re
import logging
import pytz
from datetime import datetime
from config import SOURCE_TIMEZONE, TARGET_TIMEZONE, TIME_PATTERN, ADDITIONAL_TIME_PATTERNS
from filter_manager import get_all_filters

logger = logging.getLogger(__name__)

def apply_text_filters(text):
    """Apply text filters to the message text"""
    if not text:
        return text
    
    # Get all filters (both static and dynamic)
    all_filters = get_all_filters()
    logger.info(f"Got {len(all_filters)} filters to apply")
    
    modified_text = text
    logger.info(f"Original text: {text}")
    
    for pattern, replacement in all_filters:
        logger.info(f"Applying filter: pattern='{pattern}', replacement='{replacement}'")
        try:
            new_text = re.sub(pattern, replacement, modified_text)
            # Only log if a change was made
            if new_text != modified_text:
                logger.info(f"Text changed: '{modified_text}' -> '{new_text}'")
            modified_text = new_text
        except Exception as e:
            logger.error(f"Error applying filter pattern '{pattern}': {e}")
    
    if modified_text != text:
        logger.info(f"Final modified text: {modified_text}")
    
    return modified_text

def convert_timezone(text):
    """
    Find timestamps in the text and convert them from SOURCE_TIMEZONE to TARGET_TIMEZONE
    """
    if not text:
        return text
    
    logger.info(f"Attempting to convert timestamps in: {text}")
    logger.info(f"Source timezone: {SOURCE_TIMEZONE}, Target timezone: {TARGET_TIMEZONE}")
    
    # Common timestamp formats to try parsing
    formats = [
        # Just time formats (for timestamps like 10:43:00)
        "%H:%M:%S",
        "%H:%M",
        "%I:%M:%S %p",
        "%I:%M %p",
        # Full date+time formats
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%y %H:%M",
        "%d/%m/%y %H:%M:%S",
        "%d-%m-%y %H:%M",
        "%d-%m-%y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m-%d-%Y %H:%M",
        "%m-%d-%Y %H:%M:%S",
        # With AM/PM
        "%d/%m/%Y %I:%M %p",
        "%d/%m/%Y %I:%M:%S %p",
        "%d-%m-%Y %I:%M %p",
        "%d-%m-%Y %I:%M:%S %p",
        "%Y/%m/%d %I:%M %p",
        "%Y/%m/%d %I:%M:%S %p",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d %I:%M:%S %p",
        "%d/%m/%y %I:%M %p",
        "%d/%m/%y %I:%M:%S %p",
        "%d-%m-%y %I:%M %p",
        "%d-%m-%y %I:%M:%S %p",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y %I:%M:%S %p",
        "%m-%d-%Y %I:%M %p",
        "%m-%d-%Y %I:%M:%S %p",
    ]
    
    # Get timezone objects
    source_tz = pytz.timezone(SOURCE_TIMEZONE)
    target_tz = pytz.timezone(TARGET_TIMEZONE)
    
    # Find all timestamp matches in text
    modified_text = text
    all_timestamps = []
    
    # Try with main time pattern
    try:
        main_timestamps = list(re.finditer(TIME_PATTERN, text))
        logger.info(f"Found {len(main_timestamps)} timestamp pattern matches using main pattern")
        all_timestamps.extend(main_timestamps)
    except Exception as e:
        logger.error(f"Error finding timestamps with main pattern: {e}")
    
    # Try with additional patterns if no matches found
    if len(all_timestamps) == 0:
        for pattern_idx, pattern in enumerate(ADDITIONAL_TIME_PATTERNS):
            try:
                add_timestamps = list(re.finditer(pattern, text))
                logger.info(f"Found {len(add_timestamps)} timestamp matches using additional pattern {pattern_idx+1}")
                all_timestamps.extend(add_timestamps)
            except Exception as e:
                logger.error(f"Error finding timestamps with additional pattern {pattern_idx+1}: {e}")
    
    logger.info(f"Total timestamps found: {len(all_timestamps)}")
    
    # Process each timestamp
    for match in all_timestamps:
        timestamp_str = match.group(0)
        parsed_time = None
        matched_format = None  # Store the matching format
        
        # Try parsing with different formats
        for fmt in formats:
            try:
                parsed_time = datetime.strptime(timestamp_str, fmt)
                matched_format = fmt  # Save the format that worked
                # Successfully parsed
                break
            except ValueError:
                continue
        
        if parsed_time and matched_format:
            try:
                # If it's just a time format without a date, use today's date
                if matched_format in ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"]:
                    # Get current date in source timezone
                    today = datetime.now(source_tz).date()
                    # Combine with the parsed time
                    combined_dt = datetime.combine(today, parsed_time.time())
                    # Localize to source timezone
                    source_time = source_tz.localize(combined_dt)
                else:
                    # For timestamps with date and time
                    source_time = source_tz.localize(parsed_time)
                
                # Convert to target timezone
                target_time = source_time.astimezone(target_tz)
                
                # Format the new timestamp using the same format that matched
                new_timestamp = target_time.strftime(matched_format)
                
                # Replace the timestamp in the text
                modified_text = modified_text.replace(timestamp_str, new_timestamp)
                logger.info(f"Converted timestamp: '{timestamp_str}' -> '{new_timestamp}'")
            except Exception as e:
                logger.error(f"Error converting timestamp {timestamp_str}: {e}")
        else:
            logger.warning(f"Could not parse timestamp: '{timestamp_str}'")
    
    return modified_text

def process_message_text(text):
    """
    Process a message text by applying text filters and timezone conversion
    """
    if not text:
        return text
    
    # First apply text filters
    filtered_text = apply_text_filters(text)
    
    # Then convert timestamps
    processed_text = convert_timezone(filtered_text)
    
    return processed_text
