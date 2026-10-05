import os
import io
import base64
import requests
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify

app = Flask(__name__)
app.secret_key = "super_secret_key"

# ── Gemini API Key (FREE) ─────────────────────────────────────────────────────
# Get free key at: https://aistudio.google.com/app/apikey
# Paste your key below (starts with AIzaSy...)
GEMINI_API_KEY =    # <-- paste your new key here   # <-- PASTE YOUR KEY HERE

def call_gemini(system_prompt, messages):
    """Call Google Gemini API — completely FREE."""
    import time

    # Build full prompt as plain text
    full_prompt = ""
    if system_prompt:
        full_prompt += system_prompt + "\n\n"
    for msg in messages:
        role = "Student" if msg["role"] == "user" else "Assistant"
        full_prompt += f"{role}: {msg['content']}\n"
    full_prompt += "Assistant:"

    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7}
    }

    # Only use models confirmed working for this key
    models = [
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-2.5-flash",
    ]

    last_error = "No models available"
    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            if response.status_code == 200:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            last_error = result.get("error", {}).get("message", "Gemini API error")
            # If quota exceeded on this model, wait 2 seconds and try next
            if "quota" in last_error.lower() or "429" in str(response.status_code):
                time.sleep(2)
                continue
        except requests.exceptions.ConnectionError:
            raise Exception("Network error: Cannot reach Google servers.")
        except requests.exceptions.Timeout:
            raise Exception("Request timed out.")

    # All models hit quota — wait 5 seconds and retry once with first model
    time.sleep(5)
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}"
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        if response.status_code == 200:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        last_error = result.get("error", {}).get("message", last_error)
    except:
        pass

    raise Exception(last_error)

# ── Study suggestions ────────────────────────────────────────────────────────
SUGGESTIONS = {
    'Math':     {(1,5):["Multiplication tables","Division basics"],(6,8):["Fractions","Algebra basics"],(9,12):["Advanced Algebra","Calculus basics","Trigonometry"]},
    'Maths':    {(1,5):["Multiplication tables","Division basics"],(6,8):["Fractions","Algebra basics"],(9,12):["Advanced Algebra","Calculus basics","Trigonometry"]},
    'English':  {(1,5):["Reading comprehension","Vocabulary"],(6,8):["Essay structure","Creative writing"],(9,12):["Research writing","Literary critique"]},
    'Science':  {(1,5):["States of matter","Water cycle"],(6,8):["Basic biology","Physics basics"],(9,12):["Chemistry equations","Advanced Physics"]},
    'Social':   {(1,5):["Geography basics","Cultures"],(6,8):["World history","Civics"],(9,12):["Economics basics","Political science"]},
    'Computer': {(1,5):["Word processing","Internet safety"],(6,8):["Block coding","Basic HTML"],(9,12):["Python basics","Algorithms","Databases"]},
    'Zoology':  {(1,5):["Animal classification","Habitats"],(6,8):["Cell biology","Ecosystems"],(9,12):["Genetics","Evolution","Human physiology"]},
    'Botany':   {(1,5):["Parts of a plant","Photosynthesis basics"],(6,8):["Plant reproduction","Leaf types"],(9,12):["Plant hormones","Advanced botany"]},
    'Chemistry':{(1,5):["Elements & symbols","States of matter"],(6,8):["Chemical reactions","Periodic table"],(9,12):["Organic chemistry","Thermodynamics","Electrochemistry"]},
    'Physics':  {(1,5):["Forces & motion","Light & sound"],(6,8):["Electricity","Newton's laws"],(9,12):["Quantum basics","Electromagnetism","Optics"]},
    'Biology':  {(1,5):["Living vs non-living","Plant & animal cells"],(6,8):["Genetics basics","Human body systems"],(9,12):["Molecular biology","Evolution","Microbiology"]},
    'History':  {(1,5):["Ancient civilizations","Local history"],(6,8):["World wars","Industrial revolution"],(9,12):["Modern history","Political movements","Colonialism"]},
    'Geography':{(1,5):["Maps & directions","Continents & oceans"],(6,8):["Climate zones","Natural resources"],(9,12):["Geopolitics","Environmental geography","Urbanization"]},
    'Economics':{(1,5):["Needs vs wants","Basic trade"],(6,8):["Supply & demand","Market types"],(9,12):["Macroeconomics","Fiscal policy","International trade"]},
    'Commerce': {(1,5):["Buying & selling","Money basics"],(6,8):["Accounting basics","Business types"],(9,12):["Financial statements","Business law","Marketing"]},
    'Tamil':    {(1,5):["Reading comprehension","Vocabulary"],(6,8):["Essay writing","Grammar"],(9,12):["Literature analysis","Advanced grammar","Poetry"]},
    'Hindi':    {(1,5):["Reading comprehension","Vocabulary"],(6,8):["Essay writing","Grammar"],(9,12):["Literature analysis","Advanced grammar","Poetry"]},
    'French':   {(1,5):["Basic vocabulary","Simple sentences"],(6,8):["Grammar","Conversation"],(9,12):["Advanced grammar","Literature","Oral expression"]},
}

