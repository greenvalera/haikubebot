-- Додає поле tg_id (Telegram message id) у таблицю messages
ALTER TABLE messages ADD COLUMN tg_id BIGINT;
-- Якщо потрібно, можна додати індекс для швидкого пошуку
CREATE INDEX IF NOT EXISTS messages_tg_id_idx ON messages (tg_id);
