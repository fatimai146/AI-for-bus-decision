import asyncio
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
OUT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(OUT, "build_lily")
os.makedirs(BUILD, exist_ok=True)
FINAL = os.path.join(OUT, "SplitSeat_Lily_Story.mp4")

FONT_DIR = "/usr/share/fonts/truetype/macos/"
VOICE = "en-US-AvaNeural"

PLUM, PLUM_D = (74, 33, 82), (38, 15, 44)
BLUSH1, BLUSH2 = (253, 247, 244), (246, 230, 228)
MUSTARD = (236, 172, 38)
MUSTARD_SOFT = (253, 239, 205)
ROSE = (222, 104, 128)
HEAD = (52, 28, 58)
SUB = (122, 104, 120)
GOOD = (122, 70, 170)
WHITE = (255, 255, 255)
CARD = (255, 252, 250)
LINE = (236, 222, 226)
GREY = (205, 196, 204)

PEOPLE = [
    (1, "Ben", "B", (124, 58, 130), ["Steak frites", "2 margaritas"], 56),
    (2, "Maria", "M", (90, 120, 200), ["Pasta", "Mojito", "Old fashioned"], 52),
    (3, "Lily", "L", ROSE, ["Caesar salad", "Soda"], 19),
    (4, "Kenji", "K", (200, 110, 60), ["Ribeye", "2 IPAs"], 61),
    (5, "Zoe", "Z", MUSTARD, ["Tacos", "Spicy margarita"], 47),
    (6, "Omar", "O", (80, 80, 104), ["Burger", "Whiskey sour"], 53),
]
assert sum(p[5] for p in PEOPLE) == 288


def f(size, weight="Bold"):
    return ImageFont.truetype(FONT_DIR + f"Inter-{weight}.ttf", size)


def layer(w, h):
    return Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))


def gradient_bg(c1, c2, radial=False):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    if radial:
        t = np.clip(np.hypot((x - W * 0.5) / W, (y - H * 0.45) / H) * 1.7, 0, 1)
    else:
        t = np.clip((x / W) * 0.6 + (y / H) * 0.4, 0, 1)
    arr = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        arr[..., i] = c1[i] * (1 - t) + c2[i] * t
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")


BG_DARK = gradient_bg(PLUM, PLUM_D, radial=True)
BG_LIGHT = gradient_bg(BLUSH1, BLUSH2)


def text_block(lines, size, color, weight="Bold", spacing=1.18, tracking=0):
    fnt = f(size, weight)
    lh = int(size * spacing)
    dd = ImageDraw.Draw(layer(1, 1))
    tw = max(int(dd.textlength(l, font=fnt)) + 8 + tracking * len(l) for l in lines)
    im = layer(tw, lh * len(lines) + int(size * 0.3))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = 0
        if tracking:
            for ch in l:
                d.text((x, i * lh), ch, font=fnt, fill=color)
                x += d.textlength(ch, font=fnt) + tracking
        else:
            d.text((0, i * lh), l, font=fnt, fill=color)
    return im


def label(t, color=ROSE):
    return text_block([t.upper()], 30, color, "Bold", tracking=5)


