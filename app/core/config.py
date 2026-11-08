from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_env: str = "development"
    database_url: str
    secret_key: str = Field(min_length=32)
    access_token_minutes: int = 30
    arkesel_api_key: str
    arkesel_sender_id: str = "FindIt"
    upload_dir: str = "uploads"
    max_photo_bytes: int = 3_000_000
    rate_limit_enabled: bool = True
    trust_proxy_headers: bool = False  # set TRUST_PROXY_HEADERS=true only behind your own reverse proxy


settings = Settings()
