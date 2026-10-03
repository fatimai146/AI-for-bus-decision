import asyncio
import json
import math
import os
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
OUT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(OUT, "build")
os.makedirs(BUILD, exist_ok=True)

FONT_DIR = "/usr/share/fonts/truetype/macos/"
MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
MONO_R = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
VOICE = "en-US-AvaNeural"

DARK1, DARK2 = (33, 36, 56), (20, 22, 36)
LIGHT1, LIGHT2 = (252, 248, 242), (243, 234, 223)
ACCENT = (238, 104, 56)
ACCENT_SOFT = (253, 231, 220)
HEAD = (36, 35, 44)
SUB = (112, 106, 102)
GOOD = (36, 160, 104)
WHITE = (255, 255, 255)
CARD = (255, 253, 249)
LINE = (232, 224, 214)

FRIENDS = [("P", (220, 119, 92)), ("J", (59, 89, 127)), ("A", (127, 176, 150)),
           ("M", ACCENT), ("S", (240, 162, 66)), ("R", (153, 90, 225))]


def f(size, weight="Bold"):
    if weight == "mono":
        return ImageFont.truetype(MONO, size)
    if weight == "monoR":
        return ImageFont.truetype(MONO_R, size)
    return ImageFont.truetype(FONT_DIR + f"Inter-{weight}.ttf", size)


def layer(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def gradient_bg(c1, c2, radial=False):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    if radial:
        t = np.clip(np.hypot((x - W * 0.35) / W, (y - H * 0.4) / H) * 1.6, 0, 1)
    else:
        t = np.clip((x / W) * 0.6 + (y / H) * 0.4, 0, 1)
    arr = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        arr[..., i] = c1[i] * (1 - t) + c2[i] * t
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")


BG_DARK = gradient_bg((42, 46, 70), DARK2, radial=True)
BG_LIGHT = gradient_bg(LIGHT1, LIGHT2)


def text_block(lines, size, color, weight="Bold", spacing=1.18, width=None, tracking=0):
    fnt = f(size, weight)
    lh = int(size * spacing)
    tw = width or max(int(ImageDraw.Draw(layer(1, 1)).textlength(l, font=fnt)) + 8 + tracking * len(l)
                      for l in lines)
    im = layer(tw, lh * len(lines) + int(size * 0.3))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        if tracking:
            x = 0
            for ch in l:
                d.text((x, i * lh), ch, font=fnt, fill=color)
                x += d.textlength(ch, font=fnt) + tracking
        else:
            d.text((0, i * lh), l, font=fnt, fill=color)
    return im


def label(t, color=ACCENT):
    return text_block([t.upper()], 30, color, "Bold", tracking=5)


def shadowed(im, radius=22, offset=(0, 14), alpha=60):
    pad = radius * 3
    out = layer(im.width + pad * 2, im.height + pad * 2)
    a = im.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", im.size, (40, 25, 15, 255))
    sh.putalpha(a)
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(radius))
    out.alpha_composite(im, (pad, pad))
    return out, pad


