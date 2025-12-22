from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Sale, Gift, GiftWin, MonthlyWinner
from datetime import datetime, date
from functools import wraps
import random

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# =============================================================================
# FIREWALL Korumasi Aktif
# =============================================================================
if FIREWALL_ENABLED and fw_client:
    @app.before_request
    def firewall_before_request():
        try:
            if fw_client.check_request(request):
                return fw_client.handle_blocked_response()
        except Exception as e:
            print(f"FIREWALL CLIENT HATA: {e}")
# =============================================================================

TRANSLATIONS = {
    'de': {
        'app_name': 'Bee Life Consulting',
        'welcome': 'Willkommen',
        'login': 'Anmelden',
        'logout': 'Abmelden',
        'register': 'Registrieren',
        'username': 'Benutzername',
        'password': 'Passwort',
        'email': 'E-Mail',
        'full_name': 'Vollständiger Name',
        'dashboard': 'Dashboard',
        'statistics': 'Statistiken',
        'gifts': 'Geschenke',
        'admin_panel': 'Admin-Panel',
        'users': 'Benutzer',
        'sales': 'Verkäufe',
        'add_sale': 'Verkauf hinzufügen',
        'monthly_ranking': 'Monatsrangliste',
        'balloon_game': 'Ballon-Spiel',
        'pop_balloon': 'Klicke auf einen Ballon!',
        'congratulations': 'Herzlichen Glückwunsch!',
        'you_won': 'Du hast gewonnen',
        'total_sales': 'Gesamtverkäufe',
        'rls_count': 'RLS/Stornos',
        'date': 'Datum',
        'employee': 'Mitarbeiter',
        'approve': 'Genehmigen',
        'delete': 'Löschen',
        'pending_approval': 'Warten auf Genehmigung',
        'approved': 'Genehmigt',
        'not_approved_yet': 'Ihr Konto wurde noch nicht genehmigt.',
        'login_success': 'Erfolgreich angemeldet!',
        'logout_success': 'Erfolgreich abgemeldet!',
        'register_success': 'Registrierung erfolgreich! Bitte warten Sie auf die Admin-Genehmigung.',
        'invalid_credentials': 'Ungültige Anmeldedaten',
        'rank': 'Rang',
        'monthly_champion': 'Monatsbester',
        'quarterly_champion': 'Quartalsbester',
        'yearly_champion': 'Jahresbester',
        'manage_gifts': 'Geschenke verwalten',
        'gift_name': 'Geschenkname',
        'gift_value': 'Wert (€)',
        'save': 'Speichern',
        'cancel': 'Abbrechen',
        'all_employees': 'Alle Mitarbeiter',
        'top_seller': 'Top-Verkäufer',
        'team_statistics': 'Team-Statistiken',
        'my_statistics': 'Meine Statistiken',
        'won_gifts': 'Gewonnene Geschenke',
        'no_gifts_yet': 'Noch keine Geschenke gewonnen',
        'january': 'Januar', 'february': 'Februar', 'march': 'März',
        'april': 'April', 'may': 'Mai', 'june': 'Juni',
        'july': 'Juli', 'august': 'August', 'september': 'September',
        'october': 'Oktober', 'november': 'November', 'december': 'Dezember'
    },
    'tr': {
        'app_name': 'Bee Life Consulting',
        'welcome': 'Hoş Geldiniz',
        'login': 'Giriş Yap',
        'logout': 'Çıkış Yap',
        'register': 'Kayıt Ol',
        'username': 'Kullanıcı Adı',
        'password': 'Şifre',
        'email': 'E-posta',
        'full_name': 'Ad Soyad',
        'dashboard': 'Ana Sayfa',
        'statistics': 'İstatistikler',
        'gifts': 'Hediyeler',
        'admin_panel': 'Admin Paneli',
        'users': 'Kullanıcılar',
        'sales': 'Satışlar',
        'add_sale': 'Satış Ekle',
        'monthly_ranking': 'Aylık Sıralama',
        'balloon_game': 'Balon Oyunu',
        'pop_balloon': 'Bir balona tıkla!',
        'congratulations': 'Tebrikler!',
        'you_won': 'Kazandınız',
        'total_sales': 'Toplam Satış',
        'rls_count': 'RLS/İptal',
        'date': 'Tarih',
        'employee': 'Çalışan',
        'approve': 'Onayla',
        'delete': 'Sil',
        'pending_approval': 'Onay Bekleniyor',
        'approved': 'Onaylandı',
        'not_approved_yet': 'Hesabınız henüz onaylanmadı.',
        'login_success': 'Başarıyla giriş yapıldı!',
        'logout_success': 'Başarıyla çıkış yapıldı!',
        'register_success': 'Kayıt başarılı! Lütfen admin onayını bekleyin.',
        'invalid_credentials': 'Geçersiz giriş bilgileri',
        'rank': 'Sıra',
        'monthly_champion': 'Ayın Birincisi',
        'quarterly_champion': '3 Ayın Birincisi',
        'yearly_champion': 'Yılın Birincisi',
        'manage_gifts': 'Hediyeleri Yönet',
        'gift_name': 'Hediye Adı',
        'gift_value': 'Değer (€)',
        'save': 'Kaydet',
        'cancel': 'İptal',
        'all_employees': 'Tüm Çalışanlar',
        'top_seller': 'En Çok Satan',
        'team_statistics': 'Takım İstatistikleri',
        'my_statistics': 'İstatistiklerim',
        'won_gifts': 'Kazanılan Hediyeler',
        'no_gifts_yet': 'Henüz hediye kazanılmadı',
        'january': 'Ocak', 'february': 'Şubat', 'march': 'Mart',
        'april': 'Nisan', 'may': 'Mayıs', 'june': 'Haziran',
        'july': 'Temmuz', 'august': 'Ağustos', 'september': 'Eylül',
        'october': 'Ekim', 'november': 'Kasım', 'december': 'Aralık'
    }
}

