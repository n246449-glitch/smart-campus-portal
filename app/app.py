import os
import secrets
import psycopg2
from functools import wraps
from flask import Flask, request, redirect, render_template_string, session, url_for, abort, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "smart-campus-lab11-secret-2026")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

WRITE_DB = os.getenv("WRITE_DB_URL")
READ_DB = os.getenv("READ_DB_URL")
GITHUB_REPO_URL = "https://github.com/smart-campus-team/smart-campus-portal"

def get_write_conn():
    return psycopg2.connect(WRITE_DB)

def get_read_conn():
    return psycopg2.connect(READ_DB)

# Әдепкі админді құру (Primary DB)
def init_admin():
    try:
        conn = get_write_conn()
        cur = conn.cursor()
        hashed_pw = generate_password_hash("admin123")
        cur.execute("""
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES ('admin@campus.kz', %s, 'Жүйе Әкімшісі', 'admin')
            ON CONFLICT (email) DO NOTHING;
        """, (hashed_pw,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Admin init warning:", e)

init_admin()

# CSRF қорғанысы
@app.before_request
def csrf_protect():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    if request.method == "POST":
        token = request.form.get("csrf_token")
        if not token or token != session.get("csrf_token"):
            abort(400, description="CSRF токені қате немесе жарамсыз!")

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Бұл бетке өту үшін жүйеге кіріңіз.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped

# Ортақ HTML шаблоны
BASE_HTML = """
<!DOCTYPE html>
<html lang="kk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} — Smart Campus</title>
<style>
    :root { --primary: #1e3a8a; --accent: #2563eb; --bg: #f8fafc; --card: #ffffff; --text: #0f172a; --muted: #64748b; --danger: #dc2626; --success: #16a34a; }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
    body { background: var(--bg); color: var(--text); display: flex; flex-direction: column; min-height: 100vh; line-height: 1.6; }
    header { background: var(--primary); color: white; padding: 0 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .nav { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; min-height: 70px; flex-wrap: wrap; gap: 10px; }
    .logo { color: white; text-decoration: none; font-weight: 700; font-size: 1.3rem; }
    .links { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    .links a { color: rgba(255,255,255,0.9); text-decoration: none; padding: 6px 12px; border-radius: 6px; font-size: 0.95rem; }
    .links a:hover { background: rgba(255,255,255,0.15); color: white; }
    .admin-link { background: #f59e0b !important; color: #451a03 !important; font-weight: 700; }
    .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; flex: 1; width: 100%; }
    .card { background: var(--card); border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }
    .btn { display: inline-block; background: var(--accent); color: white; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: none; cursor: pointer; font-weight: 600; font-size: 0.95rem; }
    .btn:hover { background: #1d4ed8; }
    .btn-danger { background: var(--danger); }
    .btn-sm { padding: 6px 12px; font-size: 0.85rem; }
    label { display: block; font-weight: 600; margin-bottom: 5px; font-size: 0.9rem; }
    input, textarea, select { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 0.95rem; }
    .alert { padding: 14px 18px; border-radius: 8px; margin-bottom: 20px; font-weight: 500; }
    .alert-error { background: #fef2f2; color: var(--danger); border: 1px solid #fecaca; }
    .alert-success { background: #f0fdf4; color: var(--success); border: 1px solid #bbf7d0; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
    th { background: #f1f5f9; font-weight: 700; }
    img.prod-img { width: 100%; height: 200px; object-fit: cover; border-radius: 8px; margin-bottom: 12px; }
    footer { background: white; border-top: 1px solid #e2e8f0; text-align: center; padding: 20px; color: var(--muted); font-size: 0.9rem; margin-top: auto; }
</style>
</head>
<body>
<header>
    <div class="nav">
        <a href="/" class="logo">🎓 Smart Campus</a>
        <div class="links">
            <a href="/">Басты бет</a>
            <a href="/products">Каталог</a>
            <a href="/survey">Сауалнама</a>
            <a href="/contacts">Байланыстар</a>
            {% if session.get('role') == 'admin' %}
                <a href="/admin/products" class="admin-link">⚙️ Өнімдер</a>
                <a href="/admin/offices" class="admin-link">🏢 Кеңселер</a>
                <a href="/admin/users" class="admin-link">👥 Пайдаланушылар</a>
                <a href="/admin/surveys" class="admin-link">📊 Жауаптар</a>
            {% endif %}
            {% if session.get('user_id') %}
                <a href="/profile">👤 {{ session.get('full_name') }}</a>
                <a href="/logout" style="background: rgba(220,38,38,0.25);">Шығу</a>
            {% else %}
                <a href="/login">Кіру</a>
                <a href="/register" style="background: #16a34a;">Тіркелу</a>
            {% endif %}
        </div>
    </div>
</header>

<div class="container">
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, msg in messages %}
            <div class="alert alert-{{ category }}">{{ msg }}</div>
        {% endfor %}
    {% endwith %}
    {{ content | safe }}
</div>

<footer>
    &copy; 2026 Smart Campus Portal | PostgreSQL Primary-Standby Replication
</footer>
</body>
</html>
"""

def render_page(title, content, **kwargs):
    inner = render_template_string(content, csrf_token=session.get("csrf_token"), **kwargs)
    return render_template_string(BASE_HTML, title=title, content=inner)

# 1. БАСТЫ БЕТ (GET /)
@app.route("/")
def index():
    content = """
    <div class="card" style="background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 40px;">
        <h1 style="font-size: 2rem; margin-bottom: 12px;">Smart Campus — Университеттерді цифрландыру платформасы</h1>
        <p style="font-size: 1.1rem; opacity: 0.95; margin-bottom: 20px;">
            Біздің жобаның мақсаты — оқу орындарының инфрақұрылымын заманауи IT-шешімдермен жабдықтау, студенттер мен оқытушыларға ыңғайлы цифрлық орта құру.
        </p>
        <a href="/products" class="btn" style="background: white; color: #1e3a8a;">Өнімдер каталогын көру →</a>
    </div>
    <div class="grid">
        <div class="card">
            <h3>⚡ Жоғары өнімділік</h3>
            <p style="color: var(--muted);">Оқу мен жазу сұраулары PostgreSQL Primary және Standby серверлері арасында теңгерімді бөлінген.</p>
        </div>
        <div class="card">
            <h3>🔒 Қауіпсіздік</h3>
            <p style="color: var(--muted);">Құпия сөздер заманауи криптографиялық хэштеу арқылы қорғалады, ал әкімшілік бөлім рөлдік бақылаумен шектелген.</p>
        </div>
        <div class="card">
            <h3>📊 Кері байланыс</h3>
            <p style="color: var(--muted);">Әрбір студент пен қызметкер цифрлық өнімдерге баға беріп, жүйені жақсартуға тікелей үлес қоса алады.</p>
        </div>
    </div>
    """
    return render_page("Басты бет", content)

# 2. ТІРКЕЛУ, КІРУ, ШЫҒУ (/register, /login, /logout)
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not full_name or not email or not password:
            flash("Барлық міндетті өрістерді толтырыңыз!", "error")
        elif password != confirm:
            flash("Парольдер сәйкес келмейді!", "error")
        elif len(password) < 6:
            flash("Пароль кемінде 6 таңбадан тұруы тиіс!", "error")
        else:
            pw_hash = generate_password_hash(password)
            try:
                conn = get_write_conn()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users (email, password_hash, full_name, role) VALUES (%s, %s, %s, 'user')",
                    (email, pw_hash, full_name)
                )
                conn.commit()
                cur.close()
                conn.close()
                flash("Тіркелу сәтті аяқталды! Енді жүйеге кіріңіз.", "success")
                return redirect(url_for("login"))
            except psycopg2.IntegrityError:
                flash("Бұл email тіркелген! Басқа email қолданыңыз.", "error")
            except Exception as e:
                flash(f"Дерекқор қатесі: {e}", "error")

    content = """
    <div class="card" style="max-width: 480px; margin: 0 auto;">
        <h2 style="margin-bottom: 20px;">Жаңа аккаунт тіркеу</h2>
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label for="full_name">Аты-жөніңіз *</label>
            <input id="full_name" name="full_name" required placeholder="Мысалы: Әлихан Бөкейхан">
            <label for="email">Email мекенжайы *</label>
            <input id="email" name="email" type="email" required placeholder="student@university.kz">
            <label for="password">Пароль (кемінде 6 таңба) *</label>
            <input id="password" name="password" type="password" required>
            <label for="confirm_password">Парольді растау *</label>
            <input id="confirm_password" name="confirm_password" type="password" required>
            <button type="submit" class="btn" style="width: 100%;">Тіркелу</button>
        </form>
    </div>
    """
    return render_page("Тіркелу", content)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        try:
            # Кіру кезінде Primary сервері қолданылады (репликация кідірісіне тәуелді болмау үшін)
            conn = get_write_conn()
            cur = conn.cursor()
            cur.execute("SELECT id, email, password_hash, full_name, role FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user and check_password_hash(user[2], password):
                session["user_id"] = user[0]
                session["email"] = user[1]
                session["full_name"] = user[3]
                session["role"] = user[4]
                flash(f"Қош келдіңіз, {user[3]}!", "success")
                return redirect(url_for("index"))
            else:
                flash("Email немесе пароль қате!", "error")
        except Exception as e:
            flash(f"Қосылу қатесі: {e}", "error")

    content = """
    <div class="card" style="max-width: 450px; margin: 0 auto;">
        <h2 style="margin-bottom: 20px;">Жүйеге кіру</h2>
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label for="email">Email *</label>
            <input id="email" name="email" type="email" required placeholder="admin@campus.kz">
            <label for="password">Пароль *</label>
            <input id="password" name="password" type="password" required placeholder="admin123">
            <button type="submit" class="btn" style="width: 100%;">Кіру</button>
        </form>
    </div>
    """
    return render_page("Кіру", content)

@app.route("/logout")
def logout():
    session.clear()
    flash("Сіз жүйеден сәтті шықтыңыз.", "success")
    return redirect(url_for("index"))

@app.route("/profile")
@login_required
def profile():
    content = """
    <div class="card" style="max-width: 600px; margin: 0 auto;">
        <h2>Жеке профиль</h2>
        <p style="margin-top: 15px;"><b>Аты-жөні:</b> {{ session.get('full_name') }}</p>
        <p><b>Email:</b> {{ session.get('email') }}</p>
        <p><b>Рөлі:</b> {{ session.get('role') }}</p>
    </div>
    """
    return render_page("Жеке профиль", content)

# 3. КАТАЛОГ ЖӘНЕ ӨНІМ БЕТІ (Standby серверінен оқу)
@app.route("/products")
def products():
    q = request.args.get("q", "").strip()
    items = []
    try:
        conn = get_read_conn()
        cur = conn.cursor()
        if q:
            cur.execute("""
                SELECT slug, name, summary, price, image_url FROM products
                WHERE is_active = true AND (name ILIKE %s OR summary ILIKE %s)
                ORDER BY id DESC
            """, (f"%{q}%", f"%{q}%"))
        else:
            cur.execute("SELECT slug, name, summary, price, image_url FROM products WHERE is_active = true ORDER BY id DESC")
        items = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Standby серверінен оқу қатесі: {e}", "error")

    content = """
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h2>📦 Өнімдер каталогы</h2>
                <small style="color: var(--muted);">Деректер көзі: PostgreSQL Standby (Read-only)</small>
            </div>
            <form method="GET" style="display: flex; gap: 10px; max-width: 400px; width: 100%; margin: 0;">
                <input name="q" value="{{ q }}" placeholder="Өнім атауы бойынша іздеу..." style="margin: 0;">
                <button type="submit" class="btn">Іздеу</button>
            </form>
        </div>
    </div>
    <div class="grid">
        {% for p in items %}
        <div class="card">
            <img src="{{ p[4] or 'https://via.placeholder.com/400x200' }}" alt="{{ p[1] }}" class="prod-img">
            <h3>{{ p[1] }}</h3>
            <p style="color: var(--muted); margin: 10px 0;">{{ p[2] }}</p>
            <p style="font-weight: 700; font-size: 1.1rem; color: var(--primary); margin-bottom: 15px;">
                {{ "{:,.0f}".format(p[3]) if p[3] else "Келісімді" }} ₸
            </p>
            <a href="/products/{{ p[0] }}" class="btn">Толық бетке өту</a>
        </div>
        {% else %}
        <div class="card"><p>Белсенді өнімдер табылмады.</p></div>
        {% endfor %}
    </div>
    """
    return render_page("Каталог", content, items=items, q=q)

@app.route("/products/<slug>")
def product_detail(slug):
    product = None
    try:
        conn = get_read_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, slug, name, summary, description, price, image_url FROM products WHERE slug = %s AND is_active = true", (slug,))
        product = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Қате: {e}", "error")

    if not product:
        abort(404)

    paragraphs = product[4].split("\n\n")
    content = """
    <div class="card">
        <a href="/products" style="color: var(--accent); text-decoration: none;">← Каталогқа қайту</a>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin-top: 20px;">
            <div>
                <img src="{{ product[6] or 'https://via.placeholder.com/600x400' }}" alt="{{ product[2] }}" style="width: 100%; border-radius: 12px;">
            </div>
            <div>
                <h1 style="margin-bottom: 10px;">{{ product[2] }}</h1>
                <p style="font-size: 1.4rem; font-weight: 700; color: var(--primary); margin-bottom: 15px;">
                    Бағасы: {{ "{:,.0f}".format(product[5]) if product[5] else "Сұраныс бойынша" }} ₸
                </p>
                {% for para in paragraphs %}
                    <p style="margin-bottom: 15px; color: #334155;">{{ para }}</p>
                {% endfor %}
                <div style="margin-top: 25px; display: flex; gap: 10px; flex-wrap: wrap;">
                    <a href="/survey?product_id={{ product[0] }}" class="btn">⭐ Пікір қалдыру (Сауалнама)</a>
                    <a href="/contacts" class="btn" style="background: #0f172a;">📞 Кеңес алу</a>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page(product[2], content, product=product, paragraphs=paragraphs)

# 4. САУАЛНАМА (GET/POST /survey -> Primary DB)
@app.route("/survey", methods=["GET", "POST"])
@login_required
def survey():
    if request.method == "POST":
        product_id = request.form.get("product_id")
        rating = request.form.get("rating")
        intent = request.form.get("intent", "").strip()
        comment = request.form.get("comment", "").strip()

        if not product_id or not rating or not intent:
            flash("Барлық міндетті өрістерді толтырыңыз!", "error")
        else:
            try:
                rating_int = int(rating)
                if not (1 <= rating_int <= 5):
                    raise ValueError("Баға 1 мен 5 аралығында болуы тиіс.")
                conn = get_write_conn()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO survey_responses (user_id, product_id, rating, intent, comment) VALUES (%s, %s, %s, %s, %s)",
                    (session["user_id"], product_id, rating_int, intent, comment)
                )
                conn.commit()
                cur.close()
                conn.close()
                flash("Сауалнама жауабыңыз сәтті сақталды! Рақмет!", "success")
                return redirect(url_for("products"))
            except Exception as e:
                flash(f"Сақтау қатесі: {e}", "error")

    selected_id = request.args.get("product_id", "")
    prods = []
    try:
        conn = get_read_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM products WHERE is_active = true ORDER BY name")
        prods = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        pass

    content = """
    <div class="card" style="max-width: 600px; margin: 0 auto;">
        <h2 style="margin-bottom: 15px;">📝 Өнім бойынша сауалнама</h2>
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label for="product_id">Өнімді таңдаңыз *</label>
            <select id="product_id" name="product_id" required>
                <option value="">-- Таңдаңыз --</option>
                {% for p in prods %}
                    <option value="{{ p[0] }}" {% if selected_id == p[0]|string %}selected{% endif %}>{{ p[1] }}</option>
                {% endfor %}
            </select>
            <label for="rating">Бағалау (1–5) *</label>
            <select id="rating" name="rating" required>
                <option value="5">5 — Өте жақсы</option>
                <option value="4">4 — Жақсы</option>
                <option value="3">3 — Қанағаттанарлық</option>
                <option value="2">2 — Нашар</option>
                <option value="1">1 — Өте нашар</option>
            </select>
            <label for="intent">Қолдану ниетіңіз *</label>
            <select id="intent" name="intent" required>
                <option value="Енгізуді жоспарлаймыз">Университетке енгізуді жоспарлаймыз</option>
                <option value="Демо нұсқасын сынау">Демо нұсқасын сынап көргім келеді</option>
                <option value="Тек танысу">Тек ақпарат ретінде танысудамын</option>
            </select>
            <label for="comment">Қосымша пікіріңіз</label>
            <textarea id="comment" name="comment" rows="4" placeholder="Ұсыныстарыңыз бен ескертулеріңіз..."></textarea>
            <button type="submit" class="btn" style="width: 100%;">Жауапты жіберу (Primary DB)</button>
        </form>
    </div>
    """
    return render_page("Сауалнама", content, prods=prods, selected_id=selected_id)

# 5. БАЙЛАНЫСТАР ЖӘНЕ КАРТА (GET /contacts -> Standby DB)
@app.route("/contacts")
def contacts():
    offices = []
    try:
        conn = get_read_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, address, latitude, longitude, phone, email FROM offices ORDER BY id")
        offices = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Кеңселерді жүктеу қатесі: {e}", "error")

    content = """
    <div class="card">
        <h2>📍 Байланыстар және Кеңселер картасы</h2>
        <p style="margin-top: 10px;">
            <b>Жобаның бастапқы коды (GitHub):</b>
            <a href="{{ repo }}" target="_blank" rel="noopener noreferrer" style="color: var(--accent); font-weight: 700;">{{ repo }}</a>
        </p>
    </div>
    <div class="grid">
        {% for o in offices %}
        <div class="card">
            <h3>{{ o[1] }}</h3>
            <p style="margin-top: 8px;"><b>Мекенжай:</b> {{ o[2] }}</p>
            <p><b>Телефон:</b> {{ o[5] or 'Көрсетілмеген' }}</p>
            <p><b>Email:</b> {{ o[6] or 'Көрсетілмеген' }}</p>
            <p style="font-size: 0.85rem; color: var(--muted); margin-bottom: 12px;">Координаттар: {{ o[3] }}, {{ o[4] }}</p>
            <iframe title="Кеңсе картасы — {{ o[1] }}" width="100%" height="250" style="border:0; border-radius:8px;" loading="lazy"
                src="https://www.openstreetmap.org/export/embed.html?bbox={{ o[4]|float - 0.01 }},{{ o[3]|float - 0.01 }},{{ o[4]|float + 0.01 }},{{ o[3]|float + 0.01 }}&layer=mapnik&marker={{ o[3] }},{{ o[4] }}">
            </iframe>
        </div>
        {% else %}
        <div class="card"><p>Кеңселер туралы ақпарат әзірге жоқ.</p></div>
        {% endfor %}
    </div>
    """
    return render_page("Байланыстар", content, offices=offices, repo=GITHUB_REPO_URL)

# 6. ӘКІМШІЛІК БӨЛІМ (/admin/*)
@app.route("/admin/products", methods=["GET", "POST"])
@admin_required
def admin_products():
    if request.method == "POST":
        action = request.form.get("action")
        try:
            conn = get_write_conn()
            cur = conn.cursor()
            if action == "create":
                slug = request.form.get("slug", "").strip()
                name = request.form.get("name", "").strip()
                summary = request.form.get("summary", "").strip()
                description = request.form.get("description", "").strip()
                price = request.form.get("price") or None
                image_url = request.form.get("image_url", "").strip()
                if not slug or not name or not summary or not description:
                    flash("Барлық міндетті өрістерді толтырыңыз!", "error")
                else:
                    cur.execute("""
                        INSERT INTO products (slug, name, summary, description, price, image_url, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, true)
                    """, (slug, name, summary, description, price, image_url))
                    conn.commit()
                    flash("Жаңа өнім Primary серверіне қосылды!", "success")
            elif action == "toggle":
                pid = request.form.get("id")
                cur.execute("UPDATE products SET is_active = NOT is_active WHERE id = %s", (pid,))
                conn.commit()
                flash("Өнім мәртебесі жаңартылды!", "success")
            elif action == "edit":
                pid = request.form.get("id")
                name = request.form.get("name", "").strip()
                summary = request.form.get("summary", "").strip()
                description = request.form.get("description", "").strip()
                price = request.form.get("price") or None
                cur.execute("""
                    UPDATE products SET name=%s, summary=%s, description=%s, price=%s WHERE id=%s
                """, (name, summary, description, price, pid))
                conn.commit()
                flash("Өнім деректері сәтті өзгертілді!", "success")
            cur.close()
            conn.close()
        except Exception as e:
            flash(f"Әкімшілік қате: {e}", "error")
        return redirect(url_for("admin_products"))

    # Өнімдерді Primary серверінен оқу (админ соңғы өзгерістерді кідіріссіз көруі үшін)
    prods = []
    try:
        conn = get_write_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, slug, name, summary, description, price, is_active FROM products ORDER BY id DESC")
        prods = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Қате: {e}", "error")

    content = """
    <div class="card">
        <h2>⚙️ Админ: Жаңа өнім қосу (Primary DB)</h2>
        <form method="POST" style="margin-top: 15px;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <input type="hidden" name="action" value="create">
            <div class="grid">
                <div>
                    <label for="slug">Бірегей Slug (латынша) *</label>
                    <input id="slug" name="slug" required placeholder="smart-library-2026">
                </div>
                <div>
                    <label for="name">Өнім атауы *</label>
                    <input id="name" name="name" required placeholder="Ақылды кітапхана жүйесі">
                </div>
                <div>
                    <label for="price">Бағасы (₸)</label>
                    <input id="price" name="price" type="number" step="0.01" placeholder="120000">
                </div>
                <div>
                    <label for="image_url">Сурет сілтемесі (URL)</label>
                    <input id="image_url" name="image_url" placeholder="https://...">
                </div>
            </div>
            <label for="summary">Қысқаша сипаттама *</label>
            <input id="summary" name="summary" required maxlength="300">
            <label for="description">Толық сипаттама (кемінде екі абзац) *</label>
            <textarea id="description" name="description" rows="4" required></textarea>
            <button type="submit" class="btn">Өнімді жариялау</button>
        </form>
    </div>

    <div class="card">
        <h2>📋 Барлық өнімдерді басқару</h2>
        <table>
            <thead>
                <tr><th>ID</th><th>Slug</th><th>Атауы / Өңдеу</th><th>Мәртебесі</th><th>Әрекет</th></tr>
            </thead>
            <tbody>
                {% for p in prods %}
                <tr>
                    <td>{{ p[0] }}</td>
                    <td>{{ p[1] }}</td>
                    <td>
                        <form method="POST" style="margin:0;">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                            <input type="hidden" name="action" value="edit">
                            <input type="hidden" name="id" value="{{ p[0] }}">
                            <input name="name" value="{{ p[2] }}" required style="margin-bottom:5px;">
                            <input name="summary" value="{{ p[3] }}" required style="margin-bottom:5px;">
                            <textarea name="description" rows="2" required style="margin-bottom:5px;">{{ p[4] }}</textarea>
                            <input name="price" type="number" step="0.01" value="{{ p[5] or '' }}" style="margin-bottom:5px;">
                            <button type="submit" class="btn btn-sm">Сақтау</button>
                        </form>
                    </td>
                    <td>{{ "✅ Белсенді" if p[6] else "🚫 Жасырын" }}</td>
                    <td>
                        <form method="POST" style="margin:0;">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                            <input type="hidden" name="action" value="toggle">
                            <input type="hidden" name="id" value="{{ p[0] }}">
                            <button type="submit" class="btn btn-sm" style="background: #475569;">
                                {{ "Жасыру" if p[6] else "Жариялау" }}
                            </button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page("Өнімдерді басқару", content, prods=prods)

@app.route("/admin/offices", methods=["GET", "POST"])
@admin_required
def admin_offices():
    if request.method == "POST":
        action = request.form.get("action")
        try:
            conn = get_write_conn()
            cur = conn.cursor()
            if action == "create":
                cur.execute("""
                    INSERT INTO offices (name, address, latitude, longitude, phone, email)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    request.form.get("name"), request.form.get("address"),
                    request.form.get("latitude"), request.form.get("longitude"),
                    request.form.get("phone"), request.form.get("email")
                ))
                conn.commit()
                flash("Жаңа кеңсе қосылды!", "success")
            elif action == "delete":
                cur.execute("DELETE FROM offices WHERE id = %s", (request.form.get("id"),))
                conn.commit()
                flash("Кеңсе өшірілді!", "success")
            cur.close()
            conn.close()
        except Exception as e:
            flash(f"Қате: {e}", "error")
        return redirect(url_for("admin_offices"))

    offices = []
    try:
        conn = get_write_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name, address, latitude, longitude, phone, email FROM offices ORDER BY id DESC")
        offices = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        pass

    content = """
    <div class="card">
        <h2>🏢 Жаңа кеңсе қосу</h2>
        <form method="POST" style="margin-top: 15px;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <input type="hidden" name="action" value="create">
            <div class="grid">
                <div><label>Кеңсе атауы *</label><input name="name" required></div>
                <div><label>Мекенжай *</label><input name="address" required></div>
                <div><label>Ендік (Latitude) *</label><input name="latitude" type="number" step="0.000001" required placeholder="51.128200"></div>
                <div><label>Бойлық (Longitude) *</label><input name="longitude" type="number" step="0.000001" required placeholder="71.430400"></div>
                <div><label>Телефон</label><input name="phone"></div>
                <div><label>Email</label><input name="email" type="email"></div>
            </div>
            <button type="submit" class="btn">Кеңсені сақтау</button>
        </form>
    </div>
    <div class="card">
        <h2>Кеңселер тізімі</h2>
        <table>
            <thead><tr><th>Атауы</th><th>Мекенжай</th><th>Координаттар</th><th>Әрекет</th></tr></thead>
            <tbody>
                {% for o in offices %}
                <tr>
                    <td>{{ o[1] }}</td><td>{{ o[2] }}</td><td>{{ o[3] }}, {{ o[4] }}</td>
                    <td>
                        <form method="POST" onsubmit="return confirm('Кеңсені өшіруді растайсыз ба?');" style="margin:0;">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                            <input type="hidden" name="action" value="delete">
                            <input type="hidden" name="id" value="{{ o[0] }}">
                            <button type="submit" class="btn btn-danger btn-sm">Жою</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page("Кеңселерді басқару", content, offices=offices)

@app.route("/admin/users")
@admin_required
def admin_users():
    users = []
    try:
        conn = get_read_conn()
        cur = conn.cursor()
        # password_hash мүлдем таңдалмайды және көрсетілмейді
        cur.execute("SELECT id, email, full_name, role, created_at FROM users ORDER BY id DESC")
        users = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Қате: {e}", "error")

    content = """
    <div class="card">
        <h2>👥 Тіркелген пайдаланушылар (Standby DB)</h2>
        <small style="color: var(--muted);">Қауіпсіздік талабы бойынша құпия сөздер мен хэштер жасырылған.</small>
        <table>
            <thead><tr><th>ID</th><th>Аты-жөні</th><th>Email</th><th>Рөлі</th><th>Тіркелген уақыты</th></tr></thead>
            <tbody>
                {% for u in users %}
                <tr><td>{{ u[0] }}</td><td>{{ u[2] }}</td><td>{{ u[1] }}</td><td><b>{{ u[3] }}</b></td><td>{{ u[4] }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page("Пайдаланушылар", content, users=users)

@app.route("/admin/surveys", methods=["GET", "POST"])
@admin_required
def admin_surveys():
    if request.method == "POST" and request.form.get("action") == "delete":
        try:
            conn = get_write_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM survey_responses WHERE id = %s", (request.form.get("id"),))
            conn.commit()
            cur.close()
            conn.close()
            flash("Сауалнама жауабы жойылды.", "success")
        except Exception as e:
            flash(f"Жою қатесі: {e}", "error")
        return redirect(url_for("admin_surveys"))

    prod_filter = request.args.get("product_id", "")
    rating_filter = request.args.get("rating", "")
    responses = []
    prods = []
    try:
        conn = get_read_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM products ORDER BY name")
        prods = cur.fetchall()

        query = """
            SELECT sr.id, u.full_name, p.name, sr.rating, sr.intent, sr.comment, sr.created_at
            FROM survey_responses sr
            LEFT JOIN users u ON sr.user_id = u.id
            JOIN products p ON sr.product_id = p.id
            WHERE 1=1
        """
        params = []
        if prod_filter:
            query += " AND sr.product_id = %s"
            params.append(prod_filter)
        if rating_filter:
            query += " AND sr.rating = %s"
            params.append(rating_filter)
        query += " ORDER BY sr.id DESC"

        cur.execute(query, tuple(params))
        responses = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Қате: {e}", "error")

    content = """
    <div class="card">
        <h2>📊 Сауалнама жауаптары (Standby DB)</h2>
        <form method="GET" style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 15px;">
            <select name="product_id" style="max-width: 250px; margin: 0;">
                <option value="">Барлық өнімдер</option>
                {% for p in prods %}
                    <option value="{{ p[0] }}" {% if prod_filter == p[0]|string %}selected{% endif %}>{{ p[1] }}</option>
                {% endfor %}
            </select>
            <select name="rating" style="max-width: 180px; margin: 0;">
                <option value="">Барлық бағалар</option>
                {% for r in [5,4,3,2,1] %}
                    <option value="{{ r }}" {% if rating_filter == r|string %}selected{% endif %}>{{ r }} жұлдыз</option>
                {% endfor %}
            </select>
            <button type="submit" class="btn">Сүзгілеу</button>
            <a href="/admin/surveys" class="btn" style="background: #64748b;">Тазарту</a>
        </form>
        <table>
            <thead><tr><th>ID</th><th>Пайдаланушы</th><th>Өнім</th><th>Баға</th><th>Ниет</th><th>Пікір</th><th>Әрекет</th></tr></thead>
            <tbody>
                {% for r in responses %}
                <tr>
                    <td>{{ r[0] }}</td>
                    <td>{{ r[1] or 'Аноним' }}</td>
                    <td>{{ r[2] }}</td>
                    <td><b>{{ r[3] }} / 5</b></td>
                    <td>{{ r[4] }}</td>
                    <td>{{ r[5] or '-' }}</td>
                    <td>
                        <form method="POST" onsubmit="return confirm('Бұл жауапты жоюды растайсыз ба?');" style="margin:0;">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                            <input type="hidden" name="action" value="delete">
                            <input type="hidden" name="id" value="{{ r[0] }}">
                            <button type="submit" class="btn btn-danger btn-sm">Жою</button>
                        </form>
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="7">Жауаптар табылмады.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page("Сауалнама жауаптары", content, responses=responses, prods=prods, prod_filter=prod_filter, rating_filter=rating_filter)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)