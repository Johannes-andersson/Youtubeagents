## YouTube Multi‑Agent Toolkit

A local, privacy‑friendly toolkit for analyzing long YouTube videos using multiple cooperating agents powered by a local LLM (Llama 3.2 via Ollama) and Whisper transcription.

You download a video file (MP4/MOV/MKV/WEBM), upload it into the app, and three agents will:

- **Agent 1 – Summary**: Generate a structured summary of the video content.
- **Agent 2 – Key Points**: Extract key insights and top takeaways.
- **Agent 3 – Reels Ideas**: Propose short‑form content ideas (hooks, descriptions, CTAs).

All LLM calls run against your local Ollama model; no video or transcript data is sent to external APIs.

---

### Features

- **Multi‑agent flow**: summary → key points → reels ideas.
- **Local transcription** using Whisper on your machine.
- **Streamlit UI** for easy interaction.
- **CLI pipeline** for terminal usage (optional).

---

### Requirements

- macOS (tested on Apple Silicon, 8 GB RAM).
- Python 3.10+ (your venv already uses 3.13).
- [Ollama](https://ollama.com) installed and running.
- [Homebrew](https://brew.sh) (for `ffmpeg`).
- Disk space for downloaded videos and Whisper model weights.

Python dependencies are listed in `requirements.txt`:

- `yt-dlp`
- `youtube-transcript-api`
- `requests`
- `python-dotenv`
- `streamlit`
- `openai-whisper`
- `certifi`

---

### One‑time setup

1. **Clone / open the project**

```bash
cd "/Users/johan/Documents/Ai Projects/Yotube agents"
```

2. **Create and activate a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate
```

3. **Install Python dependencies**

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. **Install `ffmpeg` for Whisper**

```bash
brew install ffmpeg
```

5. **Install and pull the Ollama model**

- Install Ollama from their website and start the Ollama app.
- Pull the Llama 3.2 model:

```bash
ollama pull llama3.2
```

(You can use another compatible model if you update the default in the code.)

---

### Running the Streamlit app

From the project root, with the virtual environment active:

```bash
cd "/Users/johan/Documents/Ai Projects/Yotube agents"
source .venv/bin/activate

streamlit run streamlit_app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`). Open it in your browser.

---

### Using the app

1. **Download a YouTube video manually**

   - Use any tool or site you prefer (for example, a browser‑based downloader) to save the video as `mp4`, `mov`, `mkv`, or `webm` on your machine.
   - This avoids YouTube’s anti‑bot restrictions and guarantees you have a local file the app can process.

2. **Upload the local file**

   - In the app, use the file uploader:
     - “Upload a local video file (mp4/mov/mkv/webm)”.
   - Optionally choose a Whisper model in the sidebar:
     - `tiny` / `base` for faster, rougher transcripts.
     - `small` (default) for a balance.
     - `medium` for higher quality if your machine can handle it.

3. **Run the agents**

   - Click **“Run agents on uploaded file”**.
   - The app will:
     - Transcribe the file with Whisper.
     - Show:
       - Agent 1: Summary.
       - Agent 2: Key Points.
       - Agent 3: Reels Ideas.
     - Show the path of the temporary file used for transcription.

---

### Command‑line pipeline (optional)

You can also run the pipeline from the terminal using `main.py` with a YouTube URL (for videos that are not heavily protected):

```bash
source .venv/bin/activate
python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

This will:

- Print the summary.
- Print key points and top takeaways.
- Print reel ideas.
- Attempt to download the video into the `downloads` folder.

Note: heavily protected videos (those that ask you to “sign in to confirm you’re not a bot”) may still fail to download; in those cases, use the manual‑download + upload workflow described above.

---

### Troubleshooting

- **Whisper failed to transcribe / SSL certificate errors**

  - Make sure dependencies are installed:

    ```bash
    python -m pip install -r requirements.txt
    ```

  - `transcription.py` sets `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` to the `certifi` CA bundle, which fixes most `CERTIFICATE_VERIFY_FAILED` issues on macOS.

- **“ffmpeg is not installed” or transcription fails immediately**

  - Ensure `ffmpeg` is installed and on your `PATH`:

    ```bash
    brew install ffmpeg
    ```

- **Ollama model not found**

  - Run:

    ```bash
    ollama pull llama3.2
    ```

  - Verify the Ollama app is running.

- **Streamlit upload size limits**

  - By default, Streamlit enforces an upload limit (often 200 MB).
  - If you need larger uploads, you can increase the limit by adding a `.streamlit/config.toml` with `server.maxUploadSize` set appropriately.

---

### Security and ethical use

- This project is for personal learning and portfolio purposes.
- Always respect YouTube’s Terms of Service and copyright law.
- Only download and analyze videos you are allowed to use.
