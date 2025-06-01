# https://github.com/yt-dlp/yt-dlp

from yt_dlp import YoutubeDL
from playwright.sync_api import sync_playwright

import logging
import subprocess
import sys
import os

logger = logging.getLogger(__name__)


class Downloader:
    def __init__(self, url, download_dir=None):
        self.url = url
        self.download_dir = download_dir
        self.supported_websites = [
            "ivysilani",
            "youtube",
        ]
        self.website = self.resolve_website()
        self.debug_info_file = "./output/info.json"

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

    def download_video(self):
        if self.website == "ivysilani":
            video_url = self.get_mpd_from_ivysilani()
        else:
            video_url = self.url

        if not self.download_dir:
            self.download_dir = os.getcwd()

        if video_url:
            ytdl_opts = {"outtmpl": f"{self.download_dir}/%(title)s.%(ext)s"}
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
