import os
import json
import datetime
from dotenv import load_dotenv
from openai import OpenAI
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext, ContextTypes, CommandHandler
from telegram import Update
import db_service

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

def invoce_model(prompt):
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()

# Dictionary to track message counts per chat
message_counts = {}

async def store_message(update: Update, context: CallbackContext):
    if update.message.from_user.is_bot or update.message.text is None:
        return

    if IS_DEBUG:
        print(f"Chat {update.message.chat_id}: {update.message.text}")

    chat_id = update.message.chat_id
    user = update.message.from_user
    text = update.message.text
    
    # Save to database
    try:
        # Get or create user
        db_service.get_or_create_user(
            user_id=user.id,
            username=user.username if user.username else '',
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Update user's last activity
        db_service.update_user_last_activity(user.id)
        
        # Save message
        db_service.save_message(
            chat_id=chat_id,
            user_id=user.id,
            text=text
        )

        if IS_DEBUG:
            print(f"Saved message to database: {text}")
    except Exception as e:
        if IS_DEBUG:
            print(f"Error saving to database: {e}")

async def process_haiku_answer(update: Update, context: CallbackContext):
    if update.message and update.message.text:
        chat_id = update.effective_chat.id
        
        # Initialize counter for this chat if it doesn't exist
        if chat_id not in message_counts:
            message_counts[chat_id] = 0
        
        # Increment message count
        message_counts[chat_id] += 1
        
        # Check if we've reached the message limit
        if message_counts[chat_id] >= message_limit:
            try:
                # Get the last N messages from the database
                messages = db_service.get_chat_messages(chat_id, limit=message_limit)
                
                # Format messages for the prompt with structured data
                messages_text = "\n".join([
                    f"Автор: {msg['from_user']}\n"
                    f"Дата: {msg.get('created_at', '')}\n"
                    f"Текст: {msg['text']}\n"
                    f"---"
                    for msg in messages
                ])
                
                # Generate haiku
                prompt = PROMPT_HAIKU.format(messages=messages_text)
                haiku = invoce_model(prompt)
                await update.message.reply_text(haiku)
                
                # Reset counter
                message_counts[chat_id] = 0
                
            except Exception as e:
                if IS_DEBUG:
                    print(f"Error generating haiku: {e}")

async def handle_message(update: Update, context: CallbackContext):
    await store_message(update, context)
    await process_haiku_answer(update, context)

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

