import logging
import asyncio
import re
import os
import json
from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from config import BOT_TOKEN, CHANNEL_ID, IS_ADMIN, PROCESS_TEXT, PROCESS_CAPTIONS, REPLY_ON_EDIT_FAILURE
from utils import process_message_text
from filter_manager import add_filter, remove_filter, list_filters, test_filter

# File to store channels list
CHANNELS_FILE = "monitored_channels.json"

def load_channels():
    """Load the list of channels to monitor from a JSON file."""
    if not os.path.exists(CHANNELS_FILE):
        # Create empty list with default channel from env var
        channels = []
        if CHANNEL_ID:
            channels.append(CHANNEL_ID)
        save_channels(channels)
        return channels
    
    try:
        with open(CHANNELS_FILE, 'r') as f:
            channels = json.load(f)
            return channels
    except Exception as e:
        logger.error(f"Error loading channels: {e}")
        return [CHANNEL_ID] if CHANNEL_ID else []

def save_channels(channels):
    """Save the list of channels to monitor to a JSON file."""
    try:
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(channels, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving channels: {e}")
        return False

def add_channel(channel_id):
    """Add a channel to the list of monitored channels."""
    channels = load_channels()
    
    # Normalize channel ID format
    if channel_id.startswith('@'):
        # Keep @ for usernames
        normalized_id = channel_id
    else:
        # Ensure numeric IDs are strings without @
        normalized_id = str(channel_id).replace('@', '')
    
    # Check if channel already exists
    if normalized_id in channels:
        return False, "Channel already in monitoring list."
    
    channels.append(normalized_id)
    if save_channels(channels):
        return True, f"Channel {normalized_id} added to monitoring list."
    else:
        return False, "Failed to save channel."

def remove_channel(channel_id):
    """Remove a channel from the list of monitored channels."""
    channels = load_channels()
    initial_count = len(channels)
    
    # Normalize channel ID for comparison
    normalized_id = str(channel_id).replace('@', '') if not channel_id.startswith('@') else channel_id
    
    # Check both formats (@username and username) for removal
    if normalized_id in channels:
        channels.remove(normalized_id)
    elif f"@{normalized_id}" in channels:
        channels.remove(f"@{normalized_id}")
    elif normalized_id.replace('@', '') in channels:
        channels.remove(normalized_id.replace('@', ''))
    
    if len(channels) < initial_count:
        if save_channels(channels):
            return True, f"Channel {channel_id} removed from monitoring list."
    
    return False, f"Channel {channel_id} not found in monitoring list."

def list_channels():
    """Get a formatted list of all monitored channels."""
    channels = load_channels()
    
    if not channels:
        return "No channels are being monitored."
    
    result = "Monitored channels:\n\n"
    for i, channel in enumerate(channels, 1):
        result += f"{i}. `{channel}`\n"
    
    return result

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Hi! I'm a channel message editor bot. I automatically edit messages in the configured channel.\n"
        "Add me to your channel as an admin with edit permissions to get started."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "How to use this bot:\n"
        "1. Add this bot to your channel as an admin\n"
        "2. Give it permission to post and edit messages\n"
        "3. Add your channel to the bot's monitoring list\n"
        "4. The bot will automatically edit new messages to apply text filters and convert timestamps\n\n"
        "Channel management commands:\n"
        "/channels - List all monitored channels\n"
        "/addchannel channel_id - Add a channel to monitor\n"
        "/removechannel channel_id - Remove a channel from monitoring\n\n"
        "Filter management commands:\n"
        "/filters - List all current text filters\n"
        "/addfilter pattern replacement - Add a new filter\n"
        "/removefilter pattern - Remove a filter\n"
        "/testfilter sample_text regex_pattern - Test a regex pattern on sample text"
    )