NAME_COLUMNS = {'studentname','name','student','rollno','rollnumber','id','sno','sl.no','slno','no'}

BLUE_PALETTE = [
    '#1e3a8a','#1d4ed8','#2563eb','#3b82f6','#60a5fa',
    '#93c5fd','#0f172a','#1e40af','#0369a1','#0284c7',
    '#0ea5e9','#38bdf8','#7dd3fc','#164e63','#155e75','#0c4a6e'
]

def get_suggestions(subject, grade):
    key = subject.strip().title()
    if key in SUGGESTIONS:
        for rng, tips in SUGGESTIONS[key].items():
            if rng[0] <= grade <= rng[1]:
                return tips
    if grade <= 5:
        return [f"Review {subject} fundamentals", f"Practice basic {subject} exercises", "Ask teacher for extra worksheets"]
    elif grade <= 8:
        return [f"Study {subject} core concepts", f"Solve previous year {subject} questions", "Form a study group"]
    else:
        return [f"Deep-dive into {subject} theory", f"Practice {subject} problem sets daily", "Refer to reference books & online resources"]

def get_colors(n):
    return [BLUE_PALETTE[i % len(BLUE_PALETTE)] for i in range(n)]

def create_plot_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    enc = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    return enc

# ── AI Assistant route ───────────────────────────────────────────────────────
@app.route('/ai_chat', methods=['POST'])
def ai_chat():
    try:
        data          = request.get_json()
        system_prompt = data.get('system', '')
        messages      = data.get('messages', [])

        if not messages:
            return jsonify({'error': 'No messages provided'}), 400

        reply = call_gemini(system_prompt, messages)
        return jsonify({'reply': reply})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Excel parser ─────────────────────────────────────────────────────────────
def parse_excel_dynamic(file):
    filename = file.filename.lower()
    try:
        df = pd.read_csv(file) if filename.endswith('.csv') else pd.read_excel(file)
    except Exception as e:
        raise ValueError(f"Could not read file: {e}")
    if df.empty or len(df.columns) < 2:
        raise ValueError("File has too few columns.")
    name_col = None
    subject_cols = []
    for col in df.columns:
        norm = str(col).strip().lower().replace(' ','').replace('_','').replace('.','')
        if norm in NAME_COLUMNS:
            name_col = col
        else:
            numeric_vals = pd.to_numeric(df[col], errors='coerce')
            if numeric_vals.notna().sum() >= len(df) * 0.5:
                subject_cols.append(col)
    if not subject_cols:
        raise ValueError("No numeric subject columns found.")
    students = []
    for idx, row in df.iterrows():
        name = str(row[name_col]).strip() if name_col else f"Student {idx+1}"
        if name.lower() in ('nan','none',''):
            name = f"Student {idx+1}"
        marks = {}
        valid = True
        for col in subject_cols:
            try:
                val = float(str(row[col]).strip())
                if np.isnan(val): valid = False; break
                marks[str(col).strip()] = int(val)
            except:
                valid = False; break
        if valid and marks:
            students.append({'name': name, 'marks': marks})
    if not students:
        raise ValueError("No valid student rows found.")
    subjects = list(students[0]['marks'].keys())
    return subjects, students

