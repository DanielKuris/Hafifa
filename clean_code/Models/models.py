from collections.abc import Callable
from dataclasses import dataclass

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

from config.settings import settings


@dataclass
class SongData:
    local_song_path: str
    title: str = "Unknown title"
    artist: str = "Unknown artist"

    def __post_init__(self) -> None:
        try:
            metadata = EasyID3(self.local_song_path)
        except (ID3NoHeaderError, OSError, ValueError):
            
            return

        self.title = metadata.get("title", [self.title])[0]
        self.artist = metadata.get("artist", [self.artist])[0]

    def __str__(self) -> str:
        return f"{self.title} - {self.artist}"


@dataclass
class ButtonConfig:
    text_display: str
    functionality: Callable[[], None]
    bg: str = settings.BUTTON_BG
    width: int = settings.BUTTON_WIDTH
    row: int = settings.LAYOUT_START_ROW
    column: int = settings.LAYOUT_START_COLUMN
    pady: int = settings.BUTTON_PADY