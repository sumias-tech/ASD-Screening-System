from flask import Flask, render_template, request, redirect, url_for, session, Blueprint
from db import get_db_connection 
from mysql.connector import IntegrityError
import pandas as pd
import pickle
import os
import numpy as np

from videoanalysis.video_processor import process_video as process_video_file
from videoanalysis.report_generator import generate_graph as generate_graph_file
from videoanalysis.pdf_report import generate_pdf as generate_pdf_file

app = Flask(__name__)
app.secret_key = "mysecretkey"


def get_required_section_names():
    return ['Section 1 - Assessment', 'Section 2 - Screening', 'Section 3 - Observation', 'Video Analysis']


video_bp = Blueprint(
    'videoanalysis',
    __name__,
    template_folder='videoanalysis/templates',
    static_folder='videoanalysis/static',
    url_prefix='/videoanalysis'
)


@app.route('/')
def home():
    return render_template("home.html")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)"
        values = (name, email, password, role)

        try:
            cursor.execute(sql, values)
            conn.commit()

            user_id = cursor.lastrowid  # ✅ get DB id

            # ✅ store in session
            session['user_id'] = user_id
            session['username'] = name
            session['email'] = email
            session['role'] = role

            cursor.close()
            conn.close()

            return redirect(url_for('dashboard'))

        except IntegrityError:
            cursor.close()
            conn.close()
            return "Email already registered ❌"
    return render_template("signup.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":

        print("FORM DATA:", request.form)

        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        print("USER:", user)

        if not user:
            return render_template("login.html", error="Invalid email or password")

        session['user_id'] = user['id']
        session['username'] = user['name']
        session['email'] = user['email']
        session['role'] = user['role']
        session['age'] = user.get('age')
        session['gender'] = user.get('gender')

        print("SESSION CREATED:", session)

        return render_template(
            "login.html",
            success=True,
            redirect_url=url_for('dashboard')
        )

    return render_template("login.html")

@app.route('/successfuly')
def successfuly():
    return render_template("successful.html")

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_id = session.get('user_id') 
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 

    try:
        # 1. Fetch data for the Table (Latest 5, Newest First)
        cursor.execute("""
            SELECT created_at, category, score, result_text 
            FROM screening_history 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 5
        """, (user_id,))
        recent_activities = cursor.fetchall()
        
        # 2. Fetch data for the Graph (All history, Oldest First for the trend)
        cursor.execute("""
            SELECT created_at, score 
            FROM screening_history 
            WHERE user_id = %s 
            ORDER BY created_at ASC
        """, (user_id,))
        history_data = cursor.fetchall()

        # 3. Format Graph Data
        graph_labels = [row['created_at'].strftime('%d %b') for row in history_data]
        graph_values = [row['score'] for row in history_data]

        cursor.execute(
            """
            SELECT DISTINCT category
            FROM screening_history
            WHERE user_id = %s
            """,
            (user_id,)
        )
        main_section_names = get_required_section_names()
        completed_categories = []
        completed_category_names = set()
        for row in cursor.fetchall():
            category = (row['category'] or '').strip()
            if not category or category == 'Final Analysis':
                continue
            category_lower = category.lower()
            for name in main_section_names:
                if name.lower() in category_lower:
                    completed_categories.append(category)
                    completed_category_names.add(name)
                    break

        completed_sections_count = len(completed_category_names)
        total_sections = len(main_section_names)
        completion_percent = int(round(min(completed_sections_count / total_sections * 100, 100)))

        missing_sections = [name for name in main_section_names if name not in completed_category_names]

        if completed_sections_count >= total_sections:
            completion_note = "All 4 sessions are complete. Check the final analysis result."
            missing_sections = []
        elif completed_sections_count == 0:
            completion_note = "Start your first assessment session to begin progress."
        else:
            remaining = total_sections - completed_sections_count
            completion_note = f"{remaining} session{'s' if remaining != 1 else ''} left to complete."
        
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        recent_activities = []
        graph_labels = []
        graph_values = []
        completed_sections_count = 0
        total_sections = 3
        completion_percent = 0
        completion_note = "Start your first session to begin progress."
    finally:
        cursor.close()
        conn.close()

    # 4. ONLY ONE RETURN AT THE END
    return render_template(
        "dashboard.html",
        username=session['username'],
        email=session['email'],
        activities=recent_activities,
        graph_labels=graph_labels,
        graph_values=graph_values,
        age=session.get('age'),
        gender=session.get('gender'),
        completed_sections_count=completed_sections_count,
        completion_percent=completion_percent,
        total_sections=total_sections,
        completion_note=completion_note,
        missing_sections=missing_sections
    )

@app.route('/final_analysis')
def final_analysis():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    latest = {}
    summary = "No saved results found. Please complete the four sessions to generate a final analysis."
    section_scores = {}
    overall_risk = None
    final_score_percent = None
    completed_date = None
    required_sections = get_required_section_names()

    def normalize_score(value):
        try:
            score = float(value)
        except Exception:
            return None
        if score <= 10:
            return round(max(score, 0.0), 2)
        return round(max(min(score / 10.0, 10.0), 0.0), 2)

    def risk_category(score_percent):
        if score_percent is None:
            return None
        if score_percent >= 70:
            return 'High'
        if score_percent >= 40:
            return 'Moderate'
        return 'Low'

    section_texts = {
        'Section 1 - Assessment': {
            'Low': 'The developmental history suggests typical patterns.',
            'Moderate': 'The developmental history shows some areas that may need follow-up.',
            'High': 'The developmental history points to several concerns that deserve closer review.'
        },
        'Section 2 - Screening': {
            'Low': 'The screening responses are within the expected range.',
            'Moderate': 'The screening responses show some areas that may need attention.',
            'High': 'The screening responses indicate a higher likelihood of developmental concerns.'
        },
        'Section 3 - Observation': {
            'Low': 'The observed behavior reflects strong social and communication patterns.',
            'Moderate': 'The observation shows some variation in social or communication behavior.',
            'High': 'The observation shows clear differences that may require further evaluation.'
        },
        'Video Analysis': {
            'Low': 'The video analysis suggests typical behavioral patterns.',
            'Moderate': 'The video analysis shows some areas that may benefit from closer observation.',
            'High': 'The video analysis indicates clear behavioral patterns that warrant further review.'
        }
    }

    try:
        cursor.execute(
            """
            SELECT category, score, result_text, created_at
            FROM screening_history
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        rows = cursor.fetchall()

        latest_section = {}
        for row in rows:
            category = (row['category'] or '').strip()
            if category not in latest_section:
                latest_section[category] = {
                    'score': row['score'],
                    'result_text': row['result_text'] or '',
                    'created_at': row['created_at']
                }

        completed_date = max((row['created_at'] for row in rows if row['created_at']), default=None)

        def find_section_match(category_name, section_name):
            category_lower = (category_name or '').lower()
            if section_name == 'Section 1 - Assessment':
                return 'section 1' in category_lower or 'assessment' in category_lower or 'session 1' in category_lower
            if section_name == 'Section 2 - Screening':
                return 'section 2' in category_lower or 'screening' in category_lower or 'session 2' in category_lower
            if section_name == 'Section 3 - Observation':
                return 'section 3' in category_lower or 'observation' in category_lower or 'session 3' in category_lower
            if section_name == 'Video Analysis':
                return 'video' in category_lower or 'analysis' in category_lower
            return False

        for section_name in required_sections:
            match_row = None
            if section_name in latest_section:
                match_row = latest_section[section_name]
            else:
                for cat, value in latest_section.items():
                    if find_section_match(cat, section_name):
                        match_row = value
                        break

            if match_row:
                raw_score = match_row['score']
                normalized = normalize_score(raw_score)
                display_score = round(normalized * 10, 1) if normalized is not None else None
                category = risk_category(display_score)
                latest[section_name] = {
                    'score': raw_score,
                    'display_score': display_score,
                    'section_category': category,
                    'section_sentence': section_texts.get(section_name, {}).get(category, ''),
                    'result_text': match_row['result_text'],
                    'created_at': match_row['created_at']
                }
                if section_name == 'Section 1 - Assessment':
                    latest[section_name]['jaundice'] = session.get('child_jaundice', -1)
                    latest[section_name]['family_asd'] = session.get('child_family_asd', -1)
                    latest[section_name]['delay_level'] = session.get('child_delay_level', -1)
                    latest[section_name]['age'] = session.get('child_age_months', 'Not provided')
                    latest[section_name]['gender'] = session.get('child_gender', 'Not provided')
                if normalized is not None:
                    section_scores[section_name] = normalized
            else:
                latest[section_name] = {
                    'score': None,
                    'display_score': None,
                    'section_category': None,
                    'section_sentence': '',
                    'result_text': 'Section not completed',
                    'created_at': None
                }

        missing = [name for name, data in latest.items() if data['score'] is None]
        if missing:
            summary = f"The following sections are incomplete and must be completed before a final combined score can be generated: {', '.join(missing)}."
        else:
            total = sum(section_scores.values())
            final_score_percent = round((total / len(required_sections)) * 10, 1)
            if final_score_percent >= 70:
                overall_risk = 'High Risk'
            elif final_score_percent >= 40:
                overall_risk = 'Moderate Risk'
            else:
                overall_risk = 'Low Risk'

            high_sections = sum(1 for data in latest.values() if data.get('section_category') == 'High')
            moderate_sections = sum(1 for data in latest.values() if data.get('section_category') == 'Moderate')
            low_sections = sum(1 for data in latest.values() if data.get('section_category') == 'Low')

            if low_sections >= 2:
                summary = 'Most indicators are within the typical range across the three assessment sections.'
            elif high_sections >= 2:
                summary = 'Multiple sections indicate patterns that may require further evaluation.'
            else:
                summary = 'The responses suggest generally typical development, with a few areas worth monitoring.'

            latest['Final Analysis'] = {
                'score': final_score_percent,
                'result_text': overall_risk,
                'created_at': completed_date
            }

            try:
                cursor.execute(
                    "SELECT id FROM screening_history WHERE user_id=%s AND category=%s AND score=%s AND DATE(created_at)=CURDATE()",
                    (user_id, 'Final Analysis', final_score_percent)
                )
                existing = cursor.fetchone()
                if not existing:
                    save_query = "INSERT INTO screening_history (user_id, score, result_text, category) VALUES (%s, %s, %s, %s)"
                    cursor.execute(save_query, (
                        user_id,
                        final_score_percent,
                        overall_risk,
                        'Final Analysis'
                    ))
                    conn.commit()
            except Exception as save_error:
                print(f"Failed to save final analysis history: {save_error}")

    except Exception as e:
        print(f"Error fetching final analysis: {e}")
        latest = {}
        summary = "Unable to load final analysis results right now. Please try again later."
    finally:
        cursor.close()
        conn.close()

    raw_age = session.get('age')
    if raw_age is None:
        raw_age = session.get('child_age')
    if raw_age is None:
        raw_age = session.get('child_age_months')

    if raw_age is None or raw_age == '':
        age = 'Not provided'
        age_months = 'Not provided'
    elif isinstance(raw_age, (int, float)):
        age = f"{int(raw_age)} months"
        age_months = f"{int(raw_age)} months"
    elif isinstance(raw_age, str):
        cleaned = raw_age.strip()
        if cleaned.isdigit():
            age = f"{int(cleaned)} months"
            age_months = f"{int(cleaned)} months"
        else:
            age = cleaned
            age_months = cleaned
    else:
        age = str(raw_age)
        age_months = str(raw_age)

    raw_gender = session.get('gender') or session.get('child_gender')
    if raw_gender in ['M', 'm', 'male', 'Male', 'MALE']:
        gender_display = 'Male'
    elif raw_gender in ['F', 'f', 'female', 'Female', 'FEMALE']:
        gender_display = 'Female'
    elif raw_gender:
        gender_display = str(raw_gender)
    else:
        gender_display = 'Not provided'

    guidance = []
    if overall_risk == 'High Risk':
        guidance = [
            'A consultation with a pediatric or developmental specialist is strongly recommended.'
        ]
    elif overall_risk == 'Moderate Risk':
        guidance = [
            'It is recommended to monitor the child’s development and consider a follow-up assessment.'
        ]
    elif overall_risk == 'Low Risk':
        guidance = [
            'No immediate action is required. Continue regular developmental monitoring.'
        ]

    parent_guidance = [
        'This report is generated automatically and is intended for screening purposes only.',
        'It is not a clinical diagnosis. Please consult a qualified professional for medical advice.'
    ]

    score_text = f"{final_score_percent:.1f}%" if final_score_percent is not None else 'Incomplete'

    return render_template(
        'final_analysis.html',
        latest=latest,
        summary=summary,
        overall_risk=overall_risk,
        final_score_percent=final_score_percent,
        score_text=score_text,
        completed_date=completed_date.strftime('%d %b %Y') if completed_date else 'Not available',
        user_name=session.get('username', 'User'),
        user_age=age,
        age_months=age_months,
        user_gender=gender_display,
        guidance=guidance,
        parent_guidance=parent_guidance
    )

@app.route('/save_final_analysis')
def save_final_analysis():
    if 'username' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('final_analysis'))

@app.route('/behaviour')
def behaviour():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("behaviour.html", username=session['username'])

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM screening_history WHERE user_id=%s ORDER BY created_at DESC",
        (session['user_id'],)
    )
    history_items = cursor.fetchall()
    cursor.close()
    conn.close()

    for item in history_items:
        if item.get('created_at') is not None:
            item['created_at'] = item['created_at'].strftime('%d %b, %Y')

    return render_template(
        "history.html",
        username=session['username'],
        history_items=history_items
    )

@app.route('/history/report/<int:history_id>')
def view_history_report(history_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM screening_history WHERE id=%s AND user_id=%s",
        (history_id, session['user_id'])
    )
    item = cursor.fetchone()
    cursor.close()
    conn.close()

    if not item:
        return redirect(url_for('history'))

    if item.get('created_at') is not None:
        item['created_at'] = item['created_at'].strftime('%d %b, %Y')

    return render_template(
        'history_report.html',
        username=session['username'],
        item=item
    )
 
@app.route('/settings')
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template("settings.html", username=session['username'])

@app.route('/screening')
def screening():
    return render_template("screening.html")
@app.route('/assessment')
def assessment():
    return render_template("assessment.html")
@app.route('/assessment2')
def assessment2():
    return render_template("assessment2.html")

@app.route('/ppage')
def ppage():
    if 'username' not in session:
        return redirect(url_for('login'))
    print("SESSION FULL:", session)
    
    

    return render_template(
        "ppage.html",
        username=session['username'],
        email=session['email'],
        role=session['role'],
        user_id=session.get('user_id')
      
    )
@app.route('/registration')
def registration():
    return render_template("registration.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


SECTION2_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'section2_model.pkl')
if os.path.exists(SECTION2_MODEL_PATH):
    with open(SECTION2_MODEL_PATH, 'rb') as f:
        screening_model = pickle.load(f)
    print("✅ Section 2 screening model loaded successfully!")
else:
    raise FileNotFoundError(f"❌ Could not find the model file at: {SECTION2_MODEL_PATH}")

SECTION1_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'section1_model.pkl')
if os.path.exists(SECTION1_MODEL_PATH):
    with open(SECTION1_MODEL_PATH, 'rb') as f:
        section1_model = pickle.load(f)
    print("✅ Section 1 model loaded successfully!")
else:
    raise FileNotFoundError(f"❌ Could not find the model file at: {SECTION1_MODEL_PATH}")

SECTION3_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'section3_model.pkl')
if os.path.exists(SECTION3_MODEL_PATH):
    with open(SECTION3_MODEL_PATH, 'rb') as f:
        section3_model = pickle.load(f)
    print("✅ Section 3 model loaded successfully!")
else:
    raise FileNotFoundError(f"❌ Could not find the model file at: {SECTION3_MODEL_PATH}")

SECTION2_FEATURES = [f'A{i}' for i in range(1, 10)] + ['A10_Autism_Spectrum_Quotient']
SECTION1_FEATURES = [
    'Age_Years',
    'Speech Delay/Language Disorder',
    'Learning disorder',
    'Genetic_Disorders',
    'Global developmental delay/intellectual disability',
    'Family_mem_with_ASD',
    'Jaundice',
    'Depression',
    'Anxiety_disorder'
]
SECTION3_FEATURES = [
    'Childhood Autism Rating Scale',
    'Social_Responsiveness_Scale',
    'Social/Behavioural Issues',
    'Anxiety_disorder',
    'Depression',
    'Age_Years',
    'Sex'
]

@app.route('/submit', methods=['POST'])
def submit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        features = []
        for i in range(1, 11):
            val = request.form.get(f"q{i}")
            if val == '2':
                features.append(1.0)
            elif val == '1':
                features.append(0.5)
            else:
                features.append(0.0)

        input_df = pd.DataFrame([features], columns=SECTION2_FEATURES, dtype=float)
        prob = screening_model.predict_proba(input_df)[0][1]
        threshold = 0.5

        if prob >= threshold:
            result_text = "⚠ High likelihood of Autism traits detected"
        else:
            result_text = "✅ Low likelihood of Autism traits"

    except Exception as e:
        result_text = f"Error: {str(e)}"
        prob = 0

    return render_template('screening.html',
                           result_ready=True,
                           result_text=result_text,
                           score=float(round(prob * 100, 2)))

# Add this so the "Save" button doesn't 404
@app.route('/save_result')
def save_result():
    # 1. Security Check
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    score = request.args.get('score')
    result_text = request.args.get('text')
    category = request.args.get('category', 'Section 2 - Screening') or 'Section 2 - Screening'

    # 2. Use your get_db_connection() function
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "INSERT INTO screening_history (user_id, score, result_text, category) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, score, result_text, category))
        conn.commit()  # This saves the changes!
        print("✅ Result saved to MySQL successfully!")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return "Failed to save result."
    finally:
        # 3. Always close the connection when done
        cursor.close()
        conn.close()

    return redirect(url_for('dashboard')) 

@app.route('/session3', methods=['POST'])
def session3():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    social = int(request.form.get('social', 1))
    play = int(request.form.get('play', 1))
    adapt = int(request.form.get('adapt', 1))

    total = social + play + adapt
    observation_score = round((total / 12) * 10, 2)
    behavior_issue = 1 if total >= 8 else 0
    sex_code = 1 if (session.get('gender') or '').lower() == 'male' else 0
    age_years = round(float(session.get('age', 3)) / 12, 2) if session.get('age') else 3

    df_input = pd.DataFrame([{
        'Childhood Autism Rating Scale': observation_score,
        'Social_Responsiveness_Scale': round(observation_score * 10, 2),
        'Social/Behavioural Issues': behavior_issue,
        'Anxiety_disorder': 0,
        'Depression': 0,
        'Age_Years': age_years,
        'Sex': sex_code
    }], columns=SECTION3_FEATURES)

    prob = section3_model.predict_proba(df_input)[0][1]
    score_percentage = round(prob * 100, 2)

    if prob < 0.3:
        risk = "Low Risk"
    elif prob < 0.6:
        risk = "Moderate Risk"
    else:
        risk = "High Risk"

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO screening_history (user_id, score, result_text, category) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (session['user_id'], score_percentage, risk, "Section 3 - Observation"))
        conn.commit()
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        cursor.close()
        conn.close()

    return render_template("assessment2.html", result_ready=True, risk=risk, score=score_percentage)

@app.route('/save_video_result')
def save_video_result():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    score = request.args.get('score')  # e.g., 86.29
    result_text = request.args.get('text')
    
    # IMPORTANT: Set this to 'Video Analysis'
    category = "Video Analysis" 

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO screening_history (user_id, score, result_text, category) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, score, result_text, category))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('dashboard'))

@app.route('/session2', methods=['POST'])
def session2():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    age_months_raw = (request.form.get('age_months') or '').strip()
    gender_raw = (request.form.get('gender') or '').strip().lower()
    jaundice_val = int(request.form.get('jaundice', 0))
    family_asd_val = int(request.form.get('family_asd', 0))
    delay_level = int(request.form.get('delay_level', 0))

    age_months_val = None
    if age_months_raw.isdigit():
        age_months_val = int(age_months_raw)
    risk = "Not assessed"
    session['child_age_months'] = f"{age_months_val} months" if age_months_val is not None else None
    session['child_age'] = age_months_val
    session['child_gender'] = gender_raw.title() if gender_raw else None
    session['age'] = age_months_val
    session['gender'] = gender_raw.title() if gender_raw else None
    session['child_jaundice'] = jaundice_val
    session['child_family_asd'] = family_asd_val
    session['child_delay_level'] = delay_level

    age_text = session['child_age_months'] or 'Not provided'
    gender_text = session['child_gender'] or 'Not provided'

    family_history_text = (
        'No known history of autism' if family_asd_val == 0
        else 'Yes, autism is present in the family' if family_asd_val == 1
        else 'Not sure'
    )
    birth_history_text = (
        'No jaundice reported' if jaundice_val == 0
        else 'Jaundice was reported' if jaundice_val == 1
        else 'Not sure'
    )
    development_text = (
        'Developing well with no major concerns' if delay_level == 0
        else 'A little delay in speaking or learning' if delay_level == 1
        else 'Noticeable delay in speaking or learning' if delay_level == 2
        else 'Significant delay in overall development' if delay_level == 3
        else 'Not sure'
    )

    all_not_sure = (jaundice_val == -1 and family_asd_val == -1 and delay_level == -1)
    some_not_sure = not all_not_sure and (-1 in [jaundice_val, family_asd_val, delay_level])

    if all_not_sure:
        interpretation_text = (
            'Not enough information to generate a reliable result. Please complete the background details for a stronger assessment.'
        )
    elif delay_level == 2 and family_asd_val == 1:
        interpretation_text = (
            'Some factors were identified that may need further attention, such as developmental delays or family history. '
            'These do not confirm any condition but are important to consider in the overall assessment.'
        )
    elif delay_level >= 1 or family_asd_val == 1 or jaundice_val == 1:
        interpretation_text = (
            'Some factors were identified that may need further attention, such as developmental delays or medical history. '
            'These do not confirm any condition but are important to consider in the overall assessment.'
        )
    else:
        interpretation_text = (
            'There are no strong medical or developmental concerns identified from the background information. '
            'This section provides supporting context for the overall assessment.'
        )

    summary = {
        'age': age_text,
        'gender': gender_text,
        'family_history': family_history_text,
        'birth_history': birth_history_text,
        'development': development_text,
        'interpretation': interpretation_text,
        'support_note': some_not_sure,
        'needs_more_info': all_not_sure
    }

    risk = None
    score_percentage = None
    show_save = True

    if not all_not_sure:
        speech_delay = 1 if delay_level >= 1 else 0
        learning_disorder = 1 if delay_level == 2 else 0
        gdd_val = 1 if delay_level == 3 else 0
        age_years = round(age_months_val / 12, 2) if age_months_val is not None else 3

        df_input = pd.DataFrame([{
            'Age_Years': age_years,
            'Speech Delay/Language Disorder': speech_delay,
            'Learning disorder': learning_disorder,
            'Genetic_Disorders': 0,
            'Global developmental delay/intellectual disability': gdd_val,
            'Family_mem_with_ASD': family_asd_val,
            'Jaundice': jaundice_val,
            'Depression': 0,
            'Anxiety_disorder': 0
        }], columns=SECTION1_FEATURES)

        prob = section1_model.predict_proba(df_input)[0][1]
        score_percentage = round(prob * 100, 2)
        if prob < 0.3:
            risk = 'Low Risk'
        elif prob < 0.6:
            risk = 'Moderate Risk'
        else:
            risk = 'High Risk'

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = 'INSERT INTO screening_history (user_id, score, result_text, category) VALUES (%s, %s, %s, %s)'
            cursor.execute(query, (session['user_id'], score_percentage, risk, 'Section 1 - Assessment'))
            conn.commit()
        except Exception as e:
            print(f'Database Error: {e}')
        finally:
            cursor.close()
            conn.close()
    else:
        show_save = False

    return render_template('assessment.html', result_ready=True, summary=summary, show_save=show_save)
@video_bp.route('/', methods=['GET'])
@video_bp.route('', methods=['GET'])
def videoanalysis():
    return render_template('upload.html')

@video_bp.route('/analyze', methods=['POST'])
def analyze_video():
    video = request.files.get('video')
    if not video:
        return redirect(url_for('videoanalysis.videoanalysis'))

    uploads_dir = os.path.join(os.path.dirname(__file__), 'videoanalysis', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    video_path = os.path.join(uploads_dir, video.filename)
    video.save(video_path)

    result = process_video_file(video_path)
    result['graph'] = generate_graph_file(result)
    result['pdf'] = generate_pdf_file(result)

    return render_template('result.html', result=result)

@app.route('/analyze', methods=['POST'])
def analyze_video_alias():
    return analyze_video()

app.register_blueprint(video_bp)
if __name__ == "__main__":
    app.run(debug=True)