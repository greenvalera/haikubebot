import os
import datetime
from supabase import create_client, Client
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
                      last_name: Optional[str]) -> Dict[str, Any]:
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
        "last_activity": now_iso
    }
    
    create_result = supabase.table("users").insert(user_data).execute()
    return create_result.data[0] if create_result.data else user_data

def update_user_last_activity(user_id: int) -> None:
    """
    Update user's last activity timestamp
    
    Args:
        user_id: Telegram user ID
    """
    supabase.table("users").update({
        "last_activity": datetime.datetime.now().isoformat()
    }).eq("user_id", user_id).execute()

def save_message(chat_id: int, user_id: int, text: str) -> List[Dict[str, Any]]:
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
    
    # Insert data into the messages table
    result = supabase.table("messages").insert(message_data).execute()
    
    # Return the result data (should be a list with the single created record)
    return result.data

def get_chat_messages(chat_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve messages for a specific chat from the database
    
    Args:
        chat_id: Telegram chat ID
        limit: Maximum number of messages to retrieve
        
    Returns:
        List of messages with user information
    """
    # Join with users table to get user information alongside messages
    result = supabase.from_("messages") \
        .select("*, users!inner(first_name, last_name)") \
        .eq("chat_id", chat_id) \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    
    # Format the result to have first_name and last_name at the top level
    # since the new API returns nested objects
    formatted_data = []
    for item in result.data:
        message = dict(item)
        if "users" in message and message["users"]:
            user_data = message.pop("users")
            message["first_name"] = user_data.get("first_name", "")
            message["last_name"] = user_data.get("last_name", "")
        formatted_data.append(message)
    
    return formatted_data

def get_user_messages(user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve messages for a specific user from the database
    
    Args:
        user_id: Telegram user ID
        limit: Maximum number of messages to retrieve
        
    Returns:
        List of messages
    """
    result = supabase.from_("messages") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    
    return result.data