def maya(scale=1.0, mood="happy"):
    k = 4 * scale
    im = layer(int(230 * k), int(380 * k))
    d = ImageDraw.Draw(im)
    S = lambda *v: [int(c * k) for c in v]
    skin, hair, shirt, shirt_d = (182, 113, 84), (28, 19, 15), (21, 140, 105), (12, 107, 78)
    d.ellipse(S(5, 250, 215, 480), fill=shirt)
    d.rectangle(S(0, 365, 230, 380), fill=(0, 0, 0, 0))
    d.rectangle(S(88, 228, 123, 262), fill=(160, 98, 72))
    d.polygon(S(78, 250, 132, 250, 105, 287), fill=shirt_d)
    d.ellipse(S(72, 0, 138, 66), fill=hair)
    d.ellipse(S(28, 62, 183, 236), fill=hair)
    d.ellipse(S(28, 154, 52, 178), fill=skin)
    d.ellipse(S(159, 154, 183, 178), fill=skin)
    d.ellipse(S(40, 96, 171, 234), fill=skin)
    d.ellipse(S(34, 172, 45, 183), fill=(51, 200, 145))
    d.ellipse(S(166, 172, 177, 183), fill=(51, 200, 145))
    for ex in (77, 133):
        d.ellipse(S(ex - 8, 148, ex + 8, 164), fill=(30, 20, 18))
        d.ellipse(S(ex + 1, 150, ex + 5, 154), fill=WHITE)
    if mood == "sad":
        d.line(S(60, 138, 92, 127), fill=hair, width=int(6 * k))
        d.line(S(118, 127, 150, 138), fill=hair, width=int(6 * k))
        d.arc(S(85, 190, 125, 214), 200, 340, fill=(90, 42, 28), width=int(5 * k))
    else:
        d.arc(S(60, 124, 94, 144), 200, 340, fill=hair, width=int(6 * k))
        d.arc(S(116, 124, 150, 144), 200, 340, fill=hair, width=int(6 * k))
        d.arc(S(82, 168, 128, 200), 20, 160, fill=(90, 42, 28), width=int(5 * k))
    return im.resize((im.width // 4, im.height // 4), Image.LANCZOS)


def chip(letter, color, size=64):
    k = 4
    im = layer(size * k, size * k)
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size * k - 1, size * k - 1), fill=color)
    fnt = f(int(size * 0.45 * k), "Bold")
    w = d.textlength(letter, font=fnt)
    d.text(((size * k - w) / 2, size * k * 0.22), letter, font=fnt, fill=WHITE)
    return im.resize((size, size), Image.LANCZOS)


def bubble(text, size=34, fill=WHITE, color=HEAD, italic_word=None, pad=(34, 22)):
    fnt = f(size, "Medium")
    tw = int(ImageDraw.Draw(layer(1, 1)).textlength(text, font=fnt))
    im = layer(tw + pad[0] * 2, size + pad[1] * 2 + 6)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=22, fill=fill)
    d.text((pad[0], pad[1]), text, font=fnt, fill=color)
    return shadowed(im, 16, (0, 8), 50)[0]


def logo(size=120):
    k = 4
    s = size * k
    im = layer(s, s)
    d = ImageDraw.Draw(im)
    cols = [ACCENT, (250, 160, 110)]
    for i in range(6):
        d.pieslice((0, 0, s - 1, s - 1), -90 + i * 60 + 3, -90 + (i + 1) * 60 - 3, fill=cols[i % 2])
    d.ellipse((s * 0.3, s * 0.3, s * 0.7, s * 0.7), fill=DARK1)
    return im.resize((size, size), Image.LANCZOS)


# ---------- product visuals ----------

def receipt_old():
    im = layer(640, 470)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 639, 469), radius=10, fill=(252, 251, 244))
    d.text((150, 34), "PRIME STEAKHOUSE", font=f(34, "mono"), fill=(30, 30, 30))
    rows = [("Ribeye x2", "$96"), ("Cocktails x6", "$84"), ("Lobster mac", "$38"),
            ("Pasta + water (Maya)", "$18"), ("Tax + tip", "$76")]
    y = 104
    for a, b in rows:
        if "Maya" in a:
            d.rectangle((36, y - 4, 604, y + 38), fill=(255, 232, 220))
        d.text((50, y), a, font=f(30, "monoR"), fill=(40, 40, 40))
        d.text((590 - d.textlength(b, font=f(30, "monoR")), y), b, font=f(30, "monoR"), fill=(40, 40, 40))
        y += 46
    for x in range(50, 590, 14):
        d.line((x, y + 6, x + 7, y + 6), fill=(170, 170, 170), width=2)
    d.text((50, y + 24), "Split 6 ways", font=f(30, "mono"), fill=(30, 30, 30))
    d.text((590 - d.textlength("$52 each", font=f(30, "mono")), y + 24), "$52 each", font=f(30, "mono"), fill=(30, 30, 30))
    d.text((50, y + 68), "Maya paid", font=f(30, "mono"), fill=(205, 60, 50))
    d.text((590 - d.textlength("$52 for $18", font=f(30, "mono")), y + 68), "$52 for $18", font=f(30, "mono"), fill=(205, 60, 50))
    return shadowed(im.rotate(2, expand=True, resample=Image.BICUBIC), 24, (0, 16), 90)[0]


