// Базовый URL API
const API_BASE = '/tests';
let currentPage = 1;
const limit = 5;

// Загрузить список тестов
async function loadTests(page = 1) {
    try {
        const response = await fetch(`${API_BASE}?page=${page}&limit=${limit}`);
        if (!response.ok) throw new Error('Ошибка загрузки');
        const data = await response.json();
        displayTests(data.data, data.meta);
    } catch (error) {
        document.getElementById('testsList').innerHTML = `<p class="error">Ошибка: ${error.message}</p>`;
    }
}

// Отобразить тесты
function displayTests(tests, meta) {
    const container = document.getElementById('testsList');
    if (!tests || tests.length === 0) {
        container.innerHTML = '<p class="empty-list">Нет доступных тестов</p>';
        return;
    }

    let html = '';
    tests.forEach(test => {
        html += `
            <div class="test-item" data-id="${test.id}">
                <div class="test-info">
                    <h3>${escapeHtml(test.title)}</h3>
                    <p>${escapeHtml(test.description || '')}</p>
                </div>
                <div class="test-actions">
                    <button class="btn-delete" onclick="deleteTest(${test.id})">Удалить</button>
                </div>
            </div>
        `;
    });

    // Добавляем пагинацию
    html += '<div class="pagination">';
    if (meta.page > 1) {
        html += `<button onclick="loadTests(${meta.page - 1})">Предыдущая</button>`;
    }
    html += `<span>Страница ${meta.page} из ${meta.total_pages}</span>`;
    if (meta.page < meta.total_pages) {
        html += `<button onclick="loadTests(${meta.page + 1})">Следующая</button>`;
    }
    html += '</div>';

    container.innerHTML = html;
}

// Удалить тест
async function deleteTest(id) {
    if (!confirm('Вы уверены, что хотите удалить тест?')) return;
    try {
        const response = await fetch(`${API_BASE}/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Ошибка удаления');
        loadTests(currentPage);
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Создать тест
document.getElementById('createTestForm').addEventListener('submit', async (e) => {
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
            body: JSON.stringify({ title, description })
        });
        if (!response.ok) throw new Error('Ошибка создания');
        document.getElementById('createTestForm').reset();
        loadTests(1); // перезагружаем первую страницу
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
});

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

// Загружаем тесты при старте
loadTests(1);