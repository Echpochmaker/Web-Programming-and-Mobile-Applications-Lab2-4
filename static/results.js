// ---------- Глобальные переменные ----------
const RESULTS_API = '/results';
let currentPage = 1;
const limit = 10;

// Убеждаемся, что window.currentUser доступен
if (typeof window.currentUser === 'undefined') {
    window.currentUser = null;
}

// ---------- Проверка авторизации ----------
async function checkAuthAndLoad() {
    console.log('Checking auth for results page...');
    
    try {
        const response = await fetch('/auth/whoami', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            window.currentUser = data.user;
            console.log('✅ User authenticated:', window.currentUser);
            await loadResults(1);
        } else {
            console.log('❌ Not authenticated');
            showUnauthorizedMessage();
        }
    } catch (error) {
        console.error('Auth check error:', error);
        showUnauthorizedMessage();
    }
}

function showUnauthorizedMessage() {
    const resultsList = document.getElementById('resultsList');
    if (resultsList) {
        resultsList.innerHTML = `
            <div class="empty-state">
                <p>🔐 Войдите чтобы увидеть свои результаты</p>
            </div>
        `;
    }
}

// ---------- Вспомогательная функция для форматирования даты ----------
function formatDate(dateString) {
    if (!dateString) return 'Не завершён';
    
    const date = new Date(dateString);
    // Добавляем 3 часа для Московского времени (UTC+3)
    const moscowDate = new Date(date.getTime() + (3 * 60 * 60 * 1000));
    
    return moscowDate.toLocaleString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ---------- Загрузка результатов ----------
async function loadResults(page = 1) {
    const resultsList = document.getElementById('resultsList');
    if (!resultsList) return;
    
    try {
        resultsList.innerHTML = '<div class="loading-spinner">Загрузка результатов...</div>';
        
        const response = await fetch(`${RESULTS_API}/?page=${page}&limit=${limit}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                resultsList.innerHTML = `
                    <div class="empty-state">
                        <p>🔐 Войдите чтобы увидеть свои результаты</p>
                    </div>
                `;
                return;
            }
            throw new Error('Ошибка загрузки');
        }
        
        const data = await response.json();
        console.log('Получены результаты:', data);
        
        if (!data.data || data.data.length === 0) {
            resultsList.innerHTML = `
                <div class="empty-state">
                    <p>📭 Вы ещё не проходили тесты</p>
                    <a href="/take-test" class="btn">Пройти тест</a>
                </div>
            `;
            return;
        }

        let html = '';
        data.data.forEach(result => {
            const date = formatDate(result.completed_at);
            const scorePercent = Math.round(result.score || 0);
            const scoreClass = scorePercent >= 70 ? 'result-good' : 'result-bad';
            
            html += `
            <div class="result-card" data-result-id="${result.id}">
                <div class="result-header">
                    <div>
                        <h3>${escapeHtml(result.test_title)}</h3>
                        <div class="result-author">👤 Автор: ${escapeHtml(result.author_email || 'Неизвестен')}</div>
                    </div>
                    <div class="result-score ${scoreClass}">${scorePercent}%</div>
                </div>
                <div class="result-stats">
                    <div class="stat-item">
                        <span class="stat-icon">✅</span>
                        <span class="stat-label">Правильно:</span>
                        <span class="stat-value">${result.correct_answers}/${result.total_questions}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-icon">📅</span>
                        <span class="stat-label">Дата:</span>
                        <span class="stat-value">${date}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-icon">📊</span>
                        <span class="stat-label">Статус:</span>
                        <span class="stat-value ${scoreClass}">${scorePercent >= 70 ? 'Пройден' : 'Не сдан'}</span>
                    </div>
                </div>
                <div class="result-actions">
                    <button class="btn btn-secondary" onclick="viewResultDetail('${result.id}')">Подробнее</button>
                </div>
            </div>
        `;
        });

        // Пагинация
        const totalPages = Math.ceil(data.meta.total / limit);
        if (totalPages > 1) {
            html += '<div class="pagination">';
            if (page > 1) {
                html += `<button onclick="loadResults(${page - 1})">◀ Предыдущая</button>`;
            }
            html += `<span>Страница ${page} из ${totalPages}</span>`;
            if (page < totalPages) {
                html += `<button onclick="loadResults(${page + 1})">Следующая ▶</button>`;
            }
            html += '</div>';
        }

        resultsList.innerHTML = html;
        
    } catch (error) {
        console.error('Ошибка загрузки результатов:', error);
        resultsList.innerHTML = `<p class="error">❌ Ошибка: ${error.message}</p>`;
    }
}
// ---------- Просмотр деталей результата ----------
async function viewResultDetail(resultId) {
    try {
        const response = await fetch(`${RESULTS_API}/${resultId}`, {
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error('Ошибка загрузки деталей');
        
        const result = await response.json();
        console.log('Детали результата:', result);
        
        showResultModal(result);
        
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

function showResultModal(result) {
    const scorePercent = Math.round(result.score || 0);
    const scoreClass = scorePercent >= 70 ? 'result-good' : 'result-bad';
    const date = formatDate(result.completed_at);
    
    let modalHtml = `
        <div id="resultModal" class="modal" style="display: flex; align-items: center; justify-content: center;">
            <div class="modal-content" style="max-width: 700px; max-height: 85vh; overflow-y: auto; margin: 20px;">
                <span class="close" style="position: sticky; top: 0; float: right; cursor: pointer; font-size: 24px;">&times;</span>
                <h2>📊 Результат теста</h2>
                <div style="text-align: center; margin-bottom: 20px;">
                    <h3>${escapeHtml(result.test_title)}</h3>
                    <div class="result-author">👤 Автор: ${escapeHtml(result.author_email || 'Неизвестен')}</div>
                </div>
                
                <div class="result-summary" style="text-align: center; margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 12px;">
                    <div class="score-circle ${scoreClass}" style="width: 120px; height: 120px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; border: 4px solid; margin: 0 auto 15px;">
                        <span style="font-size: 32px; font-weight: bold;">${scorePercent}%</span>
                    </div>
                    <div class="score-details">
                        <p><strong>✅ Правильных ответов:</strong> ${result.correct_answers} из ${result.total_questions}</p>
                        <p><strong>📅 Дата прохождения:</strong> ${date}</p>
                        <p><strong>📈 Статус:</strong> <span class="${scoreClass}">${scorePercent >= 70 ? 'Успешно сдан' : 'Не сдан'}</span></p>
                    </div>
                </div>
                
                <h3>📝 Детали по вопросам:</h3>
                <div class="answers-details">
    `;
    
    if (result.answers && result.answers.length > 0) {
        result.answers.forEach((answer, index) => {
            const answerClass = answer.is_correct ? 'answer-correct' : 'answer-wrong';
            const correctMark = answer.is_correct ? '✅' : '❌';
            
            modalHtml += `
                <div class="answer-review ${answerClass}" style="padding: 15px; margin: 12px 0; border-radius: 10px; border-left: 4px solid;">
                    <div style="font-weight: bold; margin-bottom: 10px; font-size: 16px;">
                        ${correctMark} Вопрос ${index + 1}: ${escapeHtml(answer.question_text)}
                    </div>
                    <div style="margin-left: 20px;">
                        <div style="margin: 5px 0;">
                            <span style="color: #666;">📌 Ваш ответ:</span>
                            <span style="font-weight: 500;">${escapeHtml(answer.selected_answer_text || 'Не отвечен')}</span>
                        </div>
                        <div style="margin: 5px 0;">
                            <span style="color: #4CAF50;">✅ Правильный ответ:</span>
                            <span style="font-weight: 500;">${escapeHtml(answer.correct_answer_text || '')}</span>
                        </div>
                    </div>
                </div>
            `;
        });
    } else {
        modalHtml += '<p>Нет данных об ответах</p>';
    }
    
    modalHtml += `
                </div>
                <div style="text-align: center; margin-top: 20px; padding: 10px;">
                    <button class="btn" onclick="closeResultModal()">Закрыть</button>
                </div>
            </div>
        </div>
    `;
    
    // Удаляем старый модал если есть
    const oldModal = document.getElementById('resultModal');
    if (oldModal) oldModal.remove();

    // Добавляем новый
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Получаем новый модал
    const modal = document.getElementById('resultModal');
    
    // Применяем тёмную тему, если она активна
    if (document.body.classList.contains('dark-theme')) {
        modal.classList.add('dark-theme');
    }
    
    // Добавляем обработчик для крестика
    const closeBtn = modal.querySelector('.close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeResultModal);
    }
    
    // Закрытие по клику на фон
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeResultModal();
        }
    });
}

function closeResultModal() {
    const modal = document.getElementById('resultModal');
    if (modal) modal.style.display = 'none';
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

// ---------- Инициализация ----------
async function init() {
    console.log('Results page initialized');
    
    const resultsList = document.getElementById('resultsList');
    
    // Ждём авторизацию
    window.addEventListener('auth-change', (e) => {
        console.log('auth-change event received', e.detail);
        if (e.detail.isAuthenticated) {
            loadResults(1);
        } else {
            if (resultsList) {
                resultsList.innerHTML = `
                    <div class="empty-state">
                        <p>🔐 Войдите чтобы увидеть свои результаты</p>
                    </div>
                `;
            }
        }
    });
    
    // Проверяем текущий статус
    if (window.currentUser) {
        loadResults(1);
    } else {
        // Проверяем через API
        try {
            const response = await fetch('/auth/whoami', { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                window.currentUser = data.user;
                loadResults(1);
            } else {
                if (resultsList) {
                    resultsList.innerHTML = `
                        <div class="empty-state">
                            <p>🔐 Войдите чтобы увидеть свои результаты</p>
                        </div>
                    `;
                }
            }
        } catch (error) {
            if (resultsList) {
                resultsList.innerHTML = `
                    <div class="empty-state">
                        <p>🔐 Войдите чтобы увидеть свои результаты</p>
                    </div>
                `;
            }
        }
    }
    
    // Закрытие по клику вне окна
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('resultModal');
        if (e.target === modal) {
            closeResultModal();
        }
    });
}

// Запуск после загрузки страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Экспорт функций
window.viewResultDetail = viewResultDetail;
window.closeResultModal = closeResultModal;
window.loadResults = loadResults;