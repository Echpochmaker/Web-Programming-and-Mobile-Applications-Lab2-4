# Лабораторная работа №2-4: REST API для системы онлайн-тестирования с авторизацией и автоматической документацией

Данный проект представляет собой RESTful веб-сервис для управления тестами, вопросами и вариантами ответов с полноценной системой аутентификации, авторизации и автоматически сгенерированной документацией OpenAPI (Swagger). 
Реализован на **FastAPI** с использованием **SQLAlchemy** (ORM), **PostgreSQL** в качестве СУБД, **Alembic** для миграций. 
Вся инфраструктура запускается через **Docker Compose**, что обеспечивает лёгкое развёртывание и изоляцию сервисов.

## Основные возможности

### Управление тестами (Лабораторная работа №2)
- Полноценный CRUD для сущности `Test` (тест), `Question` (вопрос) и `AnswerOption` (вариант ответа).
- Мягкое удаление (soft delete) — записи помечаются удалёнными, но не стираются из базы.
- Пагинация при получении списка тестов.
- Валидация входящих данных через Pydantic-схемы (DTO).
- Модульная архитектура: контроллеры, сервисы, модели, DTO разделены по папкам.

### Аутентификация и авторизация (Лабораторная работа №3)
- Регистрация новых пользователей с хешированием паролей (bcrypt + уникальная соль)
- Вход в систему с выдачей JWT токенов (Access и Refresh)
- Безопасное хранение токенов в HttpOnly cookies
- Refresh токены с возможностью отзыва сессий
- Защита эндпоинтов — доступ только для авторизованных пользователей
- Проверка владения ресурсами (пользователь может редактировать/удалять только свои тесты)
- Выход из текущей сессии (`/logout`) и из всех сессий (`/logout-all`)
- Эндпоинт `/whoami` для проверки статуса авторизации
- Восстановление пароля через email (генерация токена в консоли)
- Интеграция с OAuth 2.0 (Yandex ID) — ручная реализация без готовых библиотек
- Защита от CSRF с использованием параметра `state`

### Автоматическая документация OpenAPI/Swagger (Лабораторная работа №4)
- **Автоматическая генерация** спецификации OpenAPI на основе кода (Code-First подход)
- **Условный запуск** — документация доступна только в режиме разработки (`development`)
- **Интерактивный Swagger UI** для тестирования всех эндпоинтов
- **Подробные описания** всех эндпоинтов с примерами запросов и ответов
- **Схемы безопасности**:
  - `bearerAuth` — для тестирования с JWT токеном
  - `cookieAuth` — для работы с HttpOnly cookies
- **Примеры ответов** для всех HTTP статусов (200, 201, 400, 401, 403, 404)
- **Документирование DTO** — каждое поле Pydantic-модели содержит описание и пример значения

## 🛠 Технологический стек

- **Python 3.11**
- **FastAPI** — веб-фреймворк (встроенная поддержка OpenAPI/Swagger)
- **SQLAlchemy** — ORM
- **Alembic** — миграции БД
- **PostgreSQL 16** — база данных
- **Docker / Docker Compose** — контейнеризация и оркестрация
- **Jinja2** — для простого веб-интерфейса
- **bcrypt** — хеширование паролей
- **PyJWT / python-jose** — работа с JWT токенами
- **httpx** — HTTP-клиент для OAuth запросов


## Запуск проекта

### Предварительные требования

