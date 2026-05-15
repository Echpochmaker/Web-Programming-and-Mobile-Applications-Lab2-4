// ========== СТИЛИЗОВАННЫЕ МОДАЛЬНЫЕ ОКНА ==========

function showModal(options) {
    // Удаляем существующий оверлей, если есть
    const existingOverlay = document.querySelector('.modal-overlay');
    if (existingOverlay) existingOverlay.remove();
    
    const { title, message, inputType = 'text', placeholder = '', confirmText = 'OK', cancelText = 'Отмена', showCancel = true, showCheckbox = false, checkboxLabel = '' } = options;
    
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    // ← ВОТ ЧТО ДОБАВИТЬ: применяем тёмную тему, если она активна
    if (document.body.classList.contains('dark-theme')) {
        overlay.classList.add('dark-theme');
    }
    
    let bodyHtml = '';
    
    if (message) {
        bodyHtml += `<p style="margin-bottom: 15px;">${escapeHtml(message)}</p>`;
    }
    
    if (options.type === 'prompt') {
        bodyHtml += `
            <div class="form-group">
                <label>${escapeHtml(title || 'Введите значение:')}</label>
                <input type="${inputType}" id="modalInput" placeholder="${escapeHtml(placeholder)}" autofocus>
            </div>
        `;
    } else if (options.type === 'confirm') {
        bodyHtml = `<p>${escapeHtml(message || title || 'Подтвердите действие')}</p>`;
    } else if (options.type === 'addAnswer') {
        bodyHtml = `
            <div class="form-group">
                <label>Текст ответа:</label>
                <input type="text" id="modalInput" placeholder="Введите текст ответа" autofocus>
            </div>
            <div class="checkbox-group">
                <input type="checkbox" id="modalCheckbox">
                <label for="modalCheckbox">${escapeHtml(checkboxLabel || 'Это правильный ответ')}</label>
            </div>
        `;
    } else if (options.type === 'addQuestion') {
        bodyHtml = `
            <div class="form-group">
                <label>Текст вопроса:</label>
                <textarea id="modalInput" placeholder="Введите текст вопроса" rows="3"></textarea>
            </div>
        `;
    }
    
    overlay.innerHTML = `
        <div class="modal-window">
            <div class="modal-header">
                <h3>${escapeHtml(title || 'Ввод данных')}</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                ${bodyHtml}
            </div>
            <div class="modal-footer">
                ${showCancel ? `<button class="btn btn-secondary" id="modalCancel">${escapeHtml(cancelText)}</button>` : ''}
                <button class="btn" id="modalConfirm">${escapeHtml(confirmText)}</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    const input = overlay.querySelector('#modalInput');
    const checkbox = overlay.querySelector('#modalCheckbox');
    
    return new Promise((resolve) => {
        const closeModal = (result) => {
            overlay.remove();
            resolve(result);
        };
        
        overlay.querySelector('.modal-close').onclick = () => closeModal(null);
        if (showCancel) overlay.querySelector('#modalCancel').onclick = () => closeModal(null);
        overlay.querySelector('#modalConfirm').onclick = () => {
            if (options.type === 'prompt') {
                closeModal(input ? input.value : null);
            } else if (options.type === 'addAnswer') {
                closeModal({
                    text: input ? input.value : '',
                    isCorrect: checkbox ? checkbox.checked : false
                });
            } else if (options.type === 'addQuestion') {
                closeModal(input ? input.value : null);
            } else if (options.type === 'confirm') {
                closeModal(true);
            } else {
                closeModal(true);
            }
        };
        
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    overlay.querySelector('#modalConfirm').click();
                }
            });
            input.focus();
        }
        
        // Закрытие по клику на оверлей
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeModal(null);
            }
        });
    });
}

// Переопределяем стандартные функции для работы с модальными окнами
window.showPrompt = async function(title, placeholder = '') {
    const result = await showModal({
        type: 'prompt',
        title: title,
        placeholder: placeholder,
        confirmText: 'OK',
        cancelText: 'Отмена'
    });
    return result;
};

window.showConfirm = async function(message) {
    const result = await showModal({
        type: 'confirm',
        title: 'Подтверждение',
        message: message,
        confirmText: 'Да',
        cancelText: 'Нет'
    });
    return result === true;
};

window.showAddAnswerModal = async function() {
    const result = await showModal({
        type: 'addAnswer',
        title: 'Добавить ответ',
        confirmText: 'Добавить',
        cancelText: 'Отмена',
        checkboxLabel: 'Это правильный ответ'
    });
    return result;
};

window.showAddQuestionModal = async function() {
    const result = await showModal({
        type: 'addQuestion',
        title: 'Добавить вопрос',
        confirmText: 'Добавить',
        cancelText: 'Отмена',
        placeholder: 'Введите текст вопроса'
    });
    return result;
};