def shadowed(im, radius=22, offset=(0, 14), alpha=60):
    pad = radius * 3
    out = layer(im.width + pad * 2, im.height + pad * 2)
    sh = Image.new("RGBA", im.size, (40, 10, 40, 255))
    sh.putalpha(im.split()[3].point(lambda v: v * alpha // 255))
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(radius))
    out.alpha_composite(im, (pad, pad))
    return out


def lily(scale=1.0, mood="happy", soda=True):
    k = 4 * scale
    im = layer(300 * k, 400 * k)
    d = ImageDraw.Draw(im)
    S = lambda *v: [int(c * k) for c in v]
    skin, hair, top, top_d = (238, 196, 168), (92, 54, 34), ROSE, (190, 78, 104)
    d.rounded_rectangle(S(36, 70, 194, 300), radius=int(70 * k), fill=hair)
    d.ellipse(S(10, 262, 220, 492), fill=top)
    d.rectangle(S(0, 385, 300, 400), fill=(0, 0, 0, 0))
    d.rectangle(S(97, 236, 133, 272), fill=(222, 176, 148))
    d.ellipse(S(88, 256, 142, 290), fill=top_d)
    d.ellipse(S(94, 252, 136, 280), fill=(222, 176, 148))
    d.ellipse(S(48, 100, 182, 248), fill=skin)
    d.chord(S(44, 80, 186, 190), 180, 360, fill=hair)
    d.polygon(S(44, 135, 100, 112, 186, 135, 186, 120, 44, 120), fill=hair)
    for ex in (88, 142):
        d.ellipse(S(ex - 22, 160, ex + 22, 200), outline=(60, 34, 50), width=int(5 * k))
        d.ellipse(S(ex - 6, 172, ex + 6, 186), fill=(40, 24, 30))
    d.line(S(110, 178, 120, 178), fill=(60, 34, 50), width=int(5 * k))
    if mood == "sad":
        d.line(S(70, 152, 100, 145), fill=hair, width=int(5 * k))
        d.line(S(130, 145, 160, 152), fill=hair, width=int(5 * k))
        d.arc(S(96, 214, 134, 236), 200, 340, fill=(150, 70, 70), width=int(5 * k))
    else:
        d.arc(S(68, 140, 104, 158), 200, 340, fill=hair, width=int(5 * k))
        d.arc(S(126, 140, 162, 158), 200, 340, fill=hair, width=int(5 * k))
        d.arc(S(92, 196, 138, 230), 20, 160, fill=(150, 70, 70), width=int(5 * k))
    d.ellipse(S(60, 196, 80, 210), fill=(245, 170, 170))
    d.ellipse(S(150, 196, 170, 210), fill=(245, 170, 170))
    if soda:
        d.rounded_rectangle(S(222, 250, 272, 370), radius=int(8 * k), fill=(250, 250, 255), outline=(200, 190, 210), width=int(3 * k))
        d.rectangle(S(226, 280, 268, 366), fill=(150, 70, 60))
        for bx, by in ((236, 300), (252, 320), (242, 345)):
            d.ellipse(S(bx, by, bx + 8, by + 8), fill=(220, 150, 140))
        d.line(S(258, 250, 270, 214), fill=ROSE, width=int(6 * k))
    return im.resize((im.width // 4, im.height // 4), Image.LANCZOS)


def chip(letter, color, size=64):
    k = 4
    im = layer(size * k, size * k)
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size * k - 1, size * k - 1), fill=color)
    fnt = f(int(size * 0.45 * k), "Bold")
    d.text(((size * k - d.textlength(letter, font=fnt)) / 2, size * k * 0.22), letter, font=fnt, fill=WHITE)
    return im.resize((size, size), Image.LANCZOS)


def cocktail(size=60, color=MUSTARD):
    k = 4
    s = size * k
    im = layer(s, s)
    d = ImageDraw.Draw(im)
    d.polygon([(s * 0.12, s * 0.12), (s * 0.88, s * 0.12), (s * 0.5, s * 0.55)], fill=color)
    d.line([(s * 0.5, s * 0.55), (s * 0.5, s * 0.85)], fill=color, width=int(s * 0.07))
    d.line([(s * 0.3, s * 0.87), (s * 0.7, s * 0.87)], fill=color, width=int(s * 0.07))
    d.ellipse((s * 0.62, s * 0.02, s * 0.82, s * 0.22), fill=ROSE)
    return im.resize((size, size), Image.LANCZOS)


def bubble(text, size=36, fill=WHITE, color=HEAD):
    fnt = f(size, "SemiBold")
    tw = int(ImageDraw.Draw(layer(1, 1)).textlength(text, font=fnt))
    im = layer(tw + 68, size + 52)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=24, fill=fill)
    d.text((34, 22), text, font=fnt, fill=color)
    return shadowed(im, 16, (0, 8), 70)


def logo(size=120, hole=PLUM):
    k = 4
    s = size * k
    im = layer(s, s)
    d = ImageDraw.Draw(im)
    cols = [MUSTARD, ROSE]
    for i in range(6):
        d.pieslice((0, 0, s - 1, s - 1), -90 + i * 60 + 3, -90 + (i + 1) * 60 - 3, fill=cols[i % 2])
    d.ellipse((s * 0.3, s * 0.3, s * 0.7, s * 0.7), fill=hole)
    return im.resize((size, size), Image.LANCZOS)


def friends_with_drinks():
    im = layer(5 * 110, 170)
    for i, p in enumerate([q for q in PEOPLE if q[1] != "Lily"]):
        im.alpha_composite(chip(p[2], p[3], 80), (i * 110, 0))
        im.alpha_composite(cocktail(56), (i * 110 + 12, 100))
    return im


