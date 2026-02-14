-- Database Migration for Production-Ready Authentication System
-- Run this migration after deploying the new authentication code

-- Add password reset token support (optional - using token service instead)
-- These columns can be used for database-based token storage if needed in the future
-- ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(500) NULL;
-- ALTER TABLE users ADD COLUMN password_reset_expires DATETIME NULL;

-- Ensure existing users are activated (one-time migration for existing non-demo users)
-- This helps transition existing users to the new email confirmation system
UPDATE users 
SET is_active = 1, email_confirmed_at = NOW() 
WHERE (is_active IS NULL OR is_active = 0) 
  AND email NOT LIKE '%@example.com' 
  AND email NOT LIKE '%demo%'
  AND email NOT LIKE '%test%'
  AND id > 0;

-- Remove demo users if they exist
DELETE FROM users WHERE email IN ('demo@user.com', 'admin@demo.com');
DELETE FROM users WHERE id < 0;  -- Negative IDs were used for demo users

-- Remove any orphaned data from demo users
DELETE FROM bookings WHERE user_id < 0;
DELETE FROM sessions WHERE user_id < 0;

-- Verify the migration
SELECT 
  COUNT(*) as total_users,
  SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users,
  SUM(CASE WHEN email_confirmed_at IS NOT NULL THEN 1 ELSE 0 END) as confirmed_users,
  SUM(CASE WHEN google_id IS NOT NULL THEN 1 ELSE 0 END) as google_users
FROM users;

-- Show all users after migration
SELECT 
  id, 
  name, 
  email, 
  role, 
  is_active, 
  email_confirmed_at,
  google_id IS NOT NULL as has_google_auth,
  created_at
FROM users
ORDER BY id;
