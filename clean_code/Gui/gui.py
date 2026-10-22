import tkinter as tk
from collections.abc import Callable

from business_logic.player import MusicPlayer
from business_logic.playlist import PlaylistManager
from config.settings import settings
from models.models import ButtonConfig, SongData


class GUIHandler:
    def __init__(self, root: tk.Tk) -> None:
        self.root: tk.Tk = root
        self.buttons: list[tuple[tk.Button, ButtonConfig]] = []

        self.create_playlist_manager()
        self.create_music_player()
        self.create_components()
        self.arrange_components()

        self.player.on_song_change = self.update_current_song_display
        self.player.schedule_song_end_check(root)

    def create_playlist_manager(self) -> None:
        self.playlist = PlaylistManager()

    def create_music_player(self) -> None:
        self.player = MusicPlayer(self.playlist)

    def create_components(self) -> None:
        self.create_playlist_display()
        self.create_status_label()
        self.create_buttons()

    def create_playlist_display(self) -> None:
        self.playlist_display = tk.Text(
            self.root,
            width=settings.PLAYLIST_TEXT_WIDTH,
            height=settings.PLAYLIST_TEXT_HEIGHT,
            wrap=tk.WORD,
        )
        self.playlist.playlist_display = self.playlist_display

    def create_status_label(self) -> None:
        self.status_label = tk.Label(
            self.root,
            text="No song playing",
        )

    def create_button_configs(self) -> list[ButtonConfig]:
        return [
            ButtonConfig("ADD TO LIST", self.playlist.add_songs),
            ButtonConfig("PLAY SONG", self.player.play),
            ButtonConfig("PREVIOUS SONG", self.player.previous_song),
            ButtonConfig("PAUSE/UNPAUSE", self.player.toggle_pause),
            ButtonConfig("NEXT SONG", self.player.next_song),
            ButtonConfig("AUTO PLAY: ON", self.toggle_auto_play),
        ]

    def create_buttons(self) -> None:
        self.buttons = []

        for config in self.create_button_configs():
            button = tk.Button(
                self.root,
                text=config.text_display,
                command=config.functionality,
                bg=config.bg,
                width=config.width,
            )
            self.buttons.append((button, config))

    def arrange_components(self) -> None:
        current_row = settings.LAYOUT_START_ROW

        current_row = self.arrange_buttons(current_row)
        current_row = self.arrange_status_label(current_row)
        self.arrange_playlist_display(current_row)

    def arrange_buttons(self, row: int) -> int:
        current_row = row

        for button, config in self.buttons:
            button.grid(
                row=current_row,
                column=settings.LAYOUT_START_COLUMN + config.column,
                pady=config.pady,
            )
            current_row += 1

        return current_row

    def arrange_status_label(self, row: int) -> int:
        self.status_label.grid(
            row=row,
            column=settings.LAYOUT_START_COLUMN,
            pady=settings.LAYOUT_WIDGETS_PADY,
        )

        return row + 1

    def arrange_playlist_display(self, row: int) -> None:
        self.playlist_display.grid(
            row=row,
            column=settings.LAYOUT_START_COLUMN,
            pady=settings.LAYOUT_WIDGETS_PADY,
        )

    def update_current_song_display(self, song: SongData) -> None:
        self.status_label.config(text=str(song))

    def toggle_auto_play(self) -> None:
        self.player.toggle_auto_play()
        self.update_auto_play_button()

    def update_auto_play_button(self) -> None:
        state = "ON" if self.player.auto_play else "OFF"

        button = self.get_button_by_functionality(self.toggle_auto_play)
        button.config(text=f"AUTO PLAY: {state}")

    def get_button_by_functionality(
        self,
        functionality: Callable[[], None],
    ) -> tk.Button:
        for button, config in self.buttons:
            if config.functionality == functionality:
                
                return button

        raise ValueError(
            f"No button found for functionality: {functionality.__name__}"
        )