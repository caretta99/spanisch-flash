from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import random
from utils.data_validator import load_and_validate_data

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Load and validate data on startup
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'conjugations.json')
conjugations_data = load_and_validate_data(DATA_FILE)

@app.route('/')
def index():
    """Main page with quiz selection"""
    return render_template('index.html')

@app.route('/quiz/conjugations/options')
def conjugations_options():
    """Options page for conjugations quiz"""
    quiz_data = conjugations_data.get('conjugations_quiz', {})
    verbs = sorted(quiz_data.keys())
    
    # Get all unique tenses from the data
    tenses = set()
    for verb_data in quiz_data.values():
        tenses.update(verb_data.keys())
    tenses = sorted(list(tenses))
    
    # Load saved preferences from session
    saved_prefs = {
        'selected_verbs': session.get('saved_verbs', verbs),  # Default to all verbs
        'selected_tenses': session.get('saved_tenses', tenses),  # Default to all tenses
        'seconds_per_question': session.get('saved_seconds_per_question', 3),
        'num_questions': session.get('saved_num_questions', 10),
        'contestants': session.get('saved_contestants', [])
    }
    
    return render_template('options.html', 
                         verbs=verbs, 
                         tenses=tenses,
                         saved_prefs=saved_prefs)

@app.route('/quiz/conjugations/start', methods=['POST'])
def start_quiz():
    """Start quiz with selected options"""
    selected_verbs = request.form.getlist('verbs')
    selected_tenses = request.form.getlist('tenses')
    seconds_per_question = int(request.form.get('seconds_per_question', 3))
    num_questions = int(request.form.get('num_questions', 10))
    
    # Get contestant names (filter out empty strings)
    contestant_names = [name.strip() for name in request.form.getlist('contestants') if name.strip()]
    contest_mode = len(contestant_names) > 0
    
    # Validate selections
    if not selected_verbs or not selected_tenses:
        return redirect(url_for('conjugations_options'))
    
    # Generate questions
    questions = []
    quiz_data = conjugations_data.get('conjugations_quiz', {})
    
    # Generate base questions
    base_questions = []
    for _ in range(num_questions):
        verb = random.choice(selected_verbs)
        tense = random.choice(selected_tenses)
        person = random.choice(['yo', 'tu', 'el/ella/usted', 'nosotros', 'vosotros', 'ellos/ellas/ustedes'])
        
        answer = quiz_data[verb][tense][person]
        base_questions.append({
            'verb': verb,
            'tense': tense,
            'person': person,
            'answer': answer
        })
    
    # Assign questions to contestants if contest mode is enabled
    if contest_mode:
        num_contestants = len(contestant_names)
        questions_per_contestant = num_questions // num_contestants
        remaining_questions = num_questions % num_contestants
        
        # Create assignment list: each contestant gets equal share, then remaining are random
        assignment_list = []
        for name in contestant_names:
            assignment_list.extend([name] * questions_per_contestant)
        
        # Randomly assign remaining questions
        for _ in range(remaining_questions):
            assignment_list.append(random.choice(contestant_names))
        
        # Shuffle the assignment list
        random.shuffle(assignment_list)
        
        # Assign questions to contestants
        for i, question in enumerate(base_questions):
            question['contestant'] = assignment_list[i]
            questions.append(question)
    else:
        # No contest mode, just add questions without contestant assignment
        questions = base_questions
    
    # Store quiz data in session
    session['questions'] = questions
    session['current_question'] = 0
    session['seconds_per_question'] = seconds_per_question
    session['num_questions'] = num_questions
    session['contest_mode'] = contest_mode
    
    # Save user preferences for next time
    session['saved_verbs'] = selected_verbs
    session['saved_tenses'] = selected_tenses
    session['saved_seconds_per_question'] = seconds_per_question
    session['saved_num_questions'] = num_questions
    session['saved_contestants'] = contestant_names
    
    return redirect(url_for('run_quiz'))

@app.route('/quiz/conjugations/run')
def run_quiz():
    """Quiz execution page"""
    if 'questions' not in session:
        return redirect(url_for('conjugations_options'))
    
    questions = session.get('questions', [])
    current_question = session.get('current_question', 0)
    
    if current_question >= len(questions):
        # Quiz complete, return to options
        # Keep saved preferences, only remove quiz-specific data
        session.pop('questions', None)
        session.pop('current_question', None)
        session.pop('contest_mode', None)
        return redirect(url_for('conjugations_options'))
    
    question = questions[current_question]
    seconds_per_question = session.get('seconds_per_question', 4)
    contest_mode = session.get('contest_mode', False)
    
    return render_template('quiz.html', 
                         question=question,
                         question_num=current_question + 1,
                         total_questions=len(questions),
                         seconds_per_question=seconds_per_question,
                         contest_mode=contest_mode)

@app.route('/quiz/conjugations/next', methods=['POST'])
def next_question():
    """Move to next question"""
    current_question = session.get('current_question', 0)
    session['current_question'] = current_question + 1
    
    if session['current_question'] >= len(session.get('questions', [])):
        # Quiz complete
        # Keep saved preferences, only remove quiz-specific data
        session.pop('questions', None)
        session.pop('current_question', None)
        session.pop('contest_mode', None)
        return jsonify({'complete': True})
    
    return jsonify({'complete': False})

if __name__ == '__main__':
    app.run(debug=True)
