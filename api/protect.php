<?php
/**
 * FIREWALL Koruma Sayfasi
 * Her HTML sayfasinin basina eklenecek PHP wrapper
 * 
 * .htaccess ile tum .html isteklerini bu dosyaya yonlendirebilirsiniz
 * veya manuel olarak her sayfada include edebilirsiniz
 */

// FIREWALL ayarlari
define('FIREWALL_ENABLED', true);
define('FIREWALL_URL', 'http://localhost:5050');
define('FIREWALL_API_KEY', '23ab6acda8b8c93a09e16ad7e3bb81f2e1888cf2525b3e9ab7365d31540f5351');

require_once __DIR__ . '/firewall_client.php';

/**
 * Sayfayi koruma altina al
 */
function protectPage() {
    if (!FIREWALL_ENABLED) {
        return true;
    }
    
    $firewall = new FirewallClient(FIREWALL_API_KEY, FIREWALL_URL);
    
    // IP ve rate limit kontrolu
    if ($firewall->checkRequest()) {
        return false;
    }
    
    // Girdi kontrolu
    if ($firewall->validateInputs()) {
        return false;
    }
    
    return true;
}

/**
 * Engelleme sayfasi goster
 */
function showBlockedPage() {
    http_response_code(403);
    ?>
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zugriff verweigert - Bee Life Consulting</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #fff;
            }
            .container {
                text-align: center;
                padding: 40px;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
                max-width: 500px;
            }
            .icon {
                font-size: 80px;
                margin-bottom: 20px;
            }
            h1 {
                font-size: 2em;
                margin-bottom: 15px;
                color: #ff6b6b;
            }
            p {
                font-size: 1.1em;
                line-height: 1.6;
                opacity: 0.9;
                margin-bottom: 20px;
            }
            .code {
                background: rgba(0,0,0,0.3);
                padding: 10px 20px;
                border-radius: 8px;
                font-family: monospace;
                margin-top: 20px;
            }
            a {
                color: #ffd93d;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">🛡️</div>
            <h1>Zugriff verweigert</h1>
            <p>
                Ihre Anfrage wurde aus Sicherheitsgründen blockiert.<br>
                <small>Erisim engellendi - Guvenlik nedeniyle talebiniz reddedildi.</small>
            </p>
            <p>
                Wenn Sie glauben, dass dies ein Fehler ist, kontaktieren Sie uns bitte.<br>
                <a href="mailto:info@beelife-consulting.com">info@beelife-consulting.com</a>
            </p>
            <div class="code">
                Error Code: 403 | IP: <?php echo $_SERVER['REMOTE_ADDR'] ?? 'unknown'; ?>
            </div>
        </div>
    </body>
    </html>
    <?php
    exit;
}

// Koruma kontrolu
if (!protectPage()) {
    showBlockedPage();
}
?>

