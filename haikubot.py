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

MESSEGE_LIMIT_DEFAULT = 20

client = OpenAI()

# Load configuration from config.json
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

message_limit = config.get('message_limit', MESSEGE_LIMIT_DEFAULT)

messages_buffer = []

async def handle_message(update: Update, context: CallbackContext):
    if update.message and update.message.text:
        text = update.message.text.strip()
        print(text)
        messages_buffer.append(text)
        if len(messages_buffer) == message_limit:
            prompt = "З цих повідомлень: " + "\n".join(messages_buffer) + "\nЗгенеруй хокку мовою цих повідомлень."
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            haiku = completion.choices[0].message.content.strip()
            await update.message.reply_text(haiku)
            messages_buffer.clear()

if __name__ == "__main__":
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

