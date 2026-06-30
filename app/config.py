from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Bridge Service"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8086
    app_log_level: str = "info"

    bridge_api_key: str = Field(default="change-me")

    swap_api_base: str = Field(default="http://127.0.0.1:8085")
    swap_api_key: str = Field(default="change-me")

    cors_allow_origins: str = Field(default="*")

    @property
    def cors_origins_list(self) -> list[str]:
        value = self.cors_allow_origins.strip()
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]


settings = Settings()


def _validate_prod_settings() -> None:
    if settings.app_env.strip().lower() != "prod":
        return
    value = settings.bridge_api_key.strip()
    if not value or value.startswith("change-me") or len(value) < 32:
        raise RuntimeError(
            "BRIDGE_API_KEY must be set to a strong secret in production"
        )


_validate_prod_settings()
