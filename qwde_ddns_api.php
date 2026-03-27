<?php
/**
 * QWDE Protocol - Central DDNS PHP Server
 * Handles encrypted site storage and peer coordination
 * 
 * This PHP script acts as a storage layer for the QWDE protocol.
 * All data is stored encrypted and the system polls every 30 seconds
 * for new registered sites.
 * 
 * Place on: secupgrade.com/qwde_ddns_api.php
 * Or localhost for testing
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-QWDE-Peer-ID, X-QWDE-Signature');

// Handle preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Configuration - Update for secupgrade.com
$config = [
    'database' => [
        'host' => 'localhost',
        'port' => '3306',
        'name' => 'qwde_ddns',
        'user' => 'qwde_user',
        'pass' => 'qwde_secure_password_here'
    ],
    'settings' => [
        'polling_interval' => 30,  // Query every 30 seconds for new sites
        'peer_timeout' => 300,      // Peer considered dead after 5 minutes
        'max_peers' => 100,
        'max_sites_per_request' => 1000
    ]
];

// Load external config if exists
if (file_exists(__DIR__ . '/qwde_config.php')) {
    $config = array_merge_recursive($config, require __DIR__ . '/qwde_config.php');
}

/**
 * Database handler for QWDE DDNS
 */
class QWDEDatabase {
    private $pdo;
    private $config;
    
    public function __construct($config) {
        $this->config = $config;
        $this->connect();
        $this->createTables();
        $this->startPolling();
    }
    
    private function connect() {
        try {
            $dsn = "mysql:host={$this->config['host']};port={$this->config['port']};dbname={$this->config['name']};charset=utf8mb4";
            $this->pdo = new PDO($dsn, $this->config['user'], $this->config['pass'], [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false
            ]);
        } catch (PDOException $e) {
            $this->errorResponse("Database connection failed: " . $e->getMessage());
        }
    }
    
