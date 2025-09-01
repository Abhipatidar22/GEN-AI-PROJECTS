from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os, hashlib, datetime as dt
from utils import simple_sentiment, simple_intent, extract_keywords
from recommender import recommend

APP_SECRET = os.environ.get('APP_SECRET', 'dev-secret-key')
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

app = Flask(__name__)
app.secret_key = APP_SECRET

# ---------- DB Helpers ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        age INTEGER,
        profession TEXT
    );
    CREATE TABLE IF NOT EXISTS journals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        mood INTEGER,
        sentiment REAL,
        intent TEXT,
        keywords TEXT,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        status TEXT DEFAULT 'active',
        progress INTEGER DEFAULT 0,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        day TEXT,
        mood INTEGER
    );
    CREATE TABLE IF NOT EXISTS recos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        created_at TEXT
    );
    ''')
    conn.commit()

    # Seed demo user if not exists
    cur.execute("SELECT id FROM users WHERE email=?", ('demo@coach.app',))
    if cur.fetchone() is None:
        pwd = hashlib.sha256('demo123'.encode()).hexdigest()
        cur.execute("INSERT INTO users (name, email, password_hash, age, profession) VALUES (?,?,?,?,?)",
                    ('Demo User', 'demo@coach.app', pwd, 24, 'Student'))
        user_id = cur.lastrowid
        # Seed goals
        demo_goals = ['Read 10 pages daily', 'Morning jog 3x/week', 'Build portfolio project']
        for title in demo_goals:
            cur.execute("INSERT INTO goals (user_id, title, status, progress, created_at) VALUES (?,?,?,?,?)",
                        (user_id, title, 'active', 20, dt.datetime.utcnow().isoformat()))
        # Seed journals & checkins last 7 days
        moods = [3,4,2,5,3,4,2]
        notes = [
            'Feeling good and confident about my study plan.',
            'Requesting advice on how to stick to habits.',
            'Tired and a bit stressed today.',
            'Great focus sprint this morning, proud of progress.',
            'A bit lost but hopeful.',
            'Made some progress on my project goal.',
            'Frustrated and anxious about deadlines.'
        ]
        today = dt.date.today()
        for i, (m, n) in enumerate(zip(moods, notes)):
            day = today - dt.timedelta(days=(6 - i))
            s = simple_sentiment(n)
            intent = simple_intent(n)
            keys = ",".join(extract_keywords(n))
            cur.execute("INSERT INTO journals (user_id, content, mood, sentiment, intent, keywords, created_at) VALUES (?,?,?,?,?,?,?)",
                        (user_id, n, m, s, intent, keys, dt.datetime.combine(day, dt.time(9,0)).isoformat()))
            cur.execute("INSERT INTO checkins (user_id, day, mood) VALUES (?,?,?)",
                        (user_id, day.isoformat(), m))
        conn.commit()
    conn.close()

def require_login():
    if 'user_id' not in session:
        return redirect(url_for('login'))

# ---------- Auth ----------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        age = request.form.get('age') or None
        profession = request.form.get('profession')
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (name,email,password_hash,age,profession) VALUES (?,?,?,?,?)",
                         (name, email, pwd_hash, age, profession))
            conn.commit()
            conn.close()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db()
        cur = conn.execute("SELECT * FROM users WHERE email=? AND password_hash=?", (email, pwd_hash))
        user = cur.fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash('Welcome back Abhinandan Ji!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

# ---------- Pages ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    uid = session['user_id']
    conn = get_db()
    goals = conn.execute("SELECT * FROM goals WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    journals = conn.execute("SELECT * FROM journals WHERE user_id=? ORDER BY created_at DESC LIMIT 10", (uid,)).fetchall()
    checkins = conn.execute("SELECT day,mood FROM checkins WHERE user_id=? ORDER BY day", (uid,)).fetchall()
    conn.close()
    # Prepare points for inline SVG
    points = [(i, r['mood']) for i, r in enumerate(checkins)]
    return render_template('dashboard.html', goals=goals, journals=journals, checkins=checkins, points=points)

@app.route('/journal', methods=['GET','POST'])
def journal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    uid = session['user_id']
    if request.method == 'POST':
        content = request.form.get('content')
        mood = int(request.form.get('mood') or 3)
        sentiment = simple_sentiment(content)
        intent = simple_intent(content)
        keys = ",".join(extract_keywords(content))
        conn = get_db()
        conn.execute("INSERT INTO journals (user_id, content, mood, sentiment, intent, keywords, created_at) VALUES (?,?,?,?,?,?,?)",
                     (uid, content, mood, sentiment, intent, keys, dt.datetime.utcnow().isoformat()))
        # also log checkin
        today = dt.date.today().isoformat()
        conn.execute("INSERT INTO checkins (user_id, day, mood) VALUES (?,?,?)", (uid, today, mood))
        conn.commit()
        conn.close()
        flash('Journal saved with analysis.', 'success')
        return redirect(url_for('journal'))
    # list
    conn = get_db()
    journals = conn.execute("SELECT * FROM journals WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    conn.close()
    return render_template('journal.html', journals=journals)

@app.route('/goals', methods=['GET','POST'])
def goals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    uid = session['user_id']
    conn = get_db()
    if request.method == 'POST':
        title = request.form.get('title')
        progress = int(request.form.get('progress') or 0)
        conn.execute("INSERT INTO goals (user_id, title, status, progress, created_at) VALUES (?,?,?,?,?)",
                     (uid, title, 'active', progress, dt.datetime.utcnow().isoformat()))
        conn.commit()
        flash('Goal added.', 'success')
    goals = conn.execute("SELECT * FROM goals WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    conn.close()
    return render_template('goals.html', goals=goals)

@app.post('/goals/update/<int:goal_id>')
def update_goal(goal_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    progress = int(request.form.get('progress') or 0)
    status = request.form.get('status') or 'active'
    conn = get_db()
    conn.execute("UPDATE goals SET progress=?, status=? WHERE id=? AND user_id=?",
                 (progress, status, goal_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Goal updated.', 'success')
    return redirect(url_for('goals'))

@app.route('/coaching')
def coaching():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    uid = session['user_id']
    conn = get_db()
    # gather latest mood, some keywords, current goals
    last = conn.execute("SELECT mood FROM journals WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (uid,)).fetchone()
    g = conn.execute("SELECT title, status, progress FROM goals WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    j = conn.execute("SELECT keywords FROM journals WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (uid,)).fetchone()
    conn.close()
    last_mood = last['mood'] if last else None
    keywords = (j['keywords'].split(',') if j and j['keywords'] else [])
    goals = [dict(title=row['title'], status=row['status'], progress=row['progress']) for row in g]
    recos = recommend(goals, last_mood=last_mood, keywords=keywords)
    return render_template('coaching.html', recos=recos, last_mood=last_mood, goals=goals, keywords=keywords)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# ---------- Startup ----------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
