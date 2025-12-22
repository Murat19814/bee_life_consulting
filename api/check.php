<?php
/**
 * FIREWALL Check Endpoint
 * JavaScript'ten AJAX ile cagrilabilir
 * 
 * Kullanim:
 *   fetch('/api/check.php')
 *     .then(r => r.json())
 *     .then(data => { if(data.blocked) window.location = '/blocked.html'; });
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// FIREWALL ayarlari
define('FIREWALL_URL', 'http://localhost:5050');
define('FIREWALL_API_KEY', '23ab6acda8b8c93a09e16ad7e3bb81f2e1888cf2525b3e9ab7365d31540f5351');

require_once __DIR__ . '/firewall_client.php';

$firewall = new FirewallClient(FIREWALL_API_KEY, FIREWALL_URL);

// Kontrol sonucu
$blocked = false;
$reason = '';

// IP kontrolu
if ($firewall->checkRequest()) {
    $blocked = true;
    $reason = 'IP blocked or rate limit exceeded';
}

// Girdi kontrolu
if (!$blocked && $firewall->validateInputs()) {
    $blocked = true;
    $reason = 'Malicious input detected';
}

// Sonucu dondur
echo json_encode(array(
    'success' => true,
    'blocked' => $blocked,
    'reason' => $reason,
    'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
    'timestamp' => date('Y-m-d H:i:s')
), JSON_UNESCAPED_UNICODE);
?>

