import os
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler
from handlers.message_handler import store_message
from handlers.haiku_handler import process_haiku_answer
from handlers.response_handler import process_bot_response
from handlers.query_handler import handle_query_command
from utils.config import TELEGRAM_TOKEN

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load environment variables from .env file
load_dotenv()

# Tokens from the environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

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
    
    # Add command handlers
    application.add_handler(CommandHandler("ask", handle_query_command))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

