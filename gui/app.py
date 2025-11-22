"""
GUI Application Module

Main GUI application for Pro YouTube Downloader using CustomTkinter.
Handles user interface, threading for downloads, and progress tracking.
"""

import logging
import os
import threading
import tkinter
from io import BytesIO
from tkinter import filedialog, messagebox
from typing import Any, Callable, List, Optional

import customtkinter as ctk
import requests
from PIL import Image

from utils.youtube_handler import YouTubeHandler

from . import ui_components

logger = logging.getLogger(__name__)

# Configure CustomTkinter theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    """Main application class for Pro YouTube Downloader GUI."""

    def __init__(self) -> None:
        """
        Initialize the application window and set up UI components.

        Sets up the main window, initializes state variables, and creates widgets.
        """
        super().__init__()
        self.title("Pro YouTube Downloader")
        self.geometry("800x650")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # State and Handlers
        self.download_dir: str = os.path.expanduser("~/Downloads")
        self.videos_to_download: List[Any] = []
        self.video_streams: Optional[Any] = None
        self.handler: YouTubeHandler = YouTubeHandler()

        logger.info("Initializing Pro YouTube Downloader application")

        # UI Setup
        self._create_widgets()
        self.update_dir_label()

    def _create_widgets(self) -> None:
        """
        Create and arrange all UI components and widgets.

        Creates top frame (URL input), middle frame (quality/mode selection),
        list frame (video list), progress frame, and download button.
        """
        # Variables
        self.mode_var: ctk.StringVar = ctk.StringVar(value="Video")
        self.quality_var: ctk.StringVar = ctk.StringVar(value="Select Quality")

        # Create UI sections from components
        (
            self.top_frame,
            self.url_entry,
            self.fetch_button,
            self.thumbnail_label,
            self.title_label,
        ) = ui_components.create_top_frame(self, self.start_fetch_thread)

        (
            self.middle_frame,
            self.quality_menu,
            self.dir_label,
        ) = ui_components.create_middle_frame(
            self, self.mode_var, self.quality_var, self.choose_dir, self.update_quality_options
        )

        self.list_frame, self.listbox = ui_components.create_list_frame(self)

        (
            self.progress_frame,
            self.progressbar,
            self.stats_label,
        ) = ui_components.create_progress_frame(self)
            
        # Download button
        self.download_button: ctk.CTkButton = ctk.CTkButton(
            self,
            text="Download",
            command=self.start_download,
            font=ctk.CTkFont(weight="bold"),
            state="disabled",
        )
        self.download_button.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")

    # --- Threading Methods ---

    def start_fetch_thread(self) -> None:
        """Start a background thread to fetch video/playlist details."""
        self.fetch_button.configure(state="disabled", text="Fetching...")
        threading.Thread(target=self.fetch_details, daemon=True).start()

    def start_download(self) -> None:
        """Start a background thread to download the selected videos."""
        self.download_button.configure(state="disabled")
        self.fetch_button.configure(state="disabled")
        threading.Thread(target=self.download_logic, daemon=True).start()

    # --- Backend Logic (executed in threads) ---

    def fetch_details(self) -> None:
        """
        Fetch video/playlist details from the provided URL.

        Executed in a background thread to avoid blocking the UI.
        """
        url: str = self.url_entry.get().strip()
        if not url:
            logger.warning("No URL provided")
            self.after(0, self.reset_ui_state)
            return

        self.after(0, self.title_label.configure, {"text": "Fetching details, please wait..."})
        logger.info(f"Fetching details from: {url}")
        details: dict = self.handler.fetch_details(url)
        self.after(0, self.update_ui_with_details, details)

    def download_logic(self) -> None:
        """
        Handle the download process for all selected videos.

        Executed in a background thread. Updates UI progress in real-time.
        """
        mode: str = self.mode_var.get()
        quality: str = self.quality_var.get()
        is_playlist: bool = len(self.videos_to_download) > 1

        base_path: str = self.download_dir
        if is_playlist:
            playlist_title: str = self.handler.helpers.sanitize_filename(
                self.title_label.cget("text").replace("Playlist: ", "")
            )
            base_path = os.path.join(self.download_dir, playlist_title)
            os.makedirs(base_path, exist_ok=True)
            logger.info(f"Downloading playlist to: {base_path}")

        for idx, video in enumerate(self.videos_to_download):
            self.update_listbox_status(idx, "Downloading...")
            self.reset_progress()

            try:
                # Setup progress callback for pytubefix
                video.register_on_progress_callback(self.on_progress)

                # Download
                prefix: str = f"{idx+1:02d}." if is_playlist else ""
                logger.info(f"Downloading video {idx+1}/{len(self.videos_to_download)}: {video.title}")
                self.handler.download(video, quality, mode, base_path, prefix)

                self.update_listbox_status(idx, "✔ Completed")
            except Exception as e:
                logger.error(f"Download failed for video {idx+1}: {e}")
                self.update_listbox_status(idx, f"❌ FAILED - {str(e)[:50]}")
                self.after(
                    100,
                    lambda err=str(e), t=video.title: messagebox.showerror(
                        "Download Error", f"Failed to download '{t}'.\n\nError: {err}"
                    ),
                )

        self.after(0, self.finalize_downloads)

    # --- UI Update Methods (executed on main thread via self.after) ---

    def update_ui_with_details(self, details: dict) -> None:
        """
        Update UI with fetched video/playlist details.

        Args:
            details (dict): Dictionary containing video details from YouTubeHandler.fetch_details()
        """
        self.clear_listbox()
        if not details["success"]:
            self.title_label.configure(text=f"Error: {details['error']}")
            logger.error(f"Failed to fetch details: {details['error']}")
            self.reset_ui_state()
            return

        self.title_label.configure(
            text=f"{'Playlist' if details['is_playlist'] else 'Video'}: {details['title']}"
        )
        self.videos_to_download = details["videos"]
        self.video_streams = details["first_video_streams"]

        for idx, video in enumerate(self.videos_to_download, 1):
            self.add_to_listbox(f"{idx:02d}. {video.title} - Pending")

        self.update_quality_options()
        self.load_thumbnail(details["thumbnail_url"])
        self.download_button.configure(state="normal")
        self.fetch_button.configure(state="normal", text="Fetch Details")
        logger.info(f"UI updated with details for {len(self.videos_to_download)} video(s)")

    def update_quality_options(self, _: Optional[str] = None) -> None:
        """
        Update quality dropdown menu based on selected mode.

        Args:
            _ (Optional[str]): Unused parameter for event binding compatibility
        """
        if self.video_streams:
            qualities: List[str] = self.handler.get_quality_options(
                self.video_streams, self.mode_var.get()
            )
            self.quality_menu.configure(values=qualities, state="normal")
            self.quality_var.set(qualities[0])
        else:
            self.quality_menu.configure(values=["Fetch URL first"], state="disabled")
            self.quality_var.set("Fetch URL first")

    def load_thumbnail(self, url: str) -> None:
        """
        Load and display the thumbnail image from URL.

        Args:
            url (str): URL of the thumbnail image
        """
        try:
            response: requests.Response = requests.get(url, timeout=5)
            response.raise_for_status()
            img_data: Image.Image = Image.open(BytesIO(response.content))
            thumbnail_img: ctk.CTkImage = ctk.CTkImage(img_data, size=(120, 90))
            self.thumbnail_label.configure(image=thumbnail_img)
        except requests.RequestException as e:
            logger.warning(f"Failed to load thumbnail: {e}")
        except Exception as e:
            logger.warning(f"Error processing thumbnail: {e}")

    def choose_dir(self) -> None:
        """Open file dialog to choose download directory."""
        path: Optional[str] = filedialog.askdirectory(initialdir=self.download_dir)
        if path:
            self.download_dir = path
            logger.info(f"Download directory changed to: {self.download_dir}")
            self.update_dir_label()

    def update_dir_label(self) -> None:
        """Update the display label with current download directory."""
        self.dir_label.configure(text=f"Folder: {self.download_dir}")

    def on_progress(self, stream: Any, chunk: bytes, bytes_remaining: int) -> None:
        """
        Callback for download progress updates.

        Args:
            stream: Stream object from pytubefix
            chunk (bytes): Downloaded chunk
            bytes_remaining (int): Bytes remaining to download
        """
        total: int = stream.filesize
        downloaded: int = total - bytes_remaining
        percent: float = downloaded / total if total > 0 else 0
        self.progressbar.set(percent)
        self.stats_label.configure(text=f"{downloaded/1e6:.2f}MB / {total/1e6:.2f}MB")

    def reset_progress(self) -> None:
        """Reset progress bar and stats to initial state."""
        self.progressbar.set(0)
        self.stats_label.configure(text="")

    def reset_ui_state(self) -> None:
        """Reset UI buttons to their initial enabled/disabled state."""
        self.fetch_button.configure(state="normal", text="Fetch Details")
        self.download_button.configure(state="disabled")

    def finalize_downloads(self) -> None:
        """Update UI after all downloads are complete."""
        self.stats_label.configure(text="✨ All downloads complete!")
        logger.info("All downloads completed")
        self.reset_ui_state()

    def clear_listbox(self) -> None:
        """Clear all content from the video list textbox."""
        self.listbox.configure(state="normal")
        self.listbox.delete("1.0", tkinter.END)
        self.listbox.configure(state="disabled")

    def add_to_listbox(self, text: str) -> None:
        """
        Add a line of text to the video list textbox.

        Args:
            text (str): Text to add to the listbox
        """
        self.listbox.configure(state="normal")
        self.listbox.insert(tkinter.END, text + "\n")
        self.listbox.configure(state="disabled")

    def update_listbox_status(self, index: int, status: str) -> None:
        """
        Update the status of a specific video in the listbox.

        Args:
            index (int): Index of the video in the list
            status (str): New status text to display
        """
        self.after(0, self._update_listbox_on_main_thread, index, status)

    def _update_listbox_on_main_thread(self, index: int, status: str) -> None:
        """
        Update listbox status on the main thread (thread-safe).

        Args:
            index (int): Index of the video
            status (str): New status text
        """
        self.listbox.configure(state="normal")
        full_text: List[str] = self.listbox.get("1.0", tkinter.END).strip().split("\n")
        line_parts: List[str] = full_text[index].split(" - ")
        # Re-join in case title had hyphens
        original_title: str = " - ".join(line_parts[:-1])
        full_text[index] = f"{original_title} - {status}"

        self.listbox.delete("1.0", tkinter.END)
        self.listbox.insert("1.0", "\n".join(full_text))
        self.listbox.configure(state="disabled")