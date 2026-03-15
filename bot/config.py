from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    bot_token: str = ""
    database_url: str = "sqlite+aiosqlite:///rss_bot.db"
    check_interval_minutes: int = 30
    digest_hour: int = 9
    digest_minute: int = 0
    max_feeds_per_user: int = 50
    max_keywords_per_user: int = 100
    max_groups_per_user: int = 20
    fetch_timeout: int = 30
    entries_per_fetch: int = 10
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_prefix": "RSS_BOT_"}


settings = Settings()
