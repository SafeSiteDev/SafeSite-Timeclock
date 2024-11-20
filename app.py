from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timeclock.db'
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback_key_for_local_development")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'

# Clocking Model
class ClockEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_out = db.Column(db.DateTime, nullable=True)
    total_hours = db.Column(db.Float, nullable=True)

    user = db.relationship('User', back_populates="clock_entries")

User.clock_entries = db.relationship('ClockEntry', back_populates='user')

db.create_all()  # Create tables if they don't exist

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, password=password).first()
        
        if user:
            session['user_id'] = user.id
            session['role'] = user.role  # Track role (admin/user)
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials', 400
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if user.role == 'admin':
        users = User.query.all()  # Get all users
        return render_template('admin_dashboard.html', users=users)
    
    else:
        clock_entries = ClockEntry.query.filter_by(user_id=user.id).all()
        return render_template('user_dashboard.html', clock_entries=clock_entries)

@app.route('/clock_in', methods=['POST'])
def clock_in():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if user:
        clock_in_time = datetime.now()
        clock_entry = ClockEntry(user_id=user.id, clock_in=clock_in_time)
        db.session.add(clock_entry)
        db.session.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/clock_out', methods=['POST'])
def clock_out():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if user:
        clock_entry = ClockEntry.query.filter_by(user_id=user.id, clock_out=None).first()
        if clock_entry:
            clock_out_time = datetime.now()
            clock_entry.clock_out = clock_out_time
            clock_entry.total_hours = (clock_out_time - clock_entry.clock_in).seconds / 3600  # Calculate hours
            db.session.commit()
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
