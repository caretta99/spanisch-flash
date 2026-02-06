// Quiz timing and progression logic

let questionTimer;
let answerTimer;
let currentSeconds = 0;
const ANSWER_DISPLAY_TIME = 4; // seconds

function startQuestionTimer() {
    const questionDisplay = document.getElementById('question-display');
    const answerDisplay = document.getElementById('answer-display');
    const timerElement = document.getElementById('timer');
    
    // Reset display
    questionDisplay.style.display = 'block';
    answerDisplay.style.display = 'none';
    currentSeconds = secondsPerQuestion;
    timerElement.textContent = currentSeconds;
    
    // Update timer every second
    questionTimer = setInterval(() => {
        currentSeconds--;
        timerElement.textContent = currentSeconds;
        
        if (currentSeconds <= 0) {
            clearInterval(questionTimer);
            showAnswer();
        }
    }, 1000);
}

function showAnswer() {
    const questionDisplay = document.getElementById('question-display');
    const answerDisplay = document.getElementById('answer-display');
    
    // Hide question, show answer
    questionDisplay.style.display = 'none';
    answerDisplay.style.display = 'block';
    
    // Show answer for 5 seconds, then move to next question
    answerTimer = setTimeout(() => {
        moveToNextQuestion();
    }, ANSWER_DISPLAY_TIME * 1000);
}

function moveToNextQuestion() {
    // Check if quiz is complete
    fetch('/quiz/conjugations/next', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.complete) {
            // Quiz complete, redirect to options page
            window.location.href = '/quiz/conjugations/options';
        } else {
            // Reload page for next question
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Fallback: redirect to options page
        window.location.href = '/quiz/conjugations/options';
    });
}

// Start the quiz when page loads
document.addEventListener('DOMContentLoaded', () => {
    startQuestionTimer();
});
