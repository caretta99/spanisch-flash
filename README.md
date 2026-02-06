# Spanisch Flash - Spanish Verb Conjugation Quiz

A Flask web application for practicing Spanish verb conjugations through interactive flashcard-style quizzes.

## Features

- **Conjugation Quiz**: Practice irregular Spanish verb conjugations across multiple tenses
- **Customizable Options**: Choose specific verbs, tenses, timing, and number of questions
- **Flashcard Style**: Questions displayed for a set time, followed by answers
- **Data Validation**: Ensures consistency across all verb conjugations

## Project Structure

```
spanisch-flash/
├── app.py                 # Flask application entry point
├── pyproject.toml        # uv project configuration
├── .gitignore            # Git ignore rules
├── README.md             # Project documentation
├── data/
│   └── conjugations.json  # Verb conjugation data
├── utils/
│   └── data_validator.py  # Data consistency validation
├── templates/
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Main page (quiz selection)
│   ├── options.html      # Quiz options page
│   └── quiz.html         # Active quiz page
└── static/
    ├── css/
    │   └── style.css     # Custom styling
    └── js/
        └── quiz.js       # Quiz timing logic
```

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd spanisch-flash
```

2. Create a virtual environment and install dependencies using uv:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

1. **Main Page**: Select the quiz type you want to practice (currently: Conjugations Quiz)
2. **Options Page**: 
   - Choose which irregular verbs to practice
   - Select which tenses to include
   - Set the number of seconds per question (default: 4 seconds)
   - Set the total number of questions (default: 10)
   - Click "Start Quiz" to begin
3. **Quiz Page**: 
   - Each question displays the verb infinitive, tense, and person
   - After the set time, the correct answer is shown for 5 seconds
   - The quiz automatically advances to the next question
   - After completing all questions, you'll return to the options page

## Data Structure

The conjugation data is stored in `data/conjugations.json` with the following structure:

```json
{
  "conjugations_quiz": {
    "verb_name": {
      "tense_name": {
        "yo": "conjugation",
        "tu": "conjugation",
        "el/ella/usted": "conjugation",
        "nosotros": "conjugation",
        "vosotros": "conjugation",
        "ellos/ellas/ustedes": "conjugation"
      }
    }
  }
}
```

## Development

The application includes data validation that runs on startup to ensure:
- All verbs have all tenses
- All tenses have all 6 person forms
- Data consistency across the entire dataset

## License

[Add your license here]
