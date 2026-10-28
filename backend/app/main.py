from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import check_database

app = FastAPI(
    title=settings.app_name,
    description="高校学生宿舍信息管理系统后端 API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", tags=["系统"])
def root() -> dict:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "api": settings.api_prefix,
    }


@app.get(f"{settings.api_prefix}/health", tags=["系统"])
def health() -> dict:
    try:
        check_database()
        return {"status": "ok", "database": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "database": str(exc)}