async def process_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process new channel posts."""
    message = update.channel_post
    
    if not message:
        return
    
    # Check if the message is from a monitored channel
    monitored_channels = load_channels()
    channel_match = False
    
    for channel in monitored_channels:
        # Handle both username format (@channel) and numeric ID format
        if channel.startswith('@'):
            # Username format - compare with channel username
            if message.chat.username and message.chat.username.lower() == channel.replace('@', '').lower():
                channel_match = True
                break
        else:
            # Numeric ID format - compare with channel ID
            if message.chat.id and str(message.chat.id) == channel:
                channel_match = True
                break
    
    if not channel_match and monitored_channels:
        logger.info(f"Ignoring message from non-monitored channel: {message.chat.id}")
        return
    
    # Log full message details for debugging
    logger.info(f"Message details: chat_id={message.chat.id}, username={message.chat.username}, text={message.text}")
    
    logger.info(f"Processing message {message.message_id} from channel {message.chat.id}")
    
    try:
        # Process text messages
        if message.text and PROCESS_TEXT:
            original_text = message.text
            logger.info(f"Original text before processing: '{original_text}'")
            
            processed_text = process_message_text(original_text)
            logger.info(f"Processed text after filters and time conversion: '{processed_text}'")
            
            # Only edit if the text has changed
            if processed_text != original_text:
                logger.info(f"Text was changed! Will attempt to edit message {message.message_id}")
            else:
                logger.info(f"No changes needed for message {message.message_id}")
                
            # Only edit if the text has changed
            if processed_text != original_text:
                try:
                    # Try to edit message directly
                    await message.edit_text(processed_text, entities=message.entities)
                    logger.info(f"Edited text message {message.message_id}")
                except Exception as edit_error:
                    # If editing fails (e.g., no permission), try alternative method
                    logger.warning(f"Could not edit message directly: {edit_error}")
                    
                    try:
                        # Try using bot API directly with context.bot
                        await context.bot.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=message.message_id,
                            text=processed_text,
                            entities=message.entities
                        )
                        logger.info(f"Edited text message {message.message_id} using bot API")
                    except Exception as api_error:
                        # If that also fails, log detailed error
                        logger.error(f"Failed to edit message {message.message_id}: {api_error}")
                        
                        # If both editing methods fail, create a reply that shows what the text should be
                        if REPLY_ON_EDIT_FAILURE:
                            try:
                                await context.bot.send_message(
                                    chat_id=message.chat.id,
                                    text=f"*Message text should be:*\n\n{processed_text}",
                                    parse_mode="Markdown",
                                    reply_to_message_id=message.message_id
                                )
                                logger.info(f"Sent reply with corrected text for message {message.message_id}")
                            except Exception as reply_error:
                                logger.error(f"Failed to send reply: {reply_error}")
        
        # Process captions in media messages
        elif message.caption and PROCESS_CAPTIONS:
            original_caption = message.caption
            processed_caption = process_message_text(original_caption)
            
            # Only edit if the caption has changed
            if processed_caption != original_caption:
                try:
                    # Try to edit caption directly
                    await message.edit_caption(processed_caption, caption_entities=message.caption_entities)
                    logger.info(f"Edited caption in message {message.message_id}")
                except Exception as edit_error:
                    # If editing fails, try alternative method
                    logger.warning(f"Could not edit caption directly: {edit_error}")
                    
                    try:
                        # Try using bot API directly
                        await context.bot.edit_message_caption(
                            chat_id=message.chat.id,
                            message_id=message.message_id,
                            caption=processed_caption,
                            caption_entities=message.caption_entities
                        )
                        logger.info(f"Edited caption in message {message.message_id} using bot API")
                    except Exception as api_error:
                        # If that also fails, log detailed error
                        logger.error(f"Failed to edit caption in message {message.message_id}: {api_error}")
                        
                        # If both editing methods fail, create a reply that shows what the caption should be
                        if REPLY_ON_EDIT_FAILURE:
                            try:
                                await context.bot.send_message(
                                    chat_id=message.chat.id,
                                    text=f"*Caption should be:*\n\n{processed_caption}",
                                    parse_mode="Markdown",
                                    reply_to_message_id=message.message_id
                                )
                                logger.info(f"Sent reply with corrected caption for message {message.message_id}")
                            except Exception as reply_error:
                                logger.error(f"Failed to send reply: {reply_error}")
                
    except Exception as e:
        logger.error(f"Error processing message {message.message_id}: {e}")

async def filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all current filters."""
    filters_text = list_filters()
    await update.message.reply_text(filters_text, parse_mode="Markdown")

