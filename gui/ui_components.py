"""
UI Components Module

Contains factory functions for creating reusable UI components and frames
for the Pro YouTube Downloader application.
"""

from typing import Any, Callable, Optional, Tuple

import customtkinter as ctk
from PIL import Image


def create_top_frame(
    master: Any, fetch_callback: Callable
) -> Tuple[ctk.CTkFrame, ctk.CTkEntry, ctk.CTkButton, ctk.CTkLabel, ctk.CTkLabel]:
    """
    Create the top frame with URL input, fetch button, and thumbnail display.

    Args:
        master: Parent widget
        fetch_callback: Callback function when fetch button is clicked

    Returns:
        Tuple containing:
        - frame: The container frame
        - url_entry: URL entry widget
        - fetch_button: Fetch details button
        - thumbnail_label: Label for thumbnail display
        - title_label: Label for video/playlist title
    """
    frame = ctk.CTkFrame(master)
    frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
    frame.grid_columnconfigure(1, weight=1)

    url_label = ctk.CTkLabel(frame, text="URL:")
    url_label.grid(row=0, column=0, padx=(10, 5), pady=10)

    url_entry = ctk.CTkEntry(frame, placeholder_text="Enter YouTube Playlist or Video URL")
    url_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
    url_entry.bind("<Return>", lambda event: fetch_callback())

    fetch_button = ctk.CTkButton(frame, text="Fetch Details", command=fetch_callback)
    fetch_button.grid(row=0, column=2, padx=(5, 10), pady=10)

    placeholder_img = ctk.CTkImage(Image.new("RGB", (120, 90), (50, 50, 50)), size=(120, 90))
    thumbnail_label = ctk.CTkLabel(frame, text="", image=placeholder_img)
    thumbnail_label.grid(row=1, column=0, padx=10, pady=10)

    title_label = ctk.CTkLabel(
        frame, text="Title will appear here...", wraplength=450, justify="left"
    )
    title_label.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

    return frame, url_entry, fetch_button, thumbnail_label, title_label


def create_middle_frame(
    master: Any,
    mode_var: ctk.StringVar,
    quality_var: ctk.StringVar,
    dir_callback: Callable,
    mode_callback: Callable,
) -> Tuple[ctk.CTkFrame, ctk.CTkOptionMenu, ctk.CTkLabel]:
    """
    Create the middle frame with quality, mode, and directory controls.

    Args:
        master: Parent widget
        mode_var: StringVar for mode selection (Video/Audio)
        quality_var: StringVar for quality selection
        dir_callback: Callback for directory chooser button
        mode_callback: Callback when mode is changed

    Returns:
        Tuple containing:
        - frame: The container frame
        - quality_menu: Quality dropdown menu
        - dir_label: Label showing current directory
    """
    frame = ctk.CTkFrame(master)
    frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
    frame.grid_columnconfigure((0, 1, 2), weight=1)

    mode_menu = ctk.CTkOptionMenu(
        frame, values=["Video", "Audio"], variable=mode_var, command=mode_callback
    )
    mode_menu.grid(row=0, column=0, padx=10, pady=10)

    quality_menu = ctk.CTkOptionMenu(
        frame, variable=quality_var, values=["Fetch URL first"], state="disabled"
    )
    quality_menu.grid(row=0, column=1, padx=10, pady=10)

    dir_button = ctk.CTkButton(frame, text="Choose Folder", command=dir_callback)
    dir_button.grid(row=0, column=2, padx=10, pady=10)

    dir_label = ctk.CTkLabel(
        frame, text="Folder: ", wraplength=700, font=ctk.CTkFont(size=10)
    )
    dir_label.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")

    return frame, quality_menu, dir_label


def create_list_frame(master: Any) -> Tuple[ctk.CTkFrame, ctk.CTkTextbox]:
    """
    Create the frame containing the video list display.

    Args:
        master: Parent widget

    Returns:
        Tuple containing:
        - frame: The container frame
        - listbox: Textbox widget for displaying video list
    """
    frame = ctk.CTkFrame(master)
    frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    listbox = ctk.CTkTextbox(
        frame, fg_color="#2B2B2B", text_color="white", font=("Consolas", 12), border_width=0
    )
    listbox.grid(row=0, column=0, sticky="nsew")
    listbox.configure(state="disabled")  # Make it read-only

    return frame, listbox


def create_progress_frame(master: Any) -> Tuple[ctk.CTkFrame, ctk.CTkProgressBar, ctk.CTkLabel]:
    """
    Create the progress frame with progress bar and download statistics.

    Args:
        master: Parent widget

    Returns:
        Tuple containing:
        - frame: The container frame
        - progressbar: Progress bar widget
        - stats_label: Label for displaying download statistics
    """
    frame = ctk.CTkFrame(master)
    frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
    frame.grid_columnconfigure(0, weight=1)

    progress_label = ctk.CTkLabel(frame, text="Current File Progress")
    progress_label.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")

    progressbar = ctk.CTkProgressBar(frame)
    progressbar.set(0)
    progressbar.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

    stats_label = ctk.CTkLabel(frame, text="")
    stats_label.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="w")

    return frame, progressbar, stats_label