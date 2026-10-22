import base64
import json
import shutil
from pathlib import Path

from models.models import (
    PageDataResult,
    ScreenshotResult,
)


class OutputManager:
    def __init__(self, output_directory: Path) -> None:
        self.output_directory = output_directory

        if self.output_directory.exists():
            shutil.rmtree(self.output_directory)

        self.output_directory.mkdir(parents=True)

    def create_url_directory(self, index: int) -> Path:
        url_directory = self.output_directory / f"url_{index}"
        url_directory.mkdir(parents=True, exist_ok=True)

        return url_directory

    def get_screenshot_path(self, output_directory: Path) -> Path:

        return output_directory / "screenshot.png"

    def save_results(
        self,
        output_directory: Path,
        page_result: PageDataResult,
        screenshot_result: ScreenshotResult,
    ) -> None:
        output_directory.mkdir(parents=True, exist_ok=True)

        screenshot = self._encode_screenshot(screenshot_result)

        if page_result.success and page_result.data is not None:
            content = {
                "title": page_result.data.title,
                "html": page_result.data.html,
                "resources": sorted(page_result.data.resources),
                "screenshot": screenshot,
            }
        else:
            content = {
                "title": None,
                "html": None,
                "resources": [],
                "screenshot": screenshot,
                "error": page_result.error,
            }

        output_path = output_directory / "browser.json"
        output_path.write_text(
            json.dumps(content, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def _encode_screenshot(
        result: ScreenshotResult,
    ) -> str | None:
        if not result.success or result.data is None:
            return None

        screenshot_path = Path(result.data.path)

        if not screenshot_path.is_file():
            return None

        return base64.b64encode(screenshot_path.read_bytes()).decode("ascii")
