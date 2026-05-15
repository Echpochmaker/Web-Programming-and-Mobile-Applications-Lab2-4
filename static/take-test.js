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

// ---------- Форматирование даты ----------
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const moscowDate = new Date(date.getTime() + (3 * 60 * 60 * 1000));
    return moscowDate.toLocaleString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ========== СПИСОК ДОСТУПНЫХ ТЕСТОВ ==========

async function loadAvailableTests(page = 1, search = '') {
    if (!availableTestsList) return;
    
    try {
        // СНАЧАЛА ПРОВЕРЯЕМ АВТОРИЗАЦИЮ
        if (!window.currentUser) {
            availableTestsList.innerHTML = '<p class="empty-list">🔐 Войдите чтобы увидеть доступные тесты</p>';
            return;
        }
        
        availableTestsList.innerHTML = '<div class="loading-spinner">Загрузка...</div>';
        
        let url = `${RESULTS_API}/available?page=${page}&limit=${limit}`;
        if (search) {
            url += `&search=${encodeURIComponent(search)}`;
        }
        
        const response = await fetch(url, { credentials: 'include' });
        
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
                        <span>👤 Автор: ${escapeHtml(test.author_email)}</span>
                        <span>📝 Вопросов: ${test.questions_count}</span>
                    </div>
                    <p>${escapeHtml(test.description || '')}</p>
                    <div class="test-actions">
                        <button class="btn" onclick="startTest('${test.id}')">Начать тест</button>
                    </div>
                </div>
            `;
        });

        // Пагинация
        const totalPages = Math.ceil(data.meta.total / limit);
        if (totalPages > 1) {
            html += '<div class="pagination">';
            if (page > 1) {
                html += `<button class="btn" onclick="loadAvailableTests(${page - 1}, '${search}')">← Предыдущая</button>`;
            }
            html += `<span>Страница ${page} из ${totalPages}</span>`;
            if (page < totalPages) {
                html += `<button class="btn" onclick="loadAvailableTests(${page + 1}, '${search}')">Следующая →</button>`;
            }
            html += '</div>';
        }

        availableTestsList.innerHTML = html;
        currentPage = page;
        
    } catch (error) {
        console.error('Ошибка загрузки тестов:', error);
        availableTestsList.innerHTML = `<p class="error">❌ Ошибка: ${error.message}</p>`;
    }
}

// Поиск с debounce
if (searchFilter) {
    searchFilter.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => loadAvailableTests(1, e.target.value), 300);
    });
}

// ========== ПРОХОЖДЕНИЕ ТЕСТА ==========

window.startTest = async function(testId) {
    console.log('startTest called with ID:', testId);
    
    try {
        if (!window.currentUser) {
            alert('Для прохождения тестов необходимо авторизоваться');
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
        console.log('Test started:', result);
        
        currentResultId = result.id;
        currentTakingTest = result;
        userAnswers = {};
        
        showTestTakingMode(result);
    } catch (error) {
        console.error('Error starting test:', error);
        alert('Ошибка: ' + error.message);
    }
};

function showTestTakingMode(test) {
    console.log('Showing test taking mode');
    
    document.getElementById('testsListMode').style.display = 'none';
    testTakingMode.style.display = 'block';
    testResultMode.style.display = 'none';
    
    takingTestTitle.textContent = `Прохождение: ${test.test_title || 'Тест'}`;
    
    if (!test.questions || test.questions.length === 0) {
        questionsContainer.innerHTML = '<p class="empty-list">В этом тесте пока нет вопросов</p>';
        finishTestBtn.style.display = 'none';
        return;
    }
    
    let html = '';
    test.questions.forEach((q, i) => {
        const savedAnswer = userAnswers[q.id];
        
        html += `
            <div class="question-card">
                <h4>Вопрос ${i + 1}: ${escapeHtml(q.text)}</h4>
        `;
        
        if (q.answers && q.answers.length > 0) {
            html += '<div class="answers-list">';
            q.answers.forEach(a => {
                const checked = savedAnswer === a.id ? 'checked' : '';
                html += `
                    <div class="answer-item">
                        <input type="radio" 
                               name="q_${q.id}" 
                               value="${a.id}" 
                               ${checked}
                               onchange="saveAnswer('${q.id}', '${a.id}')">
                        <span>${escapeHtml(a.text)}</span>
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<p class="empty-list">Нет вариантов ответа</p>';
        }
        
        html += '</div>';
    });
    
    questionsContainer.innerHTML = html;
    finishTestBtn.style.display = 'block';
    
    updateProgress();
}

window.saveAnswer = function(questionId, answerId) {
    console.log('saveAnswer:', questionId, answerId);
    
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
    }).then(response => {
        if (!response.ok) {
            console.error('Ошибка сохранения ответа');
        } else {
            console.log('Ответ сохранен на сервере');
        }
    }).catch(error => {
        console.error('Ошибка сохранения ответа:', error);
    });
};

