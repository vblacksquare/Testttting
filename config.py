
from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Parser(BaseModel):
    root: str
    rps_limit: int
    results_path: str


class Logger(BaseModel):
    path: str = "resources/logs"
    level: str = "DEBUG"


class Settings(BaseSettings):
    parser: Parser
    logger: Logger

    model_config = SettingsConfigDict(
        env_file=f".env",
        case_sensitive=False,
        env_nested_delimiter="__",
    )


@lru_cache(maxsize=1)
def get_config() -> Settings:
    return Settings()
