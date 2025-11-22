"""
YouTube Handler Module

Handles all YouTube fetching, quality extraction, and downloading operations.
Supports both single videos and playlists with audio and video formats.
"""

import logging
import os
import re
import subprocess
from typing import Any, Dict, List

from pytubefix import YouTube, Playlist

from .helpers import sanitize_filename

logger = logging.getLogger(__name__)


class YouTubeHandler:
    """Handles all YouTube fetching and downloading operations."""

    def fetch_details(self, url: str) -> Dict[str, Any]:
        """
        Fetch details for a given YouTube URL (video or playlist).

        Args:
            url (str): YouTube URL (video or playlist)

        Returns:
            Dict[str, Any]: Dictionary containing:
                - success (bool): Whether the operation succeeded
                - is_playlist (bool): Whether it's a playlist
                - title (str): Title of the video/playlist
                - videos (list): List of YouTube objects
                - first_video_streams: Stream objects for quality selection
                - thumbnail_url (str): URL to the thumbnail
                - error (str): Error message if success is False
        """
        try:
            if "playlist" in url:
                playlist = Playlist(url)
                if not playlist.videos:
                    raise ValueError("Playlist is empty or invalid.")

                first_video = playlist.videos[0]
                logger.info(f"Fetched playlist: {playlist.title} with {len(playlist.videos)} videos")
                return {
                    "success": True,
                    "is_playlist": True,
                    "title": playlist.title,
                    "videos": playlist.videos,
                    "first_video_streams": first_video.streams,
                    "thumbnail_url": first_video.thumbnail_url,
                }
            else:
                video = YouTube(url)
                logger.info(f"Fetched video: {video.title}")
                return {
                    "success": True,
                    "is_playlist": False,
                    "title": video.title,
                    "videos": [video],
                    "first_video_streams": video.streams,
                    "thumbnail_url": video.thumbnail_url,
                }
        except Exception as e:
            logger.error(f"Failed to fetch details from URL: {e}")
            return {"success": False, "error": str(e)}

    def get_quality_options(self, streams: Any, mode: str) -> List[str]:
        """
        Get available quality options based on the mode.

        Args:
            streams: Stream object from pytubefix
            mode (str): Either "Audio" or "Video"

        Returns:
            List[str]: List of available quality options (resolutions or bitrates)
        """
        qualities: List[str] = []
        try:
            if mode == "Audio":
                audio_streams = streams.filter(only_audio=True).order_by("abr").desc()
                qualities = sorted(
                    list(set(s.abr for s in audio_streams if s.abr)),
                    key=lambda x: int(re.sub(r"\D", "", x)),
                    reverse=True,
                )
            else:  # Video
                progressive_streams = list(streams.filter(progressive=True))
                adaptive_streams = list(streams.filter(only_video=True))
                all_streams = progressive_streams + adaptive_streams

                resolutions = set(s.resolution for s in all_streams if s.resolution)
                qualities = sorted(
                    list(resolutions),
                    key=lambda x: int(x[:-1]),
                    reverse=True,
                )
        except Exception as e:
            logger.error(f"Error getting quality options: {e}")

        return qualities if qualities else ["Not Available"]

    def download(
        self, video: YouTube, quality: str, mode: str, save_path: str, filename_prefix: str = ""
    ) -> None:
        """
        Download a single video or audio stream.

        Args:
            video (YouTube): YouTube object from pytubefix
            quality (str): Selected quality (resolution or bitrate)
            mode (str): "Audio" or "Video"
            save_path (str): Directory to save the file
            filename_prefix (str): Prefix for the filename (e.g., "01." for playlists)

        Raises:
            Exception: If download fails
        """
        sanitized_title = sanitize_filename(f"{filename_prefix}{video.title}")

        try:
            if mode == "Audio":
                self._download_audio(video, quality, save_path, sanitized_title)
            else:  # Video
                self._download_video(video, quality, save_path, sanitized_title)
            logger.info(f"Successfully downloaded: {sanitized_title}")
        except Exception as e:
            logger.error(f"Download failed for {sanitized_title}: {e}")
            raise

    def _download_audio(self, yt: YouTube, quality: str, save_path: str, file_title: str) -> None:
        """
        Handle audio-only download.

        Args:
            yt (YouTube): YouTube object
            quality (str): Audio bitrate quality
            save_path (str): Directory to save
            file_title (str): Filename without extension

        Raises:
            Exception: If no audio stream is available
        """
        stream = yt.streams.filter(only_audio=True, abr=quality).first()
        if not stream:
            stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()

        if not stream:
            raise Exception("No audio stream found.")

        logger.info(f"Downloading audio: {file_title}")
        stream.download(output_path=save_path, filename=f"{file_title}.mp3")

    def _download_video(self, yt: YouTube, quality: str, save_path: str, file_title: str) -> None:
        """
        Handle video download, including merging if necessary.

        Uses FFmpeg to merge video and audio if no progressive stream is available.

        Args:
            yt (YouTube): YouTube object
            quality (str): Video resolution quality
            save_path (str): Directory to save
            file_title (str): Filename without extension

        Raises:
            Exception: If video/audio streams not found or FFmpeg fails
        """
        # Try progressive stream first (video+audio combined)
        progressive_stream = yt.streams.filter(progressive=True, res=quality).first()
        if progressive_stream:
            logger.info(f"Downloading progressive stream: {file_title}")
            progressive_stream.download(output_path=save_path, filename=f"{file_title}.mp4")
            return

        # If no progressive stream, download separately and merge
        logger.info(f"No progressive stream found. Downloading video and audio separately: {file_title}")
        video_stream = (
            yt.streams.filter(only_video=True, res=quality).order_by("resolution").desc().first()
        )
        audio_stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()

        if not video_stream or not audio_stream:
            raise Exception(f"Could not find separate video/audio streams for {quality}.")

        # Define file paths for temporary files
        video_file = os.path.join(save_path, f"{file_title}_video.mp4")
        audio_file = os.path.join(save_path, f"{file_title}_audio.mp4")
        output_file = os.path.join(save_path, f"{file_title}.mp4")

        try:
            # Download streams
            video_stream.download(filename=video_file)
            audio_stream.download(filename=audio_file)

            # Merge with FFmpeg
            logger.info(f"Merging video and audio: {file_title}")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    video_file,
                    "-i",
                    audio_file,
                    "-c",
                    "copy",
                    output_file,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            raise Exception(
                "FFmpeg not found. Please ensure FFmpeg is installed and added to your system PATH. "
                "Download from: https://ffmpeg.org/download.html"
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"FFmpeg merge failed: {e}")
        finally:
            # Clean up temporary files
            for temp_file in [video_file, audio_file]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        logger.debug(f"Cleaned up temporary file: {temp_file}")
                    except OSError as e:
                        logger.warning(f"Failed to remove temporary file {temp_file}: {e}")

        # Download streams
        video_stream.download(filename=video_file)
        audio_stream.download(filename=audio_file)

        # Merge with FFmpeg
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", video_file, "-i", audio_file,
                "-c", "copy", output_file
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise Exception("FFmpeg failed to merge files. Ensure FFmpeg is installed and in your system's PATH.")
        finally:
            # Clean up temporary files
            if os.path.exists(video_file): os.remove(video_file)
            if os.path.exists(audio_file): os.remove(audio_file)