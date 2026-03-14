import os
from typing import List, Dict

import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

from transcription import transcribe_with_whisper


class LLMClient:
    """
    Thin wrapper around a local Ollama model (e.g. llama3.2) using its HTTP API.
    """

    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str, system: str | None = None) -> str:
        """
        Call the Ollama /api/generate endpoint in non-streaming mode and return the response text.
        """
        url = f"{self.base_url}/api/generate"
        payload: Dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        resp = requests.post(url, json=payload, timeout=600)
        resp.raise_for_status()
        data = resp.json()
        # Non-streamed responses contain 'response' with the full text
        return data.get("response", "").strip()


def extract_video_id(youtube_url: str) -> str:
    """
    Extract the video ID from a standard YouTube URL.
    Handles formats like:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    """
    if "youtu.be/" in youtube_url:
        return youtube_url.rsplit("/", 1)[-1].split("?")[0]
    if "watch?v=" in youtube_url:
        return youtube_url.split("watch?v=")[-1].split("&")[0]
    # Fallback: last path segment
    return youtube_url.rstrip("/").rsplit("/", 1)[-1]


def get_transcript(
    video_url: str,
    languages: List[str] | None = None,
    use_cookies: bool = False,
    browser: str | None = None,
) -> str:
    """
    Fetch the YouTube transcript for a video as a single string.
    Strategy:
    1) Try official YouTube transcript API (fast, cheap).
    2) If that fails or is unavailable, fall back to local Whisper transcription
       on the audio, so it still works for long / no-caption videos.
    """
    video_id = extract_video_id(video_url)
    languages = languages or ["en", "en-US", "en-GB"]

    # Step 1: try YouTube transcript API
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        text_chunks = [entry["text"] for entry in transcript if entry.get("text")]
        return "\n".join(text_chunks)
    except (TranscriptsDisabled, AttributeError, Exception):
        # Step 2: fallback to Whisper on audio
        text = transcribe_with_whisper(
            video_url,
            model_name="small",
            use_cookies=use_cookies,
            browser=browser or "chrome",
        )
        return text or ""


class ResearchAgent:
    """
    Agent 1: research the URL and summarize the video.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def summarize_from_transcript(self, transcript: str) -> str:
        prompt = (
            "You are a YouTube research assistant.\n\n"
            "Here is the raw transcript of a video. Your job is to write a clear, structured summary in 3–6 short "
            "paragraphs that explains:\n"
            "- The main topic and goal of the video\n"
            "- The structure (what happens in the beginning, middle, and end)\n"
            "- Who this video is for and what they will learn\n\n"
            "Transcript:\n"
            "--------------------\n"
            f"{transcript}\n"
            "--------------------\n\n"
            "Now write the summary."
        )
        return self.llm.generate(prompt)

    def run(self, video_url: str, use_cookies: bool = False, browser: str | None = None) -> str:
        transcript = get_transcript(video_url, use_cookies=use_cookies, browser=browser)

        if not transcript:
            # Be explicit: without a transcript we cannot truly summarize the content.
            return (
                "I couldn't access a transcript for this video, so I can't reliably summarize the actual spoken "
                "content. This usually means YouTube doesn't expose a transcript for this video or the transcript "
                "API or audio download failed. For protected videos, try downloading the file manually and using "
                "the 'local file' mode in the UI."
            )

        return self.summarize_from_transcript(transcript)


class KeyPointsAgent:
    """
    Agent 2: collect key points and summarize the most important takeaways.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def extract_from_context(self, context: str) -> str:
        prompt = (
            "You are a note-taking assistant.\n\n"
            "From the information below, extract:\n"
            "- 5–10 bullet-point key insights (no fluff)\n"
            "- 3 most important takeaways for a busy viewer\n\n"
            "Format:\n"
            "KEY POINTS:\n"
            "- ...\n"
            "\n"
            "TOP 3 TAKEAWAYS:\n"
            "1. ...\n"
            "2. ...\n"
            "3. ...\n\n"
            "Information:\n"
            "--------------------\n"
            f"{context}\n"
            "--------------------\n"
        )
        return self.llm.generate(prompt)

    def run(
        self,
        video_url: str,
        base_summary: str | None = None,
        use_cookies: bool = False,
        browser: str | None = None,
    ) -> str:
        transcript = get_transcript(video_url, use_cookies=use_cookies, browser=browser)

        context_parts: List[str] = []
        if base_summary:
            context_parts.append("Base summary provided by another agent:\n" + base_summary)
        if transcript:
            context_parts.append("Raw transcript:\n" + transcript)

        context = "\n\n".join(context_parts)
        return self.extract_from_context(context)


class ReelsIdeasAgent:
    """
    Agent 3 (creative): suggest short-form reel ideas based on the video.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def ideas_from_context(self, context: str, key_points: str | None = None) -> str:
        prompt_context = key_points or context or ""
        prompt = (
            "You are a short-form content strategist.\n\n"
            "Using the context below, propose 3–7 high-impact short video (Reels/TikTok/Shorts) ideas.\n"
            "For each idea, provide:\n"
            "- A strong hook line (what the creator says in the first 3 seconds)\n"
            "- A 1–2 sentence description of what happens in the clip\n"
            "- Optional CTA if relevant\n\n"
            "Format exactly as:\n"
            "IDEA 1: <title>\n"
            "Hook: ...\n"
            "Description: ...\n"
            "CTA: ... (optional)\n"
            "\n"
            "IDEA 2: <title>\n"
            "...\n\n"
            "Context:\n"
            "--------------------\n"
            f"{prompt_context}\n"
            "--------------------\n"
        )
        return self.llm.generate(prompt)

    def run(
        self,
        video_url: str,
        key_points: str | None = None,
        use_cookies: bool = False,
        browser: str | None = None,
    ) -> str:
        transcript = get_transcript(video_url, use_cookies=use_cookies, browser=browser)
        return self.ideas_from_context(transcript, key_points=key_points)


def ensure_download_folder(folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    return folder


