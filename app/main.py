from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api import tests, questions, answers, auth, results, files, profile
from app.core.cache import cache
from app.core.database_mongo import init_mongodb
import os
from contextlib import asynccontextmanager

# Определяем окружение
APP_ENV = os.getenv("APP_ENV", "development")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=== STARTING UP ===")
    await init_mongodb()
    print("=== MongoDB connected and Beanie initialized ===")
    yield
    # Shutdown
    print("=== SHUTTING DOWN ===")

# Создаем приложение
app = FastAPI(
    title="Testing API",
    description="API для системы онлайн-тестирования с авторизацией",
    version="1.0.0",
    docs_url="/api/docs" if APP_ENV != "production" else None,
    redoc_url="/api/redoc" if APP_ENV != "production" else None,
    openapi_url="/api/openapi.json" if APP_ENV != "production" else None,
    lifespan=lifespan
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
app.include_router(results.router)
app.include_router(files.router)
app.include_router(profile.router)

# ========== СТРАНИЦЫ ==========

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница (мои тесты)"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/take-test", response_class=HTMLResponse)
async def take_test_page(request: Request):
    """Страница прохождения тестов"""
    return templates.TemplateResponse("take-test.html", {"request": request})

@app.get("/results-page", response_class=HTMLResponse)
async def results_page(request: Request):
    """Страница результатов"""
    return templates.TemplateResponse("results.html", {"request": request})

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