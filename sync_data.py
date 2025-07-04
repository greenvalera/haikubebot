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

def clear_dev_tables(dev_client: Client) -> None:
    """
    Clear development database tables (messages first due to foreign key constraints)
    
    Args:
        dev_client: Development Supabase client
    """
    print("Clearing development database tables...")
    
    # Clear messages first (due to foreign key constraint)
    dev_client.table("messages").delete().neq("id", 0).execute()
    print("Cleared messages table")
    
    # Then clear users
    dev_client.table("users").delete().neq("id", 0).execute()
    print("Cleared users table")

def sync_data(days_back: int = 30, clear_tables: bool = False) -> None:
    """
    Sync data from production to development database for the specified time period
    
    Args:
        days_back: Number of days to look back for data sync (default: 30)
        clear_tables: If True, clear development tables before sync (default: False)
    """
    # Initialize clients
    prod_client = get_supabase_client(is_prod=True)
    dev_client = get_supabase_client(is_prod=False)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Clear tables if requested
    if clear_tables:
        clear_dev_tables(dev_client)
    
    # Sync users created within the date range
    sync_users(prod_client, dev_client, start_date, end_date, skip_existing_check=clear_tables)
    
    # Sync messages (will automatically sync any referenced users that don't exist)
    sync_messages(prod_client, dev_client, start_date, end_date, skip_existing_check=clear_tables)
    
    print(f"Data sync completed for period: {start_date} to {end_date}")

def sync_users(prod_client: Client, dev_client: Client, 
              start_date: datetime, end_date: datetime, skip_existing_check: bool = False) -> None:
    """
    Sync users from production to development database
    
    Args:
        prod_client: Production Supabase client
        dev_client: Development Supabase client
        start_date: Start date for filtering
        end_date: End date for filtering
        skip_existing_check: If True, skip checking for existing records
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
        if skip_existing_check:
            # Skip existing check if tables were cleared
            dev_client.table("users").insert(user).execute()
            print(f"Synced user: {user['user_id']}")
        else:
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

def sync_user_if_needed(prod_client: Client, dev_client: Client, user_id: int) -> None:
    """
    Sync a specific user from production to development if they don't exist
    
    Args:
        prod_client: Production Supabase client
        dev_client: Development Supabase client
        user_id: The user ID to check and sync if needed
    """
    # Check if user exists in dev database
    existing_user = dev_client.table("users") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute()
        
    if not existing_user.data:
        # User doesn't exist, fetch from production and sync
        prod_user = prod_client.table("users") \
            .select("*") \
            .eq("user_id", user_id) \
            .execute()
            
        if prod_user.data:
            dev_client.table("users").insert(prod_user.data[0]).execute()
            print(f"Synced user (referenced by message): {user_id}")
        else:
            print(f"Warning: User {user_id} not found in production database")

def sync_messages(prod_client: Client, dev_client: Client,
                 start_date: datetime, end_date: datetime, skip_existing_check: bool = False) -> None:
    """
    Sync messages from production to development database
    
    Args:
        prod_client: Production Supabase client
        dev_client: Development Supabase client
        start_date: Start date for filtering
        end_date: End date for filtering
        skip_existing_check: If True, skip checking for existing records
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
        if skip_existing_check:
            # Skip existing check if tables were cleared
            # Ensure the user exists before inserting the message
            sync_user_if_needed(prod_client, dev_client, message["user_id"])
            
            dev_client.table("messages").insert(message).execute()
            print(f"Synced message: {message['id']}")
        else:
            # Check if message already exists in dev
            existing_message = dev_client.table("messages") \
                .select("*") \
                .eq("id", message["id"]) \
                .execute()
                
            if not existing_message.data:
                # Ensure the user exists before inserting the message
                sync_user_if_needed(prod_client, dev_client, message["user_id"])
                
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
    parser.add_argument("--clear", action="store_true",
                      help="Clear development tables before sync (default: False)")
    
    args = parser.parse_args()
    sync_data(args.days, args.clear)

if __name__ == "__main__":
    main() 