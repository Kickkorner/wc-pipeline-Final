"""
Step 1: Generate cinematic World Cup scenes — pure Python, no external APIs.
7 legendary moment scripts rotate daily. 4 scenes per video, all rendered
locally with rich stadium/player/trophy/crowd illustrations.
"""

import os, json, time, random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

WORK = "work"
os.makedirs(WORK, exist_ok=True)
W, H = 1920, 1080

# ---------------------------------------------------------------------------
# Legendary moments bank — rotates daily, no API needed
# ---------------------------------------------------------------------------
MOMENTS_BANK = [
    {
        "title": "Maradona's Hand of God — 1986",
        "year": 1986,
        "palette": "sunset",
        "beats": ["stadium_dusk", "strike", "goal", "celebration"],
    },
    {
        "title": "Zidane's Panenka Masterclass — 2006",
        "year": 2006,
        "palette": "night",
        "beats": ["stadium_night", "penalty", "goal", "celebration"],
    },
    {
        "title": "Germany 7 - Brazil 1 — 2014",
        "year": 2014,
        "palette": "electric",
        "beats": ["stadium_night", "strike", "goal", "crowd_shock"],
    },
    {
        "title": "Messi's Final Redemption — 2022",
        "year": 2022,
        "palette": "golden",
        "beats": ["stadium_dusk", "strike", "goal", "celebration"],
    },
    {
        "title": "France's Comeback — 2022",
        "year": 2022,
        "palette": "night",
        "beats": ["stadium_night", "penalty", "goal", "celebration"],
    },
    {
        "title": "Italy World Cup Glory — 2006",
        "year": 2006,
        "palette": "sunset",
        "beats": ["stadium_dusk", "leap", "goal", "celebration"],
    },
    {
        "title": "Spain's Tiki-Taka Triumph — 2010",
        "year": 2010,
        "palette": "golden",
        "beats": ["stadium_night", "strike", "goal", "celebration"],
    },
]

PALETTES = {
    "sunset":   {"sky1":(8,12,45),   "sky2":(180,80,20),  "pitch":(15,60,25),  "accent":(255,160,30)},
    "night":    {"sky1":(5,5,20),    "sky2":(20,15,60),   "pitch":(10,50,20),  "accent":(100,150,255)},
    "electric": {"sky1":(5,20,50),   "sky2":(10,60,120),  "pitch":(10,55,22),  "accent":(0,200,255)},
    "golden":   {"sky1":(10,8,30),   "sky2":(80,40,10),   "pitch":(15,65,25),  "accent":(255,200,50)},
}

# ---------------------------------------------------------------------------
# Core drawing helpers
# ---------------------------------------------------------------------------
def linear_gradient_arr(c1, c2, size):
    W2, H2 = size
    arr = np.zeros((H2, W2, 3), dtype=np.float32)
    for y in range(H2):
        t = y / H2
        for c in range(3):
            arr[y,:,c] = c1[c]*(1-t) + c2[c]*t
    return arr

def arr_to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def add_noise(arr, strength=6):
    return np.clip(arr + np.random.normal(0, strength, arr.shape), 0, 255)

def add_spotlight(arr, cx, cy, radius, color, intensity=1.0):
    Y2, X2 = np.mgrid[0:arr.shape[0], 0:arr.shape[1]]
    dist = np.sqrt((X2-cx)**2 + (Y2-cy)**2)
    glow = np.clip(1 - dist/radius, 0, 1)**0.6 * intensity
    for c_idx, col in enumerate(color):
        arr[:,:,c_idx] = np.clip(arr[:,:,c_idx] + glow * col, 0, 255)
    return arr

def draw_stars(draw, W2, H2, count=300):
    for _ in range(count):
        x = random.randint(0, W2)
        y = random.randint(0, H2//2)
        r = random.randint(1, 3)
        alpha = random.randint(100, 220)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(255,255,255,alpha))

