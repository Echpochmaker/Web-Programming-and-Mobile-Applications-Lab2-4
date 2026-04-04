from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.api import tests, questions, answers, auth, results
from app.core.cache import cache
import os

APP_ENV = os.getenv("APP_ENV", "development")

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

# Подключаем статические файлы (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем API роутеры
app.include_router(tests.router)
app.include_router(questions.router)
app.include_router(answers.router)
app.include_router(auth.router)
app.include_router(results.router)

# Функция для чтения HTML файлов
def read_html(filename: str) -> str:
    with open(f"templates/{filename}", "r", encoding="utf-8") as f:
        return f.read()

# ========== СТРАНИЦЫ (без Jinja2) ==========

@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница"""
    return HTMLResponse(content=read_html("index.html"))

@app.get("/take-test", response_class=HTMLResponse)
async def take_test_page():
    """Страница прохождения тестов"""
    return HTMLResponse(content=read_html("take-test.html"))

@app.get("/results", response_class=HTMLResponse)
async def results_page():
    """Страница результатов"""
    return HTMLResponse(content=read_html("results.html"))

# Тестовый эндпоинт для проверки кеша
@app.get("/cache-test")
async def cache_test():
    cache.set("test:key", {"message": "Hello Redis"}, ttl=60)
    value = cache.get("test:key")
    return {"cached": value}

# Функция для настройки OpenAPI
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
    
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
        "cookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

if APP_ENV != "production":
    app.openapi = custom_openapi