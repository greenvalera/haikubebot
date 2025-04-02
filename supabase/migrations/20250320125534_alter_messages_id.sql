-- Alter messages table id column to BIGSERIAL while preserving data
BEGIN;

-- Create a temporary sequence
CREATE SEQUENCE IF NOT EXISTS messages_id_seq;

-- Set the sequence to the maximum id value
SELECT setval('messages_id_seq', COALESCE((SELECT MAX(id) FROM messages), 0) + 1, false);

-- Alter the id column
ALTER TABLE messages 
    ALTER COLUMN id TYPE BIGINT,
    ALTER COLUMN id SET DEFAULT nextval('messages_id_seq'),
    ALTER COLUMN id SET NOT NULL;

-- Make the sequence owned by the id column
ALTER SEQUENCE messages_id_seq OWNED BY messages.id;

COMMIT; 