def get_locale():
    return session.get('language', 'de')

def t(key):
    lang = get_locale()
    return TRANSLATIONS.get(lang, TRANSLATIONS['de']).get(key, key)

@app.context_processor
def inject_translations():
    return {'t': t, 'lang': get_locale(), 'now': datetime.now}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Zugriff verweigert / Erişim reddedildi', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['de', 'tr']:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_approved:
                flash(t('not_approved_yet'), 'warning')
                return render_template('login.html')
            login_user(user)
            flash(t('login_success'), 'success')
            return redirect(url_for('dashboard'))
        flash(t('invalid_credentials'), 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        if User.query.filter_by(username=username).first():
            flash('Benutzername existiert bereits / Kullanıcı adı zaten mevcut', 'error')
            return render_template('register.html')
        
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4']
        user = User(username=username, email=email, full_name=full_name, profile_color=random.choice(colors))
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash(t('register_success'), 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(t('logout_success'), 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    users = User.query.filter_by(is_approved=True, is_admin=False).all()
    user_stats = []
    for user in users:
        total_sales = 0
        total_rls = 0
        sales = Sale.query.filter(
            Sale.user_id == user.id,
            db.extract('year', Sale.sale_date) == current_year,
            db.extract('month', Sale.sale_date) == current_month
        ).all()
        for sale in sales:
            total_sales += sale.amount
            total_rls += sale.rls_count
        
        user_stats.append({
            'user': user,
            'total_sales': total_sales,
            'total_rls': total_rls,
            'score': total_sales - (total_rls * 2)
        })
    
    user_stats.sort(key=lambda x: x['total_sales'], reverse=True)
    top_3 = user_stats[:3] if len(user_stats) >= 3 else user_stats
    
    return render_template('dashboard.html', user_stats=user_stats, top_3=top_3, current_month=current_month, current_year=current_year)

@app.route('/gifts')
@login_required
def gifts():
    today = date.today()
    last_month = today.month - 1 if today.month > 1 else 12
    last_year = today.year if today.month > 1 else today.year - 1
    
    winner = MonthlyWinner.query.filter_by(user_id=current_user.id, year=last_year, month=last_month, can_play_balloon=True).first()
    can_play = winner is not None or current_user.is_admin
    
    gifts_list = Gift.query.filter_by(is_active=True).all()
    won_gifts = GiftWin.query.filter_by(user_id=current_user.id).order_by(GiftWin.won_at.desc()).all()
    
    return render_template('gifts.html', can_play=can_play, gifts=gifts_list, won_gifts=won_gifts)

@app.route('/api/pop_balloon', methods=['POST'])
@login_required
def pop_balloon():
    gifts_list = Gift.query.filter_by(is_active=True).all()
    if not gifts_list:
        return jsonify({'error': 'Keine Geschenke verfügbar'}), 400
    
    weights = [g.probability for g in gifts_list]
    selected_gift = random.choices(gifts_list, weights=weights, k=1)[0]
    
    today = date.today()
    win = GiftWin(user_id=current_user.id, gift_id=selected_gift.id, period_type='monthly', period_year=today.year, period_month=today.month)
    db.session.add(win)
    
    winner = MonthlyWinner.query.filter_by(user_id=current_user.id, can_play_balloon=True).first()
    if winner:
        winner.can_play_balloon = False
    
    db.session.commit()
    
    lang = get_locale()
    gift_name = selected_gift.name_de if lang == 'de' else selected_gift.name_tr
    
    return jsonify({'success': True, 'gift_name': gift_name, 'gift_value': selected_gift.value, 'gift_emoji': selected_gift.emoji})

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    pending_users = User.query.filter_by(is_approved=False).all()
    all_users = User.query.filter_by(is_approved=True).all()
    return render_template('admin/dashboard.html', pending_users=pending_users, all_users=all_users)

@app.route('/admin/approve/<int:user_id>')
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'{user.full_name} wurde genehmigt / onaylandı', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Admin kann nicht gelöscht werden', 'error')
        return redirect(url_for('admin_dashboard'))
    db.session.delete(user)
    db.session.commit()
    flash(f'{user.full_name} wurde gelöscht / silindi', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/sales', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_sales():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        sale_date = datetime.strptime(request.form.get('sale_date'), '%Y-%m-%d').date()
        amount = int(request.form.get('amount', 0))
        rls_count = int(request.form.get('rls_count', 0))
        notes = request.form.get('notes', '')
        
        sale = Sale(user_id=user_id, sale_date=sale_date, amount=amount, rls_count=rls_count, notes=notes, created_by=current_user.id)
        db.session.add(sale)
        db.session.commit()
        flash('Verkauf hinzugefügt / Satış eklendi', 'success')
        return redirect(url_for('admin_sales'))
    
    users = User.query.filter_by(is_approved=True, is_admin=False).all()
    sales = Sale.query.order_by(Sale.sale_date.desc()).limit(50).all()
    return render_template('admin/sales.html', users=users, sales=sales)

@app.route('/admin/gifts', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_gifts():
    if request.method == 'POST':
        gift = Gift(
            name_de=request.form.get('name_de'),
            name_tr=request.form.get('name_tr'),
            value=float(request.form.get('value', 0)),
            emoji=request.form.get('emoji', '🎁'),
            probability=float(request.form.get('probability', 10)),
            gift_type=request.form.get('gift_type', 'monthly')
        )
        db.session.add(gift)
        db.session.commit()
        flash('Geschenk hinzugefügt / Hediye eklendi', 'success')
        return redirect(url_for('admin_gifts'))
    
    return render_template('admin/gifts.html', gifts=Gift.query.all())

@app.route('/admin/gifts/delete/<int:gift_id>')
@login_required
@admin_required
def delete_gift(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    db.session.delete(gift)
    db.session.commit()
    return redirect(url_for('admin_gifts'))

@app.route('/admin/gifts/toggle/<int:gift_id>')
@login_required
@admin_required
def toggle_gift(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    gift.is_active = not gift.is_active
    db.session.commit()
    return redirect(url_for('admin_gifts'))

@app.route('/admin/set_winner', methods=['POST'])
@login_required
@admin_required
def set_winner():
    user_id = request.form.get('user_id')
    year = int(request.form.get('year'))
    month = int(request.form.get('month'))
    winner_type = request.form.get('winner_type', 'sales')
    
    existing = MonthlyWinner.query.filter_by(user_id=user_id, year=year, month=month).first()
    if existing:
        flash('Bu kullanıcı zaten bu ayın birincisi', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    winner = MonthlyWinner(user_id=user_id, year=year, month=month, winner_type=winner_type, can_play_balloon=True)
    db.session.add(winner)
    db.session.commit()
    flash('Gewinner festgelegt / Birinci belirlendi', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=9000)


