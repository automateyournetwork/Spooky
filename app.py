import os
import json
import time
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from generate_assets import generate_all_assets
import urllib.parse
import subprocess
import socket

# === 1. Setup ===
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)
ASSETS_DIR = Path("./web/assets/scenes")

st.set_page_config(page_title="AI Adventure Studio", page_icon="🎬", layout="centered")
st.title("🎬 AI Adventure Studio")
st.markdown("Describe your world — Gemini will imagine it, Veo will animate it.")

prompt = st.text_area("🧠 Describe your adventure idea:", height=100,
                      placeholder="Example: A haunted castle by the sea, cursed by a lost alchemist...")

col1, col2 = st.columns(2)
generate_btn = col1.button("✨ Generate Story Scenes")
generate_assets_btn = col2.button("🎥 Generate Assets")

# === 2. Generate Scene JSON ===
if generate_btn and prompt:
    with st.spinner("Gemini is writing your adventure scenes..."):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                f"Create a 5-scene cinematic adventure plan based on this idea: {prompt}. "
                "For each scene, return JSON with fields: id, image_prompt, video_prompt. "
                "Scene IDs should be scene_01_xxx, scene_02_xxx, etc."
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

        try:
            scenes = json.loads(response.text)
            st.session_state["scenes"] = scenes
            st.success("✅ 5 scenes generated successfully!")
            st.json(scenes)
            # Save the generated story JSON for the web frontend
            story_json_path = Path("web/story.json")
            with open(story_json_path, "w", encoding="utf-8") as f:
                json.dump(scenes, f, indent=2)
            st.success(f"📖 Saved story.json to {story_json_path}")            
        except Exception as e:
            st.error(f"Could not parse Gemini output: {e}")
            st.stop()


# === 3. Generate Assets for Scenes ===
if generate_assets_btn:
    if "scenes" not in st.session_state:
        st.warning("Please generate the story scenes first!")
        st.stop()

    scenes = st.session_state["scenes"]
    progress = st.progress(0)
    total = len(scenes)

    for i, scene in enumerate(scenes):
        with st.spinner(f"Generating assets for {scene['id']}..."):
            try:
                generate_all_assets([scene])
            except Exception as e:
                st.error(f"Error on {scene['id']}: {e}")
        progress.progress((i + 1) / total)

    st.success("🎬 All scenes generated! Assets saved in `./web/assets/scenes/`.")
    st.session_state["assets_ready"] = True

def find_free_port(start=8000):
    """Find a free TCP port for the local web server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

# === 4. Explore Adventure ===
if st.session_state.get("assets_ready"):
    st.markdown("### Ready to Explore?")

    port = find_free_port()
    web_dir = Path("web")

    if not web_dir.exists():
        st.error("❌ web/ directory not found.")
    else:
        # Start a lightweight static server in the background
        st.info(f"🌐 Launching adventure server on port {port}...")
        subprocess.Popen(
            ["python3", "-m", "http.server", str(port)],
            cwd=web_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        url = f"http://localhost:{port}"
        st.success(f"🎮 Adventure ready! [Open in new tab ▶️]({url})")
        st.markdown(
            f"""
            <iframe src="{url}" width="100%" height="800" frameborder="0"></iframe>
            """,
            unsafe_allow_html=True
        )