from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    MAX_CONCURRENT_PAGES: int = 5
    NAVIGATION_TIMEOUT_MS: int = 30000

    INPUT_FILE: Path = Path("src/input/urls.input")
    OUTPUT_DIRECTORY: Path = Path("output")

    BROWSER_CHANNEL: str = "chrome"
    HEADLESS: bool = True

    @field_validator("INPUT_FILE", "OUTPUT_DIRECTORY", mode="before")
    @classmethod
    def resolve_path(cls, value: str | Path) -> Path:
        path = Path(value)

        return path if path.is_absolute() else BASE_DIR / path


settings = Settings(
    _env_file=BASE_DIR / ".env",
)