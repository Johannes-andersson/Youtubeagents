import argparse
from pathlib import Path

from agents import LLMClient, ResearchAgent, KeyPointsAgent, ReelsIdeasAgent
from downloader import download_youtube_video


def run_pipeline(
    url: str,
    model: str = "llama3.2",
    download_folder: str = "downloads",
    use_cookies: bool = False,
    browser: str = "chrome",
) -> None:
    """
    Orchestrate all three agents + downloader for a single YouTube URL.
    """
    llm = LLMClient(model=model)

    research_agent = ResearchAgent(llm)
    keypoints_agent = KeyPointsAgent(llm)
    reels_agent = ReelsIdeasAgent(llm)

    print("\n=== Agent 1: Research & Summary ===")
    base_summary = research_agent.run(url, use_cookies=use_cookies, browser=browser)
    print(base_summary)

    print("\n=== Agent 2: Key Points & Takeaways ===")
    key_points = keypoints_agent.run(
        url,
        base_summary=base_summary,
        use_cookies=use_cookies,
        browser=browser,
    )
    print(key_points)

    print("\n=== Agent 3: Reels Ideas ===")
    reels_ideas = reels_agent.run(
        url,
        key_points=key_points,
        use_cookies=use_cookies,
        browser=browser,
    )
    print(reels_ideas)

    print("\n=== Downloading Video ===")
    video_path: Path | None = download_youtube_video(
        url,
        output_dir=download_folder,
        use_cookies=use_cookies,
        browser=browser,
    )
    if video_path:
        print(f"Video downloaded to: {video_path}")
    else:
        print("Failed to download video.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-agent YouTube toolkit: summarize, extract key points, download, and suggest reels."
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--model",
        default="llama3.2",
        help="Ollama model name to use (default: llama3.2)",
    )
    parser.add_argument(
        "--download-folder",
        default="downloads",
        help="Folder to save downloaded videos (default: downloads)",
    )
    parser.add_argument(
        "--use-cookies",
        action="store_true",
        help="Use browser cookies for YouTube (requires logged-in browser).",
    )
    parser.add_argument(
        "--browser",
        default="chrome",
        help="Browser to read cookies from when --use-cookies is set "
        "(e.g. chrome, safari, firefox). Default: chrome.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        url=args.url,
        model=args.model,
        download_folder=args.download_folder,
        use_cookies=args.use_cookies,
        browser=args.browser,
    )

