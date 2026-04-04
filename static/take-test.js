// ---------- Прохождение тестов ----------
const API_BASE = '/tests';
const RESULTS_API = '/results';
let currentPage = 1;
const limit = 5;
let searchTimeout = null;
let currentResultId = null;
let currentTakingTest = null;
let userAnswers = {};

console.log('Take test page loaded');

// ---------- Элементы DOM ----------
const availableTestsList = document.getElementById('availableTestsList');
const searchFilter = document.getElementById('searchFilter');
const testTakingMode = document.getElementById('testTakingMode');
const testResultMode = document.getElementById('testResultMode');
const takingTestTitle = document.getElementById('takingTestTitle');
const questionsContainer = document.getElementById('questionsContainer');
const finishTestBtn = document.getElementById('finishTestBtn');
const progressFill = document.getElementById('progressFill');
const resultTitle = document.getElementById('resultTitle');
const resultScore = document.getElementById('resultScore');
const resultDetails = document.getElementById('resultDetails');

// ========== СПИСОК ДОСТУПНЫХ ТЕСТОВ ==========

// ---------- Загрузка доступных тестов ----------
async function loadAvailableTests(page = 1, search = '') {
    if (!availableTestsList) return;
    
    try {
        availableTestsList.innerHTML = '<p>Загрузка...</p>';
        
        if (!window.currentUser) {
            availableTestsList.innerHTML = '<p class="empty-list">Войдите чтобы увидеть тесты</p>';
            return;
        }
        
        let url = `${RESULTS_API}/available?page=${page}&limit=${limit}`;
        if (search) {
            url += `&search=${encodeURIComponent(search)}`;
        }
        
        const response = await fetch(url, {
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const data = await response.json();
        
        if (!data.data || data.data.length === 0) {
            availableTestsList.innerHTML = '<p class="empty-list">Нет доступных тестов</p>';
            return;
        }

        let html = '';
        data.data.forEach(test => {
            html += `
                <div class="test-card">
                    <div class="test-header">
                        <h3>${escapeHtml(test.title)}</h3>
                        <span class="test-attempts">Попыток: ${test.user_attempts || 0}</span>
                    </div>
                    <div class="test-meta">
                        <span>Автор: ${escapeHtml(test.author_email)}</span>
                        <span>Вопросов: ${test.questions_count}</span>
                    </div>
                    <p>${escapeHtml(test.description || '')}</p>
                    <div class="test-actions">
                        <button class="btn" onclick="startTest(${test.id})">Начать тест</button>
                    </div>
                </div>
            `;
        });

        const totalPages = Math.ceil(data.meta.total / limit);
        html += '<div class="pagination">';
        if (page > 1) {
            html += `<button onclick="loadAvailableTests(${page - 1})">Предыдущая</button>`;
        }
        html += `<span>Страница ${page} из ${totalPages}</span>`;
        if (page < totalPages) {
            html += `<button onclick="loadAvailableTests(${page + 1})">Следующая</button>`;
        }
        html += '</div>';

        availableTestsList.innerHTML = html;
        
    } catch (error) {
        availableTestsList.innerHTML = `<p class="error">Ошибка: ${error.message}</p>`;
    }
}

// ---------- Поиск с debounce ----------
if (searchFilter) {
    searchFilter.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            loadAvailableTests(1, e.target.value);
        }, 300);
    });
}

// ========== ПРОХОЖДЕНИЕ ТЕСТА ==========

