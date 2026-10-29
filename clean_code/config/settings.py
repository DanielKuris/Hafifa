from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_GEOMETRY: str = "500x500"

    SONG_END_CHECK_INTERVAL_MS: int = 100

    PLAYLIST_TEXT_WIDTH: int = 60
    PLAYLIST_TEXT_HEIGHT: int = 10

    LAYOUT_START_ROW: int = 0
    LAYOUT_START_COLUMN: int = 0
    LAYOUT_WIDGETS_PADY: int = 10

    BUTTON_BG: str = "AntiqueWhite1"
    BUTTON_WIDTH: int = 40
    BUTTON_PADY: int = 2

    LOG_LEVEL: str = "INFO"


settings: Settings = Settings()
