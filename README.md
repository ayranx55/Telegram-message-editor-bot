# Telegram Channel Message Editor Bot

This bot automatically edits new messages in a Telegram channel by applying text filters and converting UTC (+14:00) timestamps to GMT (+5:30).

## Features

- Monitors new messages in a specific Telegram channel
- Edits text content based on configurable text filters
- Converts timestamps from UTC (+14:00) to GMT (+5:30) / IST
- Handles both text messages and media captions
- Dynamic filter management through bot commands
- Logs all bot activity for monitoring

## Setup

### Prerequisites

- Python 3.x
- Telegram Bot Token (get from @BotFather)
- Channel ID to monitor

### Environment Variables

Set the following environment variables:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `CHANNEL_ID`: The ID or username of the channel to monitor (e.g., `-1001234567890` or `@channelname`)

### Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install python-telegram-bot pytz
```

## Bot Commands

The bot supports the following commands:

### Channel Management

- `/channels` - List all monitored channels
- `/addchannel channel_id` - Add a channel to monitor
- `/removechannel channel_id` - Remove a channel from monitoring

### Filter Management

- `/start` - Get a welcome message
- `/help` - Show help information
- `/filters` - List all current text filters
- `/addfilter pattern replacement` - Add a new filter
- `/removefilter pattern` - Remove a filter
- `/testfilter sample_text regex_pattern` - Test a regex pattern on sample text

### Example Commands

#### Channel Management Examples

```
/addchannel @mychannel
```
This adds the channel with username "mychannel" to the monitoring list.

```
/addchannel -1001234567890
```
This adds the channel with the given ID to the monitoring list.

```
/removechannel @mychannel
```
This removes the channel with username "mychannel" from the monitoring list.

#### Filter Management Examples

```
/addfilter (?i)\b(urgent)\b URGENT
```
This adds a filter that will replace any occurrence of "urgent" (case insensitive) with "URGENT".

```
/removefilter (?i)\b(urgent)\b
```
This removes the filter for "urgent".

```
/testfilter "This is urgent!" (?i)\b(urgent)\b
```
This tests if the pattern matches the provided text.
