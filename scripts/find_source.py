"""
Step 1: Decide today's topic and gather source material.
"""

import os
import json
import random
import requests
from PIL import Image, ImageDraw, ImageFilter

WORK = "work"
os.makedirs(WORK, exist_ok=True)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")


def get_topic():
    prompt = (
        "Give me one short, visually striking 'on this day in FIFA World Cup "
        "history' fact (any year, real event). Then give a 4-beat cinematic "
        "shot list (no dialogue, no on-screen text) describing still/slow-motion "
        "visuals that evoke that moment (stadium lights, crowd silhouettes, "
        "trophy close-up, goal celebration silhouette, etc). "
        "Respond ONLY as JSON: "
        '{"title": "...", "year": 1900, "beats": ["...", "...", "...", "..."]}'
    )

    if not GEMINI_KEY:
        return {
            "title": "World Cup Glory",
            "year": 1986,
            "beats": [
                "Empty stadium at dusk, floodlights flickering on",
                "Silhouette of a player striking the ball in slow motion",
                "Close-up of golden trophy under spotlight",
                "Crowd silhouettes celebrating under confetti",
            ],
        }

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
        return {
            "title": "World Cup Glory",
            "year": 1986,
            "beats": [
                "Empty stadium at dusk, floodlights flickering on",
                "Silhouette of a player striking the ball in slow motion",
                "Close-up of golden trophy under spotlight",
                "Crowd silhouettes celebrating under confetti",
            ],
        }
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    text = text.strip().strip("```json").strip("```")
    return json.loads(text)


topic = get_topic()
with open(f"{WORK}/topic.json", "w") as f:
    json.dump(topic, f, indent=2)

print("Topic:", topic["title"])


def try_archive_clip(year):
    try:
        q = f"World Cup {year} highlights"
        url = (
            "https://archive.org/advancedsearch.php"
            f"?q={requests.utils.quote(q)}"
            "&fl[]=identifier&fl[]=mediatype&rows=5&output=json"
        )
        data = requests.get(url, timeout=20).json()
        docs = data.get("response", {}).get("docs", [])
        for d in docs:
            if d.get("mediatype") == "movies":
                identifier = d["identifier"]
                meta = requests.get(
                    f"https://archive.org/metadata/{identifier}", timeout=20
                ).json()
                for file in meta.get("files", []):
                    if file["name"].lower().endswith(".mp4"):
                        clip_url = (
                            f"https://archive.org/download/{identifier}/{file['name']}"
                        )
                        r = requests.get(clip_url, stream=True, timeout=60)
                        if r.status_code == 200:
                            with open(f"{WORK}/clip.mp4", "wb") as out:
                                for chunk in r.iter_content(1 << 16):
                                    out.write(chunk)
                            return True
    except Exception as e:
        print("archive.org lookup failed:", e)
    return False


have_clip = try_archive_clip(topic.get("year", 1986))
print("Found archive.org clip:", have_clip)


def gradient(size, c1, c2):
    img = Image.new("RGB", size, c1)
    top = Image.new("RGB", size, c2)
    mask = Image.linear_gradient("L").resize(size)
    return Image.composite(top, img, mask)


def make_scene(idx, beat_text):
    W, H = 1920, 1080
    palettes = [
        ((10, 15, 40), (60, 20, 90)),
        ((5, 30, 60), (200, 160, 20)),
        ((20, 20, 20), (180, 30, 30)),
        ((10, 40, 30), (40, 120, 90)),
    ]
    c1, c2 = palettes[idx % len(palettes)]
    img = gradient((W, H), c1, c2)

    draw = ImageDraw.Draw(img)
    for i in range(3):
        r = random.randint(150, 400)
        x = random.randint(0, W)
        y = random.randint(0, H)
        draw.ellipse(
            [x - r, y - r, x + r, y + r],
            fill=None,
            outline=(255, 255, 255, 40),
            width=3,
        )

    img = img.filter(ImageFilter.GaussianBlur(2))
    path = f"{WORK}/scene_{idx}.png"
    img.save(path)
    print("Generated", path, "for beat:", beat_text)


if not have_clip:
    for i, beat in enumerate(topic["beats"]):
        make_scene(i, beat)

print("Step 1 complete.")
