from flask import Flask, render_template, request, redirect, url_for, session
import os
import csv
import json
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

USER_FILE = os.path.join(DATA_DIR, 'users.csv')
RESULT_FILE = os.path.join(DATA_DIR, 'results.csv')


# USER_FILE = 'data/users.csv'
# RESULT_FILE = 'data/results.csv'

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
        writer.writerow([
            'name', 'phone', 'phase', 'score', 'login_time',
            'question_ids', 'correct_ids', 'incorrect_ids'
        ])


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

    file_path = os.path.join(DATA_DIR, f'questions_phase{phase_id}.json')
    if not os.path.exists(file_path):
        return f"No questions available for Phase {phase_id}"

    if request.method == 'POST':
        # Load the questions shown earlier
        questions = session.get('current_questions')
        if not questions:
            return "Session expired or invalid. Please retry the quiz."

        score = 0
        answered_ids = []
        correct_ids = []
        incorrect_ids = []

        for q in questions:
            qid = f"q{q['id']}"
            user_answer = request.form.get(qid)
            correct_answer = q.get('answer')

            if user_answer:
                answered_ids.append(str(q['id']))

                if user_answer.strip().lower() == correct_answer.strip().lower():
                    score += 1
                    correct_ids.append(str(q['id']))
                else:
                    incorrect_ids.append(str(q['id']))

        login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save results to CSV
        with open(RESULT_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                name, phone, f'Phase {phase_id}', score, login_time,
                '"' + ','.join(answered_ids) + '"',
                '"' + ','.join(correct_ids) + '"',
                '"' + ','.join(incorrect_ids) + '"'
            ])

        # Clear saved questions after quiz is submitted
        session.pop('current_questions', None)

        return render_template(
            'result.html',
            score=score,
            total=len(questions),
            correct_ids=correct_ids,
            incorrect_ids=incorrect_ids
        )

    else:
        # GET request: Show quiz
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

# @app.route('/admin/dashboard')
# def admin_dashboard():
#     if not session.get('admin'):
#         return redirect(url_for('admin_login'))

#     results = []
#     with open(RESULT_FILE, 'r', newline='') as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             # Defensive check to ensure required fields exist
#             if 'name' in row and 'phone' in row:
#                 results.append(row)

#     return render_template('admin.html', results=results)


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    results = []
    try:
        with open(RESULT_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(f"Read row: {row}")  # This is our little detective!
                if 'name' in row and 'phone' in row:
                    results.append(row)
                else:
                    print(f"Skipping row because 'name' or 'phone' is missing: {row}") # Another detective!
    except FileNotFoundError:
        print(f"Error: Could not find the file {RESULT_FILE}")
    except Exception as e:
        print(f"An error occurred: {e}")

    print(f"Final results: {results}") # One more detective to see what we ended up with!
    return render_template('admin.html', results=results)

@app.route('/admin/students')
def admin_students():
    if not session.get('admin'):
        return(redirect(url_for('admin_login')))
    
    data = []
    try:
        with open(USER_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(f"Read row: {row}")  # This is our little detective!
                if 'name' in row and 'phone' in row:
                    data.append(row)
                else:
                    print(f"Skipping row because 'name' or 'phone' is missing: {row}") # Another detective!
    except FileNotFoundError:
        print(f"Error: Could not find the file {USER_FILE}")
    except Exception as e:
        print(f"An error occurred: {e}")

    print(f"Final results: {data}") # One more detective to see what we ended up with!
    return render_template('students.html', data=data)

@app.route('/admin/student/<phone>')
def student_details(phone):
    student = None
    results = []

    # Get basic info
    try:
        with open(USER_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('phone') == phone:
                    student = row
                    break
    except Exception as e:
        print(f"Error reading USER_FILE: {e}")

    # Get all result entries for this phone
    try:
        with open(RESULT_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('phone') == phone:
                    results.append(row)
    except Exception as e:
        print(f"Error reading RESULT_FILE: {e}")

    return render_template('student_detail.html', student=student, results=results)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
