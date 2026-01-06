from __future__ import annotations

from pathlib import Path
from yt_dlp import YoutubeDL  # pip install yt-dlp


def download_youtube_subtitle_files(
    video_id: str,
    out_dir: str | Path = ".",
    lang_regex: str = "en.*",
    also_auto: bool = True,
    convert_to_srt: bool = False,
) -> dict:
    """
    Downloads subtitle files for a YouTube video WITHOUT downloading the video.
    Saves into out_dir using yt-dlp output template.

    lang_regex examples:
      - "en"     (English)
      - "en.*"   (English variants like en-US) :contentReference[oaicite:6]{index=6}
      - "all,-live_chat" (all except live_chat) :contentReference[oaicite:7]{index=7}
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "skip_download": True,          # don't download video
        "writesubtitles": True,         # like --write-subs :contentReference[oaicite:8]{index=8}
        "writeautomaticsub": bool(also_auto),  # like --write-auto-subs :contentReference[oaicite:9]{index=9}
        "subtitleslangs": [lang_regex], # like --sub-langs :contentReference[oaicite:10]{index=10}
        "subtitlesformat": "best",      # like --sub-format :contentReference[oaicite:11]{index=11}
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        "quiet": True,
    }

    if convert_to_srt:
        # Equivalent to --convert-subs srt (requires ffmpeg in PATH) :contentReference[oaicite:12]{index=12}
        ydl_opts["convertsubtitles"] = "srt"

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)  # will write subs to disk
        return info


if __name__ == "__main__":
    info = download_youtube_subtitle_files(
        video_id="5W5md0Vq8hg",
        out_dir="subs",
        lang_regex="en.*",
        also_auto=True,
        convert_to_srt=True,
    )
    print("Done. Title:", info.get("title"))
