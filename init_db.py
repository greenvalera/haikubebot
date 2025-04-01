#!/usr/bin/env python3
"""
Script to initialize Supabase database tables for HaikuBot
Creates users and messages tables if they don't exist
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv
from supabase import create_client, Client

def main():
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        sys.exit(1)
    
    print("Initializing database...")
    
    # We'll use direct HTTP requests to Supabase's REST API for table creation
    # since the Python client doesn't support raw SQL execution
    
    # REST API endpoint for SQL execution
    sql_url = f"{SUPABASE_URL}/rest/v1/sql"
    
    # Headers for API requests
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    try:
        # Create users table
        print("Creating users table...")
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Send the SQL command to the SQL endpoint
        response = requests.post(
            sql_url,
            headers=headers,
            json={"query": users_sql}
        )
        
        if response.status_code >= 400:
            print(f"Error creating users table: {response.status_code} - {response.text}")
            print("Trying to continue with table verification...")
        else:
            print("Users table SQL executed successfully.")
        
        # Create messages table
        print("Creating messages table...")
        messages_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Send the messages table SQL command
        response = requests.post(
            sql_url,
            headers=headers,
            json={"query": messages_sql}
        )
        
        if response.status_code >= 400:
            print(f"Error creating messages table: {response.status_code} - {response.text}")
            print("Trying to continue with additional SQL operations...")
        else:
            print("Messages table SQL executed successfully.")
        
        # Try to add foreign key (in a separate command)
        print("Setting up foreign key constraint...")
        fk_sql = """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'messages_user_id_fkey'
            ) THEN
                ALTER TABLE messages 
                ADD CONSTRAINT messages_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Foreign key might already exist or users table doesn't exist yet
            RAISE NOTICE 'Error adding foreign key: %', SQLERRM;
        END
        $$;
        """
        
        response = requests.post(
            sql_url,
            headers=headers,
            json={"query": fk_sql}
        )
        
        if response.status_code >= 400:
            print(f"Error setting up foreign key: {response.status_code} - {response.text}")
        else:
            print("Foreign key constraint setup complete.")
        
        # Create indexes
        print("Creating indexes...")
        indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
        CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
        CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
        """
        
        response = requests.post(
            sql_url,
            headers=headers,
            json={"query": indexes_sql}
        )
        
        if response.status_code >= 400:
            print(f"Error creating indexes: {response.status_code} - {response.text}")
        else:
            print("Indexes created successfully.")
        
        # Connect to Supabase to verify tables using the Python client
        print("Connecting to Supabase to verify tables...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Verify tables
        print("Verifying tables...")
        try:
            # Check users table
            users_result = supabase.table("users").select("*", count="exact").limit(1).execute()
            print(f"Users table verified. Row count: {users_result.count}")
            
            # Check messages table
            messages_result = supabase.table("messages").select("*", count="exact").limit(1).execute()
            print(f"Messages table verified. Row count: {messages_result.count}")
            
            print("Database initialization completed successfully!")
        except Exception as e:
            print(f"Error verifying tables: {e}")
            print("You may need to manually check the Supabase dashboard to verify the tables.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()