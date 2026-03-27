<?php
/**
 * QWDE Protocol - Central API Handler
 * Hosted at: secupgrade.com/api_handler.php
 * 
 * SECURITY: Database config is EMBEDDED in this file
 * DO NOT upload qwde_config.ini to server - client side only!
 */

// ═══════════════════════════════════════════════════════════
// SERVER CONFIGURATION - EMBEDDED (NOT READABLE FROM WEB)
// ═══════════════════════════════════════════════════════════

$db_config = [
    'host' => 'localhost',
    'port' => '3306',
    'database' => 'qwde_ddns',
    'username' => 'qwde_user',
    'password' => 'TO_BE_ADDED',  // ← SET ROOT PASSWORD HERE DURING DEPLOYMENT
    'charset' => 'utf8mb4'
];

// Security settings
$security = [
    'allow_cors' => true,              // Allow cross-origin requests from browsers
    'rate_limit' => 100,               // Requests per minute per IP
    'require_auth' => false,           // Require peer authentication (false for public)
    'log_level' => 'ERROR'             // DEBUG, INFO, WARNING, ERROR
];

// ═══════════════════════════════════════════════════════════
// DO NOT EDIT BELOW THIS LINE
// ═══════════════════════════════════════════════════════════

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-QWDE-Peer-ID, X-QWDE-Signature');

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

/**
 * Database connection class
 */
class DDNSDatabase {
    private $pdo;
    private $config;
    
    public function __construct($config) {
        $this->config = $config;
        $this->connect();
        $this->initTables();
    }
    
    private function connect() {
        try {
            $dsn = "mysql:host={$this->config['host']};port={$this->config['port']};dbname={$this->config['database']};charset={$this->config['charset']}";
            $options = [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ];
            $this->pdo = new PDO($dsn, $this->config['username'], $this->config['password'], $options);
        } catch (PDOException $e) {
            http_response_code(500);
            echo json_encode(['status' => 'error', 'message' => 'Database connection failed']);
            exit();
        }
    }
    
    private function initTables() {
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
        
        // Sites poll log for 30-second polling
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
        
        // Update stats
        $this->pdo->exec("
            INSERT INTO system_stats (stat_name, stat_value) VALUES 
            ('total_sites', '0'),
            ('total_peers', '0'),
            ('fwild_counter', '0'),
            ('last_poll_time', NOW())
            ON DUPLICATE KEY UPDATE stat_name = stat_name
        ");
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
            AND last_seen > DATE_SUB(NOW(), INTERVAL 300 SECOND)
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
    
    public function getNewSitesSince($timestamp = null) {
        if ($timestamp === null) {
            $timestamp = time() - 30;
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
        $stmt = $this->pdo->query("
            SELECT 
                (SELECT COUNT(*) FROM peers WHERE is_active = TRUE) as total_peers,
                (SELECT COUNT(*) FROM peers WHERE is_active = TRUE AND last_seen > DATE_SUB(NOW(), INTERVAL 300 SECOND)) as live_peers,
                (SELECT COUNT(*) FROM sites WHERE is_active = TRUE) as total_sites,
                (SELECT COALESCE(MAX(fwild), 0) FROM sites) as fwild_counter
        ");
        return $stmt->fetch();
    }
}

/**
 * Request handler
 */
function handleRequest($db) {
    $action = $_GET['action'] ?? $_POST['action'] ?? '';
    
    $response = ['status' => 'error', 'message' => 'Invalid action'];
    
    switch ($action) {
        case 'register_peer':
            $peer_id = $_POST['peer_id'] ?? '';
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
            $creator = $_POST['creator_peer_id'] ?? '';
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
            $sites = $db->getSites();
            $response = ['status' => 'success', 'sites' => $sites, 'count' => count($sites)];
            break;
            
        case 'get_new_sites':
            $since = $_GET['since'] ?? (time() - 30);
            $sites = $db->getNewSitesSince((int)$since);
            $response = [
                'status' => 'success',
                'sites' => $sites,
                'count' => count($sites),
                'current_time' => time()
            ];
            break;
            
        case 'get_stats':
            $stats = $db->getStats();
            $response = ['status' => 'success'] + $stats;
            break;
            
        default:
            $response = [
                'status' => 'error',
                'message' => 'Unknown action',
                'available_actions' => [
                    'register_peer', 'get_peers', 'register_site', 'get_site',
                    'get_site_by_fwild', 'sync_sites', 'get_new_sites', 'get_stats'
                ]
            ];
    }
    
    return $response;
}

// Initialize and handle request
try {
    $db = new DDNSDatabase($db_config);
    $response = handleRequest($db);
    echo json_encode($response);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['status' => 'error', 'message' => 'Server error']);
}
?>
