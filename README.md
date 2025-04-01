# HaikuBot

A Telegram bot that generates haikus based on chat messages and stores message history in Supabase.

## Setup

1. Clone this repository
2. Install dependencies with Poetry:
   ```
   poetry install
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file with your Telegram token, OpenAI API key, and Supabase credentials.

4. Initialize the database:
   ```
   poetry run init-db
   ```

5. Run the bot:
   ```
   poetry run start-bot
   ```

## Features

- Listens to messages in Telegram chats
- Stores message history in Supabase database
- Generates haikus after collecting a specified number of messages
- Provides chat analysis with the `/analyze` command

## DB Migrations
supabase link --project-ref [project-id]
supabase migration create [migration-name]
supabase db push

## Deploy
Reilway
