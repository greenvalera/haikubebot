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

# Load configuration from config.json
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

# Get configuration values
MESSAGE_LIMIT = config.get('message_limit')
MODEL = config.get('model')
BOT_USER = config.get('bot')