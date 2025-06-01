# https://github.com/yt-dlp/yt-dlp

from yt_dlp import YoutubeDL
from playwright.sync_api import sync_playwright

from PySide6.QtCore import QObject, QThread, Signal

import logging
import subprocess
import sys
import os

logger = logging.getLogger(__name__)


# Designed by Anthropic Claude AI
class DownloadWorker(QObject):
    progress_update = Signal(int, str)
    status_update = Signal(str)
    download_finished = Signal(str)
    download_error = Signal(str)

    def __init__(self, downloader):
        super().__init__()
        self.downloader = downloader

    def run(self):
        try:
            self.downloader.download_video(
                self.progress_update,
                self.status_update,
                self.download_finished,
                self.download_error,
            )
        except Exception as e:
            self.download_error.emit(f"Unexpected error: {str(e)}")


class Downloader(QObject):
    progress_update = Signal(int, str)
    status_update = Signal(str)
    download_finished = Signal(str)
    download_error = Signal(str)

    def __init__(self, url, download_dir=None):
        super().__init__()

        self.url = url
        self.download_dir = download_dir
        self.supported_websites = [
            "ivysilani",
            "youtube",
        ]
        self.website = self.resolve_website()
        self.debug_info_file = "./output/info.json"
        self.download_thread = None
        self.worker = None

        self.ensure_playwright_firefox_is_installed()

    def ensure_playwright_firefox_is_installed(self):
        try:
            with sync_playwright() as p:
                browser = p.firefox.launch(headless=True)
                browser.close()
        except Exception:
            logging.info("Playwright Firefox ins't installed, installing...")
            self.install_playwright_firefox()

    def install_playwright_firefox(self):
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "playwright",
                    "install",
                    "firefox",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to install Firefox: {e}")
            return False

    def resolve_website(self):
        if "ceskatelevize.cz" in self.url:
            return "ivysilani"
        elif "youtube.com" in self.url:
            return "youtube"
        else:
            logger.error(f"Downloading from {self.url} is not supported.")
            return None

    def get_mpd_from_ivysilani(self):
        video_urls = []
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False)  # Headless blocks playback!
            context = browser.new_context()
            page = context.new_page()

            def log_request(req):
                if ".mpd" in req.url:
                    logger.debug("Found .mpd URL:", req.url)
                    video_urls.append(req.url)

            page.on("request", log_request)
            # Go to the page
            page.goto(self.url)
            # Wait for play button to load and click it
            page.wait_for_selector('[data-testid="PlayIcon"]', timeout=10000)
            page.click('[data-testid="PlayIcon"]')
            # Wait longer for manifest to load
            page.wait_for_timeout(20000)
            if not video_urls:
                logger.debug(
                    "No .mpd found. Try increasing wait time or checking for .m3u8"
                )
            browser.close()

            # The first url is an advertisement video
            try:
                download_url = video_urls[1]
            except IndexError:
                return None

            return download_url

    # # Designed by Anthropic Claude AI
    def progress_hook(self, d):
        if d["status"] == "downloading":
            if "total_bytes" in d and d["total_bytes"]:
                percentage = int((d["downloaded_bytes"] / d["total_bytes"]) * 100)
            elif "total_bytes_estimate" in d and d["total_bytes_estimate"]:
                percentage = int(
                    (d["downloaded_bytes"] / d["total_bytes_estimate"]) * 100
                )
            else:
                if "_percent_str" in d:
                    percent_str = d["_percent_str"].strip()
                    try:
                        percentage = int(float(percent_str.replace("%", "")))
                    except:
                        percentage = 0
                else:
                    percentage = 0

            speed_str = d.get("_speed_str", "")

            self.progress_update.emit(percentage, speed_str)
        elif d["status"] == "finished":
            filename = os.path.basename(d["filename"])
            self.download_finished.emit(filename)

    # # Designed by Anthropic Claude AI
    def start_download(self):
        self.download_thread = QThread()
        self.worker = DownloadWorker(self)
        self.worker.moveToThread(self.download_thread)

        # Connect worker signals to parent signals
        self.worker.progress_update.connect(self.progress_update)
        self.worker.status_update.connect(self.status_update)
        self.worker.download_error.connect(self.download_error)
        self.worker.download_finished.connect(self.download_finished)

        # Connect thread started signal to worker's run method
        self.download_thread.started.connect(self.worker.run)

        # Connect cleanup signals
        self.worker.download_finished.connect(self.download_thread.quit)
        self.worker.download_error.connect(self.download_thread.quit)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        self.download_thread.finished.connect(self.worker.deleteLater)

        self.download_thread.start()

    def download_video(
        self, progress_signal, status_signal, finished_signal, error_signal
    ):
        if self.website == "ivysilani":
            status_signal.emit("Získávám odkaz na video z iVysílání...")
            video_url = self.get_mpd_from_ivysilani()
            if not video_url:
                error_signal.emit("Nepodařilo se získat odkaz na video z iVysílání")
                return
        else:
            video_url = self.url

        if not self.download_dir:
            self.download_dir = os.getcwd()

        if video_url:
            status_signal.emit("Začínám stahování...")
            ytdl_opts = {
                "outtmpl": f"{self.download_dir}/%(title)s.%(ext)s",
                "progress_hooks": [self.progress_hook],
            }
            with YoutubeDL(ytdl_opts) as ydl:
                ydl.download(video_url)
        else:
            logging.error(f"No download url, website: {self.website}")


# downloader = Downloader(
#    #"https://www.ceskatelevize.cz/porady/901363-chalupari/275320075140001/"
#    "https://www.youtube.com/watch?v=K0SGh7OtdO4"
# )
# downloader.download_video()

# ydl_opts = {
#    "quiet": True,  # suppress download logs
#    "skip_download": True,  # don't download anything
#    "force_generic_extractor": True,  # use this if the site is not directly supported
# }
#
# formats = []
# with YoutubeDL(ydl_opts) as ydl:
#    info = ydl.extract_info(download_url, download=False)
#
#    formats = info.get("formats", [])
#
#    # Print available resolutions
#    print("Available video formats:")
#    for f in formats:
#        if f.get("vcodec") != "none":  # video-only or audio+video
#            print(f"{f['format_id']} - {f['height']}p - {f['ext']} - {f['url']}")


# ytdl_opts = {}
# with YoutubeDL(ytdl_opts) as ydl:
#    info = ydl.extract_info(download_url, download=False)
#    info_pretty = json.dumps(ydl.sanitize_info(info), indent=2)
#
#    with open(INFO_OUTPUT_FILE, "w") as f:
#        f.write(info_pretty)
