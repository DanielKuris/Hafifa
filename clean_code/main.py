from business_logic.app import MusicPlayerApp
from config.logging_config import configure_logging


def main() -> None:
    configure_logging()

    app = MusicPlayerApp()
    app.run()


if __name__ == "__main__":
    main()