ORDER = [
    (1, "Priya", ["Whole crispy fish  $32", "Thai iced tea  $5"]),
    (2, "Jordan", ["Green curry  $17", "Beer  $7"]),
    (3, "Alex", ["Seafood platter  $38"]),
    (4, "Maya", ["Red curry  $16", "Spring rolls  $7"]),
    (5, "Sam", ["Pad Thai  $15", "Mango mojito  $11"]),
    (6, "Riya", ["Basil fried rice  $15", "Thai iced tea  $5"]),
]
TOTALS = [54.61, 38.10, 48.26, 29.21, 40.64, 25.40]


def pos_tablet():
    tw, th = 980, 660
    im = layer(tw, th)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw - 1, th - 1), radius=44, fill=(30, 30, 38))
    sx, sy, sw, sh = 26, 26, tw - 52, th - 52
    d.rounded_rectangle((sx, sy, sx + sw, sy + sh), radius=24, fill=WHITE)
    d.rounded_rectangle((sx, sy, sx + sw, sy + 74), radius=24, fill=(248, 244, 238))
    d.rectangle((sx, sy + 50, sx + sw, sy + 74), fill=(248, 244, 238))
    d.text((sx + 30, sy + 20), "Lemongrass  ·  Table 12  ·  6 guests", font=f(28, "SemiBold"), fill=HEAD)
    d.text((sx + sw - 200, sy + 22), "SplitSeat on", font=f(24, "SemiBold"), fill=ACCENT)
    col_w = sw // 3
    for i, (seat, name, items) in enumerate(ORDER):
        cx = sx + 22 + (i % 3) * col_w
        cy = sy + 100 + (i // 3) * 190
        hl = name == "Maya"
        d.rounded_rectangle((cx, cy, cx + col_w - 22, cy + 170), radius=18,
                            fill=ACCENT_SOFT if hl else (250, 248, 245),
                            outline=ACCENT if hl else LINE, width=3 if hl else 2)
        c = FRIENDS[i][1]
        im.alpha_composite(chip(FRIENDS[i][0], c, 44), (cx + 16, cy + 16))
        d.text((cx + 72, cy + 22), f"Seat {seat} · {name}", font=f(24, "Bold"), fill=HEAD)
        for j, it in enumerate(items):
            d.text((cx + 18, cy + 80 + j * 36), it, font=f(22, "Regular"), fill=SUB)
    y = sy + 486
    d.rounded_rectangle((sx + 22, y, sx + sw - 22, y + 92), radius=18, fill=(244, 248, 246), outline=(196, 226, 210), width=2)
    d.text((sx + 46, y + 14), "Shared: Satay platter  $18", font=f(26, "Bold"), fill=HEAD)
    d.text((sx + 46, y + 52), "Split only between seats 1, 2 and 5", font=f(22, "Regular"), fill=SUB)
    return shadowed(im, 30, (0, 20), 80)[0]


def split_check():
    cw, ch = 700, 820
    im = layer(cw, ch)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=28, fill=CARD)
    d.text((44, 40), "LEMONGRASS · TABLE 12", font=f(22, "Bold"), fill=SUB)
    d.text((44, 76), "Your check, split by seat", font=f(36, "Bold"), fill=HEAD)
    d.line((44, 140, cw - 44, 140), fill=LINE, width=2)
    y = 162
    for i, (seat, name, _) in enumerate(ORDER):
        hl = name == "Maya"
        if hl:
            d.rounded_rectangle((26, y - 10, cw - 26, y + 66), radius=16, fill=ACCENT_SOFT)
        im.alpha_composite(chip(FRIENDS[i][0], FRIENDS[i][1], 48), (44, y))
        d.text((110, y + 8), f"Seat {seat} · {name}", font=f(30, "Bold" if hl else "Medium"), fill=HEAD)
        amt = f"${TOTALS[i]:.2f}"
        fnt = f(32, "Bold")
        d.text((cw - 44 - d.textlength(amt, font=fnt), y + 6), amt, font=fnt, fill=ACCENT if hl else HEAD)
        y += 86
    d.line((44, y + 4, cw - 44, y + 4), fill=LINE, width=2)
    d.text((44, y + 24), "Tax (7%) and tip (20%) worked out per seat.", font=f(22, "Regular"), fill=SUB)
    d.text((44, y + 56), "Shared satay split between seats 1, 2 and 5.", font=f(22, "Regular"), fill=SUB)
    return shadowed(im, 30, (0, 20), 80)[0]


