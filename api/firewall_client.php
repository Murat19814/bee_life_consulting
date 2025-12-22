<?php
/**
 * FIREWALL Client - PHP Entegrasyonu
 * beelife-consulting.com icin Merkezi Guvenlik Sistemi
 * 
 * API Key: 23ab6acda8b8c93a09e16ad7e3bb81f2e1888cf2525b3e9ab7365d31540f5351
 */

class FirewallClient {
    private $firewall_url;
    private $api_key;
    private $enabled;
    
    public function __construct($api_key, $firewall_url = 'http://localhost:5050') {
        $this->api_key = $api_key;
        $this->firewall_url = $firewall_url;
        $this->enabled = true;
    }
    
    /**
     * IP adresini al
     */
    private function getClientIP() {
        if (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
            $ips = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
            return trim($ips[0]);
        }
        if (!empty($_SERVER['HTTP_X_REAL_IP'])) {
            return $_SERVER['HTTP_X_REAL_IP'];
        }
        return $_SERVER['REMOTE_ADDR'] ?? '127.0.0.1';
    }
    
    /**
     * Istegi kontrol et
     * @return bool True ise engellendi, false ise izin verildi
     */
    public function checkRequest() {
        if (!$this->enabled) {
            return false;
        }
        
        $client_ip = $this->getClientIP();
        $endpoint = $_SERVER['REQUEST_URI'] ?? '/';
        $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
        $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? '';
        
        $data = array(
            'api_key' => $this->api_key,
            'ip' => $client_ip,
            'endpoint' => $endpoint,
            'method' => $method,
            'user_agent' => $user_agent
        );
        
        try {
            $response = $this->sendRequest('/api/check', $data);
            
            if ($response && isset($response['blocked']) && $response['blocked']) {
                $this->handleBlocked($response['reason'] ?? 'Guvenlik ihlali');
                return true;
            }
        } catch (Exception $e) {
            // Firewall'a ulasilamazsa istege izin ver (fail-open)
            error_log("FIREWALL CLIENT ERROR: " . $e->getMessage());
        }
        
        return false;
    }
    
    /**
     * Firewall'a HTTP istegi gonder
     */
    private function sendRequest($endpoint, $data) {
        $url = $this->firewall_url . $endpoint;
        
        $options = array(
            'http' => array(
                'header'  => "Content-type: application/json\r\n",
                'method'  => 'POST',
                'content' => json_encode($data),
                'timeout' => 2
            )
        );
        
        $context = stream_context_create($options);
        $result = @file_get_contents($url, false, $context);
        
        if ($result === FALSE) {
            return null;
        }
        
        return json_decode($result, true);
    }
    
    /**
     * Engelleme durumunda cevap dondur
     */
    private function handleBlocked($reason) {
        http_response_code(403);
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(array(
            'error' => true,
            'message' => 'Zugriff verweigert / Erisim engellendi',
            'reason' => $reason,
            'code' => 403
        ), JSON_UNESCAPED_UNICODE);
    }
    
    /**
     * Guvenlik olayini logla
     */
    public function logEvent($event_type, $details = '') {
        $data = array(
            'api_key' => $this->api_key,
            'event_type' => $event_type,
            'ip' => $this->getClientIP(),
            'details' => $details
        );
        
        try {
            $this->sendRequest('/api/log_event', $data);
        } catch (Exception $e) {
            error_log("FIREWALL LOG ERROR: " . $e->getMessage());
        }
    }
    
    /**
     * SQL Injection kontrolu
     */
    public function checkSQLInjection($input) {
        $patterns = array(
            '/(\%27)|(\')|(\-\-)|(\%23)|(#)/i',
            '/((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))/i',
            '/\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))/i',
            '/((\%27)|(\'))union/i',
            '/exec(\s|\+)+(s|x)p\w+/i',
            '/UNION(\s+)SELECT/i',
            '/INSERT(\s+)INTO/i',
            '/DELETE(\s+)FROM/i',
            '/DROP(\s+)TABLE/i'
        );
        
        foreach ($patterns as $pattern) {
            if (preg_match($pattern, $input)) {
                $this->logEvent('sql_injection', "Input: $input");
                return true;
            }
        }
        return false;
    }
    
    /**
     * XSS kontrolu
     */
    public function checkXSS($input) {
        $patterns = array(
            '/<script\b[^>]*>(.*?)<\/script>/is',
            '/javascript:/i',
            '/on\w+\s*=/i',
            '/<iframe/i',
            '/<object/i',
            '/<embed/i'
        );
        
        foreach ($patterns as $pattern) {
            if (preg_match($pattern, $input)) {
                $this->logEvent('xss_attack', "Input: $input");
                return true;
            }
        }
        return false;
    }
    
    /**
     * Tum girdileri kontrol et
     */
    public function validateInputs() {
        $inputs = array_merge($_GET, $_POST);
        
        foreach ($inputs as $key => $value) {
            if (is_string($value)) {
                if ($this->checkSQLInjection($value) || $this->checkXSS($value)) {
                    http_response_code(403);
                    header('Content-Type: application/json; charset=utf-8');
                    echo json_encode(array(
                        'error' => true,
                        'message' => 'Schaedlicher Inhalt erkannt / Zararli icerik tespit edildi',
                        'code' => 403
                    ), JSON_UNESCAPED_UNICODE);
                    return true;
                }
            }
        }
        return false;
    }
}
?>

