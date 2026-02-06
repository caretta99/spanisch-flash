// Quiz timing and progression logic

let questionTimer;
let answerTimer;
let currentSeconds = 0;
// Use configurable secondsPerAnswer with fallback to 4 for backward compatibility
const answerDisplayTime = typeof secondsPerAnswer !== 'undefined' ? secondsPerAnswer : 4;

function startQuestionTimer() {
    const questionDisplay = document.getElementById('question-display');
    const answerDisplay = document.getElementById('answer-display');
    const timerElement = document.getElementById('timer');
    const skipButton = document.getElementById('skip-answer-button');
    
    // Reset display
    questionDisplay.style.display = 'block';
    answerDisplay.style.display = 'none';
    
    // Hide skip button during question display
    if (skipButton) {
        skipButton.style.display = 'none';
    }
    
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
    const skipButton = document.getElementById('skip-answer-button');
    
    // Hide question, show answer
    questionDisplay.style.display = 'none';
    answerDisplay.style.display = 'block';
    
    // Show skip button during answer display
    if (skipButton) {
        skipButton.style.display = 'block';
    }
    
    // Show answer for configured time, then move to next question
    answerTimer = setTimeout(() => {
        moveToNextQuestion();
    }, answerDisplayTime * 1000);
}

function skipAnswer() {
    // Clear the answer timer
    if (answerTimer) {
        clearTimeout(answerTimer);
    }
    
    // Hide skip button
    const skipButton = document.getElementById('skip-answer-button');
    if (skipButton) {
        skipButton.style.display = 'none';
    }
    
    // Immediately move to next question
    moveToNextQuestion();
}

function moveToNextQuestion() {
    // Determine quiz type (default to conjugations for backward compatibility)
    const quizType = typeof window.quizType !== 'undefined' ? window.quizType : 'conjugations';
    const nextUrl = `/quiz/${quizType}/next`;
    const optionsUrl = `/quiz/${quizType}/options`;
    
    // Check if quiz is complete
    fetch(nextUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.complete) {
            // Quiz complete, redirect to options page
            window.location.href = optionsUrl;
        } else {
            // Reload page for next question
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Fallback: redirect to options page
        window.location.href = optionsUrl;
    });
}

// Start the quiz when page loads
document.addEventListener('DOMContentLoaded', () => {
    startQuestionTimer();
});
