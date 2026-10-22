import tkinter as tk
from collections.abc import Callable

import pygame

from business_logic.playlist import PlaylistManager
from config.settings import settings
from models.models import SongData


class MusicPlayer:
    def __init__(self, playlist: PlaylistManager) -> None:
        self.playlist = playlist
        self.current_song_index: int = 0
        self.paused: bool = False
        self.auto_play: bool = True

        self.on_song_change: Callable[[SongData], None] | None = None

        self.song_end: int = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.song_end)

    def play(self) -> None:
        song = self.get_current_song()

        if not song:

            return

        pygame.mixer.music.load(song.local_song_path)
        pygame.mixer.music.play()

        self.paused = False
        self._notify_song_change(song)

    def get_current_song(self) -> SongData | None:
        if not self.playlist.songs:

            return None

        return self.playlist.songs[self.current_song_index]

    def toggle_pause(self) -> None:
        if not self.playlist.songs:

            return

        if self.paused:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

        self.paused = not self.paused

    def next_song(self) -> None:
        if not self.playlist.songs:

            return

        self.current_song_index = (self.current_song_index + 1) % len(
            self.playlist.songs
        )
        self.play()

    def previous_song(self) -> None:
        if not self.playlist.songs:

            return

        self.current_song_index = (self.current_song_index - 1) % len(
            self.playlist.songs
        )
        self.play()

    def toggle_auto_play(self) -> None:
        self.auto_play = not self.auto_play

    def _notify_song_change(self, song: SongData) -> None:
        if self.on_song_change:
            self.on_song_change(song)

    def check_song_ended(self, root: tk.Tk) -> None:
        for event in pygame.event.get():
            if event.type == self.song_end and self.auto_play:
                self.next_song()

        self.schedule_song_end_check(root)

    def schedule_song_end_check(self, root: tk.Tk) -> None:
        root.after(
            settings.SONG_END_CHECK_INTERVAL_MS,
            lambda: self.check_song_ended(root),
        )