    private function createTables() {
        // Sites table - stores encrypted site data
        $this->pdo->exec("
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ");
        
        // Peers table
        $this->pdo->exec("
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ");
        
        // New sites log for 30-second polling
        $this->pdo->exec("
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ");
        
        // Encryption keys registry (for peer-to-peer key exchange coordination)
        $this->pdo->exec("
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ");
        
        // System stats table
        $this->pdo->exec("
            CREATE TABLE IF NOT EXISTS system_stats (
                id INT PRIMARY KEY AUTO_INCREMENT,
                stat_name VARCHAR(100) UNIQUE NOT NULL,
                stat_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ");
        
        // Initialize stats
        $this->pdo->exec("
            INSERT INTO system_stats (stat_name, stat_value) VALUES 
            ('total_sites', '0'),
            ('total_peers', '0'),
            ('fwild_counter', '0'),
            ('last_poll_time', NOW())
            ON DUPLICATE KEY UPDATE stat_name = stat_name
        ");
    }
    
    /**
     * Start background polling for new sites (every 30 seconds)
     * This runs on each request to ensure continuous monitoring
     */
    private function startPolling() {
        $interval = $this->config['settings']['polling_interval'];
        
        // Update last poll time
        $this->pdo->prepare("UPDATE system_stats SET stat_value = NOW() WHERE stat_name = 'last_poll_time'")
            ->execute();
        
        // Cleanup old peers
        $this->pdo->prepare("
            UPDATE peers SET is_active = FALSE 
            WHERE last_seen < DATE_SUB(NOW(), INTERVAL {$this->config['settings']['peer_timeout']} SECOND)
        ")->execute();
        
        // Update stats
        $this->updateStats();
    }
    
    private function updateStats() {
        $stats = [
            'total_sites' => $this->pdo->query("SELECT COUNT(*) FROM sites WHERE is_active = TRUE")->fetchColumn(),
            'total_peers' => $this->pdo->query("SELECT COUNT(*) FROM peers WHERE is_active = TRUE")->fetchColumn(),
            'fwild_counter' => $this->pdo->query("SELECT COALESCE(MAX(fwild), 0) FROM sites")->fetchColumn()
        ];
        
        foreach ($stats as $name => $value) {
            $this->pdo->prepare("UPDATE system_stats SET stat_value = ? WHERE stat_name = ?")
                ->execute([$value, $name]);
        }
    }
    
    public function registerPeer($peer_id, $host, $port, $public_key = null, $sites = []) {
        $sql = "INSERT INTO peers (peer_id, host, port, public_key, sites, is_active) 
                VALUES (:peer_id, :host, :port, :key, :sites, TRUE)
                ON DUPLICATE KEY UPDATE 
                    host = VALUES(host),
                    port = VALUES(port),
                    public_key = VALUES(public_key),
                    sites = VALUES(sites),
                    is_active = TRUE,
                    last_seen = CURRENT_TIMESTAMP";
        
        $stmt = $this->pdo->prepare($sql);
        return $stmt->execute([
            ':peer_id' => $peer_id,
            ':host' => $host,
            ':port' => $port,
            ':key' => $public_key,
            ':sites' => json_encode($sites)
        ]);
    }
    
    public function getActivePeers($limit = 10) {
        $stmt = $this->pdo->prepare("
            SELECT * FROM peers 
            WHERE is_active = TRUE 
            AND last_seen > DATE_SUB(NOW(), INTERVAL {$this->config['settings']['peer_timeout']} SECOND)
            ORDER BY last_seen DESC 
            LIMIT :limit
        ");
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->execute();
        
        $peers = $stmt->fetchAll();
        foreach ($peers as &$peer) {
            $peer['sites'] = json_decode($peer['sites'] ?? '[]', true);
            $peer['last_seen'] = strtotime($peer['last_seen']);
        }
        return $peers;
    }
    
    public function registerSite($domain, $creator_peer_id, $encrypted_data, $metadata = []) {
        // Check if exists
        $check = $this->pdo->prepare("SELECT id, version, fwild FROM sites WHERE domain = ?");
        $check->execute([$domain]);
        $existing = $check->fetch();
        
        if ($existing) {
            // Update existing
            $stmt = $this->pdo->prepare("
                UPDATE sites 
                SET site_data_encrypted = :data,
                    encryption_metadata = :meta,
                    version = version + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE domain = :domain
            ");
            $stmt->execute([
                ':data' => $encrypted_data,
                ':meta' => json_encode($metadata),
                ':domain' => $domain
            ]);
            
            // Log for polling
            $this->logSiteAction($existing['id'], $domain, $existing['fwild'], 'update');
            
            return ['fwild' => $existing['fwild'], 'version' => $existing['version'] + 1, 'updated' => true];
        } else {
            // Get next fwild
            $fwild = $this->pdo->query("SELECT COALESCE(MAX(fwild), 0) + 1 FROM sites")->fetchColumn();
            
            // Insert new
            $stmt = $this->pdo->prepare("
                INSERT INTO sites (domain, fwild, creator_peer_id, site_data_encrypted, encryption_metadata)
                VALUES (:domain, :fwild, :creator, :data, :meta)
            ");
            $stmt->execute([
                ':domain' => $domain,
                ':fwild' => $fwild,
                ':creator' => $creator_peer_id,
                ':data' => $encrypted_data,
                ':meta' => json_encode($metadata)
            ]);
            
            // Log for polling
            $site_id = $this->pdo->lastInsertId();
            $this->logSiteAction($site_id, $domain, $fwild, 'create');
            
            return ['fwild' => $fwild, 'version' => 1, 'updated' => false];
        }
    }
    
    private function logSiteAction($site_id, $domain, $fwild, $action) {
        $stmt = $this->pdo->prepare("
            INSERT INTO sites_poll_log (site_id, domain, fwild, action)
            VALUES (:site_id, :domain, :fwild, :action)
        ");
        $stmt->execute([
            ':site_id' => $site_id,
            ':domain' => $domain,
            ':fwild' => $fwild,
            ':action' => $action
        ]);
    }
    
    public function getSites($limit = null) {
        $sql = "SELECT * FROM sites WHERE is_active = TRUE ORDER BY fwild DESC";
        if ($limit) {
            $sql .= " LIMIT " . (int)$limit;
        }
        
        $stmt = $this->pdo->query($sql);
        $sites = $stmt->fetchAll();
        
        foreach ($sites as &$site) {
            $site['site_data'] = bin2hex($site['site_data_encrypted']);
            unset($site['site_data_encrypted']);
            $site['encryption_metadata'] = json_decode($site['encryption_metadata'] ?? '[]', true);
            $site['created_at'] = strtotime($site['created_at']);
            $site['updated_at'] = strtotime($site['updated_at']);
        }
        
        return $sites;
    }
    
    public function getSiteByDomain($domain) {
        $stmt = $this->pdo->prepare("SELECT * FROM sites WHERE domain = ? AND is_active = TRUE");
        $stmt->execute([$domain]);
        $site = $stmt->fetch();
        
        if ($site) {
            $site['site_data'] = bin2hex($site['site_data_encrypted']);
            unset($site['site_data_encrypted']);
            $site['encryption_metadata'] = json_decode($site['encryption_metadata'] ?? '[]', true);
            $site['created_at'] = strtotime($site['created_at']);
            $site['updated_at'] = strtotime($site['updated_at']);
        }
        
        return $site;
    }
    
    public function getSiteByFwild($fwild) {
        $stmt = $this->pdo->prepare("SELECT * FROM sites WHERE fwild = ? AND is_active = TRUE");
        $stmt->execute([$fwild]);
        $site = $stmt->fetch();
        
        if ($site) {
            $site['site_data'] = bin2hex($site['site_data_encrypted']);
            unset($site['site_data_encrypted']);
            $site['encryption_metadata'] = json_decode($site['encryption_metadata'] ?? '[]', true);
            $site['created_at'] = strtotime($site['created_at']);
            $site['updated_at'] = strtotime($site['updated_at']);
        }
        
        return $site;
    }
    
    /**
     * Get sites created/updated since timestamp (for 30-second polling)
     */
    public function getNewSitesSince($timestamp = null) {
        if ($timestamp === null) {
            $timestamp = time() - $this->config['settings']['polling_interval'];
        }
        
        $datetime = date('Y-m-d H:i:s', $timestamp);
        
        $stmt = $this->pdo->prepare("
            SELECT DISTINCT s.* FROM sites s
            INNER JOIN sites_poll_log l ON s.id = l.site_id
            WHERE l.created_at > :datetime AND s.is_active = TRUE
            ORDER BY l.created_at DESC
        ");
        $stmt->execute([':datetime' => $datetime]);
        
        $sites = $stmt->fetchAll();
        foreach ($sites as &$site) {
            $site['site_data'] = bin2hex($site['site_data_encrypted']);
            unset($site['site_data_encrypted']);
            $site['encryption_metadata'] = json_decode($site['encryption_metadata'] ?? '[]', true);
            $site['created_at'] = strtotime($site['created_at']);
            $site['updated_at'] = strtotime($site['updated_at']);
        }
        
        return $sites;
    }
    
    public function getStats() {
        $stmt = $this->pdo->query("SELECT stat_name, stat_value FROM system_stats");
        $stats = $stmt->fetchAll(PDO::FETCH_KEY_PAIR);
        
        return [
            'total_peers' => (int)($stats['total_peers'] ?? 0),
            'live_peers' => (int)($stats['total_peers'] ?? 0),
            'total_sites' => (int)($stats['total_sites'] ?? 0),
            'fwild_counter' => (int)($stats['fwild_counter'] ?? 0),
            'last_poll_time' => $stats['last_poll_time'] ?? null
        ];
    }
    
    public function storePeerKey($peer_id, $key_type, $key_data, $expires_in = 3600) {
        $stmt = $this->pdo->prepare("
            INSERT INTO peer_keys (peer_id, key_type, key_data, expires_at)
            VALUES (:peer_id, :type, :data, DATE_ADD(NOW(), INTERVAL :exp SECOND))
            ON DUPLICATE KEY UPDATE key_data = VALUES(key_data), expires_at = VALUES(expires_at)
        ");
        return $stmt->execute([
            ':peer_id' => $peer_id,
            ':type' => $key_type,
            ':data' => $key_data,
            ':exp' => $expires_in
        ]);
    }
    
    public function getPeerKey($peer_id, $key_type = 'public') {
        $stmt = $this->pdo->prepare("
            SELECT key_data FROM peer_keys 
            WHERE peer_id = ? AND key_type = ? AND is_active = TRUE
            AND (expires_at IS NULL OR expires_at > NOW())
        ");
        $stmt->execute([$peer_id, $key_type]);
        return $stmt->fetchColumn();
    }
}

/**
 * Request handler
 */
function handleRequest($db) {
    $action = $_GET['action'] ?? $_POST['action'] ?? '';
    $peer_id = $_SERVER['HTTP_X_QWDE_PEER_ID'] ?? $_POST['peer_id'] ?? '';
    
    $response = ['status' => 'error', 'message' => 'Invalid action'];
    
    switch ($action) {
        case 'register_peer':
            $host = $_POST['host'] ?? '';
            $port = $_POST['port'] ?? 0;
            $public_key = $_POST['public_key'] ?? null;
            $sites = isset($_POST['sites']) ? json_decode($_POST['sites'], true) : [];
            
            if ($peer_id && $host && $port) {
                $success = $db->registerPeer($peer_id, $host, $port, $public_key, $sites);
                $response = ['status' => $success ? 'success' : 'error'];
            } else {
                $response = ['status' => 'error', 'message' => 'Missing required fields'];
            }
            break;
            
        case 'get_peers':
            $limit = $_GET['limit'] ?? 10;
            $peers = $db->getActivePeers((int)$limit);
            $response = ['status' => 'success', 'peers' => $peers];
            break;
            
        case 'register_site':
            $creator = $_POST['creator_peer_id'] ?? $peer_id;
            $encrypted_data = hex2bin($_POST['site_data_encrypted'] ?? '');
            $metadata = isset($_POST['encryption_metadata']) ? json_decode($_POST['encryption_metadata'], true) : [];
            
            if ($_POST['domain'] && $creator && $encrypted_data) {
                $result = $db->registerSite($_POST['domain'], $creator, $encrypted_data, $metadata);
                $response = ['status' => 'success'] + $result;
            } else {
                $response = ['status' => 'error', 'message' => 'Missing required fields'];
            }
            break;
            
        case 'get_site':
            $domain = $_GET['domain'] ?? '';
            if ($domain) {
                $site = $db->getSiteByDomain($domain);
                $response = $site ? ['status' => 'success', 'site' => $site] : ['status' => 'not_found'];
            }
            break;
            
        case 'get_site_by_fwild':
            $fwild = $_GET['fwild'] ?? 0;
            if ($fwild) {
                $site = $db->getSiteByFwild((int)$fwild);
                $response = $site ? ['status' => 'success', 'site' => $site] : ['status' => 'not_found'];
            }
            break;
            
        case 'sync_sites':
            $limit = $_GET['limit'] ?? $config['settings']['max_sites_per_request'];
            $sites = $db->getSites((int)$limit);
            $response = ['status' => 'success', 'sites' => $sites, 'count' => count($sites)];
            break;
            
        case 'get_new_sites':
            // 30-second polling endpoint
            $since = $_GET['since'] ?? (time() - 30);
            $sites = $db->getNewSitesSince((int)$since);
            $response = [
                'status' => 'success',
                'sites' => $sites,
                'count' => count($sites),
                'polling_interval' => $config['settings']['polling_interval'],
                'current_time' => time()
            ];
            break;
            
        case 'get_stats':
            $response = ['status' => 'success'] + $db->getStats();
            break;
            
        case 'store_key':
            // Store encryption key for peer-to-peer exchange
            $key_type = $_POST['key_type'] ?? 'public';
            $key_data = $_POST['key_data'] ?? '';
            $expires = $_POST['expires_in'] ?? 3600;
            
            if ($peer_id && $key_data) {
                $success = $db->storePeerKey($peer_id, $key_type, $key_data, (int)$expires);
                $response = ['status' => $success ? 'success' : 'error'];
            }
            break;
            
        case 'get_key':
            // Retrieve peer's encryption key
            $target_peer = $_GET['peer_id'] ?? '';
            $key_type = $_GET['key_type'] ?? 'public';
            
            if ($target_peer) {
                $key = $db->getPeerKey($target_peer, $key_type);
                $response = $key ? ['status' => 'success', 'key_data' => $key] : ['status' => 'not_found'];
            }
            break;
            
        default:
            $response = [
                'status' => 'error',
                'message' => 'Unknown action',
                'available_actions' => [
                    'register_peer', 'get_peers', 'register_site', 'get_site',
                    'get_site_by_fwild', 'sync_sites', 'get_new_sites', 'get_stats',
                    'store_key', 'get_key'
                ],
                'polling_info' => [
                    'interval_seconds' => $config['settings']['polling_interval'],
                    'endpoint' => 'get_new_sites',
                    'description' => 'Query this endpoint every 30 seconds for new sites'
                ]
            ];
    }
    
    return $response;
}

// Initialize and handle request
try {
    $db = new QWDEDatabase($config);
    $response = handleRequest($db);
    echo json_encode($response);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['status' => 'error', 'message' => 'Server error: ' . $e->getMessage()]);
}
?>