def one_check():
    cw, ch = 620, 560
    im = layer(cw, ch)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=26, fill=CARD)
    d.text((44, 40), "TABLE 6 · 6 GUESTS", font=f(22, "Bold"), fill=SUB)
    d.text((44, 80), "Check total", font=f(34, "SemiBold"), fill=HEAD)
    d.text((44, 130), "$288.00", font=f(84, "Bold"), fill=HEAD)
    d.line((44, 250, cw - 44, 250), fill=LINE, width=2)
    d.text((44, 276), "Split evenly, 6 ways", font=f(30, "Medium"), fill=SUB)
    d.text((cw - 44 - d.textlength("$48 each", font=f(32, "Bold")), 274), "$48 each", font=f(32, "Bold"), fill=HEAD)
    d.rounded_rectangle((26, 344, cw - 26, 520), radius=18, fill=(253, 232, 236))
    d.text((50, 366), "Lily's order", font=f(28, "Medium"), fill=HEAD)
    d.text((cw - 50 - d.textlength("$19", font=f(30, "Bold")), 364), "$19", font=f(30, "Bold"), fill=HEAD)
    d.text((50, 420), "Lily's share", font=f(28, "Medium"), fill=HEAD)
    d.text((cw - 50 - d.textlength("$48", font=f(30, "Bold")), 418), "$48", font=f(30, "Bold"), fill=(200, 50, 80))
    d.text((50, 470), "Salad and a soda", font=f(22, "Regular"), fill=SUB)
    return shadowed(im.rotate(-2, expand=True, resample=Image.BICUBIC), 24, (0, 16), 110)


