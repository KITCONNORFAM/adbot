
-- Patch to add missing auto_join column
ALTER TABLE account_settings ADD COLUMN IF NOT EXISTS auto_join BOOLEAN NOT NULL DEFAULT FALSE;