# ── Per-student analysis ─────────────────────────────────────────────────────
def build_student_analysis(name, marks_dict, grade, subjects):
    total_possible = len(subjects) * 100
    total_marks    = sum(marks_dict[s] for s in subjects)
    percentage     = round((total_marks / total_possible) * 100, 2)
    if percentage >= 90:   performance = "Excellent"
    elif percentage >= 75: performance = "Very Good"
    elif percentage >= 60: performance = "Good"
    elif percentage >= 50: performance = "Average"
    else:                  performance = "Needs Improvement"
    strong_subject = max(subjects, key=lambda s: marks_dict[s])
    weak_subject   = min(subjects, key=lambda s: marks_dict[s])
    suggestions    = get_suggestions(weak_subject, grade)
    subject_status = [
        {'subject': s, 'mark': marks_dict[s], 'status': 'Pass' if marks_dict[s] >= 40 else 'Fail'}
        for s in subjects
    ]
    next_goal = ""
    if percentage < 90:
        next_tier = int(total_possible * (90 if percentage >= 75 else (75 if percentage >= 60 else 60)) / 100)
        needed    = next_tier - total_marks
        next_goal = f"You are {needed} marks away from the next performance tier. Keep pushing!"
    marks_vals = [marks_dict[s] for s in subjects]
    colors     = get_colors(len(subjects))
    rot        = 30 if len(subjects) > 5 else 0
    fig1, ax1 = plt.subplots(figsize=(max(6, len(subjects)*0.9), 4))
    ax1.bar(subjects, marks_vals, color=colors)
    ax1.set_ylim(0, 100); ax1.axhline(y=40, color='red', linestyle='--', alpha=0.5, linewidth=1)
    ax1.set_title('Scores by Subject', fontweight='bold', color='#1e293b')
    ax1.tick_params(axis='x', rotation=rot, labelsize=9); plt.tight_layout()
    chart1 = create_plot_base64(fig1)
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.pie(marks_vals, labels=subjects, autopct='%1.1f%%', colors=colors, startangle=140, textprops={'color':'#1e293b','fontsize':8})
    ax2.set_title('Score Distribution', fontweight='bold', color='#1e293b')
    chart2 = create_plot_base64(fig2)
    fig3, ax3 = plt.subplots(figsize=(max(6, len(subjects)*0.9), 4))
    ax3.plot(subjects, marks_vals, marker='o', linestyle='-', color='#0f172a', linewidth=2, markersize=8)
    ax3.set_ylim(0, 100); ax3.axhline(y=40, color='red', linestyle='--', alpha=0.5, linewidth=1)
    ax3.grid(True, linestyle='--', alpha=0.4); ax3.set_title('Performance Trend Line', fontweight='bold', color='#1e293b')
    ax3.tick_params(axis='x', rotation=rot, labelsize=9); plt.tight_layout()
    chart3 = create_plot_base64(fig3)
    fig4, ax4 = plt.subplots(figsize=(max(6, len(subjects)*0.9), 4))
    ax4.fill_between(subjects, marks_vals, color='#3b82f6', alpha=0.3)
    ax4.plot(subjects, marks_vals, color='#2563eb', linewidth=2)
    ax4.set_ylim(0, 100); ax4.set_title('Proficiency Area Coverage', fontweight='bold', color='#1e293b')
    ax4.tick_params(axis='x', rotation=rot, labelsize=9); plt.tight_layout()
    chart4 = create_plot_base64(fig4)
    return {
        'name': name, 'total': total_marks, 'total_possible': total_possible,
        'percentage': percentage, 'performance': performance,
        'strong': strong_subject, 'weak': weak_subject,
        'suggestions': suggestions, 'status': subject_status,
        'next_goal': next_goal, 'marks': marks_dict,
        'chart1': chart1, 'chart2': chart2, 'chart3': chart3, 'chart4': chart4
    }

