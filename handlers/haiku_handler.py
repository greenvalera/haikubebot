"""
Handler for generating haikus
"""
from telegram import Update
from telegram.ext import CallbackContext
import db_service
from utils.config import IS_DEBUG, MESSAGE_LIMIT, BOT_USER
from utils.openai_client import invoke_model
from utils.prompts import PROMPT_HAIKU
import logging

# Dictionary to track message counts per chat
message_counts = {}

# Dictionary to track bot's last haiku messages per chat
last_bot_haikus = {}

async def process_haiku_answer(update: Update, context: CallbackContext):
    """
    Process messages and generate haiku when message limit is reached
    
    Args:
        update: Telegram update
        context: Callback context
    """
    if update.message and update.message.text:
        chat_id = update.effective_chat.id
        
        # Initialize counter for this chat if it doesn't exist
        if chat_id not in message_counts:
            message_counts[chat_id] = 0
        
        # Increment message count
        message_counts[chat_id] += 1
        
        # Check if we've reached the message limit
        if message_counts[chat_id] >= MESSAGE_LIMIT:
            try:
                # Get the last N messages from the database, excluding bot messages
                messages = db_service.get_chat_messages(chat_id, limit=MESSAGE_LIMIT, exclude_bots=True)
                if not messages:
                    logging.info(f"[haiku_handler] No chat history found for chat_id={chat_id}")
                
                # Format messages for the prompt with structured data
                messages_text = "\n".join([
                    f"Автор: {msg['from_user']}\n"
                    f"Дата: {msg.get('created_at', '')}\n"
                    f"Текст: {msg['text']}\n"
                    f"---"
                    for msg in messages
                ])

                # Логування початку генерації хайку
                logging.info(f"[haiku_handler] Початок генерації хайку для chat_id={chat_id}")

                # Generate haiku
                prompt = PROMPT_HAIKU.format(messages=messages_text)
                haiku = invoke_model(prompt)
                logging.info(f"[haiku_handler] Згенеровано хайку для chat_id={chat_id}: {haiku}")
                sent_message = await update.message.reply_text(haiku)

                # Store the message ID of the last haiku
                last_bot_haikus[chat_id] = sent_message.message_id

                # --- Store haiku as bot message in database ---
                # Define synthetic bot user (make sure user_id is unique and consistent for the bot)
                # Use bot info from config
                db_service.get_or_create_user(
                    user_id=BOT_USER['user_id'],
                    username=BOT_USER['username'],
                    first_name=BOT_USER['first_name'],
                    last_name=BOT_USER['last_name'],
                    is_bot=True
                )
                db_service.update_user_last_activity(BOT_USER['user_id'])
                # Зберігаємо id всіх повідомлень, на основі яких створено хайку (беремо з get_chat_messages)
                source_ids = [msg.get('id') for msg in messages if msg.get('id')]
                db_service.save_message(
                    chat_id=chat_id,
                    user_id=BOT_USER['user_id'],
                    tg_id=sent_message.message_id,
                    text=haiku,
                    haiku_source_ids=source_ids
                )

                # Reset counter
                message_counts[chat_id] = 0
                
            except Exception as e:
                if IS_DEBUG:
                    print(f"Error generating haiku: {e}") 