// ---------- Начать тест ----------
window.startTest = async function(testId) {
    try {
        if (!window.currentUser) {
            alert('Для прохождения тестов необходимо авторизоваться');
            window.showLoginModal();
            return;
        }
        
        const response = await fetch(`${RESULTS_API}/start/${testId}`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка начала теста');
        }
        
        const result = await response.json();
        
        if (!result.questions || result.questions.length === 0) {
            const questionsResponse = await fetch(`${API_BASE}/${testId}/questions`, {
                credentials: 'include'
            });
            if (questionsResponse.ok) {
                result.questions = await questionsResponse.json();
            } else {
                result.questions = [];
            }
        }
        
        currentResultId = result.id;
        currentTakingTest = result;
        userAnswers = {};
        
        showTestTakingMode(result);
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
};

function showTestTakingMode(test) {
    if (!testTakingMode || !testResultMode || !takingTestTitle || !questionsContainer || !finishTestBtn) return;
    
    document.getElementById('testsListMode').style.display = 'none';
    testTakingMode.style.display = 'block';
    testResultMode.style.display = 'none';
    
    takingTestTitle.textContent = `Прохождение: ${test.test_title || 'Тест'}`;
    
    if (!test.questions || test.questions.length === 0) {
        questionsContainer.innerHTML = '<p class="empty-list">В этом тесте пока нет вопросов</p>';
        finishTestBtn.style.display = 'none';
        return;
    }
    
    renderQuestionsForTaking(test.questions);
    updateProgress();
}

function renderQuestionsForTaking(questions) {
    if (!questionsContainer) return;
    
    let html = '';
    
    questions.forEach((q, index) => {
        const answers = q.answers || [];
        const savedAnswer = userAnswers[q.id];
        
        html += `
            <div class="question-card" data-question-id="${q.id}">
                <h4>Вопрос ${index + 1}:</h4>
                <p>${escapeHtml(q.text)}</p>
                <div class="answers-list">
        `;
        
        if (answers.length === 0) {
            html += `<p class="empty-list">Нет вариантов ответа</p>`;
        } else {
            answers.forEach(a => {
                const checked = savedAnswer === a.id ? 'checked' : '';
                html += `
                    <div class="answer-item">
                        <input type="radio" 
                               name="question_${q.id}" 
                               value="${a.id}" 
                               ${checked}
                               onchange="saveAnswer(${q.id}, ${a.id})">
                        <span>${escapeHtml(a.text)}</span>
                    </div>
                `;
            });
        }
        
        html += `</div></div>`;
    });
    
    questionsContainer.innerHTML = html;
    
    if (finishTestBtn) {
        finishTestBtn.style.display = questions.length > 0 ? 'block' : 'none';
    }
}

window.saveAnswer = function(questionId, answerId) {
    userAnswers[questionId] = answerId;
    updateProgress();
    
    fetch(`${RESULTS_API}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            result_id: currentResultId,
            question_id: questionId,
            selected_answer_id: answerId
        }),
        credentials: 'include'
    }).catch(error => console.error('Ошибка сохранения ответа:', error));
};

function updateProgress() {
    if (!currentTakingTest || !progressFill) return;
    
    const total = currentTakingTest.questions.length;
    const answered = Object.keys(userAnswers).length;
    const percent = total > 0 ? (answered / total) * 100 : 0;
    
    progressFill.style.width = `${percent}%`;
}

if (finishTestBtn) {
    finishTestBtn.addEventListener('click', async () => {
        if (!currentResultId || !currentTakingTest) return;
        
        if (Object.keys(userAnswers).length < currentTakingTest.questions.length) {
            if (!confirm('Вы ответили не на все вопросы. Всё равно завершить?')) {
                return;
            }
        }
        
        try {
            const response = await fetch(`${RESULTS_API}/finish/${currentResultId}`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (!response.ok) throw new Error('Ошибка завершения теста');
            
            const result = await response.json();
            showTestResult(result);
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    });
}

function showTestResult(result) {
    if (!testTakingMode || !testResultMode || !resultTitle || !resultScore || !resultDetails) return;
    
    testTakingMode.style.display = 'none';
    testResultMode.style.display = 'block';
    
    const scorePercent = Math.round(result.score);
    const scoreClass = scorePercent >= 70 ? 'result-good' : 'result-bad';
    
    resultTitle.textContent = `Результат: ${result.test_title}`;
    resultScore.innerHTML = `
        <div class="${scoreClass}">${scorePercent}%</div>
        <div>Правильных ответов: ${result.correct_answers} из ${result.total_questions}</div>
    `;
    
    let detailsHtml = '<h3>Детали:</h3>';
    if (result.answers && result.answers.length > 0) {
        result.answers.forEach((a, index) => {
            const answerClass = a.is_correct ? 'answer-correct' : 'answer-wrong';
            detailsHtml += `
                <div class="answer-review ${answerClass}">
                    <p><strong>Вопрос ${index + 1}:</strong> ${escapeHtml(a.question_text)}</p>
                    <p>Ваш ответ: ${escapeHtml(a.selected_answer_text || 'Не отвечен')}</p>
                    <p>Правильный ответ: ${escapeHtml(a.correct_answer_text)}</p>
                </div>
            `;
        });
    } else {
        detailsHtml += '<p>Нет данных об ответах</p>';
    }
    
    resultDetails.innerHTML = detailsHtml;
}

// ---------- Возврат к списку ----------
window.goBackToList = function() {
    document.getElementById('testsListMode').style.display = 'block';
    if (testTakingMode) testTakingMode.style.display = 'none';
    if (testResultMode) testResultMode.style.display = 'none';
    loadAvailableTests(1);
};

// Защита от XSS
function escapeHtml(unsafe) {
    if (!unsafe) return unsafe;
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ---------- Инициализация ----------
document.addEventListener('DOMContentLoaded', function() {
    // Ждем загрузки auth.js
    setTimeout(() => {
        loadAvailableTests(1);
    }, 100);
});