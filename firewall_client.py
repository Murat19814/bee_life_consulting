# firewall_client.py - Diğer uygulamalar için Firewall Client
# Bu dosyayı korumak istediğiniz uygulamaların klasörüne kopyalayın

import requests
import json
from functools import wraps
from flask import request, abort, jsonify

class FirewallClient:
    """
    FIREWALL Merkezi Güvenlik Sistemi için client modülü.
    Flask uygulamalarınıza entegre ederek merkezi güvenlik kontrolü sağlar.
    """
    
    def __init__(self, firewall_url="http://localhost:5050", api_key=None, timeout=5):
        """
        Args:
            firewall_url: FIREWALL sunucu adresi
            api_key: Uygulama için oluşturulan API anahtarı
            timeout: İstek zaman aşımı (saniye)
        """
        self.firewall_url = firewall_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self._cache = {}  # Basit önbellek
        self._cache_ttl = 60  # 60 saniye önbellek
    
    def _get_headers(self):
        """API istekleri için header'ları oluştur"""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def check_ip(self, ip):
        """
        IP adresinin durumunu kontrol et.
        
        Args:
            ip: Kontrol edilecek IP adresi
            
        Returns:
            dict: {"blocked": bool, "whitelisted": bool, "action": "allow"|"block"}
        """
        try:
            response = requests.post(
                f"{self.firewall_url}/api/check-ip",
                headers=self._get_headers(),
                json={"ip": ip},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Hata durumunda güvenli tarafta kal - izin ver
                return {"blocked": False, "whitelisted": False, "action": "allow"}
                
        except requests.exceptions.RequestException as e:
            # Bağlantı hatası - güvenli tarafta kal
            print(f"Firewall bağlantı hatası: {e}")
            return {"blocked": False, "whitelisted": False, "action": "allow"}
    
    def is_blocked(self, ip):
        """
        IP'nin engellenip engellenmediğini kontrol et.
        
        Args:
            ip: Kontrol edilecek IP adresi
            
        Returns:
            bool: True eğer engelliyse
        """
        result = self.check_ip(ip)
        return result.get("blocked", False)
    
    def report_threat(self, ip, threat_type, description="", auto_block=False):
        """
        Tehdit bildirimi gönder.
        
        Args:
            ip: Tehdit kaynağı IP
            threat_type: Tehdit türü (brute_force, suspicious, ddos vb.)
            description: Detaylı açıklama
            auto_block: Otomatik engelleme yapılsın mı?
            
        Returns:
            bool: Başarılı mı?
        """
        try:
            response = requests.post(
                f"{self.firewall_url}/api/report-threat",
                headers=self._get_headers(),
                json={
                    "ip": ip,
                    "threat_type": threat_type,
                    "description": description,
                    "auto_block": auto_block
                },
                timeout=self.timeout
            )
            
            return response.status_code == 200
            
        except requests.exceptions.RequestException as e:
            print(f"Tehdit bildirimi hatası: {e}")
            return False
    
    def get_stats(self):
        """
        Güvenlik istatistiklerini getir.
        
        Returns:
            dict: Güvenlik istatistikleri
        """
        try:
            response = requests.get(
                f"{self.firewall_url}/api/stats",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            print(f"İstatistik hatası: {e}")
            return {}
    
    # ============================================
    # FLASK ENTEGRASYON DEKORATÖRLERİ
    # ============================================
    
    def protect(self, app):
        """
        Flask uygulamasını koruma altına al.
        Tüm istekleri otomatik olarak kontrol eder.
        
        Kullanım:
            fw_client = FirewallClient(api_key="...")
            fw_client.protect(app)
        """
        @app.before_request
        def firewall_check():
            ip = self._get_client_ip()
            if self.is_blocked(ip):
                abort(403)
        
        return app
    
    def _get_client_ip(self):
        """Gerçek client IP'sini al"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        return request.remote_addr
    
    def check_request(self):
        """
        Mevcut isteği kontrol et.
        before_request içinde kullanılabilir.
        
        Returns:
            None veya 403 abort
        """
        ip = self._get_client_ip()
        if self.is_blocked(ip):
            abort(403)
    
    def login_protection(self, max_attempts=5, block_duration=900):
        """
        Login koruması dekoratörü.
        Başarısız login denemelerini izler ve engeller.
        
        Kullanım:
            @app.route('/login', methods=['POST'])
            @fw_client.login_protection(max_attempts=5)
            def login():
                ...
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                ip = self._get_client_ip()
                
                # Önceden engellenmiş mi kontrol et
                if self.is_blocked(ip):
                    return jsonify({"error": "IP adresiniz engellenmiştir"}), 403
                
                # Orijinal fonksiyonu çağır
                result = f(*args, **kwargs)
                
                # Başarısız login kontrolü (status code 401 veya 403)
                if hasattr(result, 'status_code'):
                    if result.status_code in [401, 403]:
                        self.report_threat(
                            ip=ip,
                            threat_type="failed_login",
                            description="Başarısız login denemesi",
                            auto_block=False  # Merkezi sistemde sayılsın
                        )
                
                return result
            return decorated_function
        return decorator
    
    def rate_limit_protection(self, limit=100):
        """
        Rate limit koruması dekoratörü.
        
        Kullanım:
            @app.route('/api/data')
            @fw_client.rate_limit_protection(limit=50)
            def get_data():
                ...
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                ip = self._get_client_ip()
                
                # Merkezi sistemden kontrol
                if self.is_blocked(ip):
                    return jsonify({"error": "Rate limit aşıldı"}), 429
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator


# ============================================
# KOLAY ENTEGRASYON
# ============================================

def init_firewall_protection(app, firewall_url="http://localhost:5050", api_key=None):
    """
    Flask uygulamasına FIREWALL koruması ekle.
    
    Kullanım:
        from firewall_client import init_firewall_protection
        
        app = Flask(__name__)
        fw = init_firewall_protection(app, api_key="YOUR_API_KEY")
    """
    client = FirewallClient(firewall_url, api_key)
    client.protect(app)
    return client


# ============================================
# ÖRNEK KULLANIM
# ============================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           FIREWALL Client - Kullanım Kılavuzu                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Bu dosyayı korumak istediğiniz projeye kopyalayın        ║
║                                                              ║
║  2. Flask uygulamanızda:                                     ║
║                                                              ║
║     from firewall_client import FirewallClient               ║
║                                                              ║
║     fw = FirewallClient(                                     ║
║         firewall_url="http://localhost:5050",                ║
║         api_key="YOUR_API_KEY_HERE"                          ║
║     )                                                        ║
║                                                              ║
║     # Otomatik koruma                                        ║
║     fw.protect(app)                                          ║
║                                                              ║
║     # Veya manuel kontrol                                    ║
║     @app.before_request                                      ║
║     def check():                                             ║
║         fw.check_request()                                   ║
║                                                              ║
║  3. Tehdit bildirimi:                                        ║
║                                                              ║
║     fw.report_threat(                                        ║
║         ip="192.168.1.100",                                  ║
║         threat_type="brute_force",                           ║
║         auto_block=True                                      ║
║     )                                                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

