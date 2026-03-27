-- ═══════════════════════════════════════════════════════════
-- QWDE Protocol - Complete Database Setup
-- Run this to create/recreate the central directory database
-- ═══════════════════════════════════════════════════════════
-- Usage: mysql -u root -p < setup_central_database.sql
-- ═══════════════════════════════════════════════════════════

-- Drop existing database if exists (for clean reinstall)
DROP DATABASE IF EXISTS qwde_directory;

-- Create fresh database
CREATE DATABASE IF NOT EXISTS qwde_directory
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;

-- Create user (update password as needed)
DROP USER IF EXISTS 'qwde_user'@'localhost';
CREATE USER 'qwde_user'@'localhost' IDENTIFIED BY 'qwde_secure_password_change_me';

-- Grant privileges
GRANT ALL PRIVILEGES ON qwde_directory.* TO 'qwde_user'@'localhost';
FLUSH PRIVILEGES;

-- Use the database
USE qwde_directory;

-- ═══════════════════════════════════════════════════════════
-- Peer Registry - Stores peer IPs and ports
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS peers (
    peer_id VARCHAR(100) PRIMARY KEY,
    peer_ip VARCHAR(50) NOT NULL,      -- Public IP address
    peer_port INT NOT NULL DEFAULT 8766,
    public_key TEXT,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_online BOOLEAN DEFAULT TRUE,
    INDEX idx_online (is_online),
    INDEX idx_last_seen (last_seen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ═══════════════════════════════════════════════════════════
-- Site Directory - ONLY metadata, NOT content
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS site_directory (
    id INT PRIMARY KEY AUTO_INCREMENT,
    domain VARCHAR(255) UNIQUE NOT NULL,
    fwild INT UNIQUE NOT NULL,
    creator_peer_id VARCHAR(100) NOT NULL,
    ownership_token VARCHAR(64),              -- Token for deletion verification
    site_hash VARCHAR(64),              -- SHA-256 hash for verification
    site_size INT DEFAULT 0,            -- Size in bytes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    version INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_fwild (fwild),
    INDEX idx_peer (creator_peer_id),
    INDEX idx_active (is_active),
    INDEX idx_hash (site_hash),
    INDEX idx_token (ownership_token),
    FOREIGN KEY (creator_peer_id) REFERENCES peers(peer_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ═══════════════════════════════════════════════════════════
-- Peer-Site Mapping (which peer hosts which sites)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS peer_sites (
    peer_id VARCHAR(100) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT TRUE,    -- True if this is the creator
    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (peer_id, domain),
    FOREIGN KEY (peer_id) REFERENCES peers(peer_id) ON DELETE CASCADE,
    FOREIGN KEY (domain) REFERENCES site_directory(domain) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ═══════════════════════════════════════════════════════════
-- Deletion Log (tracks deleted sites)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS deletion_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    domain VARCHAR(255) NOT NULL,
    deleted_by VARCHAR(100) NOT NULL,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    INDEX idx_domain (domain),
    INDEX idx_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ═══════════════════════════════════════════════════════════
-- Cache Invalidations (broadcasts to clients for cache purge)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS cache_invalidations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    domain VARCHAR(255) NOT NULL,
    fwild INT NOT NULL,
    deleted_at BIGINT NOT NULL,
    signature VARCHAR(64) NOT NULL,
    broadcast_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_domain (domain),
    INDEX idx_broadcast_at (broadcast_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ═══════════════════════════════════════════════════════════
-- System Statistics Table
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS system_stats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stat_name VARCHAR(100) UNIQUE NOT NULL,
    stat_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Initialize system stats
INSERT INTO system_stats (stat_name, stat_value) VALUES
    ('total_peers', '0'),
    ('total_sites', '0'),
    ('fwild_counter', '0'),
    ('last_sync', NOW())
ON DUPLICATE KEY UPDATE stat_name = stat_name;

-- ═══════════════════════════════════════════════════════════
-- Views for Quick Statistics
-- ═══════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW vw_stats AS
SELECT
    (SELECT COUNT(*) FROM peers WHERE is_online = TRUE) as online_peers,
    (SELECT COUNT(*) FROM peers) as total_peers,
    (SELECT COUNT(*) FROM site_directory WHERE is_active = TRUE) as total_sites,
    (SELECT COALESCE(MAX(fwild), 0) FROM site_directory) as fwild_counter,
    (SELECT stat_value FROM system_stats WHERE stat_name = 'last_sync') as last_sync;

-- ═══════════════════════════════════════════════════════════
-- Stored Procedure for Cleanup
-- ═══════════════════════════════════════════════════════════
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS cleanup_old_peers()
BEGIN
    -- Mark peers as offline if not seen in 10 minutes
    UPDATE peers
    SET is_online = FALSE
    WHERE last_seen < DATE_SUB(NOW(), INTERVAL 10 MINUTE);
    
    -- Update stats
    UPDATE system_stats
    SET stat_value = (SELECT COUNT(*) FROM peers WHERE is_online = TRUE)
    WHERE stat_name = 'total_peers';
    
    UPDATE system_stats
    SET stat_value = (SELECT COUNT(*) FROM site_directory WHERE is_active = TRUE)
    WHERE stat_name = 'total_sites';
    
    UPDATE system_stats
    SET stat_value = NOW()
    WHERE stat_name = 'last_sync';
END //
DELIMITER ;

-- ═══════════════════════════════════════════════════════════
-- Event for Automatic Cleanup (every 5 minutes)
-- ═══════════════════════════════════════════════════════════
SET @old_time_zone = @@time_zone;
SET time_zone = 'SYSTEM';

CREATE EVENT IF NOT EXISTS auto_cleanup
ON SCHEDULE EVERY 5 MINUTE
DO CALL cleanup_old_peers();

SET time_zone = @old_time_zone;

-- ═══════════════════════════════════════════════════════════
-- Test Queries (Uncomment to test)
-- ═══════════════════════════════════════════════════════════
-- SELECT 'Database setup complete!' as status;
-- SELECT * FROM vw_stats;
-- SHOW TABLES;

-- ═══════════════════════════════════════════════════════════
-- Verification
-- ═══════════════════════════════════════════════════════════
SELECT '✓ Database created: qwde_directory' as status;
SELECT '✓ User created: qwde_user' as status;
SELECT '✓ Tables created: peers, site_directory, peer_sites, system_stats' as status;
SELECT '✓ View created: vw_stats' as status;
SELECT '✓ Stored procedure created: cleanup_old_peers' as status;
SELECT '✓ Event created: auto_cleanup (every 5 minutes)' as status;
SELECT '✓ Ready for: peer_directory_api.php' as status;