def terminal(state):
    tw, th = 420, 700
    im = layer(tw, th)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw - 1, th - 1), radius=50, fill=(38, 38, 46))
    d.rounded_rectangle((34, 40, tw - 34, 360), radius=22, fill=WHITE if state != "approved" else (232, 247, 238))
    if state == "pay":
        d.text((62, 72), "Seat 4 · Maya", font=f(30, "Bold"), fill=HEAD)
        d.text((62, 128), "$29.21", font=f(78, "Bold"), fill=ACCENT)
        d.text((62, 232), "Red curry, spring rolls,", font=f(21, "Regular"), fill=SUB)
        d.text((62, 260), "tax and tip", font=f(21, "Regular"), fill=SUB)
        d.rounded_rectangle((62, 300, tw - 62, 340), radius=20, fill=ACCENT)
        t = "Tap to pay"
        d.text(((tw - d.textlength(t, font=f(22, "Bold"))) / 2, 307), t, font=f(22, "Bold"), fill=WHITE)
    else:
        d.ellipse((tw / 2 - 52, 80, tw / 2 + 52, 184), fill=GOOD)
        d.line((tw / 2 - 24, 132, tw / 2 - 6, 152), fill=WHITE, width=12)
        d.line((tw / 2 - 8, 152, tw / 2 + 28, 112), fill=WHITE, width=12)
        for t, y, fn in (("Approved", 210, f(40, "Bold")), ("Seat 4 · $29.21", 270, f(28, "SemiBold"))):
            d.text(((tw - d.textlength(t, font=fn)) / 2, y), t, font=fn, fill=HEAD if y > 220 else GOOD)
    for r in range(4):
        for c in range(3):
            x, y = 64 + c * 104, 400 + r * 70
            d.rounded_rectangle((x, y, x + 84, y + 54), radius=14, fill=(62, 62, 74))
    return shadowed(im, 30, (0, 20), 90)[0]


def paid_row(n_paid):
    im = layer(6 * 92, 120)
    d = ImageDraw.Draw(im)
    for i in range(6):
        c = FRIENDS[i][1] if i < n_paid else (205, 200, 194)
        im.alpha_composite(chip(FRIENDS[i][0], c, 70), (i * 92, 0))
        if i < n_paid:
            d.ellipse((i * 92 + 46, 46, i * 92 + 74, 74), fill=GOOD, outline=WHITE, width=3)
            d.line((i * 92 + 53, 60, i * 92 + 58, 66), fill=WHITE, width=3)
            d.line((i * 92 + 58, 66, i * 92 + 67, 54), fill=WHITE, width=3)
    t = f"{n_paid} of 6 paid"
    d.text((0, 84), t, font=f(26, "SemiBold"), fill=GOOD if n_paid == 6 else SUB)
    return im


def stat_card(title, body, icon):
    im = layer(720, 150)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 719, 149), radius=24, fill=CARD)
    d.ellipse((30, 37, 106, 113), fill=ACCENT_SOFT)
    d.text((68 - d.textlength(icon, font=f(36, "Bold")) / 2, 52), icon, font=f(36, "Bold"), fill=ACCENT)
    d.text((134, 34), title, font=f(32, "Bold"), fill=HEAD)
    d.text((134, 84), body, font=f(23, "Regular"), fill=SUB)
    return shadowed(im, 22, (0, 12), 50)[0]


def big_price():
    im = layer(700, 200)
    d = ImageDraw.Draw(im)
    d.text((0, 0), "$29", font=f(170, "Bold"), fill=ACCENT)
    x = d.textlength("$29", font=f(170, "Bold")) + 40
    d.text((x, 70), "$39", font=f(90, "Bold"), fill=(190, 182, 174))
    w = d.textlength("$39", font=f(90, "Bold"))
    d.line((x - 6, 128, x + w + 6, 110), fill=(190, 182, 174), width=8)
    return im


