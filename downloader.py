# https://github.com/yt-dlp/yt-dlp

from yt_dlp import YoutubeDL
from playwright.sync_api import sync_playwright

import json
import time

INFO_OUTPUT_FILE = "./output/info.json"

#URLS = ["https://www.youtube.com/watch?v=K0SGh7OtdO4"]
URLS = ["https://www.ceskatelevize.cz/porady/901363-chalupari/275320075140011"]

# Collect .mpd URLs
video_urls = []
with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)  # Headless blocks playback!
    context = browser.new_context()
    page = context.new_page()

    def log_request(req):
        if ".mpd" in req.url:
            print("Found .mpd URL:", req.url)
            video_urls.append(req.url)

    page.on("request", log_request)

    # Go to the page
    page.goto("https://www.ceskatelevize.cz/porady/901363-chalupari/275320075140011")

    # Wait for play button to load and click it
    page.wait_for_selector('[data-testid="PlayIcon"]', timeout=10000)
    page.click('[data-testid="PlayIcon"]')

    # Wait longer for manifest to load
    page.wait_for_timeout(20000)

    if not video_urls:
        print("No .mpd found. Try increasing wait time or checking for .m3u8")

    browser.close()

# The first url is an advertisement video
download_url = video_urls[1]

ydl_opts = {
    "quiet": True,  # suppress download logs
    "skip_download": True,  # don't download anything
    "force_generic_extractor": True,  # use this if the site is not directly supported
}

formats = []
with YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(download_url, download=False)

    formats = info.get("formats", [])

    # Print available resolutions
    print("Available video formats:")
    for f in formats:
        if f.get("vcodec") != "none":  # video-only or audio+video
            print(f"{f['format_id']} - {f['height']}p - {f['ext']} - {f['url']}")


#ytdl_opts = {}
#with YoutubeDL(ytdl_opts) as ydl:
#    info = ydl.extract_info(download_url, download=False)
#    info_pretty = json.dumps(ydl.sanitize_info(info), indent=2)
#
#    with open(INFO_OUTPUT_FILE, "w") as f:
#        f.write(info_pretty)

#with YoutubeDL() as ydl:
#    ydl.download(download_url)
