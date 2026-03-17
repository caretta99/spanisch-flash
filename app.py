from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import random
from utils.data_validator import load_and_validate_data, load_and_validate_por_para_data, load_and_validate_vocabulary_data
from utils.settings_store import load_settings as load_persisted_settings, save_settings as save_persisted_settings, validate_settings

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Persisted options storage (global, server-side)
os.makedirs(app.instance_path, exist_ok=True)
app.config.setdefault("SETTINGS_FILE_PATH", os.path.join(app.instance_path, "quiz_settings.json"))


def _get_settings_file_path() -> str:
    return app.config.get("SETTINGS_FILE_PATH", os.path.join(app.instance_path, "quiz_settings.json"))


def _load_persisted() -> dict:
    return load_persisted_settings(_get_settings_file_path()) or {"conjugations": {}, "porpara": {}, "vocab": {}}


def _save_persisted(settings: dict) -> None:
    save_persisted_settings(_get_settings_file_path(), settings)


def _filter_list(values, allowed_set):
    if not isinstance(values, list):
        return []
    return [v for v in values if v in allowed_set]


def _persist_section(section_name: str, section_payload: dict) -> None:
    settings = _load_persisted()
    if not isinstance(settings, dict):
        settings = {"conjugations": {}, "porpara": {}, "vocab": {}}
    settings[section_name] = section_payload
    _save_persisted(validate_settings(settings))

# Person sets
DEFAULT_PERSONS = ['yo', 'tu', 'el/ella/usted', 'nosotros', 'vosotros', 'ellos/ellas/ustedes']
IMPERATIVE_TENSES = {'imperativo_afirmativo', 'imperativo_negativo'}
IMPERATIVE_PERSONS = ['tu', 'el/ella/usted', 'nosotros', 'vosotros', 'ellos/ellas/ustedes']

# Load and validate data on startup
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'conjugations.json')
conjugations_data = load_and_validate_data(DATA_FILE)

POR_PARA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'por_para.json')
por_para_data = load_and_validate_por_para_data(POR_PARA_FILE)

VOCABULARY_FILE = os.path.join(os.path.dirname(__file__), 'data', 'vocabulary.json')
vocabulary_data = load_and_validate_vocabulary_data(VOCABULARY_FILE)

# Vocab set display names mapping
VOCAB_SET_NAMES = {
    'dele_b1_info': 'DELE B1 — Info Page',
    'por_para': 'Por/Para Vocabulary',
    'dialog_01_saludo_presentacion': 'Dialog 01 — Saludo y Presentación',
    'dialog_05_hablar_del_tiempo': 'Dialog 05 — Hablar del Tiempo',
    'dialog_09_decir_la_hora': 'Dialog 09 — Decir la Hora',
    'dialog_13_describir_objetos': 'Dialog 13 — Describir Objetos',
    'dialog_18_en_el_transporte_publico': 'Dialog 18 — En el Transporte Público',
    'dialog_23_describir_el_lugar_donde_vives': 'Dialog 23 — Describir el Lugar donde Vives',
    'dialog_33_hablar_de_salud_y_ejercicio': 'Dialog 33 — Hablar de Salud y Ejercicio',
    'dialog_45_hablar_de_medio_ambiente': 'Dialog 45 — Hablar de Medio Ambiente',
}

# Category display names mapping
POR_CATEGORY_NAMES = {
    'motivation_reason': 'Motivation/Reason',
    'duration': 'Duration',
    'cost_price': 'Cost/Price',
    'location_movement': 'Location/Movement',
    'means_of_travel': 'Means of Travel',
    'means_of_communication': 'Means of Communication',
    'passive_voice_action': 'Passive Voice Action'
}

PARA_CATEGORY_NAMES = {
    'destination': 'Destination',
    'goal': 'Goal',
    'recipients': 'Recipients',
    'deadlines': 'Deadlines',
    'expression_of_opinion': 'Expression of Opinion',
    'disparate_idea': 'Disparate Idea'
}

@app.route('/')
def index():
    """Main page with quiz selection"""
    return render_template('index.html')

@app.route("/info/dele-b1")
def dele_b1_information():
    """Information page about DELE B1 competencies."""
    return render_template("dele_b1_info.html")

