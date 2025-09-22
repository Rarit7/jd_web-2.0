-- Fix: Increase tg_group.name column length from 20 to 64 characters
-- This resolves the "Data too long for column 'name'" error when adding Telegram groups

ALTER TABLE tg_group MODIFY COLUMN name VARCHAR(64) NOT NULL DEFAULT '' COMMENT 'Telegram group username or identifier';