# ── Class overview ───────────────────────────────────────────────────────────
def build_class_overview(students_data, subjects, grade):
    names       = [s['name']       for s in students_data]
    totals      = [s['total']      for s in students_data]
    percentages = [s['percentage'] for s in students_data]
    tp          = students_data[0]['total_possible']
    avg_by_subject = {subj: round(np.mean([s['marks'][subj] for s in students_data]), 1) for subj in subjects}
    class_avg      = round(np.mean(percentages), 2)
    top_student    = students_data[np.argmax(totals)]['name']
    pass_count     = sum(1 for s in students_data if s['percentage'] >= 40)
    perf_counts = {'Excellent':0,'Very Good':0,'Good':0,'Average':0,'Needs Improvement':0}
    for s in students_data:
        perf_counts[s['performance']] += 1
    subj_colors = get_colors(len(subjects))
    rot = 30 if len(subjects) > 5 else 0
    figA, axA = plt.subplots(figsize=(max(7, len(subjects)*1.1), 4))
    bars = axA.bar(subjects, [avg_by_subject[s] for s in subjects], color=subj_colors)
    axA.set_ylim(0, 100); axA.axhline(y=40, color='red', linestyle='--', alpha=0.5, label='Pass Line (40)')
    axA.set_title('Class Average by Subject', fontweight='bold', color='#1e293b'); axA.legend(fontsize=8)
    for bar, val in zip(bars, [avg_by_subject[s] for s in subjects]):
        axA.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, f'{val}', ha='center', fontsize=8, fontweight='bold')
    axA.tick_params(axis='x', rotation=rot, labelsize=9); plt.tight_layout()
    chartA = create_plot_base64(figA)
    active = {k:v for k,v in perf_counts.items() if v > 0}
    perf_colors_map = {'Excellent':'#10b981','Very Good':'#3b82f6','Good':'#60a5fa','Average':'#f59e0b','Needs Improvement':'#ef4444'}
    figB, axB = plt.subplots(figsize=(6, 4))
    axB.pie(active.values(), labels=active.keys(), autopct='%1.0f%%',
            colors=[perf_colors_map[k] for k in active], startangle=140,
            textprops={'color':'#1e293b','fontsize':9})
    axB.set_title('Performance Distribution', fontweight='bold', color='#1e293b')
    chartB = create_plot_base64(figB)
    bar_colors = ['#10b981' if t >= tp*0.6 else '#f59e0b' if t >= tp*0.4 else '#ef4444' for t in totals]
    figC, axC = plt.subplots(figsize=(7, max(4, len(names)*0.38)))
    axC.barh(names, totals, color=bar_colors)
    axC.set_xlim(0, tp); axC.axvline(x=tp*0.4, color='red', linestyle='--', alpha=0.5, label=f'Min Pass ({int(tp*0.4)})')
    axC.set_title('Student Total Scores', fontweight='bold', color='#1e293b'); axC.legend(fontsize=8)
    axC.tick_params(axis='y', labelsize=8); plt.tight_layout()
    chartC = create_plot_base64(figC)
    figD, axD = plt.subplots(figsize=(max(7, len(names)*0.5), 4))
    line_colors = get_colors(len(subjects))
    for i, subj in enumerate(subjects):
        vals = [s['marks'][subj] for s in students_data]
        axD.plot(names, vals, marker='o', linewidth=1.5, markersize=4, color=line_colors[i], label=subj, alpha=0.85)
    axD.set_ylim(0, 100); axD.legend(fontsize=7, loc='lower right', ncol=2)
    axD.tick_params(axis='x', rotation=45, labelsize=7)
    axD.set_title('Subject Scores — All Students', fontweight='bold', color='#1e293b')
    axD.grid(True, linestyle='--', alpha=0.3); plt.tight_layout()
    chartD = create_plot_base64(figD)
    return {
        'class_avg': class_avg, 'top_student': top_student,
        'total_students': len(students_data), 'pass_count': pass_count,
        'avg_by_subject': avg_by_subject, 'perf_counts': perf_counts,
        'total_possible': tp,
        'chartA': chartA, 'chartB': chartB, 'chartC': chartC, 'chartD': chartD
    }

