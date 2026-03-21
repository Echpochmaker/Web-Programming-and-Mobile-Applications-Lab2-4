// ---------- Глобальные переменные ----------
const API_BASE = '/tests';
let currentPage = 1;
const limit = 5;
let currentTestId = null;
let currentUser = null;

// ВРЕМЕННАЯ ДИАГНОСТИКА
console.log('Script started');
window.onerror = function(message, source, lineno, colno, error) {
    console.log('Ошибка:', message, 'в', source, 'строка', lineno);
};

// Принудительная проверка кук при загрузке
console.log('Текущие cookies:', document.cookie);

// Функция для проверки наличия кук
function checkCookies() {
    if (document.cookie.includes('access_token')) {
        console.log('Cookies найдены');
        return true;
    } else {
        console.log('Cookies не найдены');
        return false;
    }
}

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

// Модальные окна
const loginModal = document.getElementById('loginModal');
const registerModal = document.getElementById('registerModal');
const forgotPasswordModal = document.getElementById('forgotPasswordModal');
const forgotPasswordLink = document.getElementById('forgotPasswordLink');
const forgotPasswordForm = document.getElementById('forgotPasswordForm');
const forgotEmail = document.getElementById('forgotEmail');
const forgotMessage = document.getElementById('forgotMessage');

// ---------- Проверка авторизации (только через cookies) ----------
async function checkAuth() {
    console.log('Проверка авторизации...');
    
    try {
        const response = await fetch('/auth/whoami', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            console.log('✅ Авторизован как:', currentUser.email);
            updateUIForAuth(true);
            return;
        } else {
            console.log('❌ Не авторизован');
        }
    } catch (error) {
        console.error('Ошибка проверки авторизации:', error);
    }
    
    currentUser = null;
    updateUIForAuth(false);
}

// OAuth через Яндекс
window.yandexOAuth = async function() {
    try {
        const response = await fetch('/auth/oauth/yandex');
        const data = await response.json();
        if (data.auth_url) {
            window.location.href = data.auth_url;
        }
    } catch (error) {
        alert('Ошибка инициализации OAuth: ' + error.message);
    }
};

function updateUIForAuth(isAuthenticated) {
    if (isAuthenticated && currentUser) {
        navUser.innerHTML = `
            <div class="user-info">
                <span class="user-email">${escapeHtml(currentUser.email || 'Пользователь')}</span>
                <button class="btn-logout" onclick="logout()">Выйти</button>
                <button class="btn-logout-all" onclick="logoutAll()">Выйти из всех сессий</button>
            </div>
        `;
        if (createTestCard) createTestCard.style.display = 'block';
        if (loginPromptCard) loginPromptCard.style.display = 'none';
    } else {
        navUser.innerHTML = `
        <div class="auth-buttons">
            <button class="btn" onclick="showLoginModal()">Вход</button>
            <button class="btn btn-secondary" onclick="showRegisterModal()">Регистрация</button>
            <button class="btn yandex-btn" onclick="yandexOAuth()">Яндекс ID</button>
        </div>
        `;
        if (createTestCard) createTestCard.style.display = 'none';
        if (loginPromptCard) loginPromptCard.style.display = 'block';
    }
}

// ---------- Авторизация ----------
function showLoginModal() {
    loginModal.style.display = 'block';
}

function showRegisterModal() {
    registerModal.style.display = 'block';
}

// Показать окно восстановления пароля
forgotPasswordLink?.addEventListener('click', (e) => {
    e.preventDefault();
    loginModal.style.display = 'none';
    forgotPasswordModal.style.display = 'block';
    if (forgotMessage) forgotMessage.innerHTML = '';
});

// Отправка запроса на восстановление
forgotPasswordForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = forgotEmail.value.trim();
    
    if (!email) {
        forgotMessage.innerHTML = '<span style="color:red">Введите email</span>';
        return;
    }
    
    forgotMessage.innerHTML = 'Отправка...';
    
    try {
        const response = await fetch('/auth/forgot-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        
        if (response.ok) {
            forgotMessage.innerHTML = '<span style="color:green">✓ Ссылка для сброса пароля отправлена на email</span>';
            setTimeout(() => {
                forgotPasswordModal.style.display = 'none';
                forgotMessage.innerHTML = '';
                forgotEmail.value = '';
            }, 3000);
        } else {
            const error = await response.json();
            forgotMessage.innerHTML = '<span style="color:red">❌ ' + (error.detail || 'Ошибка') + '</span>';
        }
    } catch (error) {
        forgotMessage.innerHTML = '<span style="color:red">❌ Ошибка соединения</span>';
    }
});

