import os
import json
import datetime
import logging
from dotenv import load_dotenv
from openai import OpenAI
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext, ContextTypes, CommandHandler
from telegram import Update
import db_service
import random  # Додано для генерації випадкових чисел
from handlers.message_handler import store_message
from handlers.haiku_handler import process_haiku_answer
from handlers.response_handler import process_bot_response
from utils.config import TELEGRAM_TOKEN

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load environment variables from .env file
load_dotenv()

# Tokens from the environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
IS_DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

PROMPT_HAIKU = """
Згенеруй хокку мовою цих повідомлень, беручі до уваги умови.

Повідомлення:
{messages}

Умови:
1. Пиши хокку у форматі 5-7-5. 
2. Мова хокку - українська.
3. Ігноруй смайлики та інші символи.
4. Використовуй інформацію про автора та час повідомлення тільки для розуміння контексту розмови. Для самого хокку використовуй тільки тексти повідомлень.
"""

client = OpenAI()

# Load configuration from config.json
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

message_limit = config.get('message_limit')
model = config.get('model')  # Use model from config file

def invoke_model(prompt):
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()

# Dictionary to track message counts per chat
message_counts = {}


async def handle_message(update, context):
    """
    Main message handler that orchestrates all other handlers
    
    Args:
        update: Telegram update
        context: Callback context
    """
    await store_message(update, context)
    await process_haiku_answer(update, context)
    await process_bot_response(update, context)

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

