from flask import Flask, render_template, request, redirect, url_for, g, session
import sqlite3
import os

app = Flask(__name__)
# مفتاح سري ضروري لتشغيل خاصية تسجيل الدخول (Session)
app.secret_key = 'dr_dinaa_super_secret_key_2026'
app.config['TEMPLATES_AUTO_RELOAD'] = True
DATABASE = 'database.db'

# بيانات الدخول
ADMIN_USERNAME = 'dr dinaa'
ADMIN_PASSWORD = '2991984'

# القائمة التفصيلية مدعومة بالحد الأقصى لكل موضوع (الكوتا)
TOPICS = [
    {"id": 1, "name": "الأسبوع الثاني - تطبيق بسيط جدا (البداية 5 النهاية 8)", "desc": "4 فيديوهات", "max_teams": 1},
    {"id": 2, "name": "الأسبوع الثاني - تطبيق بسيط (البداية 9 النهاية 17)", "desc": "9 فيديوهات", "max_teams": 2},
    {"id": 3, "name": "الأسبوع الثالث - (لعبة) تطبيق متوسط 1 (البداية 19 النهاية 26)", "desc": "8 فيديوهات", "max_teams": 2},
    {"id": 4, "name": "الأسبوع الثالث - (النغمات) تطبيق متوسط 2 (البداية 28 النهاية 32)", "desc": "5 فيديوهات", "max_teams": 1},
    {"id": 5, "name": "الأسبوع الرابع - (الاختبار) تطبيق فوق متوسط (البداية 33 النهاية 43)", "desc": "11 فيديو", "max_teams": 3},
    {"id": 6, "name": "الأسبوع الرابع - برمجة تطبيق موبايل متجر", "desc": "", "max_teams": 2},
    {"id": 7, "name": "الأسبوع الخامس - (الدليل السياحي) فوق متوسط (البداية 44 النهاية 65)", "desc": "20 فيديو", "max_teams": 4},
    {"id": 8, "name": "الأسبوع السادس - برمجة تطبيق موقع عقاري", "desc": "", "max_teams": 2},
    {"id": 9, "name": "الأسبوع السابع - برمجة تطبيق الشات بوت (البداية 66 النهاية 81)", "desc": "16 فيديو", "max_teams": 3},
    {"id": 10, "name": "الأسبوع العاشر - برمجة تطبيق لادارة المهام (البداية 83 النهاية 97)", "desc": "15 فيديو", "max_teams": 3},
    {"id": 11, "name": "الأسبوع الحادي عشر - فلاتر علي الماشي + Firebase (من 97 للآخر)", "desc": "", "max_teams": 3}
]

def get_topic_by_id(topic_id):
    for t in TOPICS:
        if t['id'] == topic_id:
            return t
    return None

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                student_id TEXT NOT NULL,
                FOREIGN KEY (team_id) REFERENCES teams (id)
            )
        ''')
        db.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    if request.method == 'POST':
        topic_id = int(request.form['topic_id'])
        
        # حماية إضافية للباك إند: التأكد من أن الموضوع لم يتخطى الحد الأقصى
        topic_info = get_topic_by_id(topic_id)
        if not topic_info:
            return "موضوع غير صالح."
            
        current_count = db.execute('SELECT COUNT(id) FROM teams WHERE topic_id = ?', (topic_id,)).fetchone()[0]
        if current_count >= topic_info['max_teams']:
            return "عذراً، لقد اكتمل الحد الأقصى للفرق المسموح بها في هذا الموضوع! يرجى العودة للخلف واختيار موضوع آخر."
        
        cursor = db.cursor()
        cursor.execute('INSERT INTO teams (topic_id) VALUES (?)', (topic_id,))
        team_id = cursor.lastrowid
        
        for i in range(1, 6):
            name = request.form.get(f'name{i}')
            std_id = request.form.get(f'id{i}')
            if name and std_id:
                db.execute('INSERT INTO members (team_id, name, student_id) VALUES (?, ?, ?)', (team_id, name, std_id))
        
        db.commit()
        return render_template('success.html')

    counts_query = db.execute('SELECT topic_id, COUNT(id) as count FROM teams GROUP BY topic_id').fetchall()
    topic_counts = {row['topic_id']: row['count'] for row in counts_query}
    
    topics_with_counts = []
    for t in TOPICS:
        t_copy = dict(t)
        t_copy['count'] = topic_counts.get(t['id'], 0)
        t_copy['is_full'] = t_copy['count'] >= t_copy['max_teams']
        topics_with_counts.append(t_copy)
        
    return render_template('index.html', topics=topics_with_counts)

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'اسم المستخدم أو كلمة المرور غير صحيحة!'
    return render_template('login.html', error=error)

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    # التأكد من أن المستخدم سجل دخوله أولاً
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    db = get_db()
    teams_query = db.execute('SELECT * FROM teams ORDER BY topic_id').fetchall()
    teams = []
    for t in teams_query:
        members = db.execute('SELECT name, student_id FROM members WHERE team_id = ?', (t['id'],)).fetchall()
        topic_info = get_topic_by_id(t['topic_id'])
        teams.append({
            'team_id': t['id'],
            'topic_name': topic_info['name'] if topic_info else f"موضوع غير معروف",
            'members': members
        })
    return render_template('admin.html', teams=teams)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
