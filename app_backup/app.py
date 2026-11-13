import os
import secrets
import psycopg2
from functools import wraps
from flask import Flask, request, redirect, render_template_string, session, url_for, abort, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "smart-campus-backup-secret-2026")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

WRITE_DB = os.getenv("WRITE_DB_URL")
READ_DB = os.getenv("READ_DB_URL")
SITE_ENV = os.getenv("SITE_ENV", "BACKUP")
GITHUB_REPO_URL = "https://github.com/smart-campus-team/smart-campus-portal"

def get_write_conn():
    return psycopg2.connect(WRITE_DB)

def get_read_conn():
    return psycopg2.connect(READ_DB)

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

# Ортақ HTML шаблоны (Резервтік ортаға арналған сары плашкасымен)
BASE_HTML = """
<!DOCTYPE html>
<html lang="kk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} — Smart Campus (BACKUP)</title>
<style>
    :root { --primary: #b45309; --accent: #d97706; --bg: #f8fafc; --card: #ffffff; --text: #0f172a; --muted: #64748b; --danger: #dc2626; --success: #16a34a; }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
    body { background: var(--bg); color: var(--text); display: flex; flex-direction: column; min-height: 100vh; line-height: 1.6; }
    
    .backup-banner {
        background: #f59e0b;
        color: #451a03;
        text-align: center;
        padding: 8px;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
    }

    header { background: linear-gradient(135deg, #b45309 0%, #d97706 100%); color: white; padding: 0 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .nav { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; min-height: 70px; flex-wrap: wrap; gap: 10px; }
    .logo { color: white; text-decoration: none; font-weight: 700; font-size: 1.3rem; }
    .links { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    .links a { color: rgba(255,255,255,0.9); text-decoration: none; padding: 6px 12px; border-radius: 6px; font-size: 0.95rem; }
    .links a:hover { background: rgba(255,255,255,0.15); color: white; }
    .admin-link { background: #451a03 !important; color: #fef3c7 !important; font-weight: 700; }
    
    .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; flex: 1; width: 100%; }
    .card { background: var(--card); border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }
    .btn { display: inline-block; background: var(--accent); color: white; padding: 10px 18px; border-radius: 8px; text-decoration: none; border: none; cursor: pointer; font-weight: 600; font-size: 0.95rem; }
    .btn:hover { background: #b45309; }
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

<div class="backup-banner">
    ⚠️ НА ВНИМАНИЕ: Бұл резервтік/тесттік орта (BACKUP SERVER — Порт 8083)
</div>

<header>
    <div class="nav">
        <a href="/" class="logo">🎓 Smart Campus (Backup)</a>
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
    &copy; 2026 Smart Campus System (Backup Environment)
</footer>
</body>
</html>
"""

def render_page(title, content, **kwargs):
    inner = render_template_string(content, csrf_token=session.get("csrf_token"), **kwargs)
    return render_template_string(BASE_HTML, title=title, content=inner)

