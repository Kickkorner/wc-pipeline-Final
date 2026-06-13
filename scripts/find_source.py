"""
Step 1: Decide today's topic and generate animated cinematic scene images (4K-ready).
"""

import os
import json
import requests

WORK = "work"
os.makedirs(WORK, exist_ok=True)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")


def get_topic():
    prompt = (
        "Give me one short, visually striking 'on this day in FIFA World Cup "
        "history' fact (any year, real event). Then give a 4-beat cinematic "
        "shot list (no dialogue, no on-screen text) describing animated, "
        "stylized scenes (think viral animated football highlight style: "
        "dramatic lighting, dynamic poses, vibrant colors, stadium atmosphere). "
        "Respond ONLY as JSON: "
        '{"title": "...", "year": 1900, "beats": ["...", "...", "...", "..."]}'
    )

    if not GEMINI_KEY:
        return default_topic()

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    )
    resp = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30,
    )
    data = resp.json()
    if "candidates" not in data:
        print("Gemini API error response:", data)
        return default_topic()

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    text = text.strip().strip("```json").strip("```")
    try:
        return json.loads(text)
    except Exception as e:
        print("JSON parse error:", e, "raw:", text)
        return default_topic()


def default_topic():
    return {
        "title": "FiFa World Cup Glory",
        "year": 2026,
        "beats": [
            "Animated stadium at dusk, floodlights glowing, vibrant crowd silhouettes",
            "Dynamic animated player mid-strike, dramatic motion lines, golden light",
            "Close-up animated golden trophy gleaming under spotlight, confetti falling",
            "Wide animated celebration scene, players embracing, fireworks in the sky",
        ],
    }


topic = get_topic()
with open(f"{WORK}/topic.json", "w") as f:
    json.dump(topic, f, indent=2)

print("Topic:", topic["title"])


# ---------------------------------------------------------------------------
# Generate animated cinematic scene images via Pollinations.ai (free, no key)
# Requested at high resolution for 4K output downstream.
# ---------------------------------------------------------------------------
def generate_scene(idx, beat_text):
    style_prompt = (
        f"{beat_text}, Pixar style 3D animation, football/soccer theme, "
        "Disney Pixar render, soft cinematic lighting, vibrant colors, "
        "highly detailed character and environment design, ultra detailed, 4k"
    )
    encoded = requests.utils.quote(style_prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1920&height=1080&nologo=true&seed={idx}"
    )
    out_path = f"{WORK}/scene_{idx}.png"
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        print("Generated", out_path)
    except Exception as e:
        print("Image generation failed for scene", idx, ":", e)
        # Create a simple fallback colored image so pipeline doesn't break
        from PIL import Image
        Image.new("RGB", (1920, 1080), (20, 30, 60)).save(out_path)


for i, beat in enumerate(topic["beats"]):
    generate_scene(i, beat)

print("Step 1 complete.")
