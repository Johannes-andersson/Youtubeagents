import tempfile
from pathlib import Path

import streamlit as st

from agents import LLMClient, ResearchAgent, KeyPointsAgent, ReelsIdeasAgent
from transcription import transcribe_local_file


st.set_page_config(
    page_title="YouTube Multi-Agent Toolkit",
    layout="wide",
)

st.title("🎬 YouTube Multi-Agent Toolkit")
st.write(
    "Upload a downloaded video file so three agents (via Ollama) can summarize it, extract key points, "
    "and suggest short-form reel ideas."
)


with st.sidebar:
    st.header("Settings")
    model_name = st.text_input("Ollama model", value="llama3.2")
    whisper_model = st.selectbox(
        "Whisper model (smaller = faster)",
        options=["tiny", "base", "small", "medium"],
        index=2,
    )


st.markdown("### Upload downloaded file and run agents")
uploaded_file = st.file_uploader(
    "Upload a local video file (mp4/mov/mkv/webm)",
    type=["mp4", "mov", "mkv", "webm"],
)
analyze_btn = st.button("Run agents on uploaded file", type="primary")


def run_agents_from_file(file):
    st.session_state["summary"] = ""
    st.session_state["key_points"] = ""
    st.session_state["reels"] = ""
    st.session_state["status"] = ""

    llm = LLMClient(model=model_name)
    research_agent = ResearchAgent(llm)
    keypoints_agent = KeyPointsAgent(llm)
    reels_agent = ReelsIdeasAgent(llm)

    # Save uploaded file to a temporary location
    tmp_dir = tempfile.mkdtemp(prefix="yt_local_")
    tmp_path = Path(tmp_dir) / file.name
    with open(tmp_path, "wb") as f:
        f.write(file.getbuffer())

    with st.spinner("Transcribing local file with Whisper... (this can take a while)"):
        transcript, err = transcribe_local_file(tmp_path, model_name=whisper_model)

    if not transcript:
        st.error("Failed to transcribe the local file.")
        if err:
            st.code(err)
        return

    # Layout: 3 columns for the agent outputs
    col1, col2, col3 = st.columns(3)

    # Agent 1: Research / Summary
    with col1:
        st.subheader("Agent 1: Summary (local file)")
        summary = research_agent.summarize_from_transcript(transcript)
        st.session_state["summary"] = summary
        st.write(summary)

    # Agent 2: Key points
    with col2:
        st.subheader("Agent 2: Key Points (local file)")
        context = "Raw transcript:\n" + transcript
        key_points = keypoints_agent.extract_from_context(context)
        st.session_state["key_points"] = key_points
        st.write(key_points)

    # Agent 3: Reels ideas
    with col3:
        st.subheader("Agent 3: Reels Ideas (local file)")
        reels = reels_agent.ideas_from_context(transcript, key_points=st.session_state["key_points"])
        st.session_state["reels"] = reels
        st.write(reels)

    # Download status panel
    st.markdown("---")
    st.subheader("Status")
    st.info(f"Using uploaded local file: `{tmp_path}`.")
    st.session_state["status"] = f"Using local file at {tmp_path}"


if analyze_btn:
    if uploaded_file is not None:
        run_agents_from_file(uploaded_file)
    else:
        st.warning("Please upload a local video file from your download folder first.")

