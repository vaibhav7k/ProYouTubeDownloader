import tkinter
import customtkinter as ctk
import threading
import os
import re
import time
import subprocess
from tkinter import messagebox, filedialog
from pytubefix import Playlist, YouTube
from PIL import Image, ImageTk
import requests
from io import BytesIO


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pro YouTube Downloader")
        self.geometry("800x650")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.download_dir = os.path.expanduser("~/Downloads")
        self.is_playlist = False
        self.video_streams = None

        # UI Frames and Widgets setup...
        self.setup_ui()

    def setup_ui(self):
        # Top frame for URL input and thumbnail
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.top_frame.grid_columnconfigure(1, weight=1)
        
        # Middle frame for controls
        self.middle_frame = ctk.CTkFrame(self)
        self.middle_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.middle_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # List frame for video list
        self.list_frame = ctk.CTkFrame(self)
        self.list_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.list_frame.grid_rowconfigure(0, weight=1)
        self.list_frame.grid_columnconfigure(0, weight=1)
        
        # Progress frame
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)

        # URL input
        self.url_label = ctk.CTkLabel(self.top_frame, text="URL:")
        self.url_label.grid(row=0, column=0, padx=(10, 5), pady=10)
        
        self.url_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Enter YouTube Playlist or Video URL")
        self.url_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.url_entry.bind("<Return>", self.fetch_details_thread)
        
        self.fetch_button = ctk.CTkButton(self.top_frame, text="Fetch Details", command=self.fetch_details_thread)
        self.fetch_button.grid(row=0, column=2, padx=(5, 10), pady=10)

        # Thumbnail and title
        placeholder_img = ctk.CTkImage(Image.new("RGB", (120, 90), (50, 50, 50)), size=(120, 90))
        self.thumbnail_label = ctk.CTkLabel(self.top_frame, text="", image=placeholder_img)
        self.thumbnail_label.grid(row=1, column=0, padx=10, pady=10)
        
        self.title_label = ctk.CTkLabel(self.top_frame, text="Title will appear here...", wraplength=450, justify="left")
        self.title_label.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # Mode and quality selection
        self.mode_var = ctk.StringVar(value="Video")
        self.mode_menu = ctk.CTkOptionMenu(self.middle_frame, values=["Video", "Audio"], variable=self.mode_var, command=self.update_quality_options)
        self.mode_menu.grid(row=0, column=0, padx=10, pady=10)
        
        self.quality_var = ctk.StringVar(value="Select Quality")
        self.quality_menu = ctk.CTkOptionMenu(self.middle_frame, variable=self.quality_var, values=["Fetch URL first"], state="disabled")
        self.quality_menu.grid(row=0, column=1, padx=10, pady=10)
        
        self.dir_button = ctk.CTkButton(self.middle_frame, text="Choose Folder", command=self.choose_dir)
        self.dir_button.grid(row=0, column=2, padx=10, pady=10)
        
        self.dir_label = ctk.CTkLabel(self.middle_frame, text=f"Folder: {self.download_dir}", wraplength=700, font=ctk.CTkFont(size=10))
        self.dir_label.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")

        # Download button
        self.download_button = ctk.CTkButton(self, text="Download", command=self.start_download, font=ctk.CTkFont(weight="bold"), state="disabled")
        self.download_button.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Video listbox
        self.listbox = tkinter.Listbox(self.list_frame, bg="#2B2B2B", fg="white", selectbackground="#1F6AA5", font=("Consolas", 10), relief="flat", borderwidth=0, highlightthickness=0)
        self.listbox.grid(row=0, column=0, sticky="nsew")

        # Progress bar and stats
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Current File Progress")
        self.progress_label.grid(row=0, column=0, padx=10, pady=(5,0), sticky="w")
        
        self.progressbar = ctk.CTkProgressBar(self.progress_frame)
        self.progressbar.set(0)
        self.progressbar.grid(row=1, column=0, padx=10, pady=(0,10), sticky="ew")
        
        self.stats_label = ctk.CTkLabel(self.progress_frame, text="")
        self.stats_label.grid(row=2, column=0, padx=10, pady=(0,5), sticky="w")

    def sanitize(self, name):
        return re.sub(r'[<>:"/\\|?*]', '-', name)

    def fetch_details_thread(self, event=None):
        threading.Thread(target=self.fetch_details, daemon=True).start()
    # ... after your __init__ method ...
    def get_my_tokens(self):
        """
        This function MUST return your visitorData and po_token.
        You need to acquire these values yourself (e.g., from your
        browser's developer tools) and paste them here.
        """
        # --- IMPORTANT: REPLACE THESE PLACEHOLDERS ---
        data={"visitorData":"CgtzSkVEU3A0dy1CbyjIg53IBjIKCgJJThIEGgAgZg%3D%3D","poToken":"MnhYzVhTDMr5h1jxZdzSP3KgDtZ4_-ziEIvt4SWAsfOcM9_SHfcHKm2gnDEyv8BnQ-xFp4TIrh5S5PpsqrzNB6fEMy4T5dAoo9dvvxOu0Ee7ybPcO6-usYaeMkDKlTmRMrC55Wkl3OmJ54oPzSs3YDolgd6F6iUYPg8="}
        my_visitor_data = data["visitorData"]
        my_po_token = data["poToken"]
        return (my_visitor_data, my_po_token)

    def fetch_details(self):
        url = self.url_entry.get().strip()
        if not url: return
        
        self.title_label.configure(text="Fetching details, please wait...")
        self.listbox.delete(0, tkinter.END)
        self.download_button.configure(state="disabled")
        self.quality_menu.configure(state="disabled")
        
        try:
            if "playlist" in url:
                self.is_playlist = True
                playlist = Playlist(url, use_po_token=True, po_token_verifier=self.get_my_tokens)
                if not playlist.videos: 
                    raise ValueError("Playlist is empty or invalid.")
                
                self.title_label.configure(text=f"Playlist: {playlist.title}")
                first_video = playlist.videos[0]
                self.videos_to_download = playlist.videos
                
                for idx, video in enumerate(self.videos_to_download, 1):
                    self.listbox.insert(tkinter.END, f"{idx:02d}. {video.title} - Pending")
            else:
                self.is_playlist = False
                video = YouTube(url, use_po_token=True, po_token_verifier=self.get_my_tokens)
                self.title_label.configure(text=f"Video: {video.title}")
                first_video = video
                self.videos_to_download = [video]
                self.listbox.insert(tkinter.END, f"1. {video.title} - Pending")

            # Load thumbnail
            try:
                response = requests.get(first_video.thumbnail_url)
                img_data = Image.open(BytesIO(response.content))
                thumbnail_img = ctk.CTkImage(img_data, size=(120, 90))
                self.thumbnail_label.configure(image=thumbnail_img)
            except:
                pass  # Keep placeholder if thumbnail fails

            self.video_streams = first_video.streams
            self.update_quality_options(self.mode_var.get())
            self.download_button.configure(state="normal")
            self.quality_menu.configure(state="normal")
            
        except Exception as e:
            self.title_label.configure(text=f"Error: {e}")
            print(e)

    def update_quality_options(self, selected_mode: str):
        if self.video_streams is None:
            self.quality_menu.configure(values=["Fetch URL first"], state="disabled")
            self.quality_var.set("Fetch URL first")
            return

        qualities = []
        if selected_mode == "Audio":
            streams = self.video_streams.filter(only_audio=True).order_by("abr").desc()
            qualities = sorted(list(set([s.abr for s in streams if s.abr])), 
                             key=lambda x: int(re.sub(r'\D', '', x)), reverse=True)
        else:  # Video
            progressive_streams = self.video_streams.filter(progressive=True)
            adaptive_streams = self.video_streams.filter(only_video=True)
            all_resolutions = set()
            
            for stream in list(progressive_streams) + list(adaptive_streams):
                if stream.resolution:
                    all_resolutions.add(stream.resolution)
            
            qualities = sorted(list(all_resolutions), 
                             key=lambda x: int(x[:-1]), reverse=True)
        
        if not qualities: 
            qualities = ["Not Available"]
            
        self.quality_menu.configure(values=qualities)
        self.quality_var.set(qualities[0])
        self.quality_menu.configure(state="normal")

    def choose_dir(self):
        path = filedialog.askdirectory(initialdir=self.download_dir)
        if path:
            self.download_dir = path
            self.dir_label.configure(text=f"Folder: {self.download_dir}")

    def on_progress(self, stream, chunk, bytes_remaining):
        total = stream.filesize
        downloaded = total - bytes_remaining
        percent = downloaded / total
        self.progressbar.set(percent)
        
        try:
            elapsed = time.time() - self.start_time
            speed = downloaded / elapsed if elapsed > 0 else 0
            eta = (total - downloaded) / speed if speed > 0 else 0
            stats_str = f"{downloaded/1e6:.2f}MB / {total/1e6:.2f}MB | Speed: {speed/1e6:.2f} MB/s | ETA: {int(eta)}s"
            self.stats_label.configure(text=stats_str)
        except AttributeError:
            self.stats_label.configure(text=f"{downloaded/1e6:.2f}MB / {total/1e6:.2f}MB")
        
        self.update_idletasks()

    def start_download(self):
        self.download_button.configure(state="disabled")
        self.fetch_button.configure(state="disabled")
        threading.Thread(target=self.download_logic, daemon=True).start()

    def download_logic(self):
        mode = self.mode_var.get()
        quality = self.quality_var.get()
        
        folder_name = self.sanitize(self.title_label.cget("text").replace("Playlist: ", "").replace("Video: ", ""))
        save_path = os.path.join(self.download_dir, folder_name)
        
        if self.is_playlist:
            os.makedirs(save_path, exist_ok=True)
        else:
            save_path = self.download_dir

        for idx, video in enumerate(self.videos_to_download):
            title = self.sanitize(f"{idx+1:02d}. {video.title}")
            
            # Update listbox
            self.listbox.delete(idx)
            self.listbox.insert(idx, f"{title} - Downloading...")
            self.listbox.selection_clear(0, tkinter.END)
            self.listbox.selection_set(idx)
            self.listbox.activate(idx)

            # Reset progress
            self.progressbar.set(0)
            self.stats_label.configure(text="")
            self.start_time = time.time()
            
            # Create YouTube object with progress callback
            yt = YouTube(video.watch_url, on_progress_callback=self.on_progress, use_po_token=True, po_token_verifier=self.get_my_tokens)

            try:
                if mode == "Audio":
                    # Audio download - use original working logic
                    stream = yt.streams.filter(only_audio=True, abr=quality).first()
                    if not stream:
                        stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
                    
                    stream.download(output_path=save_path, filename=f"{title}.mp3")
                    
                else:  # Video download
                    # Try progressive first (single file with audio+video)
                    stream = yt.streams.filter(progressive=True, res=quality).first()
                    
                    if stream:
                        # Progressive stream available - direct download
                        stream.download(output_path=save_path, filename=f"{title}.mp4")
                    else:
                        # Need to merge separate video and audio streams
                        # Using the WORKING logic from your old code
                        self.listbox.delete(idx)
                        self.listbox.insert(idx, f"{title} - Merging files...")
                        self.update_idletasks()
                        
                        # Get video and audio streams (using old code's approach)
                        video_stream = yt.streams.filter(only_video=True, res=quality).order_by("resolution").desc().first()
                        audio_stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
                        
                        if not video_stream or not audio_stream:
                            raise Exception("Required streams not found")
                        
                        # File paths using old code's naming convention
                        vfile = os.path.join(save_path, title + "_v.mp4")
                        afile = os.path.join(save_path, title + "_a.mp4") 
                        merged = os.path.join(save_path, title + ".mp4")
                        
                        # Download separate streams
                        video_stream.download(output_path=save_path, filename=title + "_v.mp4")
                        audio_stream.download(output_path=save_path, filename=title + "_a.mp4")
                        
                        # Merge using ffmpeg (exact same command as old working code)
                        try:
                            subprocess.run([
                                "ffmpeg", "-y", "-i", vfile, "-i", afile, "-c", "copy", merged
                            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                        except subprocess.CalledProcessError as e:
                            raise Exception(f"FFmpeg merging failed: {e}")
                        except FileNotFoundError:
                            raise Exception("FFmpeg not found. Please install FFmpeg and add it to your PATH.")
                        
                        # Clean up temporary files
                        try:
                            os.remove(vfile)
                            os.remove(afile)
                        except:
                            pass  # Continue even if cleanup fails

                # Success
                self.listbox.delete(idx)
                self.listbox.insert(idx, f"{title} - ✔ Completed")
                
            except Exception as e:
                # Error handling
                self.listbox.delete(idx)
                self.listbox.insert(idx, f"{title} - ❌ FAILED")
                print(f"Error downloading {title}: {e}")
                
                # Show error message to user
                self.after(100, lambda err=str(e), t=title: messagebox.showerror(
                    "Download Error",
                    f"Failed to download '{t}'.\n\nError: {err}\n\n"
                    f"For video merging issues, ensure FFmpeg is installed and in your PATH."
                ))

        # All downloads complete
        self.download_button.configure(state="normal")
        self.fetch_button.configure(state="normal")
        self.stats_label.configure(text="✨ All downloads complete!")
        self.progressbar.set(0)


if __name__ == "__main__":
    app = App()
    app.mainloop()