@app.route('/quiz/conjugations/save-settings', methods=['POST'])
def save_settings():
    """Save user settings without starting quiz"""
    selected_verbs = request.form.getlist('verbs')
    selected_tenses = request.form.getlist('tenses')
    seconds_per_question = int(request.form.get('seconds_per_question', 3))
    seconds_per_answer = int(request.form.get('seconds_per_answer', 4))
    num_questions = int(request.form.get('num_questions', 10))
    
    # Get contestant names (filter out empty strings)
    contestant_names = [name.strip() for name in request.form.getlist('contestants') if name.strip()]
    
    # Save preferences to session
    session['saved_verbs'] = selected_verbs
    session['saved_tenses'] = selected_tenses
    session['saved_seconds_per_question'] = seconds_per_question
    session['saved_seconds_per_answer'] = seconds_per_answer
    session['saved_num_questions'] = num_questions
    session['saved_contestants'] = contestant_names

    _persist_section(
        "conjugations",
        {
            "selected_verbs": selected_verbs,
            "selected_tenses": selected_tenses,
            "seconds_per_question": seconds_per_question,
            "seconds_per_answer": seconds_per_answer,
            "num_questions": num_questions,
            "contestants": contestant_names,
        },
    )
    
    return redirect(url_for('index'))

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

    persisted = _load_persisted().get("conjugations", {}) or {}
    verbs_set = set(verbs)
    tenses_set = set(tenses)

    # Defaults from current data
    selected_verbs = verbs
    selected_tenses = tenses
    seconds_per_question = 3
    seconds_per_answer = 4
    num_questions = 10
    contestants = []

    # Apply persisted (filtered to current data)
    if isinstance(persisted, dict) and persisted:
        persisted_verbs = _filter_list(persisted.get("selected_verbs"), verbs_set)
        persisted_tenses = _filter_list(persisted.get("selected_tenses"), tenses_set)
        selected_verbs = persisted_verbs or selected_verbs
        selected_tenses = persisted_tenses or selected_tenses
        if isinstance(persisted.get("seconds_per_question"), int):
            seconds_per_question = persisted["seconds_per_question"]
        if isinstance(persisted.get("seconds_per_answer"), int):
            seconds_per_answer = persisted["seconds_per_answer"]
        if isinstance(persisted.get("num_questions"), int):
            num_questions = persisted["num_questions"]
        if isinstance(persisted.get("contestants"), list):
            contestants = [c for c in persisted.get("contestants", []) if isinstance(c, str) and c.strip()]

    # Session overrides (current behavior)
    selected_verbs = _filter_list(session.get("saved_verbs", selected_verbs), verbs_set) or selected_verbs
    selected_tenses = _filter_list(session.get("saved_tenses", selected_tenses), tenses_set) or selected_tenses
    seconds_per_question = session.get("saved_seconds_per_question", seconds_per_question)
    seconds_per_answer = session.get("saved_seconds_per_answer", seconds_per_answer)
    num_questions = session.get("saved_num_questions", num_questions)
    contestants = session.get("saved_contestants", contestants)

    saved_prefs = {
        "selected_verbs": selected_verbs,
        "selected_tenses": selected_tenses,
        "seconds_per_question": seconds_per_question,
        "seconds_per_answer": seconds_per_answer,
        "num_questions": num_questions,
        "contestants": contestants,
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
    seconds_per_answer = int(request.form.get('seconds_per_answer', 4))
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
        persons = IMPERATIVE_PERSONS if tense in IMPERATIVE_TENSES else DEFAULT_PERSONS
        person = random.choice(persons)
        
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
    session['seconds_per_answer'] = seconds_per_answer
    session['num_questions'] = num_questions
    session['contest_mode'] = contest_mode
    
    # Save user preferences for next time
    session['saved_verbs'] = selected_verbs
    session['saved_tenses'] = selected_tenses
    session['saved_seconds_per_question'] = seconds_per_question
    session['saved_seconds_per_answer'] = seconds_per_answer
    session['saved_num_questions'] = num_questions
    session['saved_contestants'] = contestant_names

    _persist_section(
        "conjugations",
        {
            "selected_verbs": selected_verbs,
            "selected_tenses": selected_tenses,
            "seconds_per_question": seconds_per_question,
            "seconds_per_answer": seconds_per_answer,
            "num_questions": num_questions,
            "contestants": contestant_names,
        },
    )
    
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
    seconds_per_answer = session.get('seconds_per_answer', 4)
    contest_mode = session.get('contest_mode', False)
    
    return render_template('quiz.html', 
                         question=question,
                         question_num=current_question + 1,
                         total_questions=len(questions),
                         seconds_per_question=seconds_per_question,
                         seconds_per_answer=seconds_per_answer,
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

# Por vs Para Quiz Routes
@app.route('/quiz/porpara/options')
def porpara_options():
    """Options page for por/para quiz"""
    por_data = por_para_data.get('por', {})
    para_data = por_para_data.get('para', {})
    
    # Get all por categories
    por_categories = {key: POR_CATEGORY_NAMES.get(key, key.replace('_', ' ').title()) 
                     for key in por_data.keys()}
    
    # Get all para categories
    para_categories = {key: PARA_CATEGORY_NAMES.get(key, key.replace('_', ' ').title()) 
                      for key in para_data.keys()}

    persisted = _load_persisted().get("porpara", {}) or {}
    por_keys = list(por_categories.keys())
    para_keys = list(para_categories.keys())
    por_set = set(por_keys)
    para_set = set(para_keys)

    # Defaults from current data
    selected_por_categories = por_keys
    selected_para_categories = para_keys
    seconds_per_question = 7
    seconds_per_answer = 4
    num_questions = 10
    contestants = []

    # Apply persisted (filtered to current data)
    if isinstance(persisted, dict) and persisted:
        persisted_por = _filter_list(persisted.get("selected_por_categories"), por_set)
        persisted_para = _filter_list(persisted.get("selected_para_categories"), para_set)
        selected_por_categories = persisted_por or selected_por_categories
        selected_para_categories = persisted_para or selected_para_categories
        if isinstance(persisted.get("seconds_per_question"), int):
            seconds_per_question = persisted["seconds_per_question"]
        if isinstance(persisted.get("seconds_per_answer"), int):
            seconds_per_answer = persisted["seconds_per_answer"]
        if isinstance(persisted.get("num_questions"), int):
            num_questions = persisted["num_questions"]
        if isinstance(persisted.get("contestants"), list):
            contestants = [c for c in persisted.get("contestants", []) if isinstance(c, str) and c.strip()]

    # Session overrides
    selected_por_categories = _filter_list(
        session.get("porpara_saved_por_categories", selected_por_categories),
        por_set,
    ) or selected_por_categories
    selected_para_categories = _filter_list(
        session.get("porpara_saved_para_categories", selected_para_categories),
        para_set,
    ) or selected_para_categories
    seconds_per_question = session.get("porpara_saved_seconds_per_question", seconds_per_question)
    seconds_per_answer = session.get("porpara_saved_seconds_per_answer", seconds_per_answer)
    num_questions = session.get("porpara_saved_num_questions", num_questions)
    contestants = session.get("porpara_saved_contestants", contestants)

    saved_prefs = {
        "selected_por_categories": selected_por_categories,
        "selected_para_categories": selected_para_categories,
        "seconds_per_question": seconds_per_question,
        "seconds_per_answer": seconds_per_answer,
        "num_questions": num_questions,
        "contestants": contestants,
    }
    
    return render_template('por_para_options.html',
                         por_categories=por_categories,
                         para_categories=para_categories,
                         saved_prefs=saved_prefs)

@app.route('/quiz/porpara/save-settings', methods=['POST'])
def porpara_save_settings():
    """Save por/para quiz settings without starting quiz"""
    selected_por_categories = request.form.getlist('por_categories')
    selected_para_categories = request.form.getlist('para_categories')
    seconds_per_question = int(request.form.get('seconds_per_question', 7))
    seconds_per_answer = int(request.form.get('seconds_per_answer', 4))
    num_questions = int(request.form.get('num_questions', 10))
    
    # Get contestant names (filter out empty strings)
    contestant_names = [name.strip() for name in request.form.getlist('contestants') if name.strip()]
    
    # Save preferences to session
    session['porpara_saved_por_categories'] = selected_por_categories
    session['porpara_saved_para_categories'] = selected_para_categories
    session['porpara_saved_seconds_per_question'] = seconds_per_question
    session['porpara_saved_seconds_per_answer'] = seconds_per_answer
    session['porpara_saved_num_questions'] = num_questions
    session['porpara_saved_contestants'] = contestant_names

    _persist_section(
        "porpara",
        {
            "selected_por_categories": selected_por_categories,
            "selected_para_categories": selected_para_categories,
            "seconds_per_question": seconds_per_question,
            "seconds_per_answer": seconds_per_answer,
            "num_questions": num_questions,
            "contestants": contestant_names,
        },
    )
    
    return redirect(url_for('index'))

@app.route('/quiz/porpara/start', methods=['POST'])
def porpara_start_quiz():
    """Start por/para quiz with selected options"""
    selected_por_categories = request.form.getlist('por_categories')
    selected_para_categories = request.form.getlist('para_categories')
    seconds_per_question = int(request.form.get('seconds_per_question', 7))
    seconds_per_answer = int(request.form.get('seconds_per_answer', 4))
    num_questions = int(request.form.get('num_questions', 10))
    
    # Get contestant names (filter out empty strings)
    contestant_names = [name.strip() for name in request.form.getlist('contestants') if name.strip()]
    contest_mode = len(contestant_names) > 0
    
    # Validate selections
    if not selected_por_categories and not selected_para_categories:
        return redirect(url_for('porpara_options'))
    
    # Generate questions
    questions = []
    por_data = por_para_data.get('por', {})
    para_data = por_para_data.get('para', {})
    
    # Collect all available sentences from selected categories
    available_sentences = []
    for category in selected_por_categories:
        if category in por_data:
            for sentence in por_data[category]:
                available_sentences.append({
                    'sentence': sentence,
                    'answer': 'por',
                    'category': category
                })
    
    for category in selected_para_categories:
        if category in para_data:
            for sentence in para_data[category]:
                available_sentences.append({
                    'sentence': sentence,
                    'answer': 'para',
                    'category': category
                })
    
    if not available_sentences:
        return redirect(url_for('porpara_options'))
    
    # Generate base questions
    base_questions = []
    for _ in range(num_questions):
        question = random.choice(available_sentences).copy()
        base_questions.append(question)
    
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
    session['porpara_questions'] = questions
    session['porpara_current_question'] = 0
    session['porpara_seconds_per_question'] = seconds_per_question
    session['porpara_seconds_per_answer'] = seconds_per_answer
    session['porpara_num_questions'] = num_questions
    session['porpara_contest_mode'] = contest_mode
    
    # Save user preferences for next time
    session['porpara_saved_por_categories'] = selected_por_categories
    session['porpara_saved_para_categories'] = selected_para_categories
    session['porpara_saved_seconds_per_question'] = seconds_per_question
    session['porpara_saved_seconds_per_answer'] = seconds_per_answer
    session['porpara_saved_num_questions'] = num_questions
    session['porpara_saved_contestants'] = contestant_names

    _persist_section(
        "porpara",
        {
            "selected_por_categories": selected_por_categories,
            "selected_para_categories": selected_para_categories,
            "seconds_per_question": seconds_per_question,
            "seconds_per_answer": seconds_per_answer,
            "num_questions": num_questions,
            "contestants": contestant_names,
        },
    )
    
    return redirect(url_for('porpara_run_quiz'))

@app.route('/quiz/porpara/run')
def porpara_run_quiz():
    """Por/para quiz execution page"""
    if 'porpara_questions' not in session:
        return redirect(url_for('porpara_options'))
    
    questions = session.get('porpara_questions', [])
    current_question = session.get('porpara_current_question', 0)
    
    if current_question >= len(questions):
        # Quiz complete, return to options
        # Keep saved preferences, only remove quiz-specific data
        session.pop('porpara_questions', None)
        session.pop('porpara_current_question', None)
        session.pop('porpara_contest_mode', None)
        return redirect(url_for('porpara_options'))
    
    question = questions[current_question]
    seconds_per_question = session.get('porpara_seconds_per_question', 7)
    seconds_per_answer = session.get('porpara_seconds_per_answer', 4)
    contest_mode = session.get('porpara_contest_mode', False)
    
    return render_template('por_para_quiz.html',
                         question=question,
                         question_num=current_question + 1,
                         total_questions=len(questions),
                         seconds_per_question=seconds_per_question,
                         seconds_per_answer=seconds_per_answer,
                         contest_mode=contest_mode)

@app.route('/quiz/porpara/next', methods=['POST'])
def porpara_next_question():
    """Move to next por/para question"""
    current_question = session.get('porpara_current_question', 0)
    session['porpara_current_question'] = current_question + 1
    
    if session['porpara_current_question'] >= len(session.get('porpara_questions', [])):
        # Quiz complete
        # Keep saved preferences, only remove quiz-specific data
        session.pop('porpara_questions', None)
        session.pop('porpara_current_question', None)
        session.pop('porpara_contest_mode', None)
        return jsonify({'complete': True})
    
    return jsonify({'complete': False})

# Vocabulary Quiz Routes
@app.route('/quiz/vocab/options')
def vocab_options():
    """Options page for vocabulary quiz"""
    vocab_sets = vocabulary_data.get('vocab_sets', {})
    
    # Get vocab set names with display names and word counts
    vocab_set_list = []
    for set_key in sorted(vocab_sets.keys()):
        display_name = VOCAB_SET_NAMES.get(set_key, set_key.replace('_', ' ').title())
        word_count = len(vocab_sets[set_key]) if isinstance(vocab_sets[set_key], list) else 0
        vocab_set_list.append((set_key, display_name, word_count))

    persisted = _load_persisted().get("vocab", {}) or {}
    available_set_keys = [set_key for set_key, _, _ in vocab_set_list]
    available_set_set = set(available_set_keys)

    # Defaults from current data
    selected_vocab_sets = available_set_keys
    direction = "spanish_to_german"
    seconds_per_question = 5
    seconds_per_answer = 4
    num_questions = 10
    contestants = []

    # Apply persisted (filtered to current data)
    if isinstance(persisted, dict) and persisted:
        persisted_sets = _filter_list(persisted.get("selected_vocab_sets"), available_set_set)
        selected_vocab_sets = persisted_sets or selected_vocab_sets
        if isinstance(persisted.get("direction"), str):
            direction = persisted["direction"]
        if isinstance(persisted.get("seconds_per_question"), int):
            seconds_per_question = persisted["seconds_per_question"]
        if isinstance(persisted.get("seconds_per_answer"), int):
            seconds_per_answer = persisted["seconds_per_answer"]
        if isinstance(persisted.get("num_questions"), int):
            num_questions = persisted["num_questions"]
        if isinstance(persisted.get("contestants"), list):
            contestants = [c for c in persisted.get("contestants", []) if isinstance(c, str) and c.strip()]

    # Session overrides
    selected_vocab_sets = _filter_list(
        session.get("vocab_saved_vocab_sets", selected_vocab_sets),
        available_set_set,
    ) or selected_vocab_sets
    direction = session.get("vocab_saved_direction", direction)
    seconds_per_question = session.get("vocab_saved_seconds_per_question", seconds_per_question)
    seconds_per_answer = session.get("vocab_saved_seconds_per_answer", seconds_per_answer)
    num_questions = session.get("vocab_saved_num_questions", num_questions)
    contestants = session.get("vocab_saved_contestants", contestants)

    saved_prefs = {
        "selected_vocab_sets": selected_vocab_sets,
        "direction": direction,
        "seconds_per_question": seconds_per_question,
        "seconds_per_answer": seconds_per_answer,
        "num_questions": num_questions,
        "contestants": contestants,
    }
    
    return render_template('vocab_options.html',
                         vocab_sets=vocab_set_list,
                         saved_prefs=saved_prefs)

@app.route('/quiz/vocab/save-settings', methods=['POST'])
def vocab_save_settings():
    """Save vocabulary quiz settings without starting quiz"""
    selected_vocab_sets = request.form.getlist('vocab_sets')
    direction = request.form.get('direction', 'spanish_to_german')
    seconds_per_question = int(request.form.get('seconds_per_question', 5))
    seconds_per_answer = int(request.form.get('seconds_per_answer', 4))
    num_questions = int(request.form.get('num_questions', 10))
    
    # Get contestant names (filter out empty strings)
    contestant_names = [name.strip() for name in request.form.getlist('contestants') if name.strip()]
    
    # Save preferences to session
    session['vocab_saved_vocab_sets'] = selected_vocab_sets
    session['vocab_saved_direction'] = direction
    session['vocab_saved_seconds_per_question'] = seconds_per_question
    session['vocab_saved_seconds_per_answer'] = seconds_per_answer
    session['vocab_saved_num_questions'] = num_questions
    session['vocab_saved_contestants'] = contestant_names

    _persist_section(
        "vocab",
        {
            "selected_vocab_sets": selected_vocab_sets,
            "direction": direction,
            "seconds_per_question": seconds_per_question,
            "seconds_per_answer": seconds_per_answer,
            "num_questions": num_questions,
            "contestants": contestant_names,
        },
    )
    
    return redirect(url_for('index'))

@app.route('/quiz/vocab/start', methods=['POST'])
def vocab_start_quiz():
    """Start vocabulary quiz with selected options"""
    selected_vocab_sets = request.form.getlist('vocab_sets')
    direction = request.form.get('direction', 'spanish_to_german')
    seconds_per_question = int(request.form.get('seconds_per_question', 5))
    seconds_per_answer = int(request.form.get('seconds_per_answer', 4))
    num_questions = int(request.form.get('num_questions', 10))
    
    # Get contestant names (filter out empty strings)
    contestant_names = [name.strip() for name in request.form.getlist('contestants') if name.strip()]
    contest_mode = len(contestant_names) > 0
    
    # Validate selections
    if not selected_vocab_sets:
        return redirect(url_for('vocab_options'))
    
    # Collect words from selected vocab sets
    vocab_sets = vocabulary_data.get('vocab_sets', {})
    available_words = []
    
    for set_key in selected_vocab_sets:
        if set_key in vocab_sets:
            for word_entry in vocab_sets[set_key]:
                available_words.append(word_entry.copy())
    
    if not available_words:
        return redirect(url_for('vocab_options'))
    
    # Generate base questions
    base_questions = []
    for _ in range(num_questions):
        word_entry = random.choice(available_words).copy()
        
        # Determine question and answer based on direction
        if direction == 'spanish_to_german':
            question = word_entry['spanish']
            answer = word_entry['german']
        elif direction == 'spanish_to_english':
            question = word_entry['spanish']
            answer = word_entry['english']
        elif direction == 'german_to_spanish':
            question = word_entry['german']
            answer = word_entry['spanish']
        elif direction == 'english_to_spanish':
            question = word_entry['english']
            answer = word_entry['spanish']
        else:
            # Default to spanish_to_german
            question = word_entry['spanish']
            answer = word_entry['german']
        
        base_questions.append({
            'question': question,
            'answer': answer,
            'direction': direction
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
            base_questions[i] = question
    
    questions = base_questions
    
    # Store quiz data in session
    session['vocab_questions'] = base_questions
    session['vocab_current_question'] = 0
    session['vocab_seconds_per_question'] = seconds_per_question
    session['vocab_seconds_per_answer'] = seconds_per_answer
    session['vocab_num_questions'] = num_questions
    session['vocab_contest_mode'] = contest_mode
    session['vocab_direction'] = direction
    
    # Save user preferences for next time
    session['vocab_saved_vocab_sets'] = selected_vocab_sets
    session['vocab_saved_direction'] = direction
    session['vocab_saved_seconds_per_question'] = seconds_per_question
    session['vocab_saved_seconds_per_answer'] = seconds_per_answer
    session['vocab_saved_num_questions'] = num_questions
    session['vocab_saved_contestants'] = contestant_names

    _persist_section(
        "vocab",
        {
            "selected_vocab_sets": selected_vocab_sets,
            "direction": direction,
            "seconds_per_question": seconds_per_question,
            "seconds_per_answer": seconds_per_answer,
            "num_questions": num_questions,
            "contestants": contestant_names,
        },
    )
    
    return redirect(url_for('vocab_run_quiz'))

@app.route('/quiz/vocab/run')
def vocab_run_quiz():
    """Vocabulary quiz execution page"""
    if 'vocab_questions' not in session:
        return redirect(url_for('vocab_options'))
    
    questions = session.get('vocab_questions', [])
    current_question = session.get('vocab_current_question', 0)
    
    if current_question >= len(questions):
        # Quiz complete, return to options
        # Keep saved preferences, only remove quiz-specific data
        session.pop('vocab_questions', None)
        session.pop('vocab_current_question', None)
        session.pop('vocab_contest_mode', None)
        session.pop('vocab_direction', None)
        return redirect(url_for('vocab_options'))
    
    question = questions[current_question]
    seconds_per_question = session.get('vocab_seconds_per_question', 5)
    seconds_per_answer = session.get('vocab_seconds_per_answer', 4)
    contest_mode = session.get('vocab_contest_mode', False)
    
    return render_template('vocab_quiz.html',
                         question=question,
                         question_num=current_question + 1,
                         total_questions=len(questions),
                         seconds_per_question=seconds_per_question,
                         seconds_per_answer=seconds_per_answer,
                         contest_mode=contest_mode)

@app.route('/quiz/vocab/next', methods=['POST'])
def vocab_next_question():
    """Move to next vocabulary question"""
    current_question = session.get('vocab_current_question', 0)
    session['vocab_current_question'] = current_question + 1
    
    if session['vocab_current_question'] >= len(session.get('vocab_questions', [])):
        # Quiz complete
        # Keep saved preferences, only remove quiz-specific data
        session.pop('vocab_questions', None)
        session.pop('vocab_current_question', None)
        session.pop('vocab_contest_mode', None)
        session.pop('vocab_direction', None)
        return jsonify({'complete': True})
    
    return jsonify({'complete': False})

if __name__ == '__main__':
    app.run(debug=True)