async def add_filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new filter."""
    # Check arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: /addfilter pattern replacement\n\n"
            "Example: /addfilter (?i)\\b(hello)\\b HELLO\n\n"
            "This would replace all instances of 'hello' (case insensitive) with 'HELLO'"
        )
        return
    
    # Get pattern and replacement
    pattern = context.args[0]
    replacement = ' '.join(context.args[1:])
    
    try:
        # Test if pattern is valid regex
        re.compile(pattern)
        
        # Add the filter
        if add_filter(pattern, replacement):
            await update.message.reply_text(
                f"✅ Filter added successfully!\n\n"
                f"Pattern: `{pattern}`\n"
                f"Replacement: `{replacement}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Failed to add filter.")
    except re.error as e:
        await update.message.reply_text(f"❌ Invalid regular expression: {str(e)}")

async def remove_filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a filter."""
    # Check arguments
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /removefilter pattern\n\n"
            "Example: /removefilter (?i)\\b(hello)\\b\n\n"
            "Use /filters to see all available filters and their patterns."
        )
        return
    
    # Get pattern
    pattern = context.args[0]
    
    # Remove the filter
    if remove_filter(pattern):
        await update.message.reply_text(f"✅ Filter with pattern `{pattern}` removed.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ No filter found with pattern: `{pattern}`", parse_mode="Markdown")

async def test_filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test a regex pattern on sample text."""
    # Check arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: /testfilter sample_text pattern\n\n"
            "Example: /testfilter \"Hello world\" (?i)\\b(hello)\\b\n\n"
            "This tests if the pattern matches the sample text."
        )
        return
    
    # Get sample text and pattern
    sample_text = context.args[0]
    pattern = context.args[1]
    
    try:
        # Test the pattern
        result = test_filter(sample_text, pattern)
        await update.message.reply_text(f"Test result:\n\n{result}")
    except re.error as e:
        await update.message.reply_text(f"❌ Invalid regular expression: {str(e)}")

async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all monitored channels."""
    channels_text = list_channels()
    await update.message.reply_text(channels_text, parse_mode="Markdown")

async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new channel to monitor."""
    # Check arguments
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /addchannel channel_id\n\n"
            "Example: /addchannel @mychannel\n"
            "Example: /addchannel -1001234567890\n\n"
            "You can use either the channel username (with @) or the channel ID."
        )
        return
    
    # Get channel ID
    channel_id = context.args[0]
    
    # Add the channel
    success, message = add_channel(channel_id)
    
    if success:
        await update.message.reply_text(f"✅ {message}")
    else:
        await update.message.reply_text(f"❌ {message}")

async def remove_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a channel from monitoring."""
    # Check arguments
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: /removechannel channel_id\n\n"
            "Example: /removechannel @mychannel\n"
            "Example: /removechannel -1001234567890\n\n"
            "Use /channels to see all monitored channels."
        )
        return
    
    # Get channel ID
    channel_id = context.args[0]
    
    # Remove the channel
    success, message = remove_channel(channel_id)
    
    if success:
        await update.message.reply_text(f"✅ {message}")
    else:
        await update.message.reply_text(f"❌ {message}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error: {context.error}")

def start_bot():
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("No bot token provided. Set the TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    if not CHANNEL_ID:
        logger.warning("No channel ID provided. The bot will process all channels it's added to.")
    
    # Create the Application instance
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add filter management command handlers
    application.add_handler(CommandHandler("filters", filters_command))
    application.add_handler(CommandHandler("addfilter", add_filter_command))
    application.add_handler(CommandHandler("removefilter", remove_filter_command))
    application.add_handler(CommandHandler("testfilter", test_filter_command))
    
    # Add channel management command handlers
    application.add_handler(CommandHandler("channels", channels_command))
    application.add_handler(CommandHandler("addchannel", add_channel_command))
    application.add_handler(CommandHandler("removechannel", remove_channel_command))
    
    # Use UPDATE_TYPE.CHANNEL_POST filter instead of CHANNEL
    application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, process_channel_post))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    logger.info("Starting bot polling...")
    application.run_polling()

    return application
