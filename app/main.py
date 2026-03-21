from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api import tests, questions, answers, auth, results  # добавили results
import os

# Определяем окружение
APP_ENV = os.getenv("APP_ENV", "development")

# Создаем приложение с условной документацией
app = FastAPI(
    title="Testing API",
    description="API для системы онлайн-тестирования с авторизацией",
    version="1.0.0",
    docs_url="/api/docs" if APP_ENV != "production" else None,
    redoc_url="/api/redoc" if APP_ENV != "production" else None,
    openapi_url="/api/openapi.json" if APP_ENV != "production" else None
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")

# Подключаем API роутеры
app.include_router(tests.router)
app.include_router(questions.router)
app.include_router(answers.router)
app.include_router(auth.router)
app.include_router(results.router)  # добавили

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Функция для настройки OpenAPI с security схемами
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title="Testing API",
        version="1.0.0",
        description="API для системы онлайн-тестирования с авторизацией",
        routes=app.routes,
    )
    
    # Добавляем схемы безопасности
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Введите JWT токен в формате: Bearer <token>"
        },
        "cookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": "HttpOnly cookie с access token (автоматически отправляется браузером)"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Применяем кастомную OpenAPI схему только если документация включена
if APP_ENV != "production":
    app.openapi = custom_openapi