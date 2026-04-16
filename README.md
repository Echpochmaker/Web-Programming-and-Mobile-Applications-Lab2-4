# Лабораторные работы №2-7: REST API для системы онлайн-тестирования с авторизацией, кешированием, документированием, MongoDB и MinIO

Данный проект представляет собой RESTful веб-сервис для управления тестами, вопросами и вариантами ответов с полноценной системой аутентификации, авторизации, кешированием на Redis, автоматически сгенерированной документацией OpenAPI (Swagger), документоориентированной базой данных MongoDB и объектным хранилищем файлов MinIO.

Реализован на **FastAPI** с использованием **Beanie ODM** (MongoDB), **Redis** для кеширования, **MinIO** для хранения файлов. Вся инфраструктура запускается через **Docker Compose**, что обеспечивает лёгкое развёртывание и изоляцию сервисов.


## Содержание

1. [Основные возможности по лабораторным работам](#основные-возможности-по-лабораторным-работам)
2. [Технологический стек](#технологический-стек)
3. [Запуск проекта](#запуск-проекта)
4. [Переменные окружения](#переменные-окружения)
5. [API эндпоинты](#api-эндпоинты)
6. [Документация API (Swagger/OpenAPI)](#документация-api-swaggeropenapi)
7. [Кеширование данных с Redis](#кеширование-данных-с-redis)
8. [MongoDB: документоориентированная СУБД](#mongodb-документоориентированная-субд)
9. [MinIO: объектное хранилище файлов](#minio-объектное-хранилище-файлов)
10. [Веб-интерфейс](#веб-интерфейс)
11. [Авторы](#авторы)


## Основные возможности по лабораторным работам

### Лабораторная работа №2 — CRUD ресурсов

- Полноценный CRUD для сущности `Test` (тест), `Question` (вопрос) и `AnswerOption` (вариант ответа)
- Мягкое удаление (soft delete) — записи помечаются удалёнными, но не стираются из базы
- Пагинация при получении списка тестов (параметры `page` и `limit`)
- Валидация входящих данных через Pydantic-схемы (DTO)
- Модульная архитектура: контроллеры, сервисы, модели, DTO разделены по папкам

### Лабораторная работа №3 — Аутентификация и авторизация

- Регистрация новых пользователей с хешированием паролей (bcrypt + уникальная соль)
- Вход в систему с выдачей JWT токенов (Access и Refresh)
- Безопасное хранение токенов в HttpOnly cookies
- Refresh токены с возможностью отзыва сессий
- Защита эндпоинтов — доступ только для авторизованных пользователей
- Проверка владения ресурсами (пользователь может редактировать/удалять только свои тесты)
- Выход из текущей сессии (`/logout`) и из всех сессий (`/logout-all`)
- Эндпоинт `/whoami` для проверки статуса авторизации
- Восстановление пароля через email (токен выводится в консоль Docker)
- Интеграция с OAuth 2.0 (Yandex ID) — ручная реализация без готовых библиотек
- Защита от CSRF с использованием параметра `state`

### Лабораторная работа №4 — Автоматическая документация OpenAPI/Swagger

- **Автоматическая генерация** спецификации OpenAPI на основе кода (Code-First подход)
- **Условный запуск** — документация доступна только в режиме разработки (`development`)
- **Интерактивный Swagger UI** для тестирования всех эндпоинтов
- **Подробные описания** всех эндпоинтов с примерами запросов и ответов
- **Схемы безопасности**: `bearerAuth` и `cookieAuth`
- **Примеры ответов** для всех HTTP статусов (200, 201, 400, 401, 403, 404)
- **Документирование DTO** — каждое поле Pydantic-модели содержит описание и пример значения

### Лабораторная работа №5 — Кеширование данных и управление сессиями с Redis

- **Кеширование списков тестов** — повторные запросы страниц тестов возвращаются из Redis
- **Кеширование профиля пользователя** — данные `/auth/whoami` кешируются на 5 минут
- **JTI (JWT ID) для Access токенов** — каждый токен получает уникальный идентификатор в Redis
- **Мгновенный отзыв токенов** — при логауте JTI удаляется, токен становится недействительным
- **Инвалидация кеша** — любая операция записи очищает связанные кешированные данные
- **TTL (Time To Live)** — все ключи в Redis имеют ограниченное время жизни
- **Защита паролем** — Redis защищён паролем из `.env` файла

### Лабораторная работа №6 — Миграция с PostgreSQL на MongoDB

- **Замена реляционной СУБД на документоориентированную** — PostgreSQL заменён на MongoDB
- **ObjectId вместо автоинкремента** — идентификаторы генерируются драйвером
- **Встраивание (Embedding)** — вопросы и ответы вложены в документ теста
- **Гибкая схема** — валидация на уровне приложения через Beanie ODM
- **Сохранение всей функциональности** — CRUD, пагинация, мягкое удаление, JWT, Redis, Swagger работают с MongoDB

### Лабораторная работа №7 — Хранение файлов с использованием MinIO (Object Storage)

- **Интеграция с MinIO** — объектное хранилище для пользовательских файлов
- **Потоковая загрузка и скачивание** — файлы не буферизируются в памяти полностью
- **Хранение метаданных в MongoDB** — оригинальное имя, размер, MIME-тип, ключ объекта, владелец
- **Валидация файлов** — проверка MIME-типов (`image/png`, `image/jpeg`, `image/jpg`) и размера (до 10 MB)
- **Привязка к пользователю** — доступ к файлам только для владельца
- **Мягкое удаление** — файлы помечаются удалёнными в БД и удаляются из MinIO
- **Аватар профиля** — возможность установки `avatar_file_id` через `POST /profile`
- **Кеширование метаданных** — метаданные файлов кешируются в Redis (TTL 300 сек)
- **Проверка владения** — при установке аватара проверяется, что файл принадлежит пользователю


## 🛠 Технологический стек

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| **Язык** | Python 3.11 | Основной язык разработки |
| **Веб-фреймворк** | FastAPI | Создание REST API, встроенная поддержка OpenAPI |
| **ODM** | Beanie | Асинхронный ODM для MongoDB |
| **Драйвер MongoDB** | Motor | Асинхронный драйвер MongoDB |
| **СУБД** | MongoDB 6 | Документоориентированная база данных |
| **Кеш** | Redis 7 | Кеширование данных и JTI токенов |
| **Объектное хранилище** | MinIO | Хранение пользовательских файлов |
| **Контейнеризация** | Docker / Docker Compose | Запуск и оркестрация сервисов |
| **Хеширование паролей** | bcrypt | Безопасное хранение паролей |
| **JWT** | PyJWT / python-jose | Генерация и проверка токенов |
| **OAuth клиент** | httpx | Запросы к Yandex OAuth |
| **Redis клиент** | redis-py | Работа с Redis из Python |
| **MinIO клиент** | minio-py | Работа с MinIO из Python |


## Запуск проекта

### Предварительные требования

- Установленные [Docker](https://docs.docker.com/get-docker/) и [Docker Compose](https://docs.docker.com/compose/install/)

### Инструкция по запуску

1. **Клонируйте репозиторий**:
```bash
git clone <url-репозитория>
cd testing-api
```

2. **Создайте файл `.env`** в корне проекта (см. раздел [Переменные окружения](#переменные-окружения))

3. **Запустите контейнеры**:
```bash
docker-compose up --build
```

4. **Проверьте работу**:
- API: `http://localhost:4200`
- Swagger UI: `http://localhost:4200/api/docs`
- MinIO Console: `http://localhost:9001`
- Веб-интерфейс: `http://localhost:4200`

5. **Остановка**:
```bash
docker-compose down
```

### Структура запущенных контейнеров

| Контейнер | Порт | Назначение |
|-----------|------|------------|
| `testing_mongo` | 27017 | MongoDB |
| `testing_redis` | 6379 | Redis |
| `testing_minio` | 9000 (API), 9001 (Console) | MinIO |
| `testing_app` | 4200 | FastAPI приложение |


## Документация API (Swagger/OpenAPI) — ЛР №4

| Тип | URL |
|-----|-----|
| Swagger UI | `http://localhost:4200/api/docs` |
| ReDoc | `http://localhost:4200/api/redoc` |
| OpenAPI JSON | `http://localhost:4200/api/openapi.json` |

> **Важно:** Документация доступна только в режиме разработки (`APP_ENV=development`).


## Кеширование данных с Redis — ЛР №5

### Ключи кеша и TTL

| Префикс ключа | Описание | TTL |
|---------------|----------|-----|
| `testing:tests:list:page:{page}:limit:{limit}` | Кешированные списки тестов | 300 сек |
| `testing:users:profile:{user_id}` | Кешированный профиль пользователя | 300 сек |
| `testing:auth:user:{user_id}:access:{jti}` | JTI активного Access токена | 900 сек |
| `testing:files:{file_id}:meta` | Метаданные файла | 300 сек |

### Проверка работы кеша через Redis CLI

```bash
docker exec -it testing_redis redis-cli --pass redis_secure_password_change_in_prod

KEYS testing:*
GET "testing:tests:list:page:1:limit:5"
TTL "testing:tests:list:page:1:limit:5"
```


## MongoDB: документоориентированная СУБД — ЛР №6

### Проверка данных в MongoDB

```bash
docker exec -it testing_mongo mongosh -u student -p student_secure_password --authenticationDatabase admin

use testing_db
show collections

db.tests.find().pretty()
db.users.find().pretty()
db.files.find().pretty()
```


## MinIO: объектное хранилище файлов — ЛР №7

### Эндпоинты для работы с файлами

| Метод | URI | Описание | Доступ |
|-------|-----|----------|--------|
| POST | `/files/` | Загрузка файла (multipart/form-data) | Авторизованные пользователи |
| GET | `/files/{file_id}` | Скачивание файла | Только владелец |
| DELETE | `/files/{file_id}` | Удаление файла | Только владелец |
| GET | `/profile/` | Получение профиля | Авторизованные пользователи |
| POST | `/profile/` | Обновление профиля (включая `avatar_file_id`) | Авторизованные пользователи |

### Валидация файлов

- Разрешённые MIME-типы: `image/png`, `image/jpeg`, `image/jpg`
- Максимальный размер: 10 MB (настраивается через `MAX_FILE_SIZE` в `.env`)

### Примеры запросов

**Загрузка файла:**
```bash
curl -X POST http://localhost:4200/files/ \
  -H "Content-Type: multipart/form-data" \
  -b cookies.txt \
  -F "file=@avatar.jpg"
```

**Скачивание файла:**
```bash
curl http://localhost:4200/files/{file_id} -b cookies.txt --output downloaded.jpg
```

**Обновление профиля с аватаром:**
```bash
curl -X POST http://localhost:4200/profile/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"avatar_file_id": "your-file-id"}'
```

**Удаление файла:**
```bash
curl -X DELETE http://localhost:4200/files/{file_id} -b cookies.txt
```

### Проверка файлов в MinIO

```bash
# Войти в контейнер MinIO
docker exec -it testing_minio sh

# Настроить клиент
mc alias set local http://localhost:9000 minio_admin minio_secure_password_change_in_prod

# Просмотреть файлы в бакете
mc ls local/testing-files/
```


## Веб-интерфейс

Проект включает веб-интерфейс, доступный по адресу `http://localhost:4200`.

### Функционал

- **Мои тесты** — создание, редактирование, удаление тестов
- **Пройти тест** — прохождение тестов других пользователей
- **Результаты** — просмотр результатов пройденных тестов
- **Авторизация** — регистрация, вход, OAuth через Яндекс, восстановление пароля
- **Профиль** — просмотр и обновление профиля, установка аватара
- **Тёмная тема** — переключение через виджет-меню


## Безопасность

| Требование | Реализация |
|------------|------------|
| Пароли в БД | Хешированы bcrypt с уникальной солью |
| Токены в БД | Хранятся только хеши |
| Cookies | HttpOnly, SameSite |
| Redis | Защищен паролем |
| MinIO | Доступ только через API с авторизацией |
| Валидация файлов | MIME-типы и размер |


## 🐳 Полный `docker-compose.yml`

```yaml
services:
  mongo:
    image: mongo:6
    container_name: testing_mongo
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${DB_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${DB_PASSWORD}
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - testing_network
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: testing_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - testing_network
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "--pass", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: testing_minio
    restart: unless-stopped
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    networks:
      - testing_network
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    container_name: testing_app
    restart: unless-stopped
    environment:
      MONGO_URI: ${MONGO_URI}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      CACHE_TTL_DEFAULT: 300
      YANDEX_CLIENT_ID: ${YANDEX_CLIENT_ID}
      YANDEX_CLIENT_SECRET: ${YANDEX_CLIENT_SECRET}
      YANDEX_CALLBACK_URL: ${YANDEX_CALLBACK_URL}
      JWT_ACCESS_SECRET: ${JWT_ACCESS_SECRET}
      JWT_REFRESH_SECRET: ${JWT_REFRESH_SECRET}
      JWT_ACCESS_EXPIRATION: 15m
      JWT_REFRESH_EXPIRATION: 7d
      APP_ENV: development
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
      MINIO_BUCKET: ${MINIO_BUCKET}
      MINIO_USE_SSL: "false"
      MAX_FILE_SIZE: ${MAX_FILE_SIZE:-10485760}
    ports:
      - "4200:4200"
    depends_on:
      mongo:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    networks:
      - testing_network
    command: uvicorn app.main:app --host 0.0.0.0 --port 4200

volumes:
  mongo_data:
  redis_data:
  minio_data:

networks:
  testing_network:
```


## Пример `.env` файла

```bash
# MongoDB
DB_USER=student
DB_PASSWORD=student_secure_password
MONGO_URI=mongodb://student:student_secure_password@mongo:27017/testing_db?authSource=admin

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_secure_password_change_in_prod
CACHE_TTL_DEFAULT=300

# JWT
JWT_ACCESS_SECRET=super_secret_access_key_change_in_prod_12345
JWT_REFRESH_SECRET=super_secret_refresh_key_change_in_prod_67890

# Yandex OAuth
YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_CALLBACK_URL=http://localhost:4200/auth/yandex/callback

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minio_admin
MINIO_SECRET_KEY=minio_secure_password_change_in_prod
MINIO_BUCKET=testing-files
MINIO_USE_SSL=false
MAX_FILE_SIZE=10485760

# Appы
APP_ENV=development



|    Студент    |      Группа     |
|---------------|-----------------|
| Иванов Андрей | 090304-РПИа-у24 |
| Бобылев Павел | 020303-АИСа-у24 |