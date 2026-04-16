// ---------- Глобальные переменные ----------
const API_BASE = '/tests';
let currentPage = 1;
const limit = 5;
let currentTestId = null;

console.log('Script started');
console.log('Текущие cookies:', document.cookie);

// ---------- Элементы DOM ----------
const testsListMode = document.getElementById('testsListMode');
const testEditMode = document.getElementById('testEditMode');
const backToTestsBtn = document.getElementById('backToTestsBtn');
const testsListDiv = document.getElementById('testsList');
const createTestForm = document.getElementById('createTestForm');
const editTestForm = document.getElementById('editTestForm');
const editTitle = document.getElementById('editTitle');
const editDescription = document.getElementById('editDescription');
const editTestTitle = document.getElementById('editTestTitle');
const questionsContainer = document.getElementById('questionsContainer');
const addQuestionBtn = document.getElementById('addQuestionBtn');

// Элементы авторизации
const navUser = document.getElementById('navUser');
const createTestCard = document.getElementById('createTestCard');
const loginPromptCard = document.getElementById('loginPromptCard');

// ---------- Функция обновления UI ----------
function refreshUI() {
    console.log('refreshUI, window.currentUser =', window.currentUser);
    
    if (window.currentUser) {
        // Пользователь авторизован
        if (createTestCard) createTestCard.style.display = 'block';
        if (loginPromptCard) loginPromptCard.style.display = 'none';
        
        // Загружаем тесты
        loadTests(1);
    } else {
        // Пользователь не авторизован
        if (createTestCard) createTestCard.style.display = 'none';
        if (loginPromptCard) loginPromptCard.style.display = 'block';
        
        // Показываем сообщение в списке тестов
        if (testsListDiv) {
            testsListDiv.innerHTML = '<p class="empty-list">Войдите чтобы увидеть тесты</p>';
        }
    }
}

// ---------- Слушаем событие авторизации ----------
window.addEventListener('auth-change', function(event) {
    console.log('auth-change event received', event.detail);
    refreshUI();
});

// ---------- Переключение режимов ----------
function showTestsList() {
    if (testsListMode) testsListMode.style.display = 'block';
    if (testEditMode) testEditMode.style.display = 'none';
    if (backToTestsBtn) backToTestsBtn.style.display = 'none';
    currentTestId = null;
    loadTests(currentPage);
}

function showTestEdit(testId) {
    if (testsListMode) testsListMode.style.display = 'none';
    if (testEditMode) testEditMode.style.display = 'block';
    if (backToTestsBtn) backToTestsBtn.style.display = 'inline-block';
    currentTestId = testId;
    loadTestForEdit(testId);
}

if (backToTestsBtn) {
    backToTestsBtn.addEventListener('click', showTestsList);
}

