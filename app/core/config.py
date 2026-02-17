from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "tg2eitaa"
    LOG_LEVEL: str = "INFO"

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    EITAA_TOKEN: str = ""
    DEFAULT_EITAA_CHAT_ID: str = ""

    DATABASE_URL: str

settings = Settings()
