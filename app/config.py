from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Geo News Briefing API"
    # ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    ALLOWED_ORIGINS: str = ["*"]
    GEMINI_API_KEY: str | None = None
    USE_AI_SUMMARY: bool = False
    MAX_ITEMS_PER_CATEGORY: int = 6
    REQUEST_TIMEOUT: int = 15

    class Config:
        env_file = ".env"


settings = Settings()
