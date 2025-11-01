import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from PIL import Image
from io import BytesIO

# === 1) Load environment ===
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in .env")

client = genai.Client(api_key=API_KEY)
OUTPUT_DIR = Path("./web/assets/scenes")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# === 2) Generate a single image ===
def generate_image(scene_id: str, prompt: str) -> Path:
    print(f"[gemini] Generating image for {scene_id} …")
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt],
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
            img_path = OUTPUT_DIR / f"{scene_id}.png"
            image.save(img_path)
            print(f"✅ Saved image: {img_path}")
            return img_path

    raise RuntimeError(f"No image data returned for {scene_id}")


# === 3) Generate a single video ===
def generate_video(scene_id: str, prompt: str, image_path: Path) -> Path:
    print(f"[veo3] Generating animation for {scene_id} …")
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=f"{prompt}. Use {image_path} as visual reference.",
    )

    while not operation.done:
        print("  ⏳ Waiting for video generation to complete…")
        time.sleep(15)
        operation = client.operations.get(operation)

    generated_video = operation.response.generated_videos[0]
    client.files.download(file=generated_video.video)

    video_path = OUTPUT_DIR / f"{scene_id}.mp4"
    generated_video.video.save(video_path)
    print(f"  ✅ Saved video to {video_path}")
    return video_path


# === 4) High-level helper ===
def generate_all_assets(scenes):
    for scene in scenes:
        try:
            img = generate_image(scene["id"], scene["image_prompt"])
            generate_video(scene["id"], scene["video_prompt"], img)
        except Exception as e:
            print(f"❌ Error on {scene['id']}: {e}")

    print("\n🎬 All assets ready in .web/assets/scenes/")
    return OUTPUT_DIR


if __name__ == "__main__":
    # Example: run manually
    from example_scenes import SCENES  # optional import if you keep sample data elsewhere
    generate_all_assets(SCENES)
