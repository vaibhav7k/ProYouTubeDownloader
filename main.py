"""
Pro YouTube Downloader - Main Entry Point

A modern GUI application for downloading YouTube videos and playlists.
Supports both video and audio formats with quality selection.
"""

import logging
import os
import shutil
import sys

from gui.app import App

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def check_environment() -> bool:
    """
    Check if the environment has required dependencies.

    Returns:
        bool: True if all checks pass, False otherwise.
    """
    logger.info("Checking Python environment...")
    logger.info(f"Python Executable: {sys.executable}")
    logger.info(f"Current Working Directory: {os.getcwd()}")

    logger.info("Looking for 'ffmpeg'...")
    ffmpeg_location = shutil.which("ffmpeg")
    if ffmpeg_location:
        logger.info(f"✅ Found ffmpeg at: {ffmpeg_location}")
        return True
    else:
        logger.warning(
            "⚠️ FFmpeg not found in PATH. "
            "Some features may not work. "
            "Please install FFmpeg: https://ffmpeg.org/download.html"
        )
        return False


def main() -> None:
    """Initialize and run the main application."""
    try:
        check_environment()
        logger.info("Starting Pro YouTube Downloader...")
        app = App()
        app.mainloop()
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()