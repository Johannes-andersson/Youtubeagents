import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import yt_dlp
import whisper
import certifi


_WHISPER_MODEL: Optional[whisper.Whisper] = None


def _get_whisper_model(model_name: str = "small") -> whisper.Whisper:
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        # Whisper downloads model weights over HTTPS using urllib.
        # On some macOS/proxy setups, the default cert store can fail verification.
        # Point Python at certifi's CA bundle to avoid CERTIFICATE_VERIFY_FAILED.
        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
        os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
        _WHISPER_MODEL = whisper.load_model(model_name)
    return _WHISPER_MODEL


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def download_audio(url: str, use_cookies: bool = False, browser: str = "chrome") -> Optional[Path]:
    """
    Download audio-only for a YouTube video to a temp file and return its path.
    """
    tmp_dir = tempfile.mkdtemp(prefix="yt_audio_")
    output_template = os.path.join(tmp_dir, "%(id)s.%(ext)s")

    ydl_opts: dict = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "noprogress": True,
    }

    if use_cookies:
        # Use cookies from the specified browser profile to get past
        # "sign in to confirm you're not a bot" protections.
        # This requires you to be logged into YouTube in that browser.
        ydl_opts["cookiesfrombrowser"] = (browser,)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return Path(filename)
    except Exception as e:  # noqa: BLE001
        print(f"Error downloading audio for transcription: {e}")
        return None


def transcribe_with_whisper(
    url: str,
    model_name: str = "small",
    use_cookies: bool = False,
    browser: str = "chrome",
) -> str:
    """
    Fallback transcription path using Whisper on the downloaded audio.
    Returns raw transcribed text or empty string on failure.
    """
    audio_path = download_audio(url, use_cookies=use_cookies, browser=browser)
    if not audio_path:
        return ""

    try:
        model = _get_whisper_model(model_name=model_name)
        result = model.transcribe(str(audio_path))
        return result.get("text", "").strip()
    except Exception as e:  # noqa: BLE001
        print(f"Error during Whisper transcription: {e}")
        return ""


def transcribe_local_file(path: str | Path, model_name: str = "small") -> tuple[str, str | None]:
    """
    Transcribe a local video/audio file using Whisper.
    This completely bypasses YouTube/yt-dlp and is ideal when you've already
    downloaded the video to disk via your browser or another tool.
    """
    p = Path(path)
    if not p.exists():
        msg = f"Local file not found: {p}"
        print(msg)
        return "", msg

    if not ffmpeg_available():
        msg = "ffmpeg is not installed or not on PATH. Install it with: brew install ffmpeg"
        print(msg)
        return "", msg

    try:
        model = _get_whisper_model(model_name=model_name)
        result = model.transcribe(str(p))
        return result.get("text", "").strip(), None
    except Exception as e:  # noqa: BLE001
        msg = f"Whisper failed to transcribe this file: {e}"
        print(msg)
        return "", msg