def pos_tablet():
    tw, th = 1000, 640
    im = layer(tw, th)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw - 1, th - 1), radius=44, fill=(44, 30, 48))
    sx, sy, sw, sh = 26, 26, tw - 52, th - 52
    d.rounded_rectangle((sx, sy, sx + sw, sy + sh), radius=24, fill=WHITE)
    d.rounded_rectangle((sx, sy, sx + sw, sy + 76), radius=24, fill=(250, 242, 244))
    d.rectangle((sx, sy + 50, sx + sw, sy + 76), fill=(250, 242, 244))
    d.text((sx + 30, sy + 22), "Server tablet  ·  Table 6", font=f(28, "Bold"), fill=HEAD)
    t = "Every item saved to a seat"
    d.text((sx + sw - 30 - d.textlength(t, font=f(22, "SemiBold")), sy + 26), t, font=f(22, "SemiBold"), fill=ROSE)
    col_w = sw // 3
    for i, (seat, name, ini, col, items, _) in enumerate(PEOPLE):
        cx = sx + 22 + (i % 3) * col_w
        cy = sy + 100 + (i // 3) * 250
        hl = name == "Lily"
        d.rounded_rectangle((cx, cy, cx + col_w - 22, cy + 225), radius=18,
                            fill=(253, 232, 236) if hl else (251, 248, 249),
                            outline=ROSE if hl else LINE, width=3 if hl else 2)
        im.alpha_composite(chip(ini, col, 46), (cx + 16, cy + 16))
        d.text((cx + 74, cy + 24), f"Seat {seat} · {name}", font=f(25, "Bold"), fill=HEAD)
        for j, it in enumerate(items):
            drink = any(w in it.lower() for w in ("margarita", "mojito", "old fashioned", "ipa", "whiskey"))
            if drink:
                im.alpha_composite(cocktail(26), (cx + 18, cy + 84 + j * 42))
            d.text((cx + (54 if drink else 22), cy + 82 + j * 42), it, font=f(24, "Regular"), fill=HEAD if hl else SUB)
    return shadowed(im, 30, (0, 20), 90)


SEAT_POS = [(-1, -0.62), (1, -0.62), (1.18, 0.15), (0.6, 0.85), (-0.6, 0.85), (-1.18, 0.15)]
SEAT_POS = [(-0.62, -0.95), (0.62, -0.95), (1.25, 0.05), (0.62, 1.0), (-0.62, 1.0), (-1.25, 0.05)]


def table_view(n_paid):
    w, h = 1060, 920
    im = layer(w, h)
    d = ImageDraw.Draw(im)
    cx, cy, R = w / 2, h / 2, 300
    d.ellipse((cx - R, cy - R * 0.8, cx + R, cy + R * 0.8), fill=(214, 168, 120))
    d.ellipse((cx - R + 18, cy - R * 0.8 + 16, cx + R - 18, cy + R * 0.8 - 16), fill=(226, 184, 138))
    rd_w, rd_h = 120, 170
    d.rounded_rectangle((cx - rd_w / 2, cy - rd_h / 2, cx + rd_w / 2, cy + rd_h / 2), radius=22, fill=(44, 30, 48))
    d.rounded_rectangle((cx - rd_w / 2 + 14, cy - rd_h / 2 + 14, cx + rd_w / 2 - 14, cy - 6), radius=10, fill=MUSTARD_SOFT)
    d.text((cx - d.textlength("TAP", font=f(24, "Bold")) / 2, cy - rd_h / 2 + 30), "TAP", font=f(24, "Bold"), fill=HEAD)
    for r in range(2):
        for c in range(3):
            x, y = cx - 42 + c * 30, cy + 14 + r * 30
            d.rounded_rectangle((x, y, x + 22, y + 20), radius=5, fill=(90, 72, 96))
    for i, (seat, name, ini, col, items, total) in enumerate(PEOPLE):
        ix, iy = cx + SEAT_POS[i][0] * 170, cy + SEAT_POS[i][1] * 140
        d.ellipse((ix - 34, iy - 34, ix + 34, iy + 34), fill=WHITE, outline=(200, 160, 120), width=3)
        n_drinks = sum(any(w in it.lower() for w in ("margarita", "mojito", "old fashioned", "ipa", "whiskey"))
                       for it in items) + sum(it.startswith("2 ") for it in items)
        if name == "Lily":
            d.ellipse((ix - 22, iy - 22, ix + 22, iy + 22), fill=(120, 180, 90))
            d.rounded_rectangle((ix + 40, iy - 30, ix + 64, iy + 26), radius=6, fill=(150, 70, 60))
        else:
            d.ellipse((ix - 22, iy - 22, ix + 22, iy + 22), fill=(200, 120, 80))
            for k2 in range(n_drinks):
                im.alpha_composite(cocktail(40), (int(ix + 34 + k2 * 30), int(iy - 46)))
    for i, (seat, name, ini, col, items, total) in enumerate(PEOPLE):
        px, py = cx + SEAT_POS[i][0] * 330, cy + SEAT_POS[i][1] * 300
        paid = i < n_paid
        hl = name == "Lily"
        size = 96
        im.alpha_composite(chip(ini, col, size), (int(px - size / 2), int(py - size / 2)))
        tag_w, tag_h = 190, 64
        ty = py + size / 2 + 8 if SEAT_POS[i][1] > -0.5 else py - size / 2 - tag_h - 8
        if abs(SEAT_POS[i][0]) > 1:
            ty = py + size / 2 + 8
        tx = px - tag_w / 2
        fill = (238, 226, 246) if paid else (WHITE if not hl else (253, 232, 236))
        d.rounded_rectangle((tx, ty, tx + tag_w, ty + tag_h), radius=18, fill=fill,
                            outline=GOOD if paid else (ROSE if hl else LINE), width=3)
        txt = f"${total}" + ("  paid" if paid else "")
        fnt = f(28, "Bold")
        d.text((px - d.textlength(txt, font=fnt) / 2, ty + 14), txt, font=fnt, fill=GOOD if paid else HEAD)
    return im


def big_price():
    im = layer(760, 210)
    d = ImageDraw.Draw(im)
    d.text((0, 0), "$19", font=f(180, "Bold"), fill=ROSE)
    x = d.textlength("$19", font=f(180, "Bold")) + 44
    d.text((x, 76), "$48", font=f(96, "Bold"), fill=GREY)
    w = d.textlength("$48", font=f(96, "Bold"))
    d.line((x - 6, 152, x + w + 6, 136), fill=GREY, width=9)
    return im


def L(im, x, y, t=0.0, anim="up", out=None):
    return dict(im=im, x=x, y=y, t=t, anim=anim, out=out)


def scenes():
    S = []
    S.append(dict(bg="light",
                  vo="Meet Lily. She doesn't drink, but her friends love a round of cocktails.",
                  els=[
                      L(lily(1.5, "happy"), 170, 140, 0.0, "fade"),
                      L(label("A SplitSeat story"), 840, 270, 0.2),
                      L(text_block(["Meet Lily.", "She doesn\u2019t drink.", "Her friends do."], 76, HEAD), 840, 320, 0.5),
                      L(friends_with_drinks(), 840, 640, 2.6),
                  ]))
    S.append(dict(bg="dark",
                  vo="When the check comes, someone says, let's just split it. Lily's meal was nineteen dollars. "
                     "Her share is forty eight. Asking for separate checks feels petty, so she pays, and says nothing.",
                  els=[
                      L(one_check(), 90, 150, 0.3),
                      L(bubble("\u201cLet\u2019s just split it evenly?\u201d"), 1030, 110, 1.0),
                      L(lily(1.3, "sad", soda=False), 1160, 280, 0.0, "fade"),
                  ]))
    S.append(dict(bg="light",
                  vo="At a restaurant with SplitSeat, the server's tablet saves every dish and drink to a seat, as it's ordered.",
                  els=[
                      L(label("With SplitSeat"), 110, 360, 0.2),
                      L(text_block(["Every dish and", "drink is saved", "to a seat."], 68, HEAD), 110, 410, 0.4),
                      L(pos_tablet(), 690, 140, 0.8),
                  ]))
    S.append(dict(bg="light",
                  vo="The check comes already split. Everyone taps their own card, for their own seat. Nobody had to ask.",
                  els=[
                      L(label("The check comes split"), 110, 360, 0.2),
                      L(text_block(["Everyone taps", "their own card."], 68, HEAD), 110, 410, 0.4),
                      L(text_block(["Nobody had to ask."], 36, SUB, "Medium"), 110, 600, 4.4, "fade"),
                      L(table_view(0), 820, 90, 0.6, "fade", out=2.6),
                      L(table_view(1), 820, 90, 2.6, "none", out=3.0),
                      L(table_view(3), 820, 90, 3.0, "none", out=3.4),
                      L(table_view(4), 820, 90, 3.4, "none", out=3.8),
                      L(table_view(6), 820, 90, 3.8, "none"),
                  ]))
    S.append(dict(bg="light",
                  vo="Lily pays nineteen dollars, not forty eight, and she never had to say a word.",
                  els=[
                      L(label("The result"), 110, 320, 0.2),
                      L(text_block(["She pays for", "what she ordered."], 68, HEAD), 110, 370, 0.4),
                      L(big_price(), 110, 560, 1.0),
                      L(lily(1.5, "happy"), 1200, 140, 0.0, "fade"),
                  ]))
    brand = layer(760, 150)
    bd = ImageDraw.Draw(brand)
    brand.alpha_composite(logo(130), (0, 10))
    bd.text((160, 22), "Split", font=f(100, "Bold"), fill=WHITE)
    bd.text((160 + bd.textlength("Split", font=f(100, "Bold")), 22), "Seat", font=f(100, "Bold"), fill=MUSTARD)
    S.append(dict(bg="dark", center=True,
                  vo="SplitSeat. Pay for your own order, without anyone having to ask.",
                  els=[
                      L(brand, 0, 400, 0.2, "fade"),
                      L(text_block(["Pay for your own order, without anyone having to ask."], 40, (236, 222, 240), "Medium"), 0, 600, 1.2, "fade"),
                  ]))
    return S


async def tts(text, path):
    import edge_tts
    await edge_tts.Communicate(text, VOICE, rate="-4%").save(path)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]).decode().strip())


