import logging
import tkinter as tk

import pygame

from config.settings import settings
from gui.gui import GUIHandler

logger = logging.getLogger(__name__)


class MusicPlayerApp:
    def __init__(self) -> None:
        pygame.init()

        self.root: tk.Tk = tk.Tk()
        self.root.title("MP3 Music Player")
        self.root.geometry(settings.APP_GEOMETRY)

        self.gui: GUIHandler = GUIHandler(self.root)

        self.root.protocol("WM_DELETE_WINDOW", self.close)

        logger.info("Application initialized")

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        logger.info("Closing application")

        pygame.mixer.music.stop()
        self.root.destroy()
        pygame.quit()