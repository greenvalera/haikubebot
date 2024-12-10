import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from telegram import Update

# Load environment variables from .env file
load_dotenv()

# Tokens from the environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
IS_DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

client = OpenAI()

# Load configuration from config.json
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

message_limit = config.get('message_limit')
model = config.get('model')

# Initialize the dictionary for message buffers per chat
messages_buffers = {}

async def handle_message(update: Update, context: CallbackContext):
    if update.message and update.message.text:
        chat_id = update.effective_chat.id
        text = update.message.text.strip()
        if IS_DEBUG:
            print(f"Chat {chat_id}: {text}")
        # Initialize buffer for this chat if it doesn't exist
        if chat_id not in messages_buffers:
            messages_buffers[chat_id] = []
        messages_buffers[chat_id].append(text)
        if len(messages_buffers[chat_id]) == message_limit:
            prompt = "З цих повідомлень: " + "\n".join(messages_buffers[chat_id]) + "\nЗгенеруй хокку мовою цих повідомлень."
            completion = client.chat.completions.create(
                model,
                messages=[{"role": "user", "content": prompt}]
            )
            haiku = completion.choices[0].message.content.strip()
            await update.message.reply_text(haiku)
            # Clear the buffer for this chat
            messages_buffers[chat_id] = []

if __name__ == "__main__":
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

