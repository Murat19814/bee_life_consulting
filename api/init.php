<?php
/**
 * FIREWALL Baslangic Dosyasi
 * Bu dosyayi HTML sayfalarindan once cagirin
 * 
 * Kullanim:
 *   <?php include 'api/init.php'; ?>
 *   <!DOCTYPE html>
 *   ...
 */

// Hata raporlamayi kapat (production icin)
error_reporting(0);

// FIREWALL ayarlari
define('FIREWALL_ENABLED', true);
define('FIREWALL_URL', 'http://localhost:5050');
define('FIREWALL_API_KEY', '23ab6acda8b8c93a09e16ad7e3bb81f2e1888cf2525b3e9ab7365d31540f5351');

// Firewall client'i yukle
require_once __DIR__ . '/firewall_client.php';

// Firewall kontrolu
if (FIREWALL_ENABLED) {
    $firewall = new FirewallClient(FIREWALL_API_KEY, FIREWALL_URL);
    
    // IP ve rate limit kontrolu
    if ($firewall->checkRequest()) {
        exit;
    }
    
    // Girdi kontrolu (SQL Injection, XSS)
    if ($firewall->validateInputs()) {
        exit;
    }
}
?>

