import json
import os
import re
import logging

logger = logging.getLogger(__name__)

# File to store dynamic filters
FILTERS_FILE = "user_filters.json"

def load_filters():
    """Load user-defined filters from the JSON file."""
    if not os.path.exists(FILTERS_FILE):
        # Create default empty filters file
        save_filters([])
        return []
    
    try:
        with open(FILTERS_FILE, 'r') as f:
            filters = json.load(f)
            # Convert to tuple format for compatibility with existing code
            return [(item['pattern'], item['replacement']) for item in filters]
    except Exception as e:
        logger.error(f"Error loading filters: {e}")
        return []

def save_filters(filters_list):
    """Save filters to the JSON file.
    
    Args:
        filters_list: List of (pattern, replacement) tuples
    """
    # Convert to dict format for better JSON serialization
    filters_data = [{'pattern': pattern, 'replacement': replacement} 
                   for pattern, replacement in filters_list]
    
    try:
        with open(FILTERS_FILE, 'w') as f:
            json.dump(filters_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving filters: {e}")
        return False

def add_filter(pattern, replacement):
    """Add a new filter pattern and replacement."""
    filters = load_filters()
    
    # Check if pattern already exists
    for i, (existing_pattern, _) in enumerate(filters):
        if existing_pattern == pattern:
            # Update existing filter
            filters[i] = (pattern, replacement)
            return save_filters(filters)
    
    # Add new filter
    filters.append((pattern, replacement))
    return save_filters(filters)

def remove_filter(pattern):
    """Remove a filter by its pattern."""
    filters = load_filters()
    initial_count = len(filters)
    
    # Remove all matching patterns
    filters = [(p, r) for p, r in filters if p != pattern]
    
    if len(filters) < initial_count:
        return save_filters(filters)
    return False

def list_filters():
    """Return a formatted list of all filters."""
    filters = load_filters()
    
    if not filters:
        return "No custom filters defined."
    
    result = "Current text filters:\n\n"
    for i, (pattern, replacement) in enumerate(filters, 1):
        result += f"{i}. Pattern: `{pattern}`\n   Replacement: `{replacement}`\n\n"
    
    return result

def test_filter(text, pattern):
    """Test a regex pattern on a sample text."""
    try:
        matches = re.findall(pattern, text)
        if not matches:
            return f"No matches found in the text."
        
        return f"Found {len(matches)} matches: {', '.join(repr(m) for m in matches)}"
    except Exception as e:
        return f"Error testing pattern: {e}"

def get_all_filters():
    """Get all filters (dynamic and static)."""
    from config import TEXT_FILTERS
    
    # Combine static filters from config with dynamic user filters
    dynamic_filters = load_filters()
    
    # Log all filters for debugging
    logger.info(f"Static filters from config: {TEXT_FILTERS}")
    logger.info(f"Dynamic filters from user_filters.json: {dynamic_filters}")
    
    all_filters = TEXT_FILTERS + dynamic_filters
    logger.info(f"Total filters: {len(all_filters)}")
    
    return all_filters