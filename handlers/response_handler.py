"""
Handler for processing bot responses to haiku comments
"""
import random
import logging
import json
from telegram import Update
from telegram.ext import CallbackContext
import db_service
from utils.config import IS_DEBUG, MESSAGE_LIMIT, RESPONSE_TRIGGER_PROBABILITY
from utils.openai_client import invoke_model
from utils.prompts import PROMPT_RESPONSE_BASE
from handlers.haiku_handler import last_bot_haikus

async def process_bot_response(update: Update, context: CallbackContext):
    """
    Process user's response to bot's haiku message with different styles based on probability
    
    Args:
        update: Telegram update
        context: Callback context
    """
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    
    # Check if this is a reply to bot's message
    if not update.message.reply_to_message or not update.message.reply_to_message.from_user.is_bot:
        return
        
    # Check if the replied message is a haiku
    if chat_id not in last_bot_haikus or last_bot_haikus[chat_id] != update.message.reply_to_message.message_id:
        return
        
    # Check probability trigger
    if random.random() > RESPONSE_TRIGGER_PROBABILITY:
        return
        
    try:
        logging.info(f"[response_handler] Start response generation on message: {update.message.text}")
        # Отримуємо id повідомлень, на основі яких створено хайку
        bot_message_id = update.message.reply_to_message.message_id
        try:
            haiku_msg = db_service.get_message_by_tg_id(bot_message_id)
        except Exception as e:
            logging.warning(f"[response_handler] Failed to get message by tg_id: {e}")
            
        source_ids = []
        if haiku_msg and haiku_msg.get('haiku_source_ids'):
            try:
                source_ids = json.loads(haiku_msg['haiku_source_ids'])
            except Exception as e:
                logging.warning(f"[response_handler] Failed to parse haiku_source_ids: {e}")
        try:
            messages = db_service.get_messages_by_ids(source_ids) if source_ids else []
        except Exception as e:
            logging.warning(f"[response_handler] Failed to get messages by ids: {e}")
        if not messages:
            logging.info(f"[response_handler] No haiku source messages found for haiku_msg_id={bot_message_id}")
        # Формуємо повідомлення для промпту
        messages_text = "\n".join([
            f"Автор: {msg.get('from_user', '')}\n"
            f"Дата: {msg.get('created_at', '')}\n"
            f"Текст: {msg.get('text', '')}\n"
            f"---"
            for msg in messages
        ])
        prompt = PROMPT_RESPONSE_BASE.format(
            haiku=update.message.reply_to_message.text,
            user_comment=update.message.text,
            messages=messages_text
        )
            
        response = invoke_model(prompt)
        await update.message.reply_text(response)
        
    except Exception as e:
        if IS_DEBUG:
            print(f"Error processing bot response: {e}") 