def make_music(total, path, sr=48000):
    t = np.arange(int(total * sr)) / sr
    chords = [[261.63, 329.63, 392.0], [220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 246.94, 293.66]]
    seg = 3.5
    out = np.zeros_like(t)
    for i in range(int(total / seg) + 1):
        s0 = i * seg
        idx = (t >= s0 - 0.5) & (t < s0 + seg + 1.5)
        tt = t[idx] - s0
        env = np.clip((tt + 0.5) / 1.0, 0, 1) * np.clip((seg + 1.5 - tt) / 1.6, 0, 1)
        for fr in chords[i % 4]:
            out[idx] += env * (np.sin(2 * np.pi * fr * t[idx]) + 0.25 * np.sin(2 * np.pi * fr * 2 * t[idx]))
        pluck_idx = (t >= s0) & (t < s0 + 1.2)
        tp = t[pluck_idx] - s0
        out[pluck_idx] += 0.8 * np.exp(-tp * 4) * np.sin(2 * np.pi * chords[i % 4][2] * 2 * t[pluck_idx])
    out *= np.clip(t / 0.6, 0, 1) * np.clip((total - t) / 2.5, 0, 1)
    out = out / np.max(np.abs(out)) * 0.15
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


_cache = {}


def faded(im, a):
    key = (id(im), round(a, 2))
    if key not in _cache:
        c = im.copy()
        c.putalpha(c.split()[3].point(lambda v: int(v * a)))
        _cache[key] = c
    return _cache[key]


