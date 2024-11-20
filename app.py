import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Function to get database connection
def get_db_connection():
    conn = sqlite3.connect("timeclock.db")
    conn.row_factory = sqlite3.Row  # Enable row access in dict style
    return conn

# Initialize database
def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS time_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                clock_in TEXT,
                clock_out TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')
        conn.commit()

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Employee Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:  # Validate if the name field is empty
            return render_template('login.html', error="Name cannot be empty")

        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM employees WHERE name=?", (name,))
            employee = c.fetchone()
            if not employee:
                c.execute("INSERT INTO employees (name) VALUES (?)", (name,))
                conn.commit()
                c.execute("SELECT id FROM employees WHERE name=?", (name,))
                employee = c.fetchone()
            return redirect(url_for('clock_in', employee_id=employee[0]))
    return render_template('login.html')

# Clock In Page
@app.route('/clock_in/<int:employee_id>', methods=['GET', 'POST'])
def clock_in(employee_id):
    if request.method == 'POST':
        clock_in_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO time_entries (employee_id, clock_in) VALUES (?, ?)", 
                      (employee_id, clock_in_time))
            conn.commit()
        return redirect(url_for('home'))
    return render_template('clock_in.html', employee_id=employee_id)

# Clock Out Page
@app.route('/clock_out/<int:employee_id>', methods=['GET', 'POST'])
def clock_out(employee_id):
    if request.method == 'POST':
        clock_out_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE time_entries SET clock_out=? WHERE employee_id=? AND clock_out IS NULL",
                      (clock_out_time, employee_id))
            conn.commit()
        return redirect(url_for('home'))
    return render_template('clock_out.html', employee_id=employee_id)

# View Time Entries
@app.route('/view_time/<int:employee_id>')
def view_time(employee_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM time_entries WHERE employee_id=?", (employee_id,))
        time_entries = c.fetchall()
    return render_template('view_time.html', time_entries=time_entries)

if __name__ == '__main__':
    init_db()  # Initialize the database when the app starts
    port = int(os.environ.get('PORT', 5000))  # Get the port from the environment variable, default to 5000
    app.run(host='0.0.0.0', port=port)  # Run the app on all available IPs on the specified port