// ---------- Загрузка списка тестов ----------
async function loadTests(page = 1) {
    console.log('loadTests вызван, page:', page);
    
    try {
        if (!testsListDiv) {
            console.error('testsListDiv не найден');
            return;
        }
        
        // Если пользователь не авторизован, показываем сообщение
        if (!window.currentUser) {
            testsListDiv.innerHTML = '<p class="empty-list">Войдите чтобы увидеть тесты</p>';
            return;
        }
        
        testsListDiv.innerHTML = '<p>Загрузка...</p>';
        
        const response = await fetch(`${API_BASE}?page=${page}&limit=${limit}`, {
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error('Ошибка загрузки');
        
        const data = await response.json();
        console.log('Получены тесты:', data);
        
        displayTests(data.data, data.meta, page);
        currentPage = page;
    } catch (error) {
        console.error('Ошибка загрузки тестов:', error);
        if (testsListDiv) {
            testsListDiv.innerHTML = `<p class="error">Ошибка: ${error.message}</p>`;
        }
    }
}

function displayTests(tests, meta, currentPageNum) {
    if (!testsListDiv) return;
    
    if (!tests || tests.length === 0) {
        testsListDiv.innerHTML = '<p class="empty-list">Нет доступных тестов</p>';
        return;
    }

    // Фильтруем только тесты текущего пользователя
    const myTests = tests.filter(test => window.currentUser && test.owner_id === window.currentUser.id);
    
    if (myTests.length === 0) {
        testsListDiv.innerHTML = '<p class="empty-list">У вас пока нет созданных тестов</p>';
        return;
    }

    let html = '';
    myTests.forEach(test => {
        html += `
            <div class="test-item" data-id="${test.id}">
                <div class="test-info" onclick="showTestEdit('${test.id}')" style="cursor: pointer;">
                    <h3>${escapeHtml(test.title)}</h3>
                    <p>${escapeHtml(test.description || '')}</p>
                </div>
                <div class="test-actions">
                    <button class="btn-delete" onclick="deleteTest('${test.id}'); event.stopPropagation();">Удалить</button>
                </div>
            </div>
        `;
    });

    // Пагинация
    const totalPages = Math.ceil(meta.total / limit);
    if (totalPages > 1) {
        html += '<div class="pagination">';
        if (currentPageNum > 1) {
            html += `<button onclick="loadTests(${currentPageNum - 1})">Предыдущая</button>`;
        }
        html += `<span>Страница ${currentPageNum} из ${totalPages}</span>`;
        if (currentPageNum < totalPages) {
            html += `<button onclick="loadTests(${currentPageNum + 1})">Следующая</button>`;
        }
        html += '</div>';
    }

    testsListDiv.innerHTML = html;
}

// Удаление теста
window.deleteTest = async function(id) {
    const confirmed = await window.showConfirm('Вы уверены, что хотите удалить этот тест?');
    if (!confirmed) return;
    
    try {
        const response = await fetch(`${API_BASE}/${id}`, { 
            method: 'DELETE',
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Ошибка удаления');
        loadTests(currentPage);
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
};

// Создание теста
if (createTestForm) {
    createTestForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = document.getElementById('title').value.trim();
        const description = document.getElementById('description').value.trim();
        if (!title) {
            alert('Название теста обязательно');
            return;
        }
        
        try {
            const response = await fetch(API_BASE, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, description }),
                credentials: 'include'
            });
            if (!response.ok) throw new Error('Ошибка создания');
            createTestForm.reset();
            loadTests(1);
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    });
}

// ---------- Работа с конкретным тестом ----------
async function loadTestForEdit(testId) {
    console.log('Загрузка свежих данных теста ID:', testId);
    
    try {
        const response = await fetch(`${API_BASE}/${testId}`, {
            method: 'GET',
            headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' },
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error('Тест не найден');
        
        const test = await response.json();
        console.log('Получены свежие данные:', test);
        
        if (!window.currentUser || test.owner_id !== window.currentUser.id) {
            alert('У вас нет прав для редактирования этого теста');
            showTestsList();
            return;
        }
        
        editTitle.value = test.title;
        editDescription.value = test.description || '';
        editTestTitle.textContent = `Редактирование: ${test.title}`;
        
        renderQuestions(test.questions || []);
    } catch (error) {
        alert('Ошибка загрузки теста: ' + error.message);
        showTestsList();
    }
}

function renderQuestions(questions) {
    if (!questionsContainer) return;
    
    if (!questions.length) {
        questionsContainer.innerHTML = '<p class="empty-list">В этом тесте пока нет вопросов.</p>';
        return;
    }
    let html = '';
    questions.forEach((q, qIndex) => {
        html += `
            <div class="question-card" data-question-id="${q.id}">
                <div class="question-header">
                    <h4>Вопрос ${qIndex + 1}</h4>
                    <button class="delete-question-btn" onclick="deleteQuestion('${q.id}')">Удалить вопрос</button>
                </div>
                <div class="form-group">
                    <label>Текст вопроса:</label>
                    <input type="text" class="question-text" value="${escapeHtml(q.text)}" data-question-id="${q.id}" onchange="updateQuestionText('${q.id}', this.value)">
                </div>
                <div class="answers-list" data-question-id="${q.id}">
                    ${renderAnswers(q.answers || [], q.id)}
                </div>
                <button class="btn-small add-answer-btn" onclick="addAnswer('${q.id}', '${currentTestId}')">+ Добавить ответ</button>
            </div>
        `;
    });
    questionsContainer.innerHTML = html;
}

function renderAnswers(answers, questionId) {
    if (!answers.length) return '<p class="empty-list">Нет вариантов ответа.</p>';
    let html = '';
    answers.forEach(a => {
        html += `
            <div class="answer-item" data-answer-id="${a.id}">
                <input type="checkbox" ${a.is_correct ? 'checked' : ''} onchange="toggleCorrect('${a.id}', this.checked, '${questionId}')">
                <input type="text" value="${escapeHtml(a.text)}" onchange="updateAnswerText('${a.id}', this.value, '${questionId}')">
                <button onclick="deleteAnswer('${a.id}', '${questionId}')">Удалить</button>
            </div>
        `;
    });
    return html;
}

// Сохранение изменений теста
if (editTestForm) {
    editTestForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = editTitle.value.trim();
        const description = editDescription.value.trim();
        if (!title) {
            alert('Название теста обязательно');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/${currentTestId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, description }),
                credentials: 'include'
            });
            if (!response.ok) throw new Error('Ошибка обновления');
            editTestTitle.textContent = `Редактирование: ${title}`;
            alert('Тест обновлён');
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    });
}