# ---------- scenes ----------

def L(im, x, y, t=0.0, anim="up", out=None):
    return dict(im=im, x=x, y=y, t=t, anim=anim, out=out)


def scenes():
    friends_row = layer(5 * 92, 80)
    for i, (l, c) in enumerate([FRIENDS[k] for k in (0, 1, 2, 4, 5)]):
        friends_row.alpha_composite(chip(l, c, 76), (i * 92, 0))
    money = text_block(["$35"], 130, (244, 160, 125), "Bold")
    money_note = text_block(["for dinner", "this Friday"], 34, (170, 160, 152), "Medium")

    S = []
    S.append(dict(bg="dark", vo="Same Friday night, same friends. This time, the restaurant does the splitting.", els=[
        L(label("A SplitSeat story", (250, 160, 110)), 0, 440, 0.2, "fade"),
        L(text_block(["Same Friday night."], 84, WHITE), 0, 500, 0.6, "fade"),
    ], center=True))
    S.append(dict(bg="light", vo="Remember Maya? Grad student. Five close friends. And thirty five dollars for dinner.", els=[
        L(maya(1.55, "happy"), 220, 150, 0.0, "fade"),
        L(label("Meet Maya again"), 820, 250, 0.2),
        L(text_block(["Grad student.", "Five close friends."], 76, HEAD), 820, 300, 0.5),
        L(friends_row, 820, 520, 1.6),
        L(money, 820, 640, 3.3),
        L(money_note, 1100, 690, 3.5),
    ]))
    S.append(dict(bg="dark", vo="Last time, the bill was split six ways. She paid fifty two dollars for an eighteen dollar meal, and said nothing. Asking for separate checks felt like admitting she couldn't afford it.", els=[
        L(receipt_old(), 90, 140, 0.3),
        L(maya(1.45, "sad"), 1230, 170, 0.0, "fade"),
        L(bubble("\u201cI just didn\u2019t want to be that person.\u201d"), 1080, 760, 7.6),
    ]))
    S.append(dict(bg="light", vo="This Friday, they go to a restaurant with SplitSeat. Everyone orders as usual. The server's tablet saves each dish to a seat, and the shared satay goes only to the three friends who ate it.", els=[
        L(label("Step 1 · Order as usual"), 120, 330, 0.2),
        L(text_block(["Every dish is", "saved to a seat."], 72, HEAD), 120, 380, 0.4),
        L(text_block(["Shared plates go only to", "the seats that shared them."], 32, SUB, "Regular"), 120, 580, 1.2),
        L(pos_tablet(), 760, 120, 0.6),
    ]))
    S.append(dict(bg="light", vo="When the check comes, it's already split. Each seat has its own total, with tax and tip worked out. Maya's is twenty nine dollars and twenty one cents.", els=[
        L(label("Step 2 · The check comes split"), 120, 330, 0.2),
        L(text_block(["One check.", "Six totals."], 72, HEAD), 120, 380, 0.4),
        L(text_block(["Nobody has to ask the", "server to split it."], 32, SUB, "Regular"), 120, 580, 1.2),
        L(split_check(), 1000, 20, 0.6),
    ]))
    S.append(dict(bg="light", vo="The server brings one card reader. Each person taps their own card for their own seat. Six taps, and the table is done.", els=[
        L(label("Step 3 · Tap your own card"), 120, 330, 0.2),
        L(text_block(["As fast as", "one card."], 72, HEAD), 120, 380, 0.4),
        L(terminal("pay"), 1060, 90, 0.5, "up", out=3.4),
        L(terminal("approved"), 1060, 90, 3.4, "fade"),
        L(paid_row(0), 120, 640, 1.0, "fade", out=4.2),
        L(paid_row(1), 120, 640, 4.2, "none", out=4.6),
        L(paid_row(3), 120, 640, 4.6, "none", out=5.0),
        L(paid_row(6), 120, 640, 5.0, "none"),
    ]))
    S.append(dict(bg="light", vo="An even split would have cost her thirty nine dollars. She paid twenty nine, for exactly what she ordered, without saying a word.", els=[
        L(label("The result"), 120, 300, 0.2),
        L(text_block(["Nothing to ask."], 76, HEAD), 120, 350, 0.4),
        L(big_price(), 120, 470, 0.9),
        L(text_block(["An even split would have been $39.37."], 32, SUB, "Regular"), 120, 690, 1.6),
        L(maya(1.45, "happy"), 1280, 170, 0.0, "fade"),
        L(bubble("\u201cThat was actually easy.\u201d"), 1210, 770, 5.0),
    ]))
    S.append(dict(bg="light", vo="And for the restaurant, there are no more re-run bills or six separate checks. SplitSeat works with the seat numbers most point of sale systems already use.", els=[
        L(label("For the restaurant"), 120, 330, 0.2),
        L(text_block(["One reader.", "No re-runs."], 72, HEAD), 120, 380, 0.4),
        L(stat_card("No re-run bills", "Servers stop splitting checks by hand.", "\u21ba"), 1000, 220, 1.0),
        L(stat_card("Faster table turns", "No waiting while six cards get run.", "\u00bb"), 1000, 420, 1.8),
        L(stat_card("Uses seat numbers", "Built on what most POS systems support.", "#"), 1000, 620, 2.6),
    ]))
    end_counts = layer(1000, 200)
    d = ImageDraw.Draw(end_counts)
    for i, (n, t) in enumerate((("6", "friends"), ("6", "cards"), ("0", "awkward asks"))):
        cx = 170 + i * 330
        col = (250, 160, 110) if n == "0" else WHITE
        d.text((cx - d.textlength(n, font=f(110, "Bold")) / 2, 0), n, font=f(110, "Bold"), fill=col)
        d.text((cx - d.textlength(t, font=f(30, "Medium")) / 2, 140), t, font=f(30, "Medium"), fill=(200, 196, 210))
    brand = layer(760, 150)
    bd = ImageDraw.Draw(brand)
    brand.alpha_composite(logo(130), (0, 10))
    bd.text((160, 22), "Split", font=f(100, "Bold"), fill=WHITE)
    bd.text((160 + bd.textlength("Split", font=f(100, "Bold")), 22), "Seat", font=f(100, "Bold"), fill=(250, 160, 110))
    S.append(dict(bg="dark", vo="Six friends. Six cards. Zero awkward asks. SplitSeat. Pay for your own order, without anyone having to ask.", els=[
        L(end_counts, 0, 230, 0.2, "fade"),
        L(brand, 0, 560, 3.2, "fade"),
        L(text_block(["Pay for your own order, without anyone having to ask."], 38, (220, 216, 228), "Medium"), 0, 760, 3.8, "fade"),
    ], center=True))
    return S