def place(sc):
    if sc.get("center"):
        for e in sc["els"]:
            e["x"] = (W - e["im"].width) // 2


def frame(sc, t, progress):
    img = (BG_DARK if sc["bg"] == "dark" else BG_LIGHT).copy()
    for e in sc["els"]:
        if t < e["t"]:
            continue
        a = 1.0 if e["anim"] == "none" else ease((t - e["t"]) / 0.55)
        if e["out"] is not None and t >= e["out"]:
            a = 0 if e["anim"] == "none" else min(a, 1 - ease((t - e["out"]) / 0.2))
            if a <= 0:
                continue
        dy = int((1 - a) * 40) if e["anim"] == "up" else 0
        im = e["im"] if a >= 0.999 else faded(e["im"], a)
        img.alpha_composite(im, (int(e["x"]), int(e["y"] + dy)))
    ImageDraw.Draw(img).rectangle((0, H - 8, int(W * progress), H), fill=MUSTARD)
    return img.convert("RGB")


def preview():
    S = scenes()
    for sc in S:
        place(sc)
    sheet = Image.new("RGB", (640 * 3, 360 * 2), WHITE)
    for i, sc in enumerate(S):
        t = max(e["t"] for e in sc["els"]) + 1.0
        fr = frame(sc, t, 0.5)
        fr.save(os.path.join(BUILD, f"scene{i}.jpg"))
        sheet.paste(fr.resize((640, 360)), ((i % 3) * 640, (i // 3) * 360))
    sheet.save(os.path.join(BUILD, "preview.jpg"))


def main():
    S = scenes()
    for sc in S:
        place(sc)

    async def all_tts():
        for i, sc in enumerate(S):
            sc["audio"] = os.path.join(BUILD, f"vo_{i}.mp3")
            await tts(sc["vo"], sc["audio"])
    asyncio.run(all_tts())
    LEAD, TAIL, TRANS = 0.5, 1.0, 0.5
    start = 0.0
    for i, sc in enumerate(S):
        sc["lead"] = 0.15 if i == 0 else LEAD
        sc["dur"] = sc["lead"] + duration(sc["audio"]) + TAIL
        sc["start"] = start
        start += sc["dur"]
    total = start + 0.6

    video = os.path.join(BUILD, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                           "-pix_fmt", "yuv420p", video], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for fi in range(n):
        gt = fi / FPS
        prog = gt / total
        idx = max(i for i, sc in enumerate(S) if sc["start"] <= gt)
        sc = S[idx]
        lt = gt - sc["start"]
        if idx > 0 and lt < TRANS:
            prev = S[idx - 1]
            off = int(W * ease(lt / TRANS))
            img = Image.new("RGB", (W, H))
            img.paste(frame(prev, prev["dur"], prog), (-off, 0))
            img.paste(frame(sc, lt, prog), (W - off, 0))
        else:
            img = frame(sc, lt, prog)
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()

    music = os.path.join(BUILD, "music.wav")
    make_music(total, music)
    inputs, filters = ["-i", music], []
    for i, sc in enumerate(S):
        inputs += ["-i", sc["audio"]]
        ms = int((sc["start"] + sc["lead"]) * 1000)
        filters.append(f"[{i + 1}:a]adelay={ms}|{ms},aresample=48000[v{i}]")
    mix = "".join(f"[v{i}]" for i in range(len(S)))
    filters.append(f"{mix}amix=inputs={len(S)}:normalize=0[vo];[vo][0:a]amix=inputs=2:normalize=0[a]")
    audio = os.path.join(BUILD, "audio.m4a")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(filters),
                          "-map", "[a]", "-t", f"{total:.2f}", "-c:a", "aac", "-ac", "2", "-ar", "48000",
                          "-b:a", "192k", audio])
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", audio, "-c:v", "copy", "-c:a", "copy",
                           "-shortest", "-movflags", "+faststart", FINAL])
    print("done", FINAL, round(total, 1), "s")


if __name__ == "__main__":
    preview() if "--preview" in sys.argv else main()