// Добавить вопрос
if (addQuestionBtn) {
    addQuestionBtn.addEventListener('click', async () => {
        const result = await window.showAddQuestionModal();
        if (!result) return;
        const text = result;
        
        try {
            console.log('Отправляем вопрос:', { text, answers: [] });
            const response = await fetch(`${API_BASE}/${currentTestId}/questions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, answers: [] }),
                credentials: 'include'
            });
            if (!response.ok) {
                const errorData = await response.text();
                console.error('Ошибка сервера:', errorData);
                throw new Error('Ошибка создания вопроса');
            }
            await loadTestForEdit(currentTestId);
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    });
}

// Удаление вопроса
window.deleteQuestion = async function(questionId) {
    const confirmed = await window.showConfirm('Вы уверены, что хотите удалить этот вопрос?');
    if (!confirmed) return;
    
    try {
        console.log('Удаляем вопрос ID:', questionId, 'из теста ID:', currentTestId);
        
        const response = await fetch(`${API_BASE}/${currentTestId}/questions/${questionId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        console.log('Статус ответа:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Ошибка удаления:', errorText);
            throw new Error('Ошибка удаления');
        }
        
        await loadTestForEdit(currentTestId);
        
    } catch (error) {
        console.error('Ошибка в deleteQuestion:', error);
        alert('Ошибка: ' + error.message);
    }
};

window.updateQuestionText = async function(questionId, newText) {
    if (!newText.trim()) return;
    
    try {
        const questionRes = await fetch(`${API_BASE}/${currentTestId}/questions/${questionId}`, {
            credentials: 'include'
        });
        if (!questionRes.ok) throw new Error('Не удалось получить данные вопроса');
        const question = await questionRes.json();
        question.text = newText;
        const response = await fetch(`${API_BASE}/${currentTestId}/questions/${questionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(question),
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Ошибка обновления вопроса');
    } catch (error) {
        alert('Ошибка при обновлении вопроса: ' + error.message);
    }
};

// Добавление ответа
window.addAnswer = async function(questionId, testId) {
    const result = await window.showAddAnswerModal();
    if (!result || !result.text) return;
    const text = result.text;
    const isCorrect = result.isCorrect;
    
    try {
        const response = await fetch(`/questions/${questionId}/answers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, is_correct: isCorrect }),
            credentials: 'include'
        });
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Ошибка ответа:', response.status, errorText);
            throw new Error('Ошибка создания ответа');
        }
        await loadTestForEdit(testId);
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
};

window.updateAnswerText = async function(answerId, newText, questionId) {
    if (!newText.trim()) return;
    
    try {
        const answerRes = await fetch(`/questions/${questionId}/answers`, {
            credentials: 'include'
        });
        if (!answerRes.ok) throw new Error('Не удалось получить ответы');
        const answers = await answerRes.json();
        const answer = answers.find(a => a.id === answerId);
        if (!answer) throw new Error('Ответ не найден');
        const response = await fetch(`/questions/${questionId}/answers/${answerId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: newText, is_correct: answer.is_correct }),
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Ошибка обновления ответа');
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
};

window.toggleCorrect = async function(answerId, checked, questionId) {
    try {
        const answerRes = await fetch(`/questions/${questionId}/answers`, {
            credentials: 'include'
        });
        if (!answerRes.ok) throw new Error('Не удалось получить ответы');
        const answers = await answerRes.json();
        const answer = answers.find(a => a.id === answerId);
        if (!answer) throw new Error('Ответ не найден');
        const response = await fetch(`/questions/${questionId}/answers/${answerId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: answer.text, is_correct: checked }),
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Ошибка обновления ответа');
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
};

// Удаление ответа
window.deleteAnswer = async function(answerId, questionId) {
    const confirmed = await window.showConfirm('Вы уверены, что хотите удалить этот ответ?');
    if (!confirmed) return;
    
    try {
        const response = await fetch(`/questions/${questionId}/answers/${answerId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Ошибка удаления');
        await loadTestForEdit(currentTestId);
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
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
function initialize() {
    console.log('Инициализация script.js...');
    
    // Если пользователь уже авторизован, обновляем UI
    if (window.currentUser) {
        refreshUI();
    } else {
        // Ждем событие авторизации
        window.addEventListener('auth-change', function(event) {
            if (event.detail.isAuthenticated) {
                refreshUI();
            }
        });
    }
}

// Запускаем после загрузки DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}

// Экспортируем функции
window.showTestEdit = showTestEdit;
window.deleteTest = deleteTest;
window.deleteQuestion = deleteQuestion;
window.updateQuestionText = updateQuestionText;
window.addAnswer = addAnswer;
window.updateAnswerText = updateAnswerText;
window.toggleCorrect = toggleCorrect;
window.deleteAnswer = deleteAnswer;
window.loadTests = loadTests;