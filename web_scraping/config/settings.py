from pathlib import Path

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
    OUTPUT_DIR: Path = Path("output")

    BROWSER_CHANNEL: str = "chrome"
    HEADLESS: bool = True


settings = Settings(
    _env_file=BASE_DIR / ".env",
)

settings.INPUT_FILE = (
    settings.INPUT_FILE
    if settings.INPUT_FILE.is_absolute()
    else BASE_DIR / settings.INPUT_FILE
)

settings.OUTPUT_DIR = (
    settings.OUTPUT_DIR
    if settings.OUTPUT_DIR.is_absolute()
    else BASE_DIR / settings.OUTPUT_DIR
)
