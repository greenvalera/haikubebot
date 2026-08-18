"""
Handler for processing user queries with chat history context
"""
import logging
import re
from telegram import Update
from telegram.ext import CallbackContext
import db_service
from utils.config import HISTORY_ANALYSIS_MODEL, IS_DEBUG, TEST_CHAT_ID
from utils.openai_client import invoke_model

def parse_time_period(time_str: str) -> int:
    """
    Parse time period string to minutes
    
    Args:
        time_str: Time period string like '34m', '2h', '1d'
        
    Returns:
        int: Time period in minutes
        
    Raises:
        ValueError: If time_str format is invalid
    """
    # Remove any spaces
    time_str = time_str.strip().lower()
    
    # Match pattern: number followed by m/h/d
    match = re.match(r'^(\d+)([mhd])$', time_str)
    if not match:
        raise ValueError(f"Invalid time format: {time_str}")
    
    number = int(match.group(1))
    unit = match.group(2)
    
    # Convert to minutes
    if unit == 'm':
        return number
    elif unit == 'h':
        return number * 60
    elif unit == 'd':
        return number * 60 * 24
    else:
        raise ValueError(f"Unknown time unit: {unit}")

# Default time period mappings (for examples in help)
EXAMPLE_TIME_PERIODS = {
    '15m': 15,
    '30m': 30, 
    '1h': 60,
    '6h': 360,
    '1d': 1440,  # 24 hours in minutes
}

QUERY_PROMPT_TEMPLATE = """
Ти розумний асистент, який допомагає аналізувати історію чату і відповідати на запити користувачів.

ІСТОРІЯ ПОВІДОМЛЕНЬ:
{history}

ЗАПИТ КОРИСТУВАЧА:
{user_query}

ІНСТРУКЦІЇ:
1. Проаналізуй історію повідомлень вище
2. Відповідь на запит користувача, використовуючи контекст з історії
3. Відповідай українською мовою
4. Будь конкретним і корисним
5. Якщо в історії недостатньо інформації для відповіді, так і скажи

ВІДПОВІДЬ:
"""

async def handle_query_command(update: Update, context: CallbackContext):
    """
    Handle the /ask command with time period and query
    
    Command format: /ask [число][m/h/d] <your query>
    Examples: 
        /ask 1h Про що говорили в останню годину?
        /ask 30m Хто був найактивніший?
        /ask 2h Підсумуй обговорення за 2 години
        /ask 45m Які питання обговорювали?
    
    Args:
        update: Telegram update
        context: Callback context
    """
    if not update.message or not update.message.text:
        return
        
    chat_id = update.effective_chat.id
    # Use test chat ID for local testing if configured
    if TEST_CHAT_ID:
        chat_id = TEST_CHAT_ID
        logging.info(f"[query_handler] Using test chat_id: {chat_id}")
    
    command_text = update.message.text
    
    # Parse command: /ask [time_period] query
    # Remove /ask from the beginning
    query_part = command_text[4:].strip()  # Remove "/ask"
    
    if not query_part:
        await update.message.reply_text(
            "Використання: /ask [часовий_період] <ваш запит>\n\n"
            "Формат часу: [число][m/h/d] (m=хвилини, h=години, d=дні)\n\n"
            "Приклади:\n"
            "• /ask 1h Про що говорили в останню годину?\n"
            "• /ask 30m Хто був найактивніший?\n"
            "• /ask 2h Підсумуй обговорення за 2 години\n"
            "• /ask 45m Які питання обговорювали?\n"
            "• /ask 1d Підсумуй обговорення за день"
        )
        return
    
    # Try to extract time period from the beginning
    time_period_str = None
    user_query = query_part
    minutes = 60  # Default to 1 hour
    
    # Check if the query starts with a time period pattern
    # Match pattern: number followed by m/h/d and space
    time_match = re.match(r'^(\d+[mhd])\s+(.+)$', query_part, re.IGNORECASE)
    if time_match:
        time_period_str = time_match.group(1)
        user_query = time_match.group(2)
        try:
            minutes = parse_time_period(time_period_str)
        except ValueError as e:
            await update.message.reply_text(
                f"Неправильний формат часу: {time_period_str}\n"
                f"Використовуйте формат: [число][m/h/d] (наприклад: 30m, 2h, 1d)"
            )
            return
    else:
        # No time period specified, use default
        time_period_str = '1h'
        user_query = query_part
    
    try:
        logging.info(f"[query_handler] Processing query for chat_id={chat_id}, period={time_period_str}, query='{user_query}'")
        
        # Get chat history for the specified period
        messages = db_service.get_chat_messages_by_period(
            chat_id=chat_id, 
            minutes=minutes, 
            exclude_bots=True
        )
        
        if not messages:
            await update.message.reply_text(
                f"За останні {time_period_str} не знайдено повідомлень в цьому чаті."
            )
            return
        
        # Format history for the prompt
        history_text = ""
        for msg in messages:
            history_text += f"Автор: {msg['from_user']}\n"
            history_text += f"Час: {msg['created_at']}\n"
            history_text += f"Повідомлення: {msg['text']}\n"
            history_text += "---\n"
        
        # Create the prompt
        prompt = QUERY_PROMPT_TEMPLATE.format(
            history=history_text,
            user_query=user_query
        )
        
        if IS_DEBUG:
            print(f"[query_handler] Sending prompt to LLM: {prompt[:200]}...")
        
        # Get response from LLM
        response = invoke_model(prompt, model=HISTORY_ANALYSIS_MODEL)
        
        # Send response to user
        response_text = f"📊 Аналіз за останні {time_period_str}:\n\n{response}"
        await update.message.reply_text(response_text)
        
        if IS_DEBUG:
            print(f"[query_handler] Response sent: {response[:100]}...")
        
    except Exception as e:
        logging.error(f"[query_handler] Error processing query: {e}")
        await update.message.reply_text(
            "Вибачте, сталася помилка при обробці вашого запиту. Спробуйте пізніше."
        )
