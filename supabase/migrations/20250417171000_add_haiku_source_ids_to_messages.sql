-- Migration: Add haiku_source_ids column to messages table
ALTER TABLE messages ADD COLUMN haiku_source_ids TEXT;