@app.route("/")
def index():
    content = """
    <div class="card" style="background: linear-gradient(135deg, #b45309, #d97706); color: white; padding: 40px;">
        <h1 style="font-size: 2rem; margin-bottom: 12px;">Тесттік / Резервтік ортаға қош келдіңіз!</h1>
        <p style="font-size: 1.1rem; opacity: 0.95; margin-bottom: 20px;">
            Бұл портта (8083) сіз негізгі базаға қауіп төндірмей, өзгерістерді сынай аласыз.
        </p>
        <a href="/products" class="btn" style="background: white; color: #b45309;">Өнімдер каталогына өту →</a>
    </div>
    """
    return render_page("Басты бет (Backup)", content)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not full_name or not email or not password:
            flash("Барлық өрістерді толтырыңыз!", "error")
        elif password != confirm:
            flash("Парольдер сәйкес келмейді!", "error")
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
                flash("Тіркелу сәтті аяқталды!", "success")
                return redirect(url_for("login"))
            except Exception as e:
                flash(f"Қате (Email бос болмауы тиіс): {e}", "error")

    content = """
    <div class="card" style="max-width: 480px; margin: 0 auto;">
        <h2>Тіркелу (Backup)</h2>
        <form method="POST" style="margin-top:15px;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label>Аты-жөні *</label><input name="full_name" required>
            <label>Email *</label><input name="email" type="email" required>
            <label>Пароль *</label><input name="password" type="password" required>
            <label>Парольді растау *</label><input name="confirm_password" type="password" required>
            <button type="submit" class="btn" style="width:100%;">Тіркелу</button>
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
                flash("Жүйеге сәтті кірдіңіз!", "success")
                return redirect(url_for("index"))
            else:
                flash("Email немесе пароль қате!", "error")
        except Exception as e:
            flash(f"Қате: {e}", "error")

    content = """
    <div class="card" style="max-width: 450px; margin: 0 auto;">
        <h2>Кіру (Backup)</h2>
        <form method="POST" style="margin-top:15px;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label>Email *</label><input name="email" type="email" required>
            <label>Пароль *</label><input name="password" type="password" required>
            <button type="submit" class="btn" style="width:100%;">Кіру</button>
        </form>
    </div>
    """
    return render_page("Кіру", content)

@app.route("/logout")
def logout():
    session.clear()
    flash("Жүйеден шықтыңыз.", "success")
    return redirect(url_for("index"))

@app.route("/profile")
@login_required
def profile():
    content = """
    <div class="card" style="max-width: 600px; margin: 0 auto;">
        <h2>Профиль (Backup)</h2>
        <p style="margin-top:15px;"><b>Аты:</b> {{ session.get('full_name') }}</p>
        <p><b>Email:</b> {{ session.get('email') }}</p>
        <p><b>Рөлі:</b> {{ session.get('role') }}</p>
    </div>
    """
    return render_page("Профиль", content)

@app.route("/products")
def products():
    q = request.args.get("q", "").strip()
    items = []
    try:
        conn = get_read_conn()
        cur = conn.cursor()
        if q:
            cur.execute("SELECT slug, name, summary, price, image_url FROM products WHERE is_active = true AND (name ILIKE %s OR summary ILIKE %s) ORDER BY id DESC", (f"%{q}%", f"%{q}%"))
        else:
            cur.execute("SELECT slug, name, summary, price, image_url FROM products WHERE is_active = true ORDER BY id DESC")
        items = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        flash(f"Standby қатесі: {e}", "error")

    content = """
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <h2>📦 Каталог (Standby DB)</h2>
            <form method="GET" style="display: flex; gap: 10px; max-width: 350px; width: 100%; margin:0;">
                <input name="q" value="{{ q }}" placeholder="Іздеу..." style="margin:0;">
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
            <p style="font-weight: 700; color: var(--primary); margin-bottom: 15px;">{{ "{:,.0f}".format(p[3]) if p[3] else "Сұраныс бойынша" }} ₸</p>
            <a href="/products/{{ p[0] }}" class="btn">Толығырақ</a>
        </div>
        {% else %}
        <div class="card"><p>Өнімдер жоқ.</p></div>
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
        <a href="/products" style="color: var(--accent); text-decoration: none;">← Қайту</a>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin-top: 20px;">
            <div><img src="{{ product[6] or 'https://via.placeholder.com/600x400' }}" style="width: 100%; border-radius: 12px;"></div>
            <div>
                <h1>{{ product[2] }}</h1>
                <p style="font-size: 1.3rem; font-weight: 700; color: var(--primary); margin: 15px 0;">Бағасы: {{ "{:,.0f}".format(product[5]) if product[5] else "—" }} ₸</p>
                {% for para in paragraphs %}
                    <p style="margin-bottom: 15px;">{{ para }}</p>
                {% endfor %}
                <div style="margin-top: 20px;">
                    <a href="/survey?product_id={{ product[0] }}" class="btn">⭐ Пікір қалдыру</a>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page(product[2], content, product=product, paragraphs=paragraphs)

