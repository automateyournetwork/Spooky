// === AUDIO UNLOCK FIX ===
let audioUnlocked = false;
document.body.addEventListener("click", () => {
  if (!audioUnlocked) {
    const dummy = document.createElement("video");
    dummy.muted = false;
    dummy.play().catch(() => {});
    audioUnlocked = true;
    console.log("🔊 Audio context unlocked");
  }
}, { once: true });

// === ELEMENT REFERENCES ===
const video = document.getElementById("scene-video");
const image = document.getElementById("scene-image");
const text = document.getElementById("scene-text");
const choices = document.getElementById("choices-container");
const hint = document.getElementById("click-hint");

let story = {};
let currentSceneId = null;
let videoRevealed = false;

// === LOAD STORY.JSON DYNAMICALLY ===
fetch("story.json")
  .then(r => r.json())
  .then(data => {
    // Convert list → keyed object for easy access
    story = {};
    data.forEach(scene => {
      story[scene.id] = {
        video: `assets/scenes/${scene.id}.mp4`,
        text: scene.image_prompt,  // reuse text for display
        choices: [
          { text: "Next Scene", nextScene: getNextSceneId(scene.id, data) }
        ]
      };
    });
    showScene(data[0].id);
  })
  .catch(err => console.error("Failed to load story.json:", err));

function getNextSceneId(currentId, data) {
  const index = data.findIndex(s => s.id === currentId);
  if (index === -1 || index === data.length - 1) return data[0].id;
  return data[index + 1].id;
}

// === MAIN SCENE LOADER ===
function showScene(id) {
  currentSceneId = id;
  videoRevealed = false;
  const scene = story[id];
  const imagePath = scene.video.replace(".mp4", ".png");

  video.pause();
  video.classList.remove("active");
  video.style.zIndex = 1;
  video.src = "";

  image.src = imagePath;
  image.classList.add("active");
  image.style.zIndex = 2;
  hint.textContent = "🖱️ Click the image to reveal the scene...";
  hint.style.opacity = 1;

  choices.innerHTML = "";
  text.textContent = scene.text;

  image.onclick = revealVideo;
}

function revealVideo() {
  if (videoRevealed) return;
  videoRevealed = true;

  const scene = story[currentSceneId];
  const imagePath = scene.video.replace(".mp4", ".png");
  hint.style.opacity = 0;

  video.src = scene.video;
  video.poster = imagePath;
  video.muted = false;
  video.style.zIndex = 3;

  video.load();
  video.oncanplay = () => {
    image.classList.remove("active");
    video.classList.add("active");
    video.play().catch(err => console.warn("Playback blocked:", err));
  };

  video.onended = () => {
    video.classList.remove("active");
    showChoices();
  };
}

function showChoices() {
  const scene = story[currentSceneId];
  choices.innerHTML = "";
  scene.choices.forEach(choice => {
    const btn = document.createElement("button");
    btn.textContent = choice.text;
    btn.onclick = () => showScene(choice.nextScene);
    choices.appendChild(btn);
  });
  hint.textContent = "🖱️ Choose your next move...";
  hint.style.opacity = 0.8;
}
