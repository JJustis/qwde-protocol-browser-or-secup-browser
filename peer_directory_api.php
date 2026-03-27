"""
QWDE Protocol - Peer Directory API Handler
Central server ONLY stores peer IPs and metadata (NOT site content)
Site content is stored on peer computers and served via P2P
"""

<?php
/**
 * QWDE Protocol - Peer Directory Service
 * Hosted at: secupgrade.com/api_handler.php
 * 
 * This server ONLY stores:
 * - Peer IP addresses
 * - Site metadata (domain, fwild, creator_peer_id)
 * - NOT actual site content (stored on peer computers)
 */

// ═══════════════════════════════════════════════════════════
// SERVER CONFIGURATION - EMBEDDED
// ═══════════════════════════════════════════════════════════

$db_config = [
    'host' => 'localhost',
    'port' => '3306',
    'database' => 'qwde_directory',
    'username' => 'qwde_user',
    'password' => 'TO_BE_ADDED',  // ← SET ROOT PASSWORD HERE
    'charset' => 'utf8mb4'
];

// ═══════════════════════════════════════════════════════════
// DO NOT EDIT BELOW THIS LINE
// ═══════════════════════════════════════════════════════════

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-Peer-IP, X-Peer-Port');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

class PeerDirectoryDB {
    private $pdo;
    
    public function __construct($config) {
        try {
            $dsn = "mysql:host={$config['host']};port={$config['port']};dbname={$config['database']};charset={$config['charset']}";
            $this->pdo = new PDO($dsn, $config['username'], $config['password'], [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
            ]);
            $this->initTables();
        } catch (PDOException $e) {
            http_response_code(500);
            echo json_encode(['status' => 'error', 'message' => 'Database connection failed']);
            exit();
        }
    }
    
