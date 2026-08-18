"""
Configuration settings for haikubot
"""
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Debug mode
IS_DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Response trigger probability
RESPONSE_TRIGGER_PROBABILITY = float(os.getenv('RESPONSE_TRIGGER_PROBABILITY', '0.5'))

# Test chat ID for local testing (optional)
TEST_CHAT_ID = os.getenv('TEST_CHAT_ID')
if TEST_CHAT_ID:
    try:
        TEST_CHAT_ID = int(TEST_CHAT_ID)
    except ValueError:
        TEST_CHAT_ID = None

# Test current time for local testing (optional)
# Format: "2025-06-02 16:21:28"
TEST_CURRENT_TIME = os.getenv('TEST_CURRENT_TIME')
if TEST_CURRENT_TIME:
    try:
        import datetime
        TEST_CURRENT_TIME = datetime.datetime.strptime(TEST_CURRENT_TIME, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        TEST_CURRENT_TIME = None

# Load configuration from config.json
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

# Get configuration values
MESSAGE_LIMIT = config.get('message_limit')


def get_model(env_name: str, config_name: str, default: str = None) -> str:
    """Read a model name from the environment, then fall back to config.json."""
    return os.getenv(env_name) or config.get(config_name, default)


ANSWER_MODEL = get_model('ANSWER_MODEL', 'answer_model')
HAIKU_MODEL = get_model('OPENAI_HAIKU_MODEL', 'haiku_model', ANSWER_MODEL)
HISTORY_ANALYSIS_MODEL = get_model(
    'OPENAI_HISTORY_ANALYSIS_MODEL', 'history_analysis_model', ANSWER_MODEL
)
TRANSLATION_MODEL = get_model(
    'OPENAI_TRANSLATION_MODEL', 'translation_model', ANSWER_MODEL
)
BOT_USER = config.get('bot')