@app.route("/survey", methods=["GET", "POST"])
@login_required
def survey():
    if request.method == "POST":
        product_id = request.form.get("product_id")
        rating = request.form.get("rating")
        intent = request.form.get("intent", "").strip()
        comment = request.form.get("comment", "").strip()

        try:
            conn = get_write_conn()
            cur = conn.cursor()
            cur.execute("INSERT INTO survey_responses (user_id, product_id, rating, intent, comment) VALUES (%s, %s, %s, %s, %s)", (session["user_id"], product_id, int(rating), intent, comment))
            conn.commit()
            cur.close()
            conn.close()
            flash("Сауалнама сақталды!", "success")
            return redirect(url_for("products"))
        except Exception as e:
            flash(f"Қате: {e}", "error")

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
        <h2>📝 Сауалнама</h2>
        <form method="POST" style="margin-top:15px;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label>Өнім *</label>
            <select name="product_id" required>
                <option value="">-- Таңдаңыз --</option>
                {% for p in prods %}
                    <option value="{{ p[0] }}" {% if selected_id == p[0]|string %}selected{% endif %}>{{ p[1] }}</option>
                {% endfor %}
            </select>
            <label>Баға (1-5) *</label>
            <select name="rating" required>
                <option value="5">5 — Өте жақсы</option>
                <option value="4">4 — Жақсы</option>
                <option value="3">3 — Қанағаттанарлық</option>
                <option value="2">2 — Нашар</option>
                <option value="1">1 — Өте нашар</option>
            </select>
            <label>Ниет *</label>
            <select name="intent" required>
                <option value="Енгізуді жоспарлаймыз">Енгізуді жоспарлаймыз</option>
                <option value="Демо нұсқа">Демо нұсқасын сынау</option>
                <option value="Тек танысу">Тек танысу</option>
            </select>
            <label>Пікір</label>
            <textarea name="comment" rows="3"></textarea>
            <button type="submit" class="btn" style="width:100%;">Жіберу</button>
        </form>
    </div>
    """
    return render_page("Сауалнама", content, prods=prods, selected_id=selected_id)

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
    except Exception:
        pass

    content = """
    <div class="card">
        <h2>📍 Байланыстар</h2>
        <p style="margin-top:10px;">GitHub: <a href="{{ repo }}" target="_blank" style="color:var(--accent); font-weight:700;">{{ repo }}</a></p>
    </div>
    <div class="grid">
        {% for o in offices %}
        <div class="card">
            <h3>{{ o[1] }}</h3>
            <p style="margin-top:8px;"><b>Мекенжай:</b> {{ o[2] }}</p>
            <p><b>Телефон:</b> {{ o[5] or '—' }}</p>
            <iframe width="100%" height="200" style="border:0; border-radius:8px; margin-top:10px;" loading="lazy"
                src="https://www.openstreetmap.org/export/embed.html?bbox={{ o[4]|float - 0.01 }},{{ o[3]|float - 0.01 }},{{ o[4]|float + 0.01 }},{{ o[3]|float + 0.01 }}&layer=mapnik&marker={{ o[3] }},{{ o[4] }}">
            </iframe>
        </div>
        {% endfor %}
    </div>
    """
    return render_page("Байланыстар", content, offices=offices, repo=GITHUB_REPO_URL)

@app.route("/admin/products", methods=["GET", "POST"])
@admin_required
def admin_products():
    if request.method == "POST":
        action = request.form.get("action")
        try:
            conn = get_write_conn()
            cur = conn.cursor()
            if action == "create":
                cur.execute("INSERT INTO products (slug, name, summary, description, price, image_url, is_active) VALUES (%s, %s, %s, %s, %s, %s, true)",
                            (request.form.get("slug"), request.form.get("name"), request.form.get("summary"), request.form.get("description"), request.form.get("price") or None, request.form.get("image_url")))
                conn.commit()
                flash("Өнім қосылды!", "success")
            elif action == "toggle":
                cur.execute("UPDATE products SET is_active = NOT is_active WHERE id = %s", (request.form.get("id"),))
                conn.commit()
                flash("Мәртебе өзгерді!", "success")
            cur.close()
            conn.close()
        except Exception as e:
            flash(f"Қате: {e}", "error")
        return redirect(url_for("admin_products"))

    prods = []
    try:
        conn = get_write_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, slug, name, summary, description, price, is_active FROM products ORDER BY id DESC")
        prods = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        pass

    content = """
    <div class="card">
        <h2>⚙️ Өнім қосу (Backup Admin)</h2>
        <form method="POST" style="margin-top:15px;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <input type="hidden" name="action" value="create">
            <div class="grid">
                <div><label>Slug *</label><input name="slug" required></div>
                <div><label>Атауы *</label><input name="name" required></div>
                <div><label>Бағасы</label><input name="price" type="number" step="0.01"></div>
                <div><label>Сурет URL</label><input name="image_url"></div>
            </div>
            <label>Қысқаша *</label><input name="summary" required>
            <label>Сипаттама *</label><textarea name="description" rows="3" required></textarea>
            <button type="submit" class="btn">Қосу</button>
        </form>
    </div>
    <div class="card">
        <h2>Өнімдер тізімі</h2>
        <table>
            <thead><tr><th>ID</th><th>Атауы</th><th>Мәртебесі</th><th>Әрекет</th></tr></thead>
            <tbody>
                {% for p in prods %}
                <tr>
                    <td>{{ p[0] }}</td><td>{{ p[2] }}</td><td>{{ "Актив" if p[6] else "Жасырын" }}</td>
                    <td>
                        <form method="POST" style="margin:0;">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                            <input type="hidden" name="action" value="toggle">
                            <input type="hidden" name="id" value="{{ p[0] }}">
                            <button type="submit" class="btn btn-sm">Өзгерту</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page("Админ: Өнімдер", content, prods=prods)

