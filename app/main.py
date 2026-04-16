from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.api import tests, questions, answers, auth, results, files, profile
from app.core.cache import cache
from app.core.database_mongo import init_mongodb
import os

APP_ENV = os.getenv("APP_ENV", "development")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await init_mongodb()
    yield
    print("Shutting down...")

app = FastAPI(
    title="Testing API",
    description="API для системы онлайн-тестирования с MongoDB",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if APP_ENV != "production" else None,
    redoc_url="/api/redoc" if APP_ENV != "production" else None,
    openapi_url="/api/openapi.json" if APP_ENV != "production" else None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(tests.router)
app.include_router(questions.router)
app.include_router(answers.router)
app.include_router(auth.router)
app.include_router(results.router)
app.include_router(files.router)
app.include_router(profile.router)

# Функция для чтения HTML файлов
def read_html(filename: str) -> str:
    with open(f"templates/{filename}", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=read_html("index.html"))

@app.get("/take-test", response_class=HTMLResponse)
async def take_test_page():
    return HTMLResponse(content=read_html("take-test.html"))

@app.get("/results", response_class=HTMLResponse)
async def results_page():
    return HTMLResponse(content=read_html("results.html"))

@app.get("/cache-test")
async def cache_test():
    cache.set("test:key", {"message": "Hello Redis"}, ttl=60)
    value = cache.get("test:key")
    return {"cached": value}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title="Testing API",
        version="1.0.0",
        description="API для системы онлайн-тестирования с MongoDB",
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