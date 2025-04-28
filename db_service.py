import os
import datetime
from supabase import create_client, Client
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Check if environment variables are set
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_or_create_user(user_id: int, username: str, first_name: str, 
                      last_name: Optional[str], is_bot: bool = False) -> Dict[str, Any]:
    """
    Get or create a user in the database
    
    Args:
        user_id: Telegram user ID
        username: Telegram username
        first_name: User's first name
        last_name: User's last name (can be None)
        
    Returns:
        Dictionary with the user data
    """
    # Check if user exists
    result = supabase.table("users").select("*").eq("user_id", user_id).execute()
    
    if result.data and len(result.data) > 0:
        # User exists, return the user data
        return result.data[0]
    
    # User doesn't exist, create new user
    now_iso = datetime.datetime.now().isoformat()
    user_data = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "created_at": now_iso,
        "last_activity": now_iso,
        "isBot": is_bot
    }
    
    try:
        # Try to insert or update the user (upsert)
        create_result = supabase.table("users").upsert(user_data, on_conflict=["user_id"]).execute()
        return create_result.data[0] if create_result.data else user_data
    except Exception as e:
        # If duplicate error or any other, try to fetch and return the user
        logging.warning(f"get_or_create_user: {e}, trying to fetch existing user")
        result = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        raise

def update_user_last_activity(user_id: int) -> None:
    """
    Update user's last activity timestamp
    
    Args:
        user_id: Telegram user ID
    """
    supabase.table("users").update({
        "last_activity": datetime.datetime.now().isoformat()
    }).eq("user_id", user_id).execute()

import json

def save_message(chat_id: int, user_id: int, text: str, haiku_source_ids: Optional[List[int]] = None, tg_id: Optional[int] = None) -> List[Dict[str, Any]]:
    # TODO: Якщо повідомлення містить повідомлення бота, зберігати серіалізовані id повідомлень, для яких воно згенероване, в окремому полі (наприклад, 'generated_for_message_ids')
    """
    Save a message to the database
    
    Args:
        chat_id: Telegram chat ID
        user_id: Telegram user ID
        text: Message text
        
    Returns:
        List containing the created message data
    """
    # Create message data object
    message_data = {
        "chat_id": chat_id,
        "user_id": user_id,
        "text": text,
        "created_at": datetime.datetime.now().isoformat()
    }
    if haiku_source_ids is not None:
        message_data["haiku_source_ids"] = json.dumps(haiku_source_ids)
    if tg_id is not None:
        message_data["tg_id"] = tg_id
    
    # Insert data into the messages table
    result = supabase.table("messages").insert(message_data).execute()
    
    # Return the result data (should be a list with the single created record)
    return result.data


def get_message_by_tg_id(tg_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single message by its Telegram message ID (tg_id)
    """
    result = supabase.table("messages").select("*").eq("tg_id", tg_id).single().execute()
    return result.data if result.data else None


def get_messages_by_ids(message_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Get multiple messages by their IDs (order preserved as in input list)
    """
    if not message_ids:
        return []
    # Supabase 'in_' operator expects a string of comma-separated values
    ids_str = ','.join(str(mid) for mid in message_ids)
    result = supabase.table("messages").select("*").in_("id", message_ids).execute()
    # Preserve order as in input list
    messages_by_id = {msg["id"]: msg for msg in result.data}
    return [messages_by_id[mid] for mid in message_ids if mid in messages_by_id]

def get_chat_messages(chat_id: int, limit: int = 100, before_message_id: int = None, exclude_bots: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieve messages for a specific chat from the database
    
    Args:
        chat_id: Telegram chat ID
        limit: Maximum number of messages to retrieve
        
    Returns:
        List of messages with user information in format:
        {
            'from_user': 'First Last',
            'text': 'message text',
            'created_at': 'ISO datetime string'
        }
    """
    # Get messages and join with users table using a subquery
    query = supabase.from_("messages") \
        .select("*, users!messages_user_id_fkey(first_name, last_name, isBot)") \
        .eq("chat_id", chat_id)
    if exclude_bots:
        query = query.eq("users.isBot", False)
    if before_message_id is not None:
        # Get created_at for before_message_id
        msg = supabase.from_("messages").select("created_at").eq("id", before_message_id).single().execute()
        logging.info(f"[get_chat_messages] before_message_id={before_message_id}, msg={msg}")
        if msg.data and msg.data.get("created_at"):
            before_created_at = msg.data["created_at"]
            query = query.lt("created_at", before_created_at)
    result = query.order("created_at", desc=True).limit(limit).execute()
    
    # Format the result to match the expected structure for haiku generation
    formatted_data = []
    for item in result.data:
        message = dict(item)
        msg_id = message.get('id')
        if "users" in message and message["users"]:
            user_data = message.pop("users")
            first_name = user_data.get("first_name", "")
            last_name = user_data.get("last_name", "")
            formatted_data.append({
                'id': msg_id,
                'from_user': f"{first_name} {last_name}".strip(),
                'text': message.get('text', ''),
                'created_at': message.get('created_at', '')
            })
    if not formatted_data:
        logging.info(f"No chat messages found for chat_id={chat_id} (get_chat_messages)")
        return []
    return formatted_data