function updateProgress() {
    if (!currentTakingTest || !progressFill) return;
    
    const total = currentTakingTest.total_questions || currentTakingTest.questions?.length || 0;
    const answered = Object.keys(userAnswers).length;
    const percent = total > 0 ? (answered / total) * 100 : 0;
    
    progressFill.style.width = `${percent}%`;
    progressFill.textContent = `${Math.round(percent)}%`;
}

if (finishTestBtn) {
    finishTestBtn.addEventListener('click', async () => {
        if (!currentResultId) return;
        
        const total = currentTakingTest.total_questions || currentTakingTest.questions?.length || 0;
        const answered = Object.keys(userAnswers).length;
        
        if (answered < total) {
            const confirmFinish = confirm(`Вы ответили на ${answered} из ${total} вопросов. Завершить тест?`);
            if (!confirmFinish) return;
        }
        
        try {
            finishTestBtn.disabled = true;
            finishTestBtn.textContent = 'Завершение...';
            
            const response = await fetch(`${RESULTS_API}/finish/${currentResultId}`, {
                method: 'POST',
                credentials: 'include'
            });
            
            if (!response.ok) throw new Error('Ошибка завершения теста');
            
            const result = await response.json();
            console.log('Test finished:', result);
            
            showTestResult(result);
        } catch (error) {
            console.error('Error finishing test:', error);
            alert('Ошибка: ' + error.message);
            finishTestBtn.disabled = false;
            finishTestBtn.textContent = 'Завершить тест';
        }
    });
}

function showTestResult(result) {
    testTakingMode.style.display = 'none';
    testResultMode.style.display = 'block';
    
    const scorePercent = Math.round(result.score || 0);
    const scoreClass = scorePercent >= 70 ? 'result-good' : 'result-bad';
    
    resultTitle.textContent = `Результат: ${result.test_title}`;
    resultScore.innerHTML = `
        <div class="score-circle ${scoreClass}">
            <span>${scorePercent}%</span>
        </div>
        <div class="score-details">
            <p>✅ Правильных ответов: ${result.correct_answers} из ${result.total_questions}</p>
            <p>📊 Статус: ${scorePercent >= 70 ? 'Пройден' : 'Не пройден'}</p>
        </div>
    `;
    
    let detailsHtml = '<h3>📝 Детали ответов:</h3>';
    
    if (result.answers && result.answers.length > 0) {
        result.answers.forEach((a, i) => {
            const answerClass = a.is_correct ? 'answer-correct' : 'answer-wrong';
            const icon = a.is_correct ? '✅' : '❌';
            
            detailsHtml += `
                <div class="answer-review ${answerClass}">
                    <p><strong>${icon} Вопрос ${i + 1}:</strong> ${escapeHtml(a.question_text)}</p>
                    <p>📌 Ваш ответ: ${escapeHtml(a.selected_answer_text || 'Не отвечен')}</p>
                    <p>✓ Правильный ответ: ${escapeHtml(a.correct_answer_text || '')}</p>
                </div>
            `;
        });
    } else {
        detailsHtml += '<p class="empty-list">Нет данных об ответах</p>';
    }
    
    resultDetails.innerHTML = detailsHtml;
}

window.goBackToList = function() {
    document.getElementById('testsListMode').style.display = 'block';
    testTakingMode.style.display = 'none';
    testResultMode.style.display = 'none';
    
    currentResultId = null;
    currentTakingTest = null;
    userAnswers = {};
    
    if (finishTestBtn) {
        finishTestBtn.disabled = false;
        finishTestBtn.textContent = 'Завершить тест';
    }
    
    loadAvailableTests(currentPage);
};

function escapeHtml(text) {
    if (!text) return text;
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== ИНИЦИАЛИЗАЦИЯ ==========
async function init() {
    console.log('Initializing take-test page');
    
    const availableTestsList = document.getElementById('availableTestsList');
    
    // Ждём авторизацию
    window.addEventListener('auth-change', (e) => {
        console.log('auth-change event:', e.detail);
        if (e.detail.isAuthenticated) {
            loadAvailableTests(1);
        } else {
            if (availableTestsList) {
                availableTestsList.innerHTML = '<p class="empty-list">🔐 Войдите чтобы увидеть доступные тесты</p>';
            }
        }
    });
    
    // Проверяем текущий статус
    if (window.currentUser) {
        loadAvailableTests(1);
    } else {
        // Проверяем через API
        try {
            const response = await fetch('/auth/whoami', { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                window.currentUser = data.user;
                loadAvailableTests(1);
            } else {
                if (availableTestsList) {
                    availableTestsList.innerHTML = '<p class="empty-list">🔐 Войдите чтобы увидеть доступные тесты</p>';
                }
            }
        } catch (error) {
            if (availableTestsList) {
                availableTestsList.innerHTML = '<p class="empty-list">🔐 Войдите чтобы увидеть доступные тесты</p>';
            }
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

window.loadAvailableTests = loadAvailableTests;