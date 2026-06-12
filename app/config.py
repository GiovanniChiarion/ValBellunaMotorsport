from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./calendario.db"
    jwt_secret: str = "cambia-questa-chiave-in-produzione"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    app_name: str = "CalendarioKart"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "cambia-questa-chiave-in-produzione"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