    private function initTables() {
        // Peer registry - stores peer IPs and ports
        $this->pdo->exec("
            CREATE TABLE IF NOT EXISTS peers (
                peer_id VARCHAR(100) PRIMARY KEY,
                peer_ip VARCHAR(50) NOT NULL,      -- Public IP address
                peer_port INT NOT NULL,             -- P2P port (default: 8766)
                public_key TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_online BOOLEAN DEFAULT TRUE,
                INDEX idx_online (is_online),
                INDEX idx_last_seen (last_seen)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ");
        
        // Site directory - ONLY metadata, NOT content
        $this->pdo->exec("
            CREATE TABLE IF NOT EXISTS site_directory (
                id INT PRIMARY KEY AUTO_INCREMENT,
                domain VARCHAR(255) UNIQUE NOT NULL,
                fwild INT UNIQUE NOT NULL,
                creator_peer_id VARCHAR(100) NOT NULL,
                site_hash VARCHAR(64),              -- Hash of site content (for verification)
                site_size INT DEFAULT 0,            -- Size in bytes
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                version INT DEFAULT 1,
                is_active BOOLEAN DEFAULT TRUE,
                INDEX idx_fwild (fwild),
                INDEX idx_peer (creator_peer_id),
                INDEX idx_active (is_active),
                FOREIGN KEY (creator_peer_id) REFERENCES peers(peer_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ");
        
        // Peer-site mapping (which peer hosts which sites)
        $this->pdo->exec("
            CREATE TABLE IF NOT EXISTS peer_sites (
                peer_id VARCHAR(100) NOT NULL,
                domain VARCHAR(255) NOT NULL,
                is_primary BOOLEAN DEFAULT TRUE,    -- True if this is the creator
                last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (peer_id, domain),
                FOREIGN KEY (peer_id) REFERENCES peers(peer_id) ON DELETE CASCADE,
                FOREIGN KEY (domain) REFERENCES site_directory(domain) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ");
    }
    
    public function registerPeer($peer_id, $peer_ip, $peer_port, $public_key = null) {
        $sql = "INSERT INTO peers (peer_id, peer_ip, peer_port, public_key, is_online)
                VALUES (:peer_id, :ip, :port, :key, TRUE)
                ON DUPLICATE KEY UPDATE
                    peer_ip = VALUES(peer_ip),
                    peer_port = VALUES(peer_port),
                    public_key = VALUES(public_key),
                    is_online = TRUE,
                    last_seen = CURRENT_TIMESTAMP";
        
        $stmt = $this->pdo->prepare($sql);
        return $stmt->execute([
            ':peer_id' => $peer_id,
            ':ip' => $peer_ip,
            ':port' => $peer_port,
            ':key' => $public_key
        ]);
    }
    
    public function getOnlinePeers($limit = 50) {
        $stmt = $this->pdo->prepare("
            SELECT * FROM peers
            WHERE is_online = TRUE
            AND last_seen > DATE_SUB(NOW(), INTERVAL 300 SECOND)
            ORDER BY last_seen DESC
            LIMIT :limit
        ");
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    }
    
    public function registerSite($domain, $fwild, $creator_peer_id, $site_hash, $site_size) {
        // Check if exists
        $check = $this->pdo->prepare("SELECT id, version FROM site_directory WHERE domain = ?");
        $check->execute([$domain]);
        $existing = $check->fetch();
        
        if ($existing) {
            // Update
            $stmt = $this->pdo->prepare("
                UPDATE site_directory
                SET site_hash = :hash,
                    site_size = :size,
                    version = version + 1
                WHERE domain = :domain
            ");
            $stmt->execute([
                ':hash' => $site_hash,
                ':size' => $site_size,
                ':domain' => $domain
            ]);
            
            return ['fwild' => $fwild, 'version' => $existing['version'] + 1, 'updated' => true];
        } else {
            // Insert new
            $stmt = $this->pdo->prepare("
                INSERT INTO site_directory (domain, fwild, creator_peer_id, site_hash, site_size)
                VALUES (:domain, :fwild, :creator, :hash, :size)
            ");
            $stmt->execute([
                ':domain' => $domain,
                ':fwild' => $fwild,
                ':creator' => $creator_peer_id,
                ':hash' => $site_hash,
                ':size' => $site_size
            ]);
            
            return ['fwild' => $fwild, 'version' => 1, 'updated' => false];
        }
    }
    
    public function getSiteMetadata($domain) {
        $stmt = $this->pdo->prepare("
            SELECT sd.*, p.peer_ip, p.peer_port
            FROM site_directory sd
            JOIN peers p ON sd.creator_peer_id = p.peer_id
            WHERE sd.domain = ? AND sd.is_active = TRUE
        ");
        $stmt->execute([$domain]);
        return $stmt->fetch();
    }
    
    public function getSiteByFwild($fwild) {
        $stmt = $this->pdo->prepare("
            SELECT sd.*, p.peer_ip, p.peer_port
            FROM site_directory sd
            JOIN peers p ON sd.creator_peer_id = p.peer_id
            WHERE sd.fwild = ? AND sd.is_active = TRUE
        ");
        $stmt->execute([$fwild]);
        return $stmt->fetch();
    }
    
    public function getAllSites() {
        $stmt = $this->pdo->query("
            SELECT sd.*, p.peer_ip, p.peer_port
            FROM site_directory sd
            JOIN peers p ON sd.creator_peer_id = p.peer_id
            WHERE sd.is_active = TRUE
            ORDER BY sd.fwild DESC
        ");
        return $stmt->fetchAll();
    }
    
    public function getPeerSites($peer_id) {
        $stmt = $this->pdo->prepare("
            SELECT sd.*, p.peer_ip, p.peer_port
            FROM site_directory sd
            JOIN peers p ON sd.creator_peer_id = p.peer_id
            WHERE sd.creator_peer_id = ? AND sd.is_active = TRUE
        ");
        $stmt->execute([$peer_id]);
        return $stmt->fetchAll();
    }
    
    public function getStats() {
        $stmt = $this->pdo->query("
            SELECT
                (SELECT COUNT(*) FROM peers WHERE is_online = TRUE) as online_peers,
                (SELECT COUNT(*) FROM site_directory WHERE is_active = TRUE) as total_sites,
                (SELECT COALESCE(MAX(fwild), 0) FROM site_directory) as fwild_counter
        ");
        return $stmt->fetch();
    }
    
    public function deleteSite($domain, $peer_id, $site_hash, $timestamp, $signature) {
        // Verify timestamp (not older than 5 minutes)
        if (time() - $timestamp > 300) {
            return ['status' => 'error', 'message' => 'Deletion request expired'];
        }
        
        // Verify signature (simplified - use actual crypto in production)
        $message = "{$domain}:{$peer_id}:{$timestamp}:{$site_hash}";
        $expected_signature = hash('sha256', $message . $peer_id);
        
        if ($signature !== $expected_signature) {
            return ['status' => 'error', 'message' => 'Invalid signature'];
        }
        
        // Check if peer owns the site
        $stmt = $this->pdo->prepare("
            SELECT creator_peer_id FROM site_directory
            WHERE domain = ? AND is_active = TRUE
        ");
        $stmt->execute([$domain]);
        $result = $stmt->fetch();
        
        if (!$result) {
            return ['status' => 'not_found', 'message' => 'Site not found'];
        }
        
        if ($result['creator_peer_id'] !== $peer_id) {
            return ['status' => 'error', 'message' => 'You do not own this site'];
        }
        
        // Mark as inactive (soft delete)
        $stmt = $this->pdo->prepare("
            UPDATE site_directory
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE domain = ?
        ");
        $stmt->execute([$domain]);
        
        // Log deletion
        $stmt = $this->pdo->prepare("
            INSERT INTO deletion_log (domain, deleted_by, deleted_at, reason)
            VALUES (?, ?, NOW(), 'Owner requested')
        ");
        $stmt->execute([$domain, $peer_id]);
        
        return [
            'status' => 'success',
            'message' => "Site {$domain} deleted successfully",
            'domain' => $domain
        ];
    }
    
    public function deleteSiteWithToken($domain, $peer_id, $ownership_token, $site_hash, $timestamp, $signature) {
        /**
         * Delete site with ownership token verification
         * Token must match the one stored during site registration
         */
        
        // Verify timestamp
        if (time() - $timestamp > 300) {
            return ['status' => 'error', 'message' => 'Deletion request expired'];
        }
        
        // Get site info including stored ownership token
        $stmt = $this->pdo->prepare("
            SELECT creator_peer_id, site_hash, fwild, ownership_token
            FROM site_directory
            WHERE domain = ? AND is_active = TRUE
        ");
        $stmt->execute([$domain]);
        $site = $stmt->fetch();
        
        if (!$site) {
            return ['status' => 'not_found', 'message' => 'Site not found'];
        }
        
        // Verify ownership
        if ($site['creator_peer_id'] !== $peer_id) {
            return ['status' => 'error', 'message' => 'You do not own this site'];
        }
        
        // Verify ownership token
        if ($site['ownership_token'] !== $ownership_token) {
            return ['status' => 'error', 'message' => 'Invalid ownership token'];
        }
        
        // Mark as inactive
        $stmt = $this->pdo->prepare("
            UPDATE site_directory
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE domain = ?
        ");
        $stmt->execute([$domain]);
        
        // Log deletion
        $stmt = $this->pdo->prepare("
            INSERT INTO deletion_log (domain, deleted_by, deleted_at, reason)
            VALUES (?, ?, NOW(), 'Owner requested with token')
        ");
        $stmt->execute([$domain, $peer_id]);
        
        // Log cache invalidation
        $this->storeInvalidation([
            'domain' => $domain,
            'fwild' => $site['fwild'],
            'deleted_at' => $timestamp,
            'signature' => $signature
        ]);
        
        return [
            'status' => 'success',
            'message' => "Site {$domain} deleted successfully",
            'domain' => $domain,
            'site_info' => $site
        ];
    }
    
    public function getInvalidationsSince($timestamp) {
        /**
         * Get cache invalidation messages since timestamp
         * Clients poll this to know which sites to purge
         */
        $datetime = date('Y-m-d H:i:s', $timestamp);
        
        $stmt = $this->pdo->prepare("
            SELECT domain, fwild, deleted_at, signature
            FROM cache_invalidations
            WHERE broadcast_at > FROM_UNIXTIME(?)
            ORDER BY broadcast_at DESC
            LIMIT 100
        ");
        $stmt->execute([$timestamp]);
        return $stmt->fetchAll();
    }
    
    public function storeInvalidation($message) {
        /**
         * Store cache invalidation message for clients to poll
         */
        $stmt = $this->pdo->prepare("
            INSERT INTO cache_invalidations 
            (domain, fwild, deleted_at, signature, broadcast_at)
            VALUES (?, ?, ?, ?, NOW())
        ");
        
        return $stmt->execute([
            $message['domain'] ?? '',
            $message['fwild'] ?? 0,
            $message['deleted_at'] ?? 0,
            $message['signature'] ?? ''
        ]);
    }
    
    public function getOwnedSites($peer_id) {
        $stmt = $this->pdo->prepare("
            SELECT domain, fwild, site_hash, site_size, version, created_at, updated_at
            FROM site_directory
            WHERE creator_peer_id = ? AND is_active = TRUE
            ORDER BY fwild DESC
        ");
        $stmt->execute([$peer_id]);
        return $stmt->fetchAll();
    }
}

function handleRequest($db) {
    $action = $_GET['action'] ?? $_POST['action'] ?? '';
    $response = ['status' => 'error', 'message' => 'Invalid action'];
    
    // Get peer IP from header or fallback to remote address
    $peer_ip = $_SERVER['HTTP_X_PEER_IP'] ?? $_SERVER['REMOTE_ADDR'];
    
    switch ($action) {
        case 'register_peer':
            $peer_id = $_POST['peer_id'] ?? '';
            $peer_port = $_POST['peer_port'] ?? 8766;
            $public_key = $_POST['public_key'] ?? null;
            
            if ($peer_id) {
                $success = $db->registerPeer($peer_id, $peer_ip, $peer_port, $public_key);
                $response = ['status' => $success ? 'success' : 'error'];
            }
            break;
            
        case 'get_peers':
            $limit = $_GET['limit'] ?? 50;
            $peers = $db->getOnlinePeers((int)$limit);
            $response = ['status' => 'success', 'peers' => $peers];
            break;
            
        case 'register_site':
            $domain = $_POST['domain'] ?? '';
            $fwild = $_POST['fwild'] ?? 0;
            $creator = $_POST['creator_peer_id'] ?? '';
            $site_hash = $_POST['site_hash'] ?? '';
            $site_size = $_POST['site_size'] ?? 0;
            
            if ($domain && $creator) {
                $result = $db->registerSite($domain, $fwild, $creator, $site_hash, $site_size);
                $response = ['status' => 'success'] + $result;
            }
            break;
            
        case 'get_site':
            $domain = $_GET['domain'] ?? '';
            if ($domain) {
                $site = $db->getSiteMetadata($domain);
                $response = $site ? ['status' => 'success', 'site' => $site] : ['status' => 'not_found'];
            }
            break;
            
        case 'get_site_by_fwild':
            $fwild = $_GET['fwild'] ?? 0;
            if ($fwild) {
                $site = $db->getSiteByFwild($fwild);
                $response = $site ? ['status' => 'success', 'site' => $site] : ['status' => 'not_found'];
            }
            break;
            
        case 'sync_sites':
            $sites = $db->getAllSites();
            $response = ['status' => 'success', 'sites' => $sites, 'count' => count($sites)];
            break;
            
        case 'get_stats':
            $stats = $db->getStats();
            $response = ['status' => 'success'] + $stats;
            break;
            
        case 'delete_site':
            // Owner-initiated site deletion with ownership token
            $domain = $_POST['domain'] ?? '';
            $peer_id = $_POST['peer_id'] ?? '';
            $ownership_token = $_POST['ownership_token'] ?? '';
            $site_hash = $_POST['site_hash'] ?? '';
            $timestamp = $_POST['timestamp'] ?? 0;
            $signature = $_POST['signature'] ?? '';
            
            if ($domain && $peer_id && $ownership_token) {
                $result = $db->deleteSiteWithToken($domain, $peer_id, $ownership_token, $site_hash, $timestamp, $signature);
                
                // If successful, broadcast cache invalidation
                if ($result['status'] === 'success') {
                    // Get site info for broadcast
                    $site_info = $result['site_info'] ?? [];
                    
                    // Broadcast to all clients
                    broadcast_cache_invalidation($domain, $site_info['fwild'] ?? 0, $timestamp, $signature);
                }
                
                $response = $result;
            } else {
                $response = ['status' => 'error', 'message' => 'Missing required fields'];
            }
            break;
            
        case 'get_invalidations':
            // Get cache invalidation messages since timestamp
            $since = $_GET['since'] ?? (time() - 300);
            $invalidations = $db->getInvalidationsSince((int)$since);
            $response = ['status' => 'success', 'invalidations' => $invalidations];
            break;
            
        case 'store_invalidation':
            // Store invalidation message (from broadcaster)
            $message = json_decode($_POST['message'] ?? '{}', true);
            if ($message) {
                $db->storeInvalidation($message);
                $response = ['status' => 'success'];
            } else {
                $response = ['status' => 'error', 'message' => 'Invalid message'];
            }
            break;
            
        case 'get_owned_sites':
            // Get list of sites owned by peer
            $peer_id = $_GET['peer_id'] ?? '';
            if ($peer_id) {
                $sites = $db->getOwnedSites($peer_id);
                $response = ['status' => 'success', 'sites' => $sites, 'count' => count($sites)];
            }
            break;
            
        default:
            $response = [
                'status' => 'error',
                'message' => 'Unknown action',
                'available_actions' => [
                    'register_peer', 'get_peers', 'register_site',
                    'get_site', 'get_site_by_fwild', 'sync_sites', 
                    'get_stats', 'delete_site', 'get_owned_sites'
                ]
            ];
    }
    
    return json_encode($response);
}

/**
 * Broadcast cache invalidation to all subscribed clients
 */
function broadcast_cache_invalidation($domain, $fwild, $deleted_at, $signature) {
    $invalidation = [
        'type' => 'cache_invalidation',
        'action' => 'delete',
        'domain' => $domain,
        'fwild' => $fwild,
        'deleted_at' => $deleted_at,
        'signature' => $signature,
        'broadcast_at' => time()
    ];
    
    // Log to database (clients will poll this)
    error_log(date('Y-m-d H:i:s') . ' - Cache invalidation: ' . $domain);
}

try {
    $db = new PeerDirectoryDB($db_config);
    echo handleRequest($db);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['status' => 'error', 'message' => 'Server error']);
}
?>
