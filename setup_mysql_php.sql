-- QWDE Protocol - MySQL Database Setup for PHP Backend
-- Run this on your MySQL server to set up the central database
-- Usage: mysql -u root -p < setup_mysql_php.sql

-- Create database
CREATE DATABASE IF NOT EXISTS qwde_ddns 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

-- Create user (CHANGE PASSWORD IN PRODUCTION!)
CREATE USER IF NOT EXISTS 'qwde_user'@'%' IDENTIFIED BY 'qwde_secure_password_change_me';

-- Grant privileges
GRANT ALL PRIVILEGES ON qwde_ddns.* TO 'qwde_user'@'%';
FLUSH PRIVILEGES;

-- Use the database
USE qwde_ddns;

-- Sites table - stores encrypted site data
CREATE TABLE IF NOT EXISTS sites (
    id INT PRIMARY KEY AUTO_INCREMENT,
    domain VARCHAR(255) UNIQUE NOT NULL,
    fwild INT UNIQUE NOT NULL,
    creator_peer_id VARCHAR(100) NOT NULL,
    site_data_encrypted LONGBLOB NOT NULL,
    encryption_metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_fwild (fwild),
    INDEX idx_created (created_at DESC),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Peers table
CREATE TABLE IF NOT EXISTS peers (
    peer_id VARCHAR(100) PRIMARY KEY,
    host VARCHAR(50) NOT NULL,
    port INT NOT NULL,
    public_key TEXT,
    sites JSON,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_last_seen (last_seen),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Sites poll log for 30-second polling
-- This table logs all site changes for efficient polling
CREATE TABLE IF NOT EXISTS sites_poll_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    site_id INT NOT NULL,
    domain VARCHAR(255) NOT NULL,
    fwild INT NOT NULL,
    action ENUM('create', 'update', 'delete') DEFAULT 'create',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created (created_at DESC),
    INDEX idx_site (site_id),
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Peer keys registry for encryption key exchange
CREATE TABLE IF NOT EXISTS peer_keys (
    id INT PRIMARY KEY AUTO_INCREMENT,
    peer_id VARCHAR(100) NOT NULL,
    key_type VARCHAR(50) NOT NULL,
    key_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_peer (peer_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- System stats table
CREATE TABLE IF NOT EXISTS system_stats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stat_name VARCHAR(100) UNIQUE NOT NULL,
    stat_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Initialize system stats
INSERT INTO system_stats (stat_name, stat_value) VALUES 
    ('total_sites', '0'),
    ('total_peers', '0'),
    ('fwild_counter', '0'),
    ('last_poll_time', NOW())
ON DUPLICATE KEY UPDATE stat_name = stat_name;

-- Create view for quick stats
CREATE OR REPLACE VIEW vw_stats AS
SELECT 
    (SELECT COUNT(*) FROM peers WHERE is_active = TRUE) as total_peers,
    (SELECT COUNT(*) FROM peers WHERE is_active = TRUE AND last_seen > DATE_SUB(NOW(), INTERVAL 300 SECOND)) as live_peers,
    (SELECT COUNT(*) FROM sites WHERE is_active = TRUE) as total_sites,
    (SELECT AUTO_INCREMENT - 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'qwde_ddns' AND TABLE_NAME = 'sites') as fwild_counter,
    (SELECT stat_value FROM system_stats WHERE stat_name = 'last_poll_time') as last_poll_time;

-- Create stored procedure for cleanup (optional - can be called periodically)
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS cleanup_old_data()
BEGIN
    -- Mark old peers as inactive
    UPDATE peers 
    SET is_active = FALSE 
    WHERE last_seen < DATE_SUB(NOW(), INTERVAL 600 SECOND);
    
    -- Clean up old poll log entries (keep last 1000)
    DELETE FROM sites_poll_log 
    WHERE id NOT IN (
        SELECT id FROM (
            SELECT id FROM sites_poll_log 
            ORDER BY created_at DESC 
            LIMIT 1000
        ) temp
    );
    
    -- Clean up expired keys
    DELETE FROM peer_keys 
    WHERE expires_at IS NOT NULL 
    AND expires_at < NOW();
    
    -- Update stats
    UPDATE system_stats SET stat_value = (SELECT COUNT(*) FROM sites WHERE is_active = TRUE) WHERE stat_name = 'total_sites';
    UPDATE system_stats SET stat_value = (SELECT COUNT(*) FROM peers WHERE is_active = TRUE) WHERE stat_name = 'total_peers';
    UPDATE system_stats SET stat_value = (SELECT COALESCE(MAX(fwild), 0) FROM sites) WHERE stat_name = 'fwild_counter';
    UPDATE system_stats SET stat_value = NOW() WHERE stat_name = 'last_poll_time';
END //
DELIMITER ;

-- Create event for automatic cleanup every 5 minutes (optional)
SET @old_time_zone = @@time_zone;
SET time_zone = 'SYSTEM';

CREATE EVENT IF NOT EXISTS auto_cleanup
ON SCHEDULE EVERY 5 MINUTE
DO CALL cleanup_old_data();

SET time_zone = @old_time_zone;

-- Test queries
SELECT 'Database setup complete!' as status;
SELECT * FROM vw_stats;

-- Show table structure
SHOW TABLES;
