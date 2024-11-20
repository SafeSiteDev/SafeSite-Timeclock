import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Secret key for session management
app.secret_key = os.environ.get('SECRET_KEY', 'your_default_secret_key')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///timeclock.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Admin or Employee

class Timesheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)

# Initialize database before the first request
@app.before_first_request
def create_tables():
    db.create_all()

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_role'] = user.role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('employee_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']
            hashed_password = generate_password_hash(password, method='sha256')

            # Check if username already exists
            if User.query.filter_by(username=username).first():
                return render_template('register.html', error="Username already exists. Please choose another.")

            new_user = User(username=username, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login'))
        except Exception as e:
            return render_template('register.html', error=f"An error occurred: {e}")
    return render_template('register.html')

# Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('login'))

    users = User.query.filter(User.role != 'admin').all()
    timesheets = Timesheet.query.all()
    return render_template('admin_dashboard.html', users=users, timesheets=timesheets)

# Employee Dashboard
@app.route('/employee_dashboard', methods=['GET', 'POST'])
def employee_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'employee':
        return redirect(url_for('login'))

    user_id = session['user_id']
    if request.method == 'POST':
        action = request.form['action']
        if action == 'clock_in':
            timesheet = Timesheet(user_id=user_id, clock_in=datetime.now())
            db.session.add(timesheet)
            db.session.commit()
        elif action == 'clock_out':
            timesheet = Timesheet.query.filter_by(user_id=user_id, clock_out=None).first()
            if timesheet:
                timesheet.clock_out = datetime.now()
                db.session.commit()

    timesheets = Timesheet.query.filter_by(user_id=user_id).all()
    return render_template('employee_dashboard.html', timesheets=timesheets)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
