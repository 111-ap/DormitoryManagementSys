from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    """应用配置，优先读取项目根目录 .env。"""

    model_config = SettingsConfigDict(
        env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "DormitoryManagementSystem"
    app_env: str = "development"
    api_prefix: str = "/api/v1"

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str = "dormitory_db"
    db_user: str = "dorm_app"
    db_password: str = "change_me"

    jwt_secret: str = "change_me_to_a_long_random_string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    upload_dir: str = "backend/uploads"
    max_upload_mb: int = 5

    admin_username: str = "admin"
    admin_initial_password: str = "change_me_admin_password"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def database_url(self) -> str:
        password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{self.db_user}:{password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
