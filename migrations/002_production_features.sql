# Run this interactive migration (paste the whole block)
mysql -h localhost -u robot_console -p robot_console << 'EOF'

-- Check and add columns only if they don't exist
SET @db = DATABASE();

-- Add password_reset_token if missing
SET @col = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'users' AND COLUMN_NAME = 'password_reset_token');
SET @sql = IF(@col = 0, 
  'ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(500) NULL', 
  'SELECT "✓ password_reset_token exists" AS Status');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add password_reset_expires if missing
SET @col = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'users' AND COLUMN_NAME = 'password_reset_expires');
SET @sql = IF(@col = 0, 
  'ALTER TABLE users ADD COLUMN password_reset_expires DATETIME NULL', 
  'SELECT "✓ password_reset_expires exists" AS Status');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add last_login if missing
SET @col = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'users' AND COLUMN_NAME = 'last_login');
SET @sql = IF(@col = 0, 
  'ALTER TABLE users ADD COLUMN last_login DATETIME NULL', 
  'SELECT "✓ last_login exists" AS Status');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add last_activity if missing
SET @col = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'users' AND COLUMN_NAME = 'last_activity');
SET @sql = IF(@col = 0, 
  'ALTER TABLE users ADD COLUMN last_activity DATETIME NULL', 
  'SELECT "✓ last_activity exists" AS Status');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add login_count if missing
SET @col = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'users' AND COLUMN_NAME = 'login_count');
SET @sql = IF(@col = 0, 
  'ALTER TABLE users ADD COLUMN login_count INT DEFAULT 0', 
  'SELECT "✓ login_count exists" AS Status');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add indexes (ignore errors if exist)
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_password_reset_token ON users(password_reset_token);
CREATE INDEX idx_users_last_activity ON users(last_activity);

-- Clean up demo/test data
DELETE FROM users WHERE email IN ('demo@user.com', 'admin@demo.com');
DELETE FROM users WHERE id < 0;
DELETE FROM users WHERE email LIKE '%@example.com%';
DELETE FROM users WHERE email LIKE '%demo%' AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
DELETE FROM users WHERE email LIKE '%test%' AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);

-- Activate existing legitimate users
UPDATE users 
SET is_active = 1, email_confirmed_at = NOW() 
WHERE (is_active IS NULL OR is_active = 0)
  AND email NOT LIKE '%@example.com%'
  AND email NOT LIKE '%demo%'
  AND email NOT LIKE '%test%'
  AND id > 0;

-- Initialize activity tracking
UPDATE users SET last_activity = created_at WHERE last_activity IS NULL;
UPDATE users SET login_count = 0 WHERE login_count IS NULL;

-- Show final schema
SELECT 'Migration completed! Column summary:' AS Info;
SELECT 
  COUNT(*) as total_columns,
  SUM(CASE WHEN COLUMN_NAME IN ('password_reset_token','password_reset_expires','last_login','last_activity','login_count') THEN 1 ELSE 0 END) as new_columns
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users';

-- Show user statistics
SELECT 'User statistics:' AS Info;
SELECT 
  COUNT(*) as total_users,
  SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users,
  SUM(CASE WHEN email LIKE '%demo%' OR email LIKE '%test%' THEN 1 ELSE 0 END) as demo_test_users
FROM users;

EOF
