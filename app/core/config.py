# veritas_app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    OPENAI_API_KEY: str = "not_set"
    GOOGLE_API_KEY: str = "not_set"
    GOOGLE_CX: str = "not_set"
    AUTO_APPROVE_THRESHOLD: float = 0.9


settings = Settings()