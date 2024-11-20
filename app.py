from flask import Flask, render_template, request, redirect, url_for
import csv
import os
from datetime import datetime

app = Flask(__name__)

# File paths
employee_data_file = 'employees.csv'
timeclock_data_file = 'timeclock_data.csv'

# Helper function to write data to a CSV file
def write_to_csv(file, data):
    with open(file, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data)

# Helper function to read CSV files into lists
def read_csv(file):
    data = []
    if os.path.exists(file):
        with open(file, mode='r', newline='') as f:
            reader = csv.reader(f)
            data = list(reader)
    return data

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route for clocking in
@app.route('/clockin', methods=['GET', 'POST'])
def clockin():
    if request.method == 'POST':
        username = request.form['username']
        clockin_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Log the clock-in time
        write_to_csv(timeclock_data_file, [username, clockin_time, 'Clock In'])
        return redirect(url_for('index'))
    
    return render_template('clockin.html')

# Route for clocking out
@app.route('/clockout', methods=['GET', 'POST'])
def clockout():
    if request.method == 'POST':
        username = request.form['username']
        clockout_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Log the clock-out time
        write_to_csv(timeclock_data_file, [username, clockout_time, 'Clock Out'])
        return redirect(url_for('index'))

    return render_template('clockout.html')

if __name__ == '__main__':
    app.run(debug=True)
