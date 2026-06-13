"""
Step 1: Generate today's "Legendary Moments" hype reel concept + 4K Pixar-style scenes.
"""

import os
import json
import time
import requests

WORK = "work"
os.makedirs(WORK, exist_ok=True)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
HF_TOKEN = os.environ.get("HF_TOKEN")


def get_topic():
    prompt = (
        "Create a concept for a DRAMATIC, HYPE 'Legendary World Cup Moments' "
        "animated reel — think movie-trailer energy, slow-motion glory, epic "
        "comebacks, iconic goals, trophy lifts (any era, real or iconic in spirit). "
        "Give a punchy title and a 4-beat shot list for an EPIC animated hype "
        "trailer (no dialogue, no on-screen text): each beat should be a vivid, "
        "dramatic visual moment (rising action -> climax -> triumph -> celebration). "
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
        url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30
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
        "title": "Legendary Moments: Glory Awaits",
        "year": 1986,
        "beats": [
            "Tense animated stadium under stormy dusk sky, player silhouette walking toward the pitch, dramatic backlighting",
            "Explosive animated moment of a player striking the ball mid-air, motion lines, intense crowd reaction, golden hour glow",
            "Slow-motion animated ball entering the goal net, net rippling, stadium lights flaring, time freeze effect",
            "Epic animated celebration, teammates leaping in joy, fireworks and confetti exploding over a packed stadium",
        ],
    }


topic = get_topic()
with open(f"{WORK}/topic.json", "w") as f:
    json.dump(topic, f, indent=2)

print("Topic:", topic["title"])


# ---------------------------------------------------------------------------
# Generate Pixar-style hype scenes via Hugging Face Inference API (SDXL)
# Falls back to Pollinations, then a solid color, if HF fails.
# ---------------------------------------------------------------------------
HF_MODEL_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"


def generate_via_hf(prompt_text, out_path):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt_text, "options": {"wait_for_model": True}}
    for attempt in range(3):
        r = requests.post(HF_MODEL_URL, headers=headers, json=payload, timeout=180)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            with open(out_path, "wb") as f:
                f.write(r.content)
            return True
        print("HF attempt", attempt, "failed:", r.status_code, r.text[:200])
        time.sleep(10)
    return False


def generate_via_pollinations(prompt_text, out_path, seed):
    encoded = requests.utils.quote(prompt_text)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1920&height=1080&nologo=true&seed={seed}"
    )
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)


def generate_scene(idx, beat_text):
    style_prompt = (
        f"{beat_text}, Pixar style 3D animation, Disney Pixar render, "
        "epic movie trailer composition, dramatic cinematic lighting, "
        "vibrant saturated colors, highly detailed, 8k, hyper-detailed render"
    )
    out_path = f"{WORK}/scene_{idx}.png"

    if HF_TOKEN and generate_via_hf(style_prompt, out_path):
        print("Generated via HF:", out_path)
        return

    try:
        generate_via_pollinations(style_prompt, out_path, idx)
        print("Generated via Pollinations:", out_path)
    except Exception as e:
        print("All image generation failed for scene", idx, ":", e)
        from PIL import Image
        Image.new("RGB", (1920, 1080), (20, 30, 60)).save(out_path)


for i, beat in enumerate(topic["beats"]):
    generate_scene(i, beat)

print("Step 1 complete.")