// Закрытие модальных окон
document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.addEventListener('click', () => {
        loginModal.style.display = 'none';
        registerModal.style.display = 'none';
        forgotPasswordModal.style.display = 'none';
    });
});

window.addEventListener('click', (e) => {
    if (e.target === loginModal) loginModal.style.display = 'none';
    if (e.target === registerModal) registerModal.style.display = 'none';
    if (e.target === forgotPasswordModal) forgotPasswordModal.style.display = 'none';
});

// Переключение между модальными окнами
document.getElementById('switchToRegister')?.addEventListener('click', (e) => {
    e.preventDefault();
    loginModal.style.display = 'none';
    registerModal.style.display = 'block';
});

document.getElementById('switchToLogin')?.addEventListener('click', (e) => {
    e.preventDefault();
    registerModal.style.display = 'none';
    loginModal.style.display = 'block';
});

// Обработчики для кнопок в блоке "Требуется авторизация"
document.getElementById('showLoginBtn')?.addEventListener('click', () => {
    showLoginModal();
});

document.getElementById('showRegisterBtn')?.addEventListener('click', () => {
    showRegisterModal();
});

// Регистрация
document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('regEmail').value.trim();
    const phone = document.getElementById('regPhone').value.trim() || null;
    const password = document.getElementById('regPassword').value.trim();

    if (!email || !password) {
        alert('Email и пароль обязательны');
        return;
    }

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, phone, password })
        });

        if (response.ok) {
            alert('Регистрация успешна! Теперь можно войти.');
            registerModal.style.display = 'none';
            showLoginModal();
        } else {
            const error = await response.json();
            alert('Ошибка: ' + (error.detail || 'Неизвестная ошибка'));
        }
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
});

// Вход
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const login = document.getElementById('loginInput').value.trim();
    const password = document.getElementById('passwordInput').value.trim();

    if (!login || !password) {
        alert('Логин и пароль обязательны');
        return;
    }

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ login, password }),
            credentials: 'include'
        });

        if (response.ok) {
            loginModal.style.display = 'none';
            await checkAuth();
            loadTests(1);
        } else {
            const error = await response.json();
            alert('Ошибка: ' + (error.detail || 'Неверные данные'));
        }
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
});

