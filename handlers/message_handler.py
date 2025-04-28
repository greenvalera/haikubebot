"""
Handler for storing messages in the database
"""
from telegram import Update
from telegram.ext import CallbackContext
import db_service
from utils.config import IS_DEBUG

async def store_message(update: Update, context: CallbackContext):
    """
    Store message in the database
    
    Args:
        update: Telegram update
        context: Callback context
    """
    if update.message.text is None:
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
            last_name=user.last_name,
            is_bot=user.is_bot
        )
        
        # Update user's last activity
        db_service.update_user_last_activity(user.id)
        
        # Save message
        db_service.save_message(
            chat_id=chat_id,
            user_id=user.id,
            text=text,
            tg_id=update.message.message_id
        )

        if IS_DEBUG:
            print(f"Saved message to database: {text}")
    except Exception as e:
        if IS_DEBUG:
            print(f"Error saving to database: {e}") 