# ── Manual entry ─────────────────────────────────────────────────────────────
def run_manual_analysis(grade, marks_dict):
    subjects   = list(marks_dict.keys())
    marks_vals = list(marks_dict.values())
    total_marks = sum(marks_vals)
    percentage  = round((total_marks / 500) * 100, 2)
    if percentage >= 90:   performance = "Excellent"
    elif percentage >= 75: performance = "Very Good"
    elif percentage >= 60: performance = "Good"
    elif percentage >= 50: performance = "Average"
    else:                  performance = "Needs Improvement"
    strong_subject = max(marks_dict, key=marks_dict.get)
    weak_subject   = min(marks_dict, key=marks_dict.get)
    suggestions    = get_suggestions(weak_subject, grade)
    subject_status = [
        {'subject': s, 'mark': marks_dict[s], 'status': 'Pass' if marks_dict[s] >= 40 else 'Fail'}
        for s in marks_dict
    ]
    next_goal = ""
    if percentage < 90:
        next_tier    = int(500 * (90 if percentage >= 75 else (75 if percentage >= 60 else 60)) / 100)
        marks_needed = next_tier - total_marks
        next_goal    = f"You are {marks_needed} marks away from the next performance tier. Keep pushing!"
    colors = get_colors(5)
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.bar(subjects, marks_vals, color=colors); ax1.set_ylim(0, 100)
    ax1.set_title('Scores by Subject', fontweight='bold', color='#1e293b')
    chart1 = create_plot_base64(fig1)
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.pie(marks_vals, labels=subjects, autopct='%1.1f%%', colors=colors, startangle=140, textprops={'color':'#1e293b'})
    ax2.set_title('Score Distribution', fontweight='bold', color='#1e293b')
    chart2 = create_plot_base64(fig2)
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    ax3.plot(subjects, marks_vals, marker='o', linestyle='-', color='#0f172a', linewidth=2, markersize=8)
    ax3.set_ylim(0, 100); ax3.grid(True, linestyle='--', alpha=0.5)
    ax3.set_title('Performance Trend Line', fontweight='bold', color='#1e293b')
    chart3 = create_plot_base64(fig3)
    fig4, ax4 = plt.subplots(figsize=(6, 4))
    ax4.fill_between(subjects, marks_vals, color='#3b82f6', alpha=0.3)
    ax4.plot(subjects, marks_vals, color='#2563eb', linewidth=2); ax4.set_ylim(0, 100)
    ax4.set_title('Proficiency Area Coverage', fontweight='bold', color='#1e293b')
    chart4 = create_plot_base64(fig4)
    return render_template('result.html', grade=grade, total=total_marks, percentage=percentage,
                           performance=performance, strong=strong_subject, weak=weak_subject,
                           suggestions=suggestions, status=subject_status, next_goal=next_goal,
                           chart1=chart1, chart2=chart2, chart3=chart3, chart4=chart4)

# ── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        excel_file = request.files.get('excel_file')
        if excel_file and excel_file.filename:
            ext = os.path.splitext(excel_file.filename)[1].lower()
            if ext not in ('.xlsx', '.xls', '.xlsm', '.csv'):
                flash("Unsupported file type. Please upload .xlsx, .xls or .csv")
                return redirect(url_for('index'))
            try:
                grade = int(request.form.get('excel_grade', 11))
            except:
                grade = 11
            try:
                subjects, students = parse_excel_dynamic(excel_file)
            except ValueError as e:
                flash(str(e))
                return redirect(url_for('index'))
            students_data  = [build_student_analysis(s['name'], s['marks'], grade, subjects) for s in students]
            class_overview = build_class_overview(students_data, subjects, grade)
            return render_template('result_class.html', grade=grade,
                                   subjects=subjects,
                                   students=students_data,
                                   overview=class_overview)
        grade = int(request.form.get('grade'))
        marks_dict = {
            'Math':     int(request.form.get('math')),
            'English':  int(request.form.get('english')),
            'Science':  int(request.form.get('science')),
            'Social':   int(request.form.get('social')),
            'Computer': int(request.form.get('computer'))
        }
        return run_manual_analysis(grade, marks_dict)
    except ValueError:
        flash("Invalid input. Please ensure all fields contain valid numbers.")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)