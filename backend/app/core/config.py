"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    API_PREFIX: str

    DEBUG: bool

    HOST: str
    PORT: int

    GROQ_API_KEY: str

    MODEL_NAME: str
    EMBEDDING_MODEL: str

    DOCUMENT_PATH: str
    VECTOR_PATH: str

    LANGUAGE: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()