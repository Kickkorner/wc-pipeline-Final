"""
Step 1: Generate today's Legendary Moments hype reel concept + Pixar-style scenes.
Uses OpenRouter (free tier) for topic generation, Pollinations for images.
"""

import os
import json
import time
import random
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

WORK = "work"
os.makedirs(WORK, exist_ok=True)

# ---------------------------------------------------------------------------
# Legendary moments bank — used when API is unavailable
# Rotates daily so content stays fresh without needing any API
# ---------------------------------------------------------------------------
MOMENTS_BANK = [
    {
        "title": "Maradona's Hand of God — 1986",
        "year": 1986,
        "beats": [
            "Packed Azteca Stadium under blazing Mexican sun, electric atmosphere, 100,000 fans in vivid animated detail",
            "Dramatic close-up of animated player leaping skyward, fist raised, ball brushing fingertips in slow motion",
            "Animated goalkeeper frozen in disbelief, ball crossing the line, crowd erupting in chaos",
            "Epic wide shot of celebrating players, golden confetti, dramatic sunbeams cutting through stadium smoke",
        ],
    },
    {
        "title": "Zidane's Masterclass Final — 2006",
        "year": 2006,
        "beats": [
            "Berlin Olympic Stadium at night, floodlights blazing, animated crowd a sea of color and noise",
            "Animated Zidane stepping up to the penalty spot, intense close-up, stadium holding its breath",
            "Slow-motion animated Panenka chip, goalkeeper diving wrong way, ball floating in perfect arc",
            "Animated team erupting in celebration, fireworks lighting the Berlin sky, trophy gleaming",
        ],
    },
    {
        "title": "Germany vs Brazil 7-1 — 2014",
        "year": 2014,
        "beats": [
            "Animated Estadio Mineirao at night, electric atmosphere, Brazilian fans waving flags in unison",
            "Rapid-fire animated goal sequence, ball hitting net repeatedly, scoreboard climbing dramatically",
            "Animated Brazilian fans in stunned silence, tears streaming, flags lowered in disbelief",
            "Animated German players raising the trophy in Rio, golden confetti raining over Maracana",
        ],
    },
    {
        "title": "Messi's Final Redemption — 2022",
        "year": 2022,
        "beats": [
            "Animated Lusail Stadium glowing under Qatar night sky, 90,000 fans creating a wall of noise",
            "Dramatic animated Messi in golden kit, eyes locked on goal, defenders frozen in his wake",
            "Slow-motion animated ball curling into top corner, net rippling, crowd erupting in slow-mo",
            "Epic animated Messi lifting the golden trophy, teammates mobbing him, fireworks painting the sky",
        ],
    },
    {
        "title": "France's Comeback Final — 2022",
        "year": 2022,
        "beats": [
            "Animated stadium split in blue and white, tension visible on every animated face in the crowd",
            "Animated Mbappe striking his hat-trick goal, pure power and technique in slow motion",
            "Dramatic animated penalty shootout, goalkeeper diving, nation watching breathlessly",
            "Animated trophy presentation, both teams' emotions raw, confetti in red white and blue",
        ],
    },
    {
        "title": "Italy's Euro Glory — Legends of the Azzurri",
        "year": 2006,
        "beats": [
            "Animated Berlin Olympic Stadium bathed in blue light, Italian fans creating a ocean of color",
            "Animated Materazzi rising to head the equalizer, perfect timing, crowd frozen then exploding",
            "Tense animated penalty shootout sequence, Buffon's saves legendary, hands raised to sky",
            "Animated Cannavaro lifting the World Cup, tears of joy, golden trophy catching stadium light",
        ],
    },
    {
        "title": "Spain's Tiki-Taka Dominance — 2010",
        "year": 2010,
        "beats": [
            "Animated Soccer City Stadium at dusk, vuvuzelas creating visible sound waves in the air",
            "Fluid animated passing sequences, ball moving like liquid through animated defenders",
            "Animated Iniesta's extra-time winner, pure emotion, shirt torn off in celebration",
            "Animated Spanish squad lifting the first ever World Cup, golden trophy, confetti storm",
        ],
    },
]


def get_topic():
    # Rotate through moments bank based on day of year — no API needed
    day_of_year = int(time.strftime("%j"))
    return MOMENTS_BANK[day_of_year % len(MOMENTS_BANK)]


topic = get_topic()
with open(f"{WORK}/topic.json", "w") as f:
    json.dump(topic, f, indent=2)

print("Topic:", topic["title"])


# ---------------------------------------------------------------------------
# Generate Pixar-style cinematic scenes via Pollinations.ai
# Multiple fallback strategies to guarantee output
# ---------------------------------------------------------------------------
def generate_via_pollinations(prompt_text, out_path, seed):
    encoded = requests.utils.quote(prompt_text)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1920&height=1080&nologo=true&seed={seed}&model=flux"
    )
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and len(r.content) > 10000:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                return True
            print(f"Pollinations attempt {attempt} failed: status {r.status_code}")
        except Exception as e:
            print(f"Pollinations attempt {attempt} error:", e)
        time.sleep(5)
    return False


def generate_fallback(idx, out_path):
    """High-quality cinematic gradient fallback with visual interest."""
    W, H = 1920, 1080
    palettes = [
        [(8, 12, 35), (40, 20, 80), (180, 100, 20)],
        [(5, 20, 50), (20, 80, 120), (200, 160, 20)],
        [(30, 5, 5), (120, 20, 20), (220, 140, 0)],
        [(5, 25, 15), (10, 80, 60), (0, 180, 120)],
    ]
    colors = palettes[idx % len(palettes)]

    img = Image.new("RGB", (W, H), colors[0])
    draw = ImageDraw.Draw(img)

    # Gradient layers
    for y in range(H):
        ratio = y / H
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Spotlight circles for cinematic feel
    for _ in range(5):
        cx = random.randint(W // 4, 3 * W // 4)
        cy = random.randint(H // 4, 3 * H // 4)
        for radius in range(300, 0, -20):
            alpha = max(0, int(30 * (1 - radius / 300)))
            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                outline=(*colors[2], alpha),
                width=2,
            )

    img = img.filter(ImageFilter.GaussianBlur(3))
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)
    img.save(out_path, quality=95)


def generate_scene(idx, beat_text):
    style_prompt = (
        f"{beat_text}, "
        "Pixar Disney 3D animation style, epic cinematic movie poster composition, "
        "dramatic volumetric lighting, vibrant saturated colors, "
        "FIFA World Cup football soccer theme, heroic atmosphere, "
        "ultra detailed environment, photorealistic Pixar render, 4K"
    )
    out_path = f"{WORK}/scene_{idx}.png"

    print(f"Generating scene {idx}: {beat_text[:60]}...")

    if generate_via_pollinations(style_prompt, out_path, seed=idx * 42):
        print(f"Scene {idx} generated via Pollinations")
        return

    print(f"Scene {idx}: all APIs failed, using cinematic fallback")
    generate_fallback(idx, out_path)


for i, beat in enumerate(topic["beats"]):
    generate_scene(i, beat)
    time.sleep(3)  # be polite to free APIs

print("Step 1 complete.")