// Выход
async function logout() {
    try {
        const response = await fetch('/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            currentUser = null;
            await checkAuth();
            showTestsList();
        } else {
            console.error('Ошибка выхода:', response.status);
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка: ' + error.message);
    }
}

// Выход из всех сессий
async function logoutAll() {
    if (!confirm('Вы уверены, что хотите выйти из всех сессий? Это действие нельзя отменить.')) return;
    
    try {
        const response = await fetch('/auth/logout-all', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            currentUser = null;
            await checkAuth();
            showTestsList();
        } else {
            console.error('Ошибка выхода из всех сессий:', response.status);
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка: ' + error.message);
    }
}

// ---------- Переключение режимов ----------
function showTestsList() {
    testsListMode.style.display = 'block';
    testEditMode.style.display = 'none';
    backToTestsBtn.style.display = 'none';
    loadTests(currentPage);
}

function showTestEdit(testId) {
    testsListMode.style.display = 'none';
    testEditMode.style.display = 'block';
    backToTestsBtn.style.display = 'inline-block';
    currentTestId = testId;
    loadTestForEdit(testId);
}

backToTestsBtn.addEventListener('click', showTestsList);

// ---------- Загрузка списка тестов ----------
async function loadTests(page = 1) {
    try {
        const response = await fetch(`${API_BASE}?page=${page}&limit=${limit}`, {
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Ошибка загрузки');
        const data = await response.json();
        displayTests(data.data, data.meta);
    } catch (error) {
        testsListDiv.innerHTML = `<p class="error">Ошибка: ${error.message}</p>`;
    }
}

function displayTests(tests, meta) {
    if (!tests || tests.length === 0) {
        testsListDiv.innerHTML = '<p class="empty-list">Нет доступных тестов</p>';
        return;
    }

    let html = '';
    tests.forEach(test => {
        const isOwner = currentUser && test.owner_id === currentUser.id;
        
        html += `
            <div class="test-item" data-id="${test.id}">
                <div class="test-info" onclick="showTestEdit(${test.id})" style="cursor: pointer;">
                    <h3>${escapeHtml(test.title)} ${isOwner ? '<span class="owner-badge">(Мой тест)</span>' : ''}</h3>
                    <p>${escapeHtml(test.description || '')}</p>
                </div>
                <div class="test-actions">
                    ${isOwner ? `<button class="btn-delete" onclick="deleteTest(${test.id}); event.stopPropagation();">Удалить</button>` : ''}
                </div>
            </div>
        `;
    });

    // Пагинация
    html += '<div class="pagination">';
    if (meta.page > 1) {
        html += `<button onclick="loadTests(${meta.page - 1})">Предыдущая</button>`;
    }
    html += `<span>Страница ${meta.page} из ${meta.total_pages}</span>`;
    if (meta.page < meta.total_pages) {
        html += `<button onclick="loadTests(${meta.page + 1})">Следующая</button>`;
    }
    html += '</div>';

    testsListDiv.innerHTML = html;
}

// Удаление теста
async function deleteTest(id) {
    if (!confirm('Вы уверены, что хотите удалить тест?')) return;
    
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
}

// Создание теста
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
        
        if (!currentUser || test.owner_id !== currentUser.id) {
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
                    <button class="delete-question-btn" onclick="deleteQuestion(${q.id})">Удалить вопрос</button>
                </div>
                <div class="form-group">
                    <label>Текст вопроса:</label>
                    <input type="text" class="question-text" value="${escapeHtml(q.text)}" data-question-id="${q.id}" onchange="updateQuestionText(${q.id}, this.value)">
                </div>
                <div class="answers-list" data-question-id="${q.id}">
                    ${renderAnswers(q.answers || [], q.id)}
                </div>
                <button class="btn-small add-answer-btn" onclick="addAnswer(${q.id}, ${currentTestId})">+ Добавить ответ</button>
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
                <input type="checkbox" ${a.is_correct ? 'checked' : ''} onchange="toggleCorrect(${a.id}, this.checked, ${questionId})">
                <input type="text" value="${escapeHtml(a.text)}" onchange="updateAnswerText(${a.id}, this.value, ${questionId})">
                <button onclick="deleteAnswer(${a.id}, ${questionId})">Удалить</button>
            </div>
        `;
    });
    return html;
}

// Сохранение изменений теста
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

// Добавить вопрос
addQuestionBtn.addEventListener('click', async () => {
    const text = prompt('Введите текст вопроса:');
    if (!text) return;
    
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

async function deleteQuestion(questionId) {
    if (!confirm('Удалить вопрос?')) return;
    
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
}

// Обновить текст вопроса
async function updateQuestionText(questionId, newText) {
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
}

// Добавить ответ
async function addAnswer(questionId, testId) {
    const text = prompt('Введите текст ответа:');
    if (!text) return;
    const isCorrect = confirm('Это правильный ответ? (OK - да, Отмена - нет)');
    
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
}

// Обновить текст ответа
async function updateAnswerText(answerId, newText, questionId) {
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
}

// Переключить правильность ответа
async function toggleCorrect(answerId, checked, questionId) {
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
}

// Удалить ответ
async function deleteAnswer(answerId, questionId) {
    if (!confirm('Удалить ответ?')) return;
    
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
}

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

// ---------- Инициализация приложения ----------
async function initializeApp() {
    console.log('Инициализация приложения...');
    
    await checkAuth();
    await loadTests(1);
    console.log('Инициализация завершена');
}

initializeApp();

window.logout = logout;
window.logoutAll = logoutAll;
window.showLoginModal = showLoginModal;
window.showRegisterModal = showRegisterModal;