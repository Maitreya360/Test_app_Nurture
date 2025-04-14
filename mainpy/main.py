from flask import Flask, render_template, request, redirect, url_for, session
import os
import csv
import json
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

USER_FILE = 'data/users.csv'
RESULT_FILE = 'data/results.csv'

# Ensure data folder exists
os.makedirs('data', exist_ok=True)

# Initialize CSV files if they don't exist
if not os.path.exists(USER_FILE):
    with open(USER_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'phone'])

if not os.path.exists(RESULT_FILE):
    with open(RESULT_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'phone', 'phase', 'score', 'login_time', 'question_ids'])

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        session['name'] = name
        session['phone'] = phone

        exists = False
        with open(USER_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if row and row[0] == name and row[1] == phone:
                    exists = True
                    break

        if not exists:
            with open(USER_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([name, phone])

        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('name') or not session.get('phone'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/phase/<int:phase_id>', methods=['GET', 'POST'])
def phase(phase_id):
    name = session.get('name')
    phone = session.get('phone')

    if not name or not phone:
        return redirect(url_for('login'))

    file_path = f'data/questions_phase{phase_id}.json'
    if not os.path.exists(file_path):
        return f"No questions available for Phase {phase_id}"

    if request.method == 'POST':
        # Load the questions shown earlier
        questions = session.get('current_questions')
        if not questions:
            return "Session expired or invalid. Please retry the quiz."

        score = 0
        answered_ids = []

        for q in questions:
            qid = f"q{q['id']}"
            user_answer = request.form.get(qid)
            correct_answer = q.get('answer')

            if user_answer and user_answer.strip().lower() == correct_answer.strip().lower():
                score += 1
            if user_answer:
                answered_ids.append(str(q['id']))

        login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(RESULT_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([name, phone, f'Phase {phase_id}', score, login_time, '"' + ','.join(answered_ids) + '"'])

        # Clear saved questions after quiz is submitted
        session.pop('current_questions', None)

        return render_template('result.html', score=score, total=len(questions))

    else:
        with open(file_path, 'r') as f:
            all_questions = json.load(f)

        for idx, q in enumerate(all_questions):
            if 'id' not in q or q['id'] is None:
                q['id'] = idx + 1

        questions = random.sample(all_questions, min(10, len(all_questions)))

        # Save the selected questions in session
        session['current_questions'] = questions

        return render_template('questions.html', questions=questions, phase_id=phase_id)



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'Cosmos@360':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    results = []
    with open(RESULT_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Defensive check to ensure required fields exist
            if 'name' in row and 'phone' in row:
                results.append(row)

    return render_template('admin.html', results=results)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
