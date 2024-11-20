from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Use your own secret key
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your actual secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timeclock.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # admin or employee

    def __repr__(self):
        return f"<User {self.username}>"

# Define Timesheet model
class Timesheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    clock_out = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('timesheets', lazy=True))

    def __repr__(self):
        return f"<Timesheet {self.user_id} - {self.clock_in} to {self.clock_out}>"

# Initialize the database at the start if it doesn't exist
@app.before_first_request
def create_tables():
    # Create all database tables if they don't exist
    db.create_all()

# Routes for the application
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard')) if session['role'] == 'admin' else redirect(url_for('employee_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard') if user.role == 'admin' else url_for('employee_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    users = User.query.all()
    timesheets = Timesheet.query.all()
    return render_template('admin_dashboard.html', users=users, timesheets=timesheets)

@app.route('/employee/dashboard')
def employee_dashboard():
    if 'user_id' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))

    return render_template('employee_dashboard.html')

@app.route('/clock_in_out', methods=['POST'])
def clock_in_out():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_timesheet = Timesheet.query.filter_by(user_id=user_id, clock_out=None).first()

    if user_timesheet:  # Clock out if already clocked in
        user_timesheet.clock_out = datetime.utcnow()
        db.session.commit()
        flash('Clocked out successfully.', 'success')
    else:  # Clock in if not already clocked in
        new_timesheet = Timesheet(user_id=user_id)
        db.session.add(new_timesheet)
        db.session.commit()
        flash('Clocked in successfully.', 'success')

    return redirect(url_for('employee_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
