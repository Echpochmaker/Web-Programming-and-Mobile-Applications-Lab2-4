// ---------- Общие функции авторизации ----------
let currentUser = null;

console.log('Auth script loaded');
console.log('Текущие cookies:', document.cookie);

// ---------- Управление тёмной темой ----------
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
    syncThemeToggle();
}

function toggleTheme() {
    if (document.body.classList.contains('dark-theme')) {
        document.body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
    } else {
        document.body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
    }
    syncThemeToggle();
}

function syncThemeToggle() {
    const themeCheckbox = document.getElementById('themeToggleCheckbox');
    if (themeCheckbox) {
        const isDark = document.body.classList.contains('dark-theme');
        themeCheckbox.checked = isDark;
    }
}

// ---------- Виджет-меню (полностью отдельный) ----------
function createWidgetMenu() {
    console.log('createWidgetMenu вызван');
    
    // Ищем отдельный контейнер для виджета
    const widgetContainer = document.getElementById('widgetContainer');
    if (!widgetContainer) {
        console.error('#widgetContainer не найден!');
        return;
    }
    
    // Очищаем контейнер (на случай повторного вызова)
    widgetContainer.innerHTML = '';
    
    // Кнопка виджета
    const widgetBtn = document.createElement('button');
    widgetBtn.className = 'widget-btn';
    widgetBtn.innerHTML = '👤';
    widgetBtn.setAttribute('aria-label', 'Меню');
    
    // Выпадающее меню
    const dropdown = document.createElement('div');
    dropdown.className = 'widget-dropdown';
    
    dropdown.innerHTML = `
        <a href="#" class="dropdown-item" id="profile-item">
            <span class="dropdown-icon">👤</span>
            <span class="dropdown-text">Профиль</span>
        </a>
        <a href="#" class="dropdown-item" id="settings-item">
            <span class="dropdown-icon">⚙️</span>
            <span class="dropdown-text">Настройки</span>
        </a>
        <div class="dropdown-divider"></div>
        <div class="dropdown-item" id="theme-item">
            <span class="dropdown-icon">🌓</span>
            <span class="dropdown-text">Тёмная тема</span>
            <label class="theme-switch">
                <input type="checkbox" id="themeToggleCheckbox">
                <span class="theme-switch-slider"></span>
            </label>
        </div>
    `;
    
    widgetContainer.appendChild(widgetBtn);
    widgetContainer.appendChild(dropdown);
    
    // Обработчики
    widgetBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
    });
    
    // Закрытие при клике вне меню
    document.addEventListener('click', (e) => {
        if (!widgetContainer.contains(e.target)) {
            dropdown.classList.remove('show');
        }
    });
    
    // Профиль (пока заглушка)
    const profileItem = document.getElementById('profile-item');
    if (profileItem) {
        profileItem.addEventListener('click', (e) => {
            e.preventDefault();
            alert('Профиль — в разработке');
            dropdown.classList.remove('show');
        });
    }
    
    // Настройки (пока заглушка)
    const settingsItem = document.getElementById('settings-item');
    if (settingsItem) {
        settingsItem.addEventListener('click', (e) => {
            e.preventDefault();
            alert('Настройки — в разработке');
            dropdown.classList.remove('show');
        });
    }
    
    // Переключатель темы
    const themeCheckbox = document.getElementById('themeToggleCheckbox');
    if (themeCheckbox) {
        const isDark = document.body.classList.contains('dark-theme');
        themeCheckbox.checked = isDark;
        
        themeCheckbox.addEventListener('change', () => {
            toggleTheme();
        });
    }
    
    console.log('Виджет-меню создан успешно');
}

// ---------- Проверка авторизации ----------
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
            
            window.currentUser = currentUser;
            
            window.dispatchEvent(new CustomEvent('auth-change', { 
                detail: { isAuthenticated: true, user: currentUser } 
            }));
            
            updateNavUI(true);
            return true;
        } else {
            console.log('❌ Не авторизован');
        }
    } catch (error) {
        console.error('Ошибка проверки авторизации:', error);
    }
    
    currentUser = null;
    window.currentUser = null;
    
    window.dispatchEvent(new CustomEvent('auth-change', { 
        detail: { isAuthenticated: false, user: null } 
    }));
    
    updateNavUI(false);
    return false;
}

// Обновление навигационной панели (только блок авторизации)
function updateNavUI(isAuthenticated) {
    const navUser = document.getElementById('navUser');
    if (!navUser) return;
    
    if (isAuthenticated && currentUser) {
        navUser.innerHTML = `
            <div class="user-info">
                <span class="user-email">${escapeHtml(currentUser.email || 'Пользователь')}</span>
                <button class="btn-logout" onclick="logout()">Выйти</button>
                <button class="btn-logout-all" onclick="logoutAll()">Выйти из всех сессий</button>
            </div>
        `;
    } else {
        navUser.innerHTML = `
            <div class="auth-buttons">
                <button class="btn" onclick="showLoginModal()">Вход</button>
                <button class="btn btn-secondary" onclick="showRegisterModal()">Регистрация</button>
                <button class="btn yandex-btn" onclick="yandexOAuth()">Яндекс ID</button>
            </div>
        `;
    }
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

// ---------- Модальные окна ----------
window.showLoginModal = function() {
    const modal = document.getElementById('loginModal');
    if (modal) modal.style.display = 'block';
};

window.showRegisterModal = function() {
    const modal = document.getElementById('registerModal');
    if (modal) modal.style.display = 'block';
};

// Закрытие модальных окон
document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.addEventListener('click', () => {
        const loginModal = document.getElementById('loginModal');
        const registerModal = document.getElementById('registerModal');
        const forgotModal = document.getElementById('forgotPasswordModal');
        if (loginModal) loginModal.style.display = 'none';
        if (registerModal) registerModal.style.display = 'none';
        if (forgotModal) forgotModal.style.display = 'none';
    });
});

