from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'dr_dinaa_super_secret_key_2026'

db_url = os.environ.get("DATABASE_URL", "sqlite:///database.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, nullable=False)
    members = db.relationship('Member', backref='team', lazy=True, cascade="all, delete-orphan")

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    student_id = db.Column(db.String(50), nullable=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        topic_id = int(request.form['topic_id'])
        topic_info = get_topic_by_id(topic_id)
        if not topic_info:
            return "موضوع غير صالح."
            
        current_count = Team.query.filter_by(topic_id=topic_id).count()
        if current_count >= topic_info['max_teams']:
            return "عذراً، لقد اكتمل الحد الأقصى للفرق المسموح بها في هذا الموضوع!"
        
        new_team = Team(topic_id=topic_id)
        db.session.add(new_team)
        db.session.commit()
        
        for i in range(1, 6):
            name = request.form.get(f'name{i}')
            std_id = request.form.get(f'id{i}')
            if name and std_id:
                new_member = Member(team_id=new_team.id, name=name, student_id=std_id)
                db.session.add(new_member)
        
        db.session.commit()
        return render_template('success.html')

    topics_with_counts = []
    for t in TOPICS:
        t_copy = dict(t)
        t_copy['count'] = Team.query.filter_by(topic_id=t['id']).count()
        t_copy['is_full'] = t_copy['count'] >= t_copy['max_teams']
        topics_with_counts.append(t_copy)
        
    return render_template('index.html', topics=topics_with_counts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == 'dr dinaa' and request.form['password'] == '2991984':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'اسم المستخدم أو كلمة المرور غير صحيحة!'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    teams = Team.query.order_by(Team.topic_id).all()
    teams_data = []
    for t in teams:
        topic_info = get_topic_by_id(t.topic_id)
        teams_data.append({
            'team_id': t.id,
            'topic_name': topic_info['name'] if topic_info else "موضوع غير معروف",
            'members': t.members
        })
    return render_template('admin.html', teams=teams_data)

@app.route('/admin/delete/<int:team_id>', methods=['POST'])
def delete_team(team_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    team = Team.query.get_or_404(team_id)
    db.session.delete(team)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:team_id>', methods=['GET', 'POST'])
def edit_team(team_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    team = Team.query.get_or_404(team_id)
    
    if request.method == 'POST':
        new_topic_id = int(request.form['topic_id'])
        if new_topic_id != team.topic_id:
            topic_info = get_topic_by_id(new_topic_id)
            current_count = Team.query.filter_by(topic_id=new_topic_id).count()
            if current_count >= topic_info['max_teams']:
                return "عذراً، الحد الأقصى للموضوع الجديد مكتمل!"
            team.topic_id = new_topic_id

        # Update members
        Member.query.filter_by(team_id=team.id).delete()
        for i in range(1, 6):
            name = request.form.get(f'name{i}')
            std_id = request.form.get(f'id{i}')
            if name and std_id:
                new_member = Member(team_id=team.id, name=name, student_id=std_id)
                db.session.add(new_member)
        
        db.session.commit()
        return redirect(url_for('admin'))
        
    return render_template('edit.html', team=team, topics=TOPICS, members=team.members)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
