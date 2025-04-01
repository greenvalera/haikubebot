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
"""

client = OpenAI()

# Load configuration from config.json
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)


message_limit = config.get('message_limit')
model = config.get('model')  # Use model from config file

# Global variable to store messages
chat_history = {}

def invoce_model(prompt):
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()

MAX_MESSAGES_PER_CHAT = 1000

async def store_message(update: Update, context: CallbackContext):
    if update.message.from_user.is_bot or update.message.text is None:
        return

    if IS_DEBUG:
        print(f"Chat {update.message.chat_id}: {update.message.text}")

    chat_id = update.message.chat_id
    user = update.message.from_user
    text = update.message.text
    
    # Store in local memory for backward compatibility
    if chat_id not in chat_history:
        chat_history[chat_id] = []

    # Store the message text with the author's name
    first_name = user.first_name
    last_name = user.last_name
    chat_history[chat_id].append({
        'from_user': f"{first_name} {last_name if last_name else ''}",
        'text': text
    })

    # Ensure only the latest MAX_MESSAGES_PER_CHAT messages are kept
    if len(chat_history[chat_id]) > MAX_MESSAGES_PER_CHAT:
        chat_history[chat_id] = chat_history[chat_id][-MAX_MESSAGES_PER_CHAT:]
    
    # Save to database
    try:
        # Get or create user
        db_service.get_or_create_user(
            user_id=user.id,
            username=user.username if user.username else '',
            first_name=first_name,
            last_name=last_name
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

async def get_chat_history(chat_id, limit=100):
    # First try to get messages from database
    try:
        db_messages = db_service.get_chat_messages(chat_id, limit)
        if db_messages and len(db_messages) > 0:
            # Format messages to match the expected structure
            return [
                {
                    'from_user': f"{msg.get('first_name', '')} {msg.get('last_name', '')}".strip(),
                    'text': msg.get('text', '')
                }
                for msg in db_messages
            ]
    except Exception as e:
        if IS_DEBUG:
            print(f"Error retrieving from database: {e}")
    
    # Fall back to in-memory storage if database fails or has no messages
    if chat_id in chat_history:
        return chat_history[chat_id][-limit:]
    return []

prompt_to_analize = """
Ось останні {n} повідомлень чату: {messages}.
Повідомлення представлені в форматі "author: message".
Аналізуй їх зміст за по тексу 'message' та виведи коротку суть про що обговорюється в чаті.
Не відповідай на повідомлення, а лише коротко підсумуй суть їх змісту.
Переказуй факти, а не власні думки.
Враховуй, що автори повідомлень можуть бути різними.
Якщо важливо посилання на автора, використовуй його ім'я.
Заміть посилання "автор на ім'я Жовта Зелень" використовуй просто ім'я "Жовта Зелень".
Не перераховуй всі повідомлення, лише виведи коротку суть.
"""
# Команда /analyze
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        n = int(context.args[0])
        chat_id = update.message.chat_id
        messages = await get_chat_history(chat_id, limit=n)
        # Include authors' names in the model context
        text_messages = [f"{msg['from_user']}: {msg['text']}" for msg in messages if 'text' in msg]

        print(f"Analyzing {n} messages: {text_messages}")

        # Аналіз повідомлень за допомогою LangChain
        response = invoce_model(prompt_to_analize.format(n=n, messages="\n".join(text_messages)))
        await update.message.reply_text(response)
    except (IndexError, ValueError):
        await update.message.reply_text("Будь ласка, вкажи правильну кількість повідомлень. Наприклад: /analyze 5")

# Initialize the dictionary for message buffers per chat
messages_buffers = {}

analyze_handler = CommandHandler('analyze', analyze)

async def process_haiku_answer(update: Update, context: CallbackContext):
    if update.message and update.message.text:
        chat_id = update.effective_chat.id
        text = update.message.text.strip()

        if IS_DEBUG:
            print(f"Handle message in chat {chat_id}: {text}")
            
        # Initialize buffer for this chat if it doesn't exist
        if chat_id not in messages_buffers:
            messages_buffers[chat_id] = []
        messages_buffers[chat_id].append(text)

        if len(messages_buffers[chat_id]) == message_limit:
            messeges_str = "\n".join(messages_buffers[chat_id])
            prompt = PROMPT_HAIKU.format(messages=messeges_str)
            haiku = invoce_model(prompt)
            await update.message.reply_text(haiku)
            # Clear the buffer for this chat
            messages_buffers[chat_id] = []

async def handle_message(update: Update, context: CallbackContext):
    await store_message(update, context)
    await process_haiku_answer(update, context)

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(analyze_handler)
    application.run_polling()

