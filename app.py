from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Initialize Flask app
app = Flask(__name__)

# Secret key for session management (set via Render environment variable)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///timeclock.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    logs = db.relationship('TimeLog', backref='user', lazy=True)

# TimeLog model
class TimeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_out = db.Column(db.DateTime, nullable=True)

@app.route('/')
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            return redirect(url_for('home'))
        return 'Invalid credentials. Try again.'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    logs = TimeLog.query.filter_by(user_id=user.id).order_by(TimeLog.clock_in.desc()).all()
    return render_template('user_dashboard.html', user=user, logs=logs)

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

@app.route('/clock_in', methods=['POST'])
def clock_in():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    new_log = TimeLog(user_id=session['user_id'], clock_in=datetime.now())
    db.session.add(new_log)
    db.session.commit()
    return redirect(url_for('user_dashboard'))

@app.route('/clock_out/<int:log_id>', methods=['POST'])
def clock_out(log_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    log = TimeLog.query.get(log_id)
    if log and log.user_id == session['user_id']:
        log.clock_out = datetime.now()
        db.session.commit()
    return redirect(url_for('user_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
