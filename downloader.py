import os
from pathlib import Path
from typing import Optional

import yt_dlp


def download_youtube_video(
    url: str,
    output_dir: str = "downloads",
    use_cookies: bool = False,
    browser: str = "chrome",
) -> Optional[Path]:
    """
    Download a YouTube video as an MP4 into output_dir.
    Returns the Path to the downloaded file or None on failure.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Use video title as filename, save as mp4
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    ydl_opts: dict = {
        "outtmpl": output_template,
        "format": "mp4/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "noprogress": True,
    }

    if use_cookies:
        # Use cookies from the specified browser profile to bypass
        # "sign in to confirm you're not a bot" prompts.
        # Requires that you're logged into YouTube in that browser.
        ydl_opts["cookiesfrombrowser"] = (browser,)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Ensure .mp4 extension if merged differently
            path = Path(filename)
            if path.suffix.lower() != ".mp4":
                # yt-dlp sometimes uses other extensions; we leave as-is rather than renaming blindly
                return path
            return path
    except Exception as e:  # noqa: BLE001
        print(f"Error downloading video: {e}")
        return None


