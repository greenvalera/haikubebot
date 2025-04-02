-- Add foreign key constraint between messages and users tables
ALTER TABLE messages
ADD CONSTRAINT messages_user_id_fkey
FOREIGN KEY (user_id)
REFERENCES users(user_id)
ON DELETE CASCADE; 