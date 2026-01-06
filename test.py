#!/usr/bin/env python3
import argparse
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

def fmt_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}" if h else f"{m:d}:{s:05.2f}"

def get_heatmap(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info.get("heatmap"), info

def most_replayed_points(heatmap: list[dict], top_n: int):
    # heatmap entries look like: {"start_time": <sec>, "end_time": <sec>, "value": <0..1>}
    ranked = sorted(heatmap, key=lambda p: float(p.get("value") or 0.0), reverse=True)
    out = []
    for p in ranked[:top_n]:
        start = float(p["start_time"])
        end = float(p["end_time"])
        value = float(p["value"])
        out.append({
            "start": start,
            "end": end,
            "midpoint": (start + end) / 2.0,
            "value": value,
        })
    return out

def main():
    ap = argparse.ArgumentParser(description="Find most replayed part(s) of a YouTube video using the heatmap.")
    ap.add_argument("video_id", help="YouTube video id (e.g. dQw4w9WgXcQ)")
    ap.add_argument("--top", type=int, default=1, help="How many peaks to return (default: 1)")
    args = ap.parse_args()

    try:
        heatmap, info = get_heatmap(args.video_id)
    except DownloadError as e:
        raise SystemExit(f"yt-dlp failed: {e}") from e

    if not heatmap:
        title = info.get("title") or args.video_id
        raise SystemExit(
            f"No heatmap available for this video ({title}). "
            "YouTube only shows 'Most replayed' for some videos."
        )

    peaks = most_replayed_points(heatmap, args.top)
    title = info.get("title") or args.video_id
    print(f"Title: {title}")
    print(f"Video: https://www.youtube.com/watch?v={args.video_id}\n")

    for i, p in enumerate(peaks, 1):
        print(
            f"#{i}: {fmt_time(p['start'])} – {fmt_time(p['end'])} "
            f"(mid {fmt_time(p['midpoint'])}), value={p['value']:.4f}"
        )
        # Handy deep-link near the peak:
        print(f"    Link: https://www.youtube.com/watch?v={args.video_id}&t={int(p['midpoint'])}s")

if __name__ == "__main__":
    main()
