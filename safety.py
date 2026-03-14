from dataclasses import dataclass
from typing import Dict, Any, List

import yt_dlp
from yt_dlp.utils import DownloadError


@dataclass
class SafetyResult:
    allowed: bool
    reasons: List[str]
    metadata: Dict[str, Any]


def fetch_video_metadata(url: str) -> Dict[str, Any]:
    """
    Use yt_dlp in 'info' mode (no download) to get video metadata.
    If YouTube requires sign-in / anti-bot, we catch the error and return {}.
    """
    ydl_opts = {
        "quiet": True,
        "noprogress": True,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except DownloadError as e:  # noqa: BLE001
        # Return empty metadata and let the caller decide how to handle it.
        return {}


def basic_safety_check(url: str) -> SafetyResult:
    """
    Perform a minimal "portfolio-friendly" safety check.

    Rules (you can tweak later):
    - Block private / unlisted videos (privacy != 'public')
    - Block age-restricted videos (age_limit and/or 'age_limit' flag)
    - Warn (but allow) if duration > 2h
    - Warn (but allow) if description mentions very sensitive topics (simple keyword scan)
    - If metadata cannot be fetched (e.g. YouTube asks you to sign in),
      block and explain clearly.
    """
    metadata = fetch_video_metadata(url)

    reasons: List[str] = []
    allowed = True

    if not metadata:
        return SafetyResult(
            allowed=False,
            reasons=[
                "Could not fetch video metadata. YouTube is asking for sign-in or blocking automated access. "
                "Try another URL or configure yt-dlp with browser cookies if you really need this video."
            ],
            metadata={},
        )

    privacy_status = metadata.get("privacy_status") or metadata.get("privacy", "")
    if privacy_status and privacy_status != "public":
        allowed = False
        reasons.append(f"Video is not public (privacy status: {privacy_status}).")

    age_limit = metadata.get("age_limit")
    if age_limit and age_limit >= 18:
        allowed = False
        reasons.append("Video is age-restricted (18+).")

    # Soft warnings (do not block)
    duration = metadata.get("duration")
    if duration and duration > 2 * 60 * 60:
        reasons.append("Warning: video is longer than 2 hours, summaries may be less precise.")

    description = (metadata.get("description") or "").lower()
    sensitive_keywords = ["self-harm", "suicide", "extremism", "terrorism"]
    if any(k in description for k in sensitive_keywords):
        reasons.append(
            "Warning: description mentions potentially sensitive topics "
            "(self-harm, extremism, etc.). Review carefully before sharing."
        )

    return SafetyResult(allowed=allowed, reasons=reasons, metadata=metadata)


