# Jona's Spanish Flash - Spanish Verb Conjugation Quiz

A Flask web application for practicing Spanish verb conjugations through interactive flashcard-style quizzes.

## Features

- **Conjugation Quiz**: Practice irregular Spanish verb conjugations across multiple tenses
- **Customizable Options**: Choose specific verbs, tenses, timing, and number of questions
- **Flashcard Style**: Questions displayed for a set time, followed by answers
- **Data Validation**: Ensures consistency across all verb conjugations
- **Contest Mode**: Assign questions to multiple contestants for competitive practice
- **Responsive Design**: Optimized for both desktop and mobile devices

## Screenshots

### Main Page
![Main Page](docs/screenshot_mainpage.png)

### Options Page
![Options Page](docs/screenshot_conjugations_options.png)

### Quiz - Question Display
![Quiz Question](docs/screenshot_conjugations_question.png)

### Quiz - Answer Display
![Quiz Answer](docs/screenshot_conjugations_answer.png)

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

### 1. Main Page
Select the quiz type you want to practice (currently: Conjugations Quiz).

### 2. Options Page
Configure your quiz preferences:
- Choose which irregular verbs to practice (select/deselect all buttons available)
- Select which tenses to include (select/deselect all buttons available)
- **Contest Mode (Optional)**: Add contestant names to assign questions to specific players
- Set the number of seconds per question (default: 3 seconds)
- Set the total number of questions (default: 10)
- Click "Start Quiz" to begin, or "Return to Main" to save settings and go back

Your settings are automatically saved and will be restored when you return to the options page.

### 3. Quiz Page
- Each question displays the verb infinitive, tense, and person
- In contest mode, the assigned contestant name is shown above the question
- A countdown timer shows the remaining time
- After the set time, the correct answer is displayed for 4 seconds
- The quiz automatically advances to the next question
- Use "Return to Options" button to exit the quiz early
- After completing all questions, you'll return to the options page with your settings preserved

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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
