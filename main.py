import logging
from bot import start_bot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Create a Flask application instance variable in the module
# This allows gunicorn to access the app variable
from app import app

if __name__ == "__main__":
    logger.info("Starting Telegram channel message editor bot")
    start_bot()
