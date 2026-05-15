# Лабораторные работы №2-9: REST API для системы онлайн-тестирования

Данный проект представляет собой RESTful веб-сервис для управления тестами, вопросами и вариантами ответов с полноценной системой аутентификации, авторизации, кешированием на Redis, автоматически сгенерированной документацией OpenAPI (Swagger), документоориентированной базой данных MongoDB, объектным хранилищем файлов MinIO, асинхронной обработкой событий через RabbitMQ и развёртыванием в Kubernetes.

Реализован на **FastAPI** с использованием **Beanie ODM** (MongoDB), **Redis** для кеширования, **MinIO** для хранения файлов, **RabbitMQ** для асинхронной обработки, **Kubernetes** для оркестрации. Вся инфраструктура запускается через **Docker Compose** (локально) или **kubectl** (в Kubernetes).


## Содержание

1. [Основные возможности по лабораторным работам](#основные-возможности-по-лабораторным-работам)
2. [Технологический стек](#технологический-стек)
3. [Запуск проекта (Docker Compose)](#запуск-проекта-docker-compose)
4. [Запуск проекта (Kubernetes)](#запуск-проекта-kubernetes)
5. [Переменные окружения](#переменные-окружения)
6. [API эндпоинты](#api-эндпоинты)
7. [Health Check эндпоинты (ЛР №9)](#health-check-эндпоинты)
8. [RabbitMQ: асинхронная обработка событий (ЛР №8)](#rabbitmq-асинхронная-обработка-событий)
9. [Документация API (Swagger/OpenAPI)](#документация-api-swaggeropenapi)
10. [Кеширование данных с Redis](#кеширование-данных-с-redis)
11. [MongoDB: документоориентированная СУБД](#mongodb-документоориентированная-субд)
12. [MinIO: объектное хранилище файлов](#minio-объектное-хранилище-файлов)
13. [Веб-интерфейс](#веб-интерфейс)
14. [Безопасность](#безопасность)
15. [Авторы](#авторы)


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

### Лабораторная работа №8 — Асинхронная обработка событий с использованием RabbitMQ

- **Публикация события** `user.registered` при успешной регистрации пользователя
- **Фоновый consumer** для асинхронной обработки сообщений
- **Отправка приветственного email** через SMTP Яндекса
- **Retry-механизм** — до 3 повторных попыток при временных ошибках SMTP
- **Dead Letter Queue** — `wp.auth.user.registered.dlq` для сообщений после исчерпания попыток
- **Идемпотентность** — защита от повторной отправки через `eventId` в Redis (TTL 24 часа)
- **Persistent messages** — сообщения сохраняются на диск (`delivery_mode=PERSISTENT`)
- **Durable queues** — очереди не удаляются при перезапуске RabbitMQ

### Лабораторная работа №9 — Развёртывание в Kubernetes
- **Health Check эндпоинты** (`/health/live`, `/health/ready`, `/health`)
- **Kubernetes-манифесты** для всех сервисов
- **Liveness/Readiness Probes** для автоматического восстановления
- **Горизонтальное масштабирование** (`kubectl scale --replicas=4`)
- **Распределённая блокировка** через Redis при регистрации
- **Docker Desktop Kubernetes** как среда развёртывания

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
| **Брокер сообщений** | RabbitMQ 3.12 | Асинхронная обработка событий |
| **SMTP клиент** | aiosmtplib | Отправка приветственных писем |
| **RabbitMQ клиент** | aio-pika | Асинхронная работа с RabbitMQ |
| **Оркестрация** | Kubernetes (Docker Desktop) | Развёртывание и масштабирование |
| **Контейнеризация** | Docker / Docker Compose | Запуск и оркестрация сервисов |
| **Хеширование паролей** | bcrypt | Безопасное хранение паролей |
| **JWT** | PyJWT / python-jose | Генерация и проверка токенов |
| **OAuth клиент** | httpx | Запросы к Yandex OAuth |


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
- RabbitMQ Management UI: `http://localhost:15672` (логин/пароль из `.env`)
- MinIO Console: `http://localhost:9001`
- Веб-интерфейс: `http://localhost:4200`

5. **Остановка**:
```bash
docker-compose down
```
##  Запуск проекта (Kubernetes)

##  Предварительные требования
##  Docker Desktop с включённым Kubernetes

kubectl (входит в Docker Desktop)

## Инструкция
Сборка образа:


docker build -t wp-labs/api:1.0.0 .
## Развёртывание:


kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/02-mongodb/
kubectl apply -f k8s/03-redis/
kubectl apply -f k8s/04-minio/
kubectl apply -f k8s/05-rabbitmq/
kubectl apply -f k8s/06-api/
## Проверка:


kubectl get all -n wp-labs
kubectl get pods -n wp-labs
Проброс порта:


kubectl port-forward svc/api 4200:4200 -n wp-labs
Масштабирование:

kubectl scale deployment/api --replicas=4 -n wp-labs
Очистка:

kubectl delete namespace wp-labs
Health Check эндпоинты (ЛР №9)
Эндпоинт	Назначение	Проверяет
GET /health/live	Liveness Probe	Процесс жив?
GET /health/ready	Readiness Probe	MongoDB, Redis, RabbitMQ, MinIO
GET /health	Общий статус	Информация о сервисе
Примеры:


curl http://localhost:4200/health/live
# → {"status":"ok"}

curl http://localhost:4200/health/ready
# → {"status":"ok","checks":{"mongodb":"ok","redis":"ok","rabbitmq":"ok","minio":"ok"}}



### Структура запущенных контейнеров

| Контейнер | Порт | Назначение |
|-----------|------|------------|
| `testing_mongo` | 27017 | MongoDB |
| `testing_redis` | 6379 | Redis |
| `testing_minio` | 9000 (API), 9001 (Console) | MinIO |
| `testing_rabbitmq` | 5672 (AMQP), 15672 (UI) | RabbitMQ |
| `testing_app` | 4200 | FastAPI приложение |


## Переменные окружения

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

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=student
RABBITMQ_PASS=student_secure_rabbit_pass

# SMTP (Яндекс)
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=465
SMTP_USER=your_email@yandex.ru
SMTP_PASS=your_app_password
SMTP_FROM=your_email@yandex.ru
SMTP_SECURE=true

# App
APP_ENV=development
```

## RabbitMQ: асинхронная обработка событий (ЛР №8)

### Архитектура взаимодействия

```
Клиент → POST /auth/register
           ↓
      Auth Service → Сохранение в MongoDB
           ↓
      QueueService.publish() → RabbitMQ (app.events)
           ↓
      Ответ 201 Created (быстрый)

В фоне:
      RabbitMQ → wp.auth.user.registered
           ↓
      QueueConsumer → EmailService.send_welcome_email()
           ↓
      SMTP Яндекс → Письмо на почту
           ↓
      Ack → Сообщение удалено из очереди
```

### Сущности RabbitMQ

| Сущность | Имя | Тип | Свойства |
|----------|-----|-----|----------|
| Exchange | `app.events` | Direct | Durable |
| Очередь | `wp.auth.user.registered` | Classic | Durable, DLX |
| DLX | `app.dlx` | Direct | Durable |
| DLQ | `wp.auth.user.registered.dlq` | Classic | Durable |

### Структура сообщения

```json
{
  "eventId": "550e8400-e29b-41d4-a716-446655440000",
  "eventType": "user.registered",
  "timestamp": "2026-05-03T10:30:00Z",
  "payload": {
    "userId": "69f75da9f0e1b58ed384e546",
    "email": "user@example.com",
    "displayName": "User"
  },
  "metadata": {
    "attempt": 1,
    "sourceService": "auth-service"
  }
}
```

### Гарантии доставки

| Механизм | Реализация |
|----------|------------|
| **Persistent messages** | `delivery_mode=aio_pika.DeliveryMode.PERSISTENT` — запись на диск |
| **Durable queues** | `durable=True` — очереди выживают после перезапуска |
| **Ack** | `message.ack()` только после успешной отправки email |
| **Retry** | До 3 попыток при ошибке SMTP |
| **Dead Letter Queue** | `wp.auth.user.registered.dlq` после 3 неудач |
| **Идемпотентность** | `eventId` сохраняется в Redis на 24 часа |

### Ключи Redis для идемпотентности

```
testing:email:sent:{eventId} → TTL 86400 сек (24 часа)
```

### Тестирование

**Регистрация пользователя:**
```bash
curl -X POST http://localhost:4200/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123456"}'
```

**Проверка RabbitMQ UI:**
Откройте `http://localhost:15672` (логин: `student`, пароль из `.env`). Перейдите в Queues → `wp.auth.user.registered`. Сообщение должно появиться и исчезнуть после обработки.

**Проверка почты:**
На указанный email должно прийти приветственное письмо с темой "Добро пожаловать в Систему Тестирования!".

**Проверка DLQ (с неверным SMTP паролем):**
1. Укажите неверный `SMTP_PASS` в `.env`
2. Зарегистрируйте пользователя
3. После 3 попыток сообщение попадёт в `wp.auth.user.registered.dlq`

### Проверка через Redis CLI

```bash
docker exec -it testing_redis redis-cli --pass redis_secure_password_change_in_prod

# Просмотр ключей идемпотентности
KEYS testing:email:sent:*

# Просмотр всех ключей приложения
KEYS testing:*
```


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
| `testing:email:sent:{event_id}` | Идемпотентность email (ЛР №8) | 86400 сек |

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

### Примеры запросов

**Загрузка файла:**
```bash
curl -X POST http://localhost:4200/files/ \
  -H "Content-Type: multipart/form-data" \
  -b cookies.txt \
  -F "file=@avatar.jpg"
```

**Обновление профиля с аватаром:**
```bash
curl -X POST http://localhost:4200/profile/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"avatar_file_id": "your-file-id"}'
```

**Проверка файлов в MinIO:**
```bash
docker exec -it testing_minio sh
mc alias set local http://localhost:9000 minio_admin minio_secure_password_change_in_prod
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
| RabbitMQ | Защищен паролем (не guest) |
| MinIO | Доступ только через API с авторизацией |
| Валидация файлов | MIME-типы и размер |
| Сообщения RabbitMQ | Без паролей, токенов, хешей |


## Авторы
| Студент | Группа |
|---------|--------|
| Иванов Андрей | 090304-РПИа-у24 |
| Бобылев Павел | 020302-АИСа-у24 |