# ---------- audio ----------

async def tts(text, path):
    import edge_tts
    await edge_tts.Communicate(text, VOICE, rate="-4%").save(path)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]).decode().strip())


def make_music(total, path, sr=44100):
    t = np.arange(int(total * sr)) / sr
    chords = [[220.0, 277.18, 329.63], [174.61, 220.0, 261.63], [261.63, 329.63, 392.0], [196.0, 246.94, 293.66]]
    seg = 4.0
    out = np.zeros_like(t)
    for i in range(int(total / seg) + 1):
        s0 = i * seg
        idx = (t >= s0 - 0.5) & (t < s0 + seg + 1.5)
        tt = t[idx] - s0
        env = np.clip((tt + 0.5) / 1.2, 0, 1) * np.clip((seg + 1.5 - tt) / 1.6, 0, 1)
        for fr in chords[i % 4]:
            out[idx] += env * (np.sin(2 * np.pi * fr * t[idx]) + 0.3 * np.sin(2 * np.pi * fr * 2 * t[idx]))
    out *= np.clip(t / 2, 0, 1) * np.clip((total - t) / 3, 0, 1)
    out = out / np.max(np.abs(out)) * 0.09
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


# ---------- render ----------

def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


_alpha_cache = {}


def faded(im, a):
    key = (id(im), round(a, 2))
    if key not in _alpha_cache:
        c = im.copy()
        c.putalpha(c.split()[3].point(lambda v: int(v * a)))
        _alpha_cache[key] = c
    return _alpha_cache[key]


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
            a = 0 if e["anim"] == "none" else min(a, 1 - ease((t - e["out"]) / 0.25))
            if a <= 0:
                continue
        dy = int((1 - a) * 40) if e["anim"] == "up" else 0
        im = e["im"] if a >= 0.999 else faded(e["im"], a)
        img.alpha_composite(im, (int(e["x"]), int(e["y"] + dy)))
    d = ImageDraw.Draw(img)
    d.rectangle((0, H - 8, int(W * progress), H), fill=ACCENT)
    return img.convert("RGB")


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
    for sc in S:
        sc["vo_dur"] = duration(sc["audio"])
        sc["dur"] = LEAD + sc["vo_dur"] + TAIL
        sc["start"] = start
        start += sc["dur"]
    total = start + 0.8
    json.dump([{k: sc[k] for k in ("vo", "start", "dur")} for sc in S], open(os.path.join(BUILD, "timeline.json"), "w"), indent=1)

    video = os.path.join(BUILD, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                           "-pix_fmt", "yuv420p", video], stdin=subprocess.PIPE)
    n = int(total * FPS)
    last = {}
    for fi in range(n):
        gt = fi / FPS
        prog = gt / total
        idx = max(i for i, sc in enumerate(S) if sc["start"] <= gt) if gt < S[-1]["start"] + S[-1]["dur"] else len(S) - 1
        sc = S[idx]
        lt = gt - sc["start"]
        if idx > 0 and lt < TRANS:
            prev = S[idx - 1]
            a_img = frame(prev, prev["dur"], prog)
            b_img = frame(sc, lt, prog)
            off = int(W * ease(lt / TRANS))
            out = Image.new("RGB", (W, H))
            out.paste(a_img, (-off, 0))
            out.paste(b_img, (W - off, 0))
            img = out
        else:
            img = frame(sc, lt, prog)
        ff.stdin.write(img.tobytes())
        if fi % 300 == 0:
            print(f"frame {fi}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()

    music = os.path.join(BUILD, "music.wav")
    make_music(total, music)
    inputs, filters = ["-i", music], []
    for i, sc in enumerate(S):
        inputs += ["-i", sc["audio"]]
        ms = int((sc["start"] + LEAD) * 1000)
        filters.append(f"[{i + 1}:a]adelay={ms}|{ms},aresample=44100[v{i}]")
    mix = "".join(f"[v{i}]" for i in range(len(S)))
    filters.append(f"[0:a]volume=1.0[m];{mix}amix=inputs={len(S)}:normalize=0,volume=1.0[vo];[vo][m]amix=inputs=2:normalize=0[a]")
    audio = os.path.join(BUILD, "audio.m4a")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(filters),
                          "-map", "[a]", "-t", f"{total:.2f}", "-c:a", "aac", "-b:a", "160k", audio])
    final = os.path.join(OUT, "SplitSeat_Maya_Story.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", audio, "-c:v", "copy", "-c:a", "copy",
                           "-shortest", "-movflags", "+faststart", final])
    print("done", final, round(total, 1), "s")


def preview():
    S = scenes()
    for sc in S:
        place(sc)
    thumbs = []
    for sc in S:
        last_t = max(e["t"] for e in sc["els"]) + 1.0
        thumbs.append(frame(sc, last_t, 0.5).resize((640, 360)))
    sheet = Image.new("RGB", (640 * 3, 360 * 3), WHITE)
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % 3) * 640, (i // 3) * 360))
    sheet.save(os.path.join(BUILD, "preview.jpg"))
    for i in (1, 3, 4, 5):
        sc = S[i]
        frame(sc, max(e["t"] for e in sc["els"]) + 1.0, 0.5).save(os.path.join(BUILD, f"scene{i}.jpg"))


if __name__ == "__main__":
    import sys
    preview() if "--preview" in sys.argv else main()
