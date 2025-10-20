\
import os, time, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from threading import Lock
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from apscheduler.schedulers.background import BackgroundScheduler
import yfinance as yf
from flask_socketio import SocketIO

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Bolsas Automation")
SECRET_KEY = os.getenv("SECRET_KEY", "troque_esta_chave")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///cotacoes.db")
SCHED_FETCH_INTERVAL = int(os.getenv("SCHED_FETCH_INTERVAL", "60"))
ALERT_THRESHOLD_PCT = float(os.getenv("ALERT_THRESHOLD_PCT", "3.0"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
admin = Admin(app, name="Admin", template_mode="bootstrap5")

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
thread_lock = Lock()

COINGECKO_API = "https://api.coingecko.com/api/v3"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    def set_password(self, pw):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(pw)
    def check_password(self, pw):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, pw)

class Symbol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(128), nullable=False, index=True)
    name = db.Column(db.String(255))
    category = db.Column(db.String(64))
    exchange = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=True)

class Price(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol_id = db.Column(db.Integer, db.ForeignKey("symbol.id"), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    price = db.Column(db.Float, nullable=False)
    symbol = db.relationship("Symbol", backref=db.backref("prices", lazy="dynamic"))

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, "is_admin", False)

admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Symbol, db.session))
admin.add_view(SecureModelView(Price, db.session))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def fetch_price_for_symbol(sym: Symbol):
    try:
        if sym.category == "CRYPTO" or (sym.exchange and sym.exchange.upper() == "CRYPTO"):
            r = requests.get(f"{COINGECKO_API}/simple/price", params={"ids": sym.symbol, "vs_currencies": "usd,brl"}, timeout=10)
            j = r.json()
            if sym.symbol in j and "usd" in j[sym.symbol]:
                return float(j[sym.symbol]["usd"])
            return None
        else:
            t = yf.Ticker(sym.symbol)
            try:
                info = t.info or {}
                price = info.get("regularMarketPrice")
                if price:
                    return float(price)
            except Exception:
                hist = t.history(period="1d", interval="1m")
                if not hist.empty:
                    return float(hist["Close"].iloc[-1])
            return None
    except Exception as e:
        app.logger.exception("fetch error: %s", e)
    return None

def store_price(sym: Symbol, price: float):
    if price is None:
        return
    previous = Price.query.filter_by(symbol_id=sym.id).order_by(Price.timestamp.desc()).first()
    p = Price(symbol_id=sym.id, timestamp=datetime.utcnow(), price=price)
    db.session.add(p)
    db.session.commit()
    try:
        socketio.emit("price_update", {"symbol": sym.symbol, "price": price, "time": p.timestamp.isoformat()}, namespace="/cotacoes")
    except Exception:
        app.logger.exception("socket emit error")

def scheduled_fetch_all():
    syms = Symbol.query.filter_by(active=True).all()
    app.logger.info("Scheduler: fetching %d symbols", len(syms))
    for s in syms:
        try:
            price = fetch_price_for_symbol(s)
            if price is not None:
                store_price(s, price)
            time.sleep(0.2)
        except Exception as e:
            app.logger.exception("Scheduled fetch error: %s", e)

@app.context_processor
def inject_app_name():
    return dict(app_name=APP_NAME)

@app.route("/")
@login_required
def dashboard():
    exchanges = {}
    syms = Symbol.query.order_by(Symbol.exchange, Symbol.symbol).all()
    for s in syms:
        exchanges.setdefault(s.exchange or "OTHER", []).append({"symbol": s.symbol, "name": s.name})
    return render_template("dashboard.html", exchanges=exchanges)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if not username or not password:
            flash("Preencha usuário e senha", "danger")
            return redirect(url_for("register"))
        if User.query.filter_by(username=username).first():
            flash("Usuário já existe", "danger")
            return redirect(url_for("register"))
        u = User(username=username)
        u.set_password(password)
        if User.query.count() == 0:
            u.is_admin = True
        db.session.add(u)
        db.session.commit()
        flash("Conta criada. Faça login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        u = User.query.filter_by(username=username).first()
        if u and u.check_password(password):
            login_user(u)
            flash("Logado com sucesso", "success")
            return redirect(url_for("dashboard"))
        flash("Usuário ou senha inválidos", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Desconectado", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scheduled_fetch_all, trigger="interval", seconds=SCHED_FETCH_INTERVAL, id="fetch_all", replace_existing=True)
    scheduler.start()
    try:
        socketio.run(app, host="0.0.0.0", port=5000)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
