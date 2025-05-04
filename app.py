import os
import logging
from flask import Flask, render_template_string, jsonify
from filter_manager import list_filters
from bot import list_channels

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Create a simple HTML template for the status page
STATUS_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Telegram Bot Status</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
    <style>
        body {
            padding: 20px;
        }
        .status-card {
            margin-bottom: 20px;
            border-radius: 8px;
        }
        .card-header {
            font-weight: bold;
        }
        pre {
            white-space: pre-wrap;
            word-break: break-word;
        }
    </style>
</head>
<body data-bs-theme="dark">
    <div class="container">
        <h1 class="mb-4">Telegram Bot Status</h1>
        
        <div class="card status-card">
            <div class="card-header">Bot Status</div>
            <div class="card-body">
                <p>✅ Bot is running and monitoring channels</p>
                <p><strong>Monitored Channels:</strong></p>
                <pre>{{ channels }}</pre>
            </div>
        </div>
        
        <div class="card status-card">
            <div class="card-header">Active Filters</div>
            <div class="card-body">
                <pre>{{ filters }}</pre>
            </div>
        </div>
        
        <div class="card status-card">
            <div class="card-header">Configuration</div>
            <div class="card-body">
                <p><strong>Source Timezone:</strong> {{ source_tz }}</p>
                <p><strong>Target Timezone:</strong> {{ target_tz }}</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Display bot status page"""
    from config import SOURCE_TIMEZONE, TARGET_TIMEZONE
    
    try:
        # Get filters as string (strip Markdown formatting)
        filters_text = list_filters().replace('`', '')
        
        # Get channels text
        channels_text = list_channels().replace('`', '')
        
        return render_template_string(
            STATUS_PAGE_TEMPLATE,
            filters=filters_text,
            channels=channels_text,
            source_tz=SOURCE_TIMEZONE,
            target_tz=TARGET_TIMEZONE
        )
    except Exception as e:
        logger.error(f"Error rendering status page: {e}")
        return f"Error: {str(e)}", 500

@app.route('/api/status')
def status_api():
    """Return bot status as JSON"""
    try:
        channels_list = list_channels().split('\n')
        filters_list = list_filters().split('\n')
        
        return jsonify({
            "status": "online",
            "channels_count": len(channels_list) - 1 if len(channels_list) > 1 else 0,
            "filters_count": len(filters_list) - 2 if len(filters_list) > 2 else 0,
        })
    except Exception as e:
        logger.error(f"Error in status API: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # This code only runs when app.py is executed directly, not when imported
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)