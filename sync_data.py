import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def get_supabase_client(is_prod: bool = False) -> Client:
    """
    Get Supabase client for either production or development environment
    
    Args:
        is_prod: If True, returns production client, otherwise development client
        
    Returns:
        Supabase client instance
    """
    if is_prod:
        url = os.getenv('SUPABASE_URL_PROD')
        key = os.getenv('SUPABASE_KEY_PROD')
    else:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
    if not url or not key:
        raise ValueError(f"Missing {'production' if is_prod else 'development'} database credentials")
        
    return create_client(url, key)

def sync_data(days_back: int = 30) -> None:
    """
    Sync data from production to development database for the specified time period
    
    Args:
        days_back: Number of days to look back for data sync (default: 30)
    """
    # Initialize clients
    prod_client = get_supabase_client(is_prod=True)
    dev_client = get_supabase_client(is_prod=False)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Sync users
    sync_users(prod_client, dev_client, start_date, end_date)
    
    # Sync messages
    sync_messages(prod_client, dev_client, start_date, end_date)
    
    print(f"Data sync completed for period: {start_date} to {end_date}")

def sync_users(prod_client: Client, dev_client: Client, 
              start_date: datetime, end_date: datetime) -> None:
    """
    Sync users from production to development database
    
    Args:
        prod_client: Production Supabase client
        dev_client: Development Supabase client
        start_date: Start date for filtering
        end_date: End date for filtering
    """
    # Get users from production
    prod_users = prod_client.table("users") \
        .select("*") \
        .gte("created_at", start_date.isoformat()) \
        .lte("created_at", end_date.isoformat()) \
        .execute()
    
    if not prod_users.data:
        print("No users found to sync")
        return
        
    # Insert users into development
    for user in prod_users.data:
        # Check if user already exists in dev
        existing_user = dev_client.table("users") \
            .select("*") \
            .eq("user_id", user["user_id"]) \
            .execute()
            
        if not existing_user.data:
            dev_client.table("users").insert(user).execute()
            print(f"Synced user: {user['user_id']}")
        else:
            print(f"User already exists: {user['user_id']}")

def sync_messages(prod_client: Client, dev_client: Client,
                 start_date: datetime, end_date: datetime) -> None:
    """
    Sync messages from production to development database
    
    Args:
        prod_client: Production Supabase client
        dev_client: Development Supabase client
        start_date: Start date for filtering
        end_date: End date for filtering
    """
    # Get messages from production
    prod_messages = prod_client.table("messages") \
        .select("*") \
        .gte("created_at", start_date.isoformat()) \
        .lte("created_at", end_date.isoformat()) \
        .execute()
    
    if not prod_messages.data:
        print("No messages found to sync")
        return
        
    # Insert messages into development
    for message in prod_messages.data:
        # Check if message already exists in dev
        existing_message = dev_client.table("messages") \
            .select("*") \
            .eq("id", message["id"]) \
            .execute()
            
        if not existing_message.data:
            dev_client.table("messages").insert(message).execute()
            print(f"Synced message: {message['id']}")
        else:
            print(f"Message already exists: {message['id']}")

def main():
    """
    Main entry point for the database synchronization script.
    Parses command line arguments and runs the sync operation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync data from production to development database")
    parser.add_argument("--days", type=int, default=30,
                      help="Number of days to look back for data sync (default: 30)")
    
    args = parser.parse_args()
    sync_data(args.days)

if __name__ == "__main__":
    main() 