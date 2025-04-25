# https://github.com/yt-dlp/yt-dlp

from yt_dlp import YoutubeDL
import json

INFO_OUTPUT_FILE = "./output/info.json"

URLS = ["https://www.youtube.com/watch?v=K0SGh7OtdO4"]

ytdl_opts = {}
with YoutubeDL(ytdl_opts) as ydl:
    info = ydl.extract_info(URLS[0], download=False)
    info_pretty = json.dumps(ydl.sanitize_info(info), indent=2)

    with open(INFO_OUTPUT_FILE, "w") as f:
        f.write(info_pretty)

#with YoutubeDL() as ydl:
    #ydl.download(URLS)