@app.route("/admin/offices", methods=["GET", "POST"])
@admin_required
def admin_offices():
    if request.method == "POST":
        try:
            conn = get_write_conn()
            cur = conn.cursor()
            cur.execute("INSERT INTO offices (name, address, latitude, longitude, phone, email) VALUES (%s, %s, %s, %s, %s, %s)",
                        (request.form.get("name"), request.form.get("address"), request.form.get("latitude"), request.form.get("longitude"), request.form.get("phone"), request.form.get("email")))
            conn.commit()
            cur.close()
            conn.close()
            flash("Кеңсе қосылды!", "success")
        except Exception as e:
            flash(f"Қате: {e}", "error")
        return redirect(url_for("admin_offices"))
    return render_page("Кеңселер", "<div class='card'><h2>Кеңсе басқару</h2><p>Негізгі нұсқадағыдай жұмыс істейді.</p></div>")

@app.route("/admin/users")
@admin_required
def admin_users():
    users = []
    try:
        conn = get_read_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, email, full_name, role, created_at FROM users ORDER BY id DESC")
        users = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        pass

    content = """
    <div class="card">
        <h2>👥 Пайдаланушылар (Backup Standby)</h2>
        <table>
            <thead><tr><th>ID</th><th>Аты</th><th>Email</th><th>Рөл</th></tr></thead>
            <tbody>
                {% for u in users %}
                <tr><td>{{ u[0] }}</td><td>{{ u[2] }}</td><td>{{ u[1] }}</td><td><b>{{ u[3] }}</b></td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page("Пайдаланушылар", content, users=users)

@app.route("/admin/surveys")
@admin_required
def admin_surveys():
    responses = []
    try:
        conn = get_read_conn()
        cur = conn.cursor()
        cur.execute("SELECT sr.id, u.full_name, p.name, sr.rating, sr.intent, sr.comment FROM survey_responses sr LEFT JOIN users u ON sr.user_id = u.id JOIN products p ON sr.product_id = p.id ORDER BY sr.id DESC")
        responses = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        pass

    content = """
    <div class="card">
        <h2>📊 Сауалнама жауаптары (Backup Standby)</h2>
        <table>
            <thead><tr><th>ID</th><th>Пайдаланушы</th><th>Өнім</th><th>Баға</th><th>Ниет</th><th>Пікір</th></tr></thead>
            <tbody>
                {% for r in responses %}
                <tr><td>{{ r[0] }}</td><td>{{ r[1] or '—' }}</td><td>{{ r[2] }}</td><td>{{ r[3] }}/5</td><td>{{ r[4] }}</td><td>{{ r[5] or '—' }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    """
    return render_page("Жауаптар", content, responses=responses)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)