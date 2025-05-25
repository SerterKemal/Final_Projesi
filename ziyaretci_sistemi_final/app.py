from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizlisifre'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///veritabani.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'giris'

# KULLANICI MODELİ
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ZİYARETÇİ MODELİ
class Ziyaretci(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    soyad = db.Column(db.String(100), nullable=False)
    sebep = db.Column(db.String(200), nullable=False)
    tarih = db.Column(db.DateTime, default=datetime.utcnow)
    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- YÖNETİCİ GİRİŞ ---
@app.route('/giris', methods=['GET', 'POST'])
def giris():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Hatalı kullanıcı adı veya şifre!')
    return render_template('giris.html')

# --- YÖNETİCİ ÇIKIŞ ---
@app.route('/cikis')
@login_required
def cikis():
    logout_user()
    return redirect(url_for('giris'))

# --- ANA MENÜ ---
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# --- ZİYARETÇİ LİSTESİ ---
@app.route('/ziyaretci-listesi')
@login_required
def ziyaretci_listesi():
    ziyaretciler = Ziyaretci.query.order_by(Ziyaretci.tarih.desc()).all()
    return render_template('ziyaretci_listesi.html', ziyaretciler=ziyaretciler)

# --- ZİYARETÇİ EKLEME ---
@app.route('/ziyaretci-ekle', methods=['GET', 'POST'])
@login_required
def ziyaretci_ekle():
    if request.method == 'POST':
        ad = request.form['ad']
        soyad = request.form['soyad']
        sebep = request.form['sebep']
        yeni = Ziyaretci(ad=ad, soyad=soyad, sebep=sebep)
        db.session.add(yeni)
        db.session.commit()
        flash('Ziyaretçi başarıyla eklendi!')
        return redirect(url_for('ziyaretci_listesi'))
    return render_template('ziyaretci_ekle.html')

# --- ZİYARETÇİ DÜZENLEME ---
@app.route('/ziyaretci-duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
def ziyaretci_duzenle(id):
    ziyaretci = Ziyaretci.query.get_or_404(id)
    if request.method == 'POST':
        ziyaretci.ad = request.form['ad']
        ziyaretci.soyad = request.form['soyad']
        ziyaretci.sebep = request.form['sebep']
        db.session.commit()
        flash('Ziyaretçi başarıyla güncellendi!')
        return redirect(url_for('ziyaretci_listesi'))
    return render_template('ziyaretci_ekle.html', ziyaretci=ziyaretci, duzenleme=True)

# --- ZİYARETÇİ SİLME ---
@app.route('/ziyaretci-sil/<int:id>', methods=['POST'])
@login_required
def ziyaretci_sil(id):
    ziyaretci = Ziyaretci.query.get_or_404(id)
    db.session.delete(ziyaretci)
    db.session.commit()
    flash('Ziyaretçi silindi.')
    return redirect(url_for('ziyaretci_listesi'))


# --- İSTATİSTİKLER ---
@app.route('/istatistikler')
@login_required
def istatistikler():
    toplam = Ziyaretci.query.count()
    bugun = datetime.utcnow().date()
    bugun_ziyaret = Ziyaretci.query.filter(db.func.date(Ziyaretci.tarih) == bugun).count()
    son_7_gun = Ziyaretci.query.filter(Ziyaretci.tarih >= datetime.utcnow() - timedelta(days=7)).count()
    return render_template('istatistikler.html',
                           toplam=toplam,
                           bugun=bugun_ziyaret,
                           son_7_gun=son_7_gun)

# --- VERİTABANI OLUŞTURMA ---
def create_admin():
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('1234')  # Şifreni buradan değiştir
        db.session.add(admin)
        db.session.commit()

import os
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))