def draw_stadium_walls(draw, W2, H2, color):
    ground_y = int(H2*0.78)
    draw.rectangle([0, ground_y, W2, H2], fill=(*color,255))
    for side, direction in [(0.07, 1), (0.93, -1)]:
        x = int(W2*side)
        w = int(W2*0.07)
        pts = [
            (x - w*direction, H2),
            (x - int(w*0.3)*direction, ground_y - int(H2*0.14)),
            (x + int(w*0.3)*direction, ground_y - int(H2*0.14)),
            (x + w*direction, H2),
        ]
        draw.polygon(pts, fill=(*color,255))

def draw_floodlights(draw, W2, H2, color, beam_color):
    for pole_x in [int(W2*0.1), int(W2*0.9)]:
        pole_y = int(H2*0.33)
        draw.rectangle([pole_x-5, pole_y, pole_x+5, int(H2*0.78)], fill=(*color,220))
        # Crossbar
        draw.rectangle([pole_x-25, pole_y-8, pole_x+25, pole_y+8], fill=(*color,220))
        draw.ellipse([pole_x-18, pole_y-18, pole_x+18, pole_y+18], fill=(*color,255))
        # Beams
        for angle in range(-35, 40, 12):
            rad = math.radians(90 + angle)
            ex = pole_x + int(math.cos(rad) * W2 * 0.7)
            ey = pole_y + int(math.sin(rad) * H2)
            for w in range(3, 0, -1):
                draw.line([pole_x, pole_y, ex, ey], fill=(*beam_color, 12*w), width=w*5)

def draw_crowd(draw, W2, H2, base_color, y_start, rows=4, colors=None):
    crowd_colors = colors or [base_color]
    for row in range(rows):
        y = y_start + row * 20
        for x in range(0, W2, 20):
            jx = x + random.randint(-4, 4)
            jy = y + random.randint(-3, 3)
            hh = random.randint(14, 22)
            wh = random.randint(10, 16)
            alpha = max(60, 200 - row*35)
            c = random.choice(crowd_colors)
            draw.ellipse([jx, jy-hh, jx+wh, jy], fill=(*c, alpha))
            draw.rectangle([jx-2, jy, jx+wh+2, jy+10], fill=(*c, alpha-20))

