-- Migration: Add isBot column to users table
ALTER TABLE users ADD COLUMN "isBot" BOOLEAN DEFAULT FALSE;
