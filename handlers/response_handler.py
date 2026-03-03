"""
Handler for processing bot responses to messages that quote the bot's posts
"""
import logging
import json
from telegram import Update
from telegram.ext import CallbackContext
import db_service
from utils.config import IS_DEBUG, BOT_USER
from utils.openai_client import invoke_model
from utils.prompts import PROMPT_RESPONSE_BASE


async def process_bot_response(update: Update, context: CallbackContext):
    """
    Process user's reply to any bot post and generate a contextual response.

    Args:
        update: Telegram update
        context: Callback context
    """
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id

    # Check if this is a reply to the bot's message
    if not update.message.reply_to_message or not update.message.reply_to_message.from_user.is_bot:
        return

    try:
        bot_message_tg_id = update.message.reply_to_message.message_id
        bot_post_text = update.message.reply_to_message.text or ""

        logging.info(
            f"[response_handler] Generating response for message: {update.message.text}, "
            f"bot post tg_id={bot_message_tg_id}"
        )

        # Get source messages (messages that the bot post was generated from)
        source_messages = []
        try:
            haiku_msg = db_service.get_message_by_tg_id(bot_message_tg_id)
            if haiku_msg and haiku_msg.get("haiku_source_ids"):
                source_ids = json.loads(haiku_msg["haiku_source_ids"])
                source_messages = db_service.get_messages_by_ids(source_ids) if source_ids else []
        except Exception as e:
            logging.warning(f"[response_handler] Failed to get source messages: {e}")

        # Get thread conversation history (previous exchanges around this bot post)
        thread_messages = []
        try:
            thread_messages = db_service.get_thread_messages(chat_id, bot_message_tg_id)
        except Exception as e:
            logging.warning(f"[response_handler] Failed to get thread messages: {e}")

        # Format source context
        if source_messages:
            source_text = "\n".join([
                f"Автор: {msg.get('from_user', '')}\n"
                f"Дата: {msg.get('created_at', '')}\n"
                f"Текст: {msg.get('text', '')}\n"
                f"---"
                for msg in source_messages
            ])
        else:
            source_text = "(немає даних)"

        # Format thread history
        if thread_messages:
            thread_text = "\n".join([
                f"{'Бот' if msg.get('is_bot') else msg.get('from_user', 'Користувач')}: {msg.get('text', '')}"
                for msg in thread_messages
            ])
        else:
            thread_text = "(порожньо)"

        prompt = PROMPT_RESPONSE_BASE.format(
            bot_post=bot_post_text,
            user_comment=update.message.text,
            source_messages=source_text,
            thread_history=thread_text,
        )

        response = invoke_model(prompt)
        sent_message = await update.message.reply_text(response)

        # Save bot response to database for future context
        try:
            db_service.save_message(
                chat_id=chat_id,
                user_id=BOT_USER["user_id"],
                tg_id=sent_message.message_id,
                text=response,
                reply_to_tg_id=update.message.message_id,
            )
        except Exception as e:
            logging.warning(f"[response_handler] Failed to save bot response: {e}")

    except Exception as e:
        logging.error(f"[response_handler] Error processing bot response: {e}")
        if IS_DEBUG:
            print(f"Error processing bot response: {e}")