window.addEventListener('click', (e) => {
    if (e.target === document.getElementById('loginModal')) {
        document.getElementById('loginModal').style.display = 'none';
    }
    if (e.target === document.getElementById('registerModal')) {
        document.getElementById('registerModal').style.display = 'none';
    }
    if (e.target === document.getElementById('forgotPasswordModal')) {
        document.getElementById('forgotPasswordModal').style.display = 'none';
    }
});

// Переключение между модальными окнами
const switchToRegister = document.getElementById('switchToRegister');
if (switchToRegister) {
    switchToRegister.addEventListener('click', (e) => {
        e.preventDefault();
        const loginModal = document.getElementById('loginModal');
        const registerModal = document.getElementById('registerModal');
        if (loginModal) loginModal.style.display = 'none';
        if (registerModal) registerModal.style.display = 'block';
    });
}

const switchToLogin = document.getElementById('switchToLogin');
if (switchToLogin) {
    switchToLogin.addEventListener('click', (e) => {
        e.preventDefault();
        const loginModal = document.getElementById('loginModal');
        const registerModal = document.getElementById('registerModal');
        if (registerModal) registerModal.style.display = 'none';
        if (loginModal) loginModal.style.display = 'block';
    });
}

// Вход
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
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
                const loginModal = document.getElementById('loginModal');
                if (loginModal) loginModal.style.display = 'none';
                
                await checkAuth();
                window.location.reload();
            } else {
                const error = await response.json();
                alert('Ошибка: ' + (error.detail || 'Неверные данные'));
            }
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    });
}

// Регистрация
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
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
                const registerModal = document.getElementById('registerModal');
                if (registerModal) registerModal.style.display = 'none';
                showLoginModal();
            } else {
                const error = await response.json();
                alert('Ошибка: ' + (error.detail || 'Неизвестная ошибка'));
            }
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    });
}

// Выход
window.logout = async function() {
    try {
        const response = await fetch('/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            currentUser = null;
            window.currentUser = null;
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка: ' + error.message);
    }
};

window.logoutAll = async function() {
    if (!confirm('Вы уверены, что хотите выйти из всех сессий?')) return;
    
    try {
        const response = await fetch('/auth/logout-all', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            currentUser = null;
            window.currentUser = null;
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка: ' + error.message);
    }
};

// Забыли пароль
const forgotPasswordLink = document.getElementById('forgotPasswordLink');
if (forgotPasswordLink) {
    forgotPasswordLink.addEventListener('click', (e) => {
        e.preventDefault();
        const loginModal = document.getElementById('loginModal');
        const forgotModal = document.getElementById('forgotPasswordModal');
        if (loginModal) loginModal.style.display = 'none';
        if (forgotModal) forgotModal.style.display = 'block';
    });
}

const forgotPasswordForm = document.getElementById('forgotPasswordForm');
if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('forgotEmail').value.trim();
        const messageDiv = document.getElementById('forgotMessage');
        
        if (!email) {
            if (messageDiv) messageDiv.innerHTML = '<span style="color:red">Введите email</span>';
            return;
        }
        
        if (messageDiv) messageDiv.innerHTML = 'Отправка...';
        
        try {
            const response = await fetch('/auth/forgot-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            
            if (response.ok) {
                if (messageDiv) {
                    messageDiv.innerHTML = '<span style="color:green">✓ Ссылка для сброса пароля отправлена на email</span>';
                }
                setTimeout(() => {
                    const forgotModal = document.getElementById('forgotPasswordModal');
                    const forgotEmail = document.getElementById('forgotEmail');
                    if (forgotModal) forgotModal.style.display = 'none';
                    if (messageDiv) messageDiv.innerHTML = '';
                    if (forgotEmail) forgotEmail.value = '';
                }, 3000);
            } else {
                const error = await response.json();
                if (messageDiv) {
                    messageDiv.innerHTML = '<span style="color:red">❌ ' + (error.detail || 'Ошибка') + '</span>';
                }
            }
        } catch (error) {
            if (messageDiv) {
                messageDiv.innerHTML = '<span style="color:red">❌ Ошибка соединения</span>';
            }
        }
    });
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

// Делаем переменную доступной глобально
window.currentUser = currentUser;

// ---------- Инициализация ----------
function init() {
    console.log('Инициализация auth.js...');
    initTheme();
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            createWidgetMenu();
            checkAuth();
        });
    } else {
        createWidgetMenu();
        checkAuth();
    }
    
    window.addEventListener('pageshow', function() {
        syncThemeToggle();
    });
}

init();