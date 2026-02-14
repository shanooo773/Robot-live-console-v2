-- Migration 002: Production Features
-- This migration adds all production-ready authentication features
-- Run this migration after deploying the updated codebase

-- Part 1: Add new columns for password reset
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(500) NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_expires DATETIME NULL;

-- Part 2: Add new columns for user activity tracking
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login DATETIME NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity DATETIME NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS login_count INT DEFAULT 0;

-- Part 3: Add Google OAuth column if not exists
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255) NULL;

-- Part 4: Add email confirmation columns if not exists
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_confirmed_at DATETIME NULL;

-- Part 5: Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_password_reset_token ON users(password_reset_token);
CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Part 6: Clean up demo/test data (IMPORTANT: Run this in production)
DELETE FROM users WHERE email IN ('demo@user.com', 'admin@demo.com');
DELETE FROM users WHERE id < 0;
DELETE FROM users WHERE email LIKE '%@example.com%';
DELETE FROM users WHERE email LIKE '%demo%test%' AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);

-- Part 7: Activate existing legitimate users (one-time migration)
-- This is for existing users who were created before email confirmation was required
UPDATE users 
SET is_active = 1, email_confirmed_at = NOW() 
WHERE (is_active IS NULL OR is_active = 0)
  AND email NOT LIKE '%@example.com%'
  AND email NOT LIKE '%demo%'
  AND email NOT LIKE '%test%'
  AND id > 0;

-- Part 8: Initialize activity tracking for existing users
UPDATE users SET last_activity = created_at WHERE last_activity IS NULL;
UPDATE users SET login_count = 0 WHERE login_count IS NULL;

-- Part 9: Ensure created_at has default if missing
ALTER TABLE users MODIFY COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