def draw_pitch(draw, W2, H2, color):
    gy = int(H2*0.75)
    draw.rectangle([0, gy, W2, H2], fill=(*color, 255))
    # Stripe effect
    for i in range(0, W2, 80):
        alpha = 15 if (i//80) % 2 == 0 else 0
        draw.rectangle([i, gy, i+80, H2], fill=(255,255,255,alpha))
    # Center circle
    cx, cy2 = W2//2, H2
    draw.ellipse([cx-350, cy2-350, cx+350, cy2+350], outline=(255,255,255,60), width=3)
    # Center line
    draw.line([W2//2, gy, W2//2, H2], fill=(255,255,255,40), width=3)

def draw_player(draw, cx, cy, scale, body_color, pose="strike"):
    s = scale
    c = (*body_color, 255)

    def head(ox=0, oy=0):
        draw.ellipse([cx+ox-int(11*s), cy+oy-int(52*s), cx+ox+int(11*s), cy+oy-int(30*s)], fill=c)
    def torso(ox=0, oy=0):
        draw.rounded_rectangle([cx+ox-int(9*s), cy+oy-int(30*s), cx+ox+int(9*s), cy+oy+int(10*s)],
                               radius=int(4*s), fill=c)
    def limb(x1,y1,x2,y2,w=6):
        draw.line([int(cx+x1*s),int(cy+y1*s),int(cx+x2*s),int(cy+y2*s)],
                  fill=c, width=max(3,int(w*s)))

    if pose == "strike":
        head(); torso()
        limb(0,-20, 32,-48, 7)   # right arm flung back
        limb(0,-20,-18,-5, 7)    # left arm
        limb(0, 10,-14, 42, 8)   # left leg planted
        limb(0, 10, 38, 28, 8)   # right leg kicking
    elif pose == "celebrate":
        head(); torso()
        limb(0,-25,-38,-52, 7)   # left arm raised
        limb(0,-25, 38,-52, 7)   # right arm raised
        limb(0,  10,-13, 42, 8)
        limb(0,  10, 13, 42, 8)
    elif pose == "leap":
        head(); torso()
        limb(0,-22,-32,-42, 7)
        limb(0,-22, 26,-12, 7)
        limb(0,  8,-26, 32, 8)
        limb(0,  8, 22, 34, 8)
    elif pose == "penalty":
        head(); torso()
        limb(0,-20, 25,-44, 7)
        limb(0,-20,-15,-4, 7)
        limb(0, 10,-12, 42, 8)
        limb(0, 10, 42, 22, 8)   # leg swinging through

def draw_goal_post(draw, W2, H2):
    gx1, gx2 = W2//2-270, W2//2+270
    gy1, gy2 = int(H2*0.22), int(H2*0.62)
    white = (240, 240, 240, 255)
    draw.rectangle([gx1-9, gy1, gx1+9, gy2], fill=white)
    draw.rectangle([gx2-9, gy1, gx2+9, gy2], fill=white)
    draw.rectangle([gx1, gy1-9, gx2, gy1+9], fill=white)
    # Net
    for x in range(gx1+10, gx2, 28):
        draw.line([x, gy1+10, x, gy2], fill=(200,200,200,50), width=1)
    for y2 in range(gy1+10, gy2, 24):
        draw.line([gx1+10, y2, gx2, y2], fill=(200,200,200,50), width=1)
    return gx1, gx2, gy1, gy2

def draw_ball(draw, cx, cy, r, white=True):
    fill = (245,245,245,255) if white else (30,30,30,255)
    panel = (30,30,30,200) if white else (245,245,245,200)
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=fill)
    for i in range(5):
        a = math.radians(i*72-90)
        px = cx + int(r*0.42*math.cos(a))
        py = cy + int(r*0.42*math.sin(a))
        pr = int(r*0.18)
        draw.ellipse([px-pr, py-pr, px+pr, py+pr], fill=panel)

def draw_trophy(draw, cx, cy, s):
    gold = (220, 170, 20, 255)
    shine = (255, 240, 140, 140)
    dark_gold = (160, 120, 10, 255)
    # Bowl
    bowl = [(cx-int(32*s), cy-int(42*s)), (cx+int(32*s), cy-int(42*s)),
            (cx+int(22*s), cy+int(2*s)),  (cx-int(22*s), cy+int(2*s))]
    draw.polygon(bowl, fill=gold)
    draw.polygon(bowl, outline=dark_gold, width=2)
    # Handles
    draw.arc([cx-int(55*s), cy-int(42*s), cx-int(18*s), cy-int(5*s)], 195, 345, fill=gold, width=int(7*s))
    draw.arc([cx+int(18*s), cy-int(42*s), cx+int(55*s), cy-int(5*s)], 195, 345, fill=gold, width=int(7*s))
    # Stem + base
    draw.rectangle([cx-int(9*s), cy+int(2*s), cx+int(9*s), cy+int(32*s)], fill=gold)
    draw.rounded_rectangle([cx-int(28*s), cy+int(32*s), cx+int(28*s), cy+int(43*s)],
                           radius=int(4*s), fill=gold)
    # Shine
    draw.ellipse([cx-int(12*s), cy-int(40*s), cx+int(6*s), cy-int(20*s)], fill=shine)

def draw_confetti(draw, W2, H2, colors, count=300):
    for _ in range(count):
        x = random.randint(0, W2)
        y = random.randint(0, int(H2*0.75))
        c = random.choice(colors)
        size = random.randint(5, 14)
        angle = random.randint(0, 30)
        draw.rectangle([x, y, x+size, y+int(size*0.5)], fill=(*c, random.randint(160,230)))

def draw_fireworks(draw, W2, H2, colors, count=10):
    for _ in range(count):
        cx2 = random.randint(W2//5, 4*W2//5)
        cy2 = random.randint(int(H2*0.05), int(H2*0.35))
        c = random.choice(colors)
        for a in range(0, 360, 18):
            rad = math.radians(a)
            length = random.randint(35, 85)
            ex = cx2 + int(math.cos(rad)*length)
            ey = cy2 + int(math.sin(rad)*length)
            draw.line([cx2, cy2, ex, ey], fill=(*c, random.randint(160,255)), width=2)
        draw.ellipse([cx2-7, cy2-7, cx2+7, cy2+7], fill=(*c, 255))

# ---------------------------------------------------------------------------
# Scene generators — 5 unique scene types
# ---------------------------------------------------------------------------
def scene_stadium_dusk(pal):
    arr = linear_gradient_arr(pal["sky1"], pal["sky2"], (W, H))
    arr = add_spotlight(arr, W//2, 0, H*0.9, [80, 50, 10], 0.6)
    arr = add_noise(arr, 5)
    img = arr_to_img(arr)
    draw = ImageDraw.Draw(img, 'RGBA')
    draw_stars(draw, W, H, 150)
    draw_floodlights(draw, W, H, (255,240,180), (255,220,100))
    draw_stadium_walls(draw, W, H, (10, 7, 25))
    crowd_c = [(220,50,50),(50,100,220),(255,200,0),(255,255,255),(0,180,80)]
    draw_crowd(draw, W, H, (20,15,40), int(H*0.57), rows=5, colors=crowd_c)
    draw_pitch(draw, W, H, (15,55,22))
    for r in range(350, 0, -40):
        draw.ellipse([W//2-r, H//2-r, W//2+r, H//2+r], fill=(255,210,80,int(15*(1-r/350))+2))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    return ImageEnhance.Contrast(img).enhance(1.18)

def scene_stadium_night(pal):
    arr = linear_gradient_arr(pal["sky1"], (pal["sky1"][0]+15, pal["sky1"][1]+10, pal["sky1"][2]+40), (W, H))
    arr = add_noise(arr, 4)
    img = arr_to_img(arr)
    draw = ImageDraw.Draw(img, 'RGBA')
    draw_stars(draw, W, H, 400)
    draw_floodlights(draw, W, H, (240,230,170), (255,220,80))
    draw_stadium_walls(draw, W, H, (8,5,20))
    crowd_c = [(220,50,50),(50,100,220),(255,200,0),(255,255,255),(0,180,80),(200,50,200)]
    draw_crowd(draw, W, H, (15,10,30), int(H*0.56), rows=5, colors=crowd_c)
    draw_pitch(draw, W, H, (12,50,18))
    img = img.filter(ImageFilter.GaussianBlur(1.0))
    return ImageEnhance.Contrast(img).enhance(1.2)

def scene_strike(pal):
    arr = linear_gradient_arr(pal["sky1"], (pal["sky1"][0]+25, pal["sky1"][1]+15, pal["sky1"][2]+50), (W, H))
    arr = add_spotlight(arr, W//2, 0, H*0.95, [pal["accent"][0]*0.5, pal["accent"][1]*0.4, pal["accent"][2]*0.1], 0.9)
    arr = add_noise(arr, 5)
    img = arr_to_img(arr)
    draw = ImageDraw.Draw(img, 'RGBA')
    draw_crowd(draw, W, H, (15,10,30), int(H*0.6), rows=3)
    draw_pitch(draw, W, H, pal["pitch"])
    # Motion lines
    for _ in range(25):
        y2 = random.randint(int(H*0.15), int(H*0.65))
        x1 = random.randint(0, W//3)
        length = random.randint(70,200)
        draw.line([x1, y2, x1+length, y2], fill=(*pal["accent"], random.randint(30,90)), width=2)
    # Players
    draw_player(draw, W//2, int(H*0.67), 2.3, (35,22,65), "strike")
    draw_player(draw, W//3-30, int(H*0.69), 1.4, (22,14,48), "leap")
    draw_player(draw, 2*W//3+20, int(H*0.69), 1.3, (22,14,48), "leap")
    # Ball + impact
    bx, by = int(W*0.61), int(H*0.5)
    for i in range(5,0,-1):
        draw.ellipse([bx-i*7-26,by-i*5-26,bx-i*7+26,by-i*5+26], fill=(255,255,255,25))
    draw_ball(draw, bx, by, 30)
    for r in range(110,0,-22):
        draw.ellipse([bx-r,by-r,bx+r,by+r], fill=(*pal["accent"], int(35*(1-r/110))))
    img = img.filter(ImageFilter.GaussianBlur(1.1))
    return ImageEnhance.Contrast(img).enhance(1.22)

def scene_penalty(pal):
    arr = linear_gradient_arr(pal["sky1"], pal["sky2"], (W, H))
    arr = add_spotlight(arr, W//2, H//2, H*0.7, [60,60,80], 0.5)
    arr = add_noise(arr, 5)
    img = arr_to_img(arr)
    draw = ImageDraw.Draw(img, 'RGBA')
    draw_stars(draw, W, H, 200)
    draw_goal_post(draw, W, H)
    draw_crowd(draw, W, H, (12,8,28), int(H*0.65), rows=4,
               colors=[(220,50,50),(50,100,220),(255,200,0),(255,255,255)])
    draw_pitch(draw, W, H, pal["pitch"])
    # Penalty spot + taker
    draw.ellipse([W//2-6, int(H*0.88)-6, W//2+6, int(H*0.88)+6], fill=(255,255,255,200))
    draw_player(draw, W//2, int(H*0.82), 2.0, (35,22,65), "penalty")
    draw_ball(draw, W//2+10, int(H*0.875), 22)
    # Goalkeeper
    draw_player(draw, W//2-40, int(H*0.52), 1.6, (200,80,20), "leap")
    img = img.filter(ImageFilter.GaussianBlur(1.0))
    return ImageEnhance.Contrast(img).enhance(1.2)

def scene_goal(pal):
    arr = linear_gradient_arr((5,15,60), (15,55,110), (W, H))
    arr = add_spotlight(arr, W//2, H//2, H*0.55, [150,150,160], 1.2)
    arr = add_noise(arr, 4)
    img = arr_to_img(arr)
    draw = ImageDraw.Draw(img, 'RGBA')
    gx1, gx2, gy1, gy2 = draw_goal_post(draw, W, H)
    # Ball in top corner with ripple
    bx, by2 = int(W//2+100), int(H*0.3)
    for r in range(20,200,28):
        draw.ellipse([bx-r,by2-r,bx+r,by2+r], outline=(255,255,255,max(0,70-r//3)), width=2)
    draw_ball(draw, bx, by2, 34)
    # Goal flash
    for r in range(200,0,-30):
        draw.ellipse([bx-r,by2-r,bx+r,by2+r], fill=(255,255,200,int(20*(1-r/200))))
    draw_crowd(draw, W, H, (15,10,35), int(H*0.67), rows=4,
               colors=[(220,50,50),(50,100,220),(255,200,0),(255,255,255)])
    # Goalkeeper diving
    draw_player(draw, gx1+80, int(H*0.56), 1.5, (200,50,50), "leap")
    # Net ripple lines
    for r in range(15, 120, 22):
        draw.ellipse([bx-r,by2-r,bx+r,by2+r], outline=(200,200,255,40), width=1)
    img = img.filter(ImageFilter.GaussianBlur(0.9))
    return ImageEnhance.Contrast(img).enhance(1.25)

def scene_crowd_shock(pal):
    arr = linear_gradient_arr(pal["sky1"], pal["sky2"], (W, H))
    arr = add_noise(arr, 5)
    img = arr_to_img(arr)
    draw = ImageDraw.Draw(img, 'RGBA')
    draw_stars(draw, W, H, 200)
    draw_stadium_walls(draw, W, H, (10,7,25))
    # Large shocked crowd — muted colors, heads in hands
    draw_crowd(draw, W, H, (20,15,40), int(H*0.5), rows=7,
               colors=[(60,40,80),(50,35,70),(40,30,65),(55,40,75)])
    draw_pitch(draw, W, H, pal["pitch"])
    # Scoreboard glow at top center
    sb_x, sb_y = W//2, int(H*0.15)
    draw.rounded_rectangle([sb_x-200, sb_y-50, sb_x+200, sb_y+50],
                           radius=12, fill=(20,20,40,220))
    draw.rounded_rectangle([sb_x-198, sb_y-48, sb_x+198, sb_y+48],
                           radius=10, outline=(100,100,180,200), width=2)
    for r in range(250,0,-30):
        draw.ellipse([sb_x-r,sb_y-r,sb_x+r,sb_y+r], fill=(80,100,200,int(12*(1-r/250))))
    img = img.filter(ImageFilter.GaussianBlur(1.3))
    return ImageEnhance.Contrast(img).enhance(1.15)

def scene_celebration(pal):
    arr = linear_gradient_arr(pal["sky1"], (pal["sky1"][0]+10,pal["sky1"][1]+5,pal["sky1"][2]+35), (W, H))
    arr = add_noise(arr, 5)
    img = arr_to_img(arr)
    draw = ImageDraw.Draw(img, 'RGBA')
    draw_stars(draw, W, H, 200)
    fw_colors = [(255,200,0),(255,100,50),(100,200,255),(255,50,150),(100,255,100),(200,100,255)]
    draw_fireworks(draw, W, H, fw_colors, count=10)
    draw_stadium_walls(draw, W, H, (10,6,25))
    crowd_c = [(255,200,0),(220,50,50),(50,100,220),(255,255,255),(0,200,100),(255,100,200)]
    draw_crowd(draw, W, H, (20,12,40), int(H*0.6), rows=4, colors=crowd_c)
    # Main player lifting trophy
    cx, cy = W//2, int(H*0.66)
    draw_player(draw, cx, cy, 2.6, (40,25,80), "celebrate")
    draw_trophy(draw, cx, cy-int(H*0.37), 3.2)
    # Side players
    for offset in [(-230,-5),(-145,5),(145,5),(230,-5)]:
        draw_player(draw, cx+offset[0], cy+offset[1]+random.randint(-8,8),
                   random.uniform(1.3,1.9), (30,18,60), "celebrate")
    draw_confetti(draw, W, H, [(255,200,0),(220,50,50),(50,150,220),(255,255,255),(0,200,80),(255,100,200)], 400)
    # Trophy spotlight
    tx, ty = cx, int(H*0.27)
    for r in range(280,0,-28):
        draw.ellipse([tx-r,ty-r,tx+r,ty+r], fill=(255,215,50,int(22*(1-r/280))))
    img = img.filter(ImageFilter.GaussianBlur(1.1))
    return ImageEnhance.Contrast(img).enhance(1.18)

# ---------------------------------------------------------------------------
# Scene dispatcher
# ---------------------------------------------------------------------------
SCENE_FNS = {
    "stadium_dusk":  scene_stadium_dusk,
    "stadium_night": scene_stadium_night,
    "strike":        scene_strike,
    "penalty":       scene_penalty,
    "goal":          scene_goal,
    "crowd_shock":   scene_crowd_shock,
    "celebration":   scene_celebration,
    "leap":          scene_strike,   # reuse with different seed
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
day_of_year = int(time.strftime("%j"))
topic = MOMENTS_BANK[day_of_year % len(MOMENTS_BANK)]
pal = PALETTES[topic["palette"]]

with open(f"{WORK}/topic.json", "w") as f:
    json.dump(topic, f, indent=2)

print("Topic:", topic["title"])
random.seed(day_of_year)

for i, beat_name in enumerate(topic["beats"]):
    random.seed(day_of_year + i * 100)
    fn = SCENE_FNS.get(beat_name, scene_stadium_dusk)
    img = fn(pal)
    path = f"{WORK}/scene_{i}.png"
    img.save(path, quality=95)
    print(f"Scene {i} ({beat_name}) -> {path}")

print("Step 1 complete.")