- Установленные [Docker](https://docs.docker.com/get-docker/) и [Docker Compose](https://docs.docker.com/compose/install/)
- (Опционально) для локальной разработки: Python 3.11, виртуальное окружение

### Инструкция по запуску

1. **Клонируйте репозиторий**:
   git clone <url-репозитория>
   cd testing-api
Создайте файл .env в корне проекта. Используйте шаблон из .env.example:

env
# Database
DB_USER=postgres
DB_PASSWORD=mysecretpassword
DB_NAME=testing_db
DB_HOST=postgres
DB_PORT=5432

# JWT Secrets
JWT_ACCESS_SECRET=your_super_secret_access_key
JWT_REFRESH_SECRET=your_super_secret_refresh_key
JWT_ACCESS_EXPIRATION=15m
JWT_REFRESH_EXPIRATION=7d

# Yandex OAuth (опционально)
YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_CALLBACK_URL=http://localhost:4200/auth/yandex/callback

# Application environment
APP_ENV=development  # development или production

## Запустите контейнеры:

docker-compose up --build
Проверьте работу:

## API доступно по адресу: http://localhost:4200

## Документация Swagger: http://localhost:4200/api/docs (только в режиме development)

## Веб-интерфейс: http://localhost:4200 — главная страница

## Остановка:

docker-compose down

📋 Переменные окружения (файл .env)
Переменная	Описание	Пример значения
DB_USER	Имя пользователя PostgreSQL	postgres
DB_PASSWORD	Пароль пользователя	mysecretpassword
DB_NAME	Название базы данных	testing_db
DB_HOST	Хост базы данных (внутри сети)	postgres
DB_PORT	Порт PostgreSQL	5432
JWT_ACCESS_SECRET	Секретный ключ для Access токенов	your_super_secret_access_key
JWT_REFRESH_SECRET	Секретный ключ для Refresh токенов	your_super_secret_refresh_key
JWT_ACCESS_EXPIRATION	Время жизни Access токена	15m
JWT_REFRESH_EXPIRATION	Время жизни Refresh токена	7d
YANDEX_CLIENT_ID	Client ID для Yandex OAuth	your_yandex_client_id
YANDEX_CLIENT_SECRET	Client Secret для Yandex OAuth	your_yandex_client_secret
YANDEX_CALLBACK_URL	Callback URL для Yandex OAuth	http://localhost:4200/auth/yandex/callback
APP_ENV	Режим работы приложения	development / production
Шаблон для копирования — файл .env.example.

## Миграции базы данных
Миграции управляются с помощью Alembic. При запуске контейнера app автоматически выполняется команда alembic upgrade head, которая приводит схему БД к актуальному состоянию.

## Для создания новой миграции после изменения моделей:

docker-compose run --rm app alembic revision --autogenerate -m "описание изменений"
docker-compose run --rm app alembic upgrade head

#### API эндпоинты

## Аутентификация (/auth)

Метод	URI	Описание	Статус успеха	Доступ
POST	/auth/register	Регистрация нового пользователя	201 Created	Public
POST	/auth/login	Вход (установка cookies)	200 OK	Public
POST	/auth/refresh	Обновление пары токенов	200 OK	Public (требуется valid Refresh Cookie)
GET	/auth/whoami	Проверка статуса и данные пользователя	200 OK	Private
POST	/auth/logout	Завершение текущей сессии	200 OK	Private
POST	/auth/logout-all	Завершение всех сессий пользователя	200 OK	Private
GET	/auth/oauth/yandex	Инициация входа через Yandex	200 OK (возвращает URL)	Public
GET	/auth/oauth/yandex/callback	Обработка ответа от Yandex	200 OK	Public
POST	/auth/forgot-password	Запрос на сброс пароля	200 OK	Public
POST	/auth/reset-password	Установка нового пароля	200 OK	Public
GET	/reset-password	Страница для ввода нового пароля	200 OK	Public

## Управление тестами (/tests)

Метод	URI	Описание	Статус успеха	Доступ
GET	/tests	Получить список активных тестов (с пагинацией)	200 OK	Public
GET	/tests/{id}	Получить активный тест по ID	200 OK	Public
POST	/tests	Создать новый тест	201 Created	Private
PUT	/tests/{id}	Полностью обновить тест	200 OK	Private (только владелец)
PATCH	/tests/{id}	Частично обновить тест	200 OK	Private (только владелец)
DELETE	/tests/{id}	Мягко удалить тест	204 No Content	Private (только владелец)

## Управление вопросами (/tests/{test_id}/questions)

Метод	URI	Описание	Статус успеха
GET	/tests/{test_id}/questions	Получить вопросы теста	200 OK
POST	/tests/{test_id}/questions	Создать вопрос	201 Created
GET	/tests/{test_id}/questions/{id}	Получить вопрос по ID	200 OK
PUT	/tests/{test_id}/questions/{id}	Обновить вопрос	200 OK
DELETE	/tests/{test_id}/questions/{id}	Удалить вопрос	204 No Content

## Управление ответами (/questions/{question_id}/answers)

Метод	URI	Описание	Статус успеха
GET	/questions/{question_id}/answers	Получить ответы на вопрос	200 OK
POST	/questions/{question_id}/answers	Создать ответ	201 Created
PUT	/questions/{question_id}/answers/{id}	Обновить ответ	200 OK
DELETE	/questions/{question_id}/answers/{id}	Удалить ответ	204 No Content

## Документация API (Лабораторная работа №4)
Доступ к документации
Swagger UI: http://localhost:4200/api/docs

ReDoc: http://localhost:4200/api/redoc

OpenAPI JSON: http://localhost:4200/api/openapi.json

Важно: Документация доступна только в режиме разработки (APP_ENV=development). В production режиме все эндпоинты документации возвращают 404 Not Found.

Особенности документации
Автоматическая генерация — спецификация создаётся на основе кода (аннотации FastAPI и Pydantic)

Подробные описания — каждый эндпоинт содержит summary и description

Примеры ответов — для всех успешных и ошибочных статусов приведены примеры

Документирование DTO — все поля Pydantic-моделей имеют описания и примеры значений

Схемы безопасности — настроены две схемы:

bearerAuth — для передачи JWT токена в заголовке

cookieAuth — для работы с HttpOnly cookies (автоматическая отправка браузером)

## Тестирование защищенных эндпоинтов
Через cookies (автоматически):

Выполните POST /auth/login с данными пользователя

После успешного входа все последующие запросы будут автоматически содержать cookies

Через Bearer токен (ручной ввод):

Нажмите кнопку Authorize в правом верхнем углу Swagger UI

В поле bearerAuth введите JWT токен

Нажмите Authorize, затем Close

Теперь все защищенные эндпоинты будут доступны для тестирования

## Восстановление пароля
В проекте реализована функция восстановления пароля. Так как в учебном проекте не настроена реальная отправка писем, токен для сброса пароля выводится в консоль Docker.

Инструкция по восстановлению пароля:
Запрос на сброс пароля:

Нажмите кнопку "Забыли пароль?" в форме входа

Введите свой email

Или выполните запрос через Swagger: POST /auth/forgot-password

## Получение токена:

docker logs testing_app --tail 20
В выводе вы увидите:

=== PASSWORD RESET ===
Email: ваш_email@example.com
Token: abc123def456...
Reset link: http://localhost:4200/reset-password?token=abc123def456...
=== ===

## Сброс пароля:

Скопируйте ссылку из консоли и откройте её в браузере

Или используйте POST /auth/reset-password в Swagger с токеном и новым паролем

Вход с новым паролем:

После успешного сброса войдите в систему с новым паролем

## Параметры пагинации
Для GET /tests поддерживаются query-параметры:

page — номер страницы (целое число ≥1, по умолчанию 1)

limit — количество элементов на странице (целое число от 1 до 100, по умолчанию 10)

Пример запроса:


GET /tests?page=2&limit=5
Формат ответа для списка
json
{
  "data": [
    {
      "id": 1,
      "title": "Основы Python",
      "description": "Тест на знание Python",
      "created_at": "2026-03-05T16:44:59.080448Z",
      "updated_at": null
    }
  ],
  "meta": {
    "total": 42,
    "page": 2,
    "limit": 5,
    "total_pages": 9
  }
}
Формат ответа для /auth/whoami
json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "phone": null,
    "created_at": "2026-03-16T20:45:45.123456Z"
  },
  "message": "Authenticated"
}

## Веб-интерфейс
Проект включает простой веб-интерфейс, доступный по адресу http://localhost:4200.
На главной странице можно:

Просматривать список тестов (с пагинацией)

Создавать новый тест

Добавлять вопросы и ответы

Удалять тесты (мягкое удаление)

Помечать правильные ответы

Регистрироваться и входить в систему

Восстанавливать пароль

Для доступа к созданию тестов необходимо авторизоваться.

## Авторы
Студент - Иванов Андрей
Группа: 090304-РПИа-у24

Студент - Бобылев Павел
Группа: 020302-АИСа-у24

## Что добавлено нового:

1. **Раздел "Автоматическая документация OpenAPI/Swagger (Лабораторная работа №4)"** в "Основных возможностях"
2. **Подробное описание** настроек документации
3. **Инструкция по доступу** к Swagger UI и ReDoc
4. **Особенности документации** — 5 ключевых пунктов
5. **Инструкция по тестированию защищенных эндпоинтов** через Authorize
6. **Упоминание `APP_ENV`** в переменных окружения
7. **Обновленный технологический стек** с упором на OpenAPI