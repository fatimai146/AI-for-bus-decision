import asyncio
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
OUT = os.path.dirname(os.path.abspath(__file__))
SCENES_DIR = os.path.join(OUT, "restaurant_scenes")
BUILD = os.path.join(OUT, "build_restaurant")
os.makedirs(BUILD, exist_ok=True)
FINAL = os.path.join(OUT, "SplitSeat_Restaurant_Story.mp4")

FONT_DIR = "/usr/share/fonts/truetype/macos/"
VOICE = "en-US-AndrewNeural"

PLUM, PLUM_D = (70, 30, 78), (34, 13, 40)
MUSTARD = (240, 178, 50)
ROSE = (222, 104, 128)
INK = (44, 24, 50)
SUB = (120, 100, 118)
CARD = (255, 251, 247)
LINE = (236, 222, 226)
PAID = (120, 64, 168)
WHITE = (255, 255, 255)


def f(size, weight="Bold"):
    return ImageFont.truetype(FONT_DIR + f"Inter-{weight}.ttf", size)


def layer(w, h):
    return Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))


def shadowed(im, radius=24, offset=(0, 14), alpha=120):
    pad = radius * 3
    out = layer(im.width + pad * 2, im.height + pad * 2)
    sh = Image.new("RGBA", im.size, (10, 0, 12, 255))
    sh.putalpha(im.split()[3].point(lambda v: v * alpha // 255))
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(radius))
    out.alpha_composite(im, (pad, pad))
    return out, pad


def chip(letter, color, size=48):
    k = 4
    im = layer(size * k, size * k)
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size * k - 1, size * k - 1), fill=color)
    fnt = f(int(size * 0.46 * k))
    d.text(((size * k - d.textlength(letter, font=fnt)) / 2, size * k * 0.2), letter, font=fnt, fill=WHITE)
    return im.resize((size, size), Image.LANCZOS)


def logo(size=120, hole=PLUM):
    k = 4
    s = size * k
    im = layer(s, s)
    d = ImageDraw.Draw(im)
    for i in range(6):
        d.pieslice((0, 0, s - 1, s - 1), -90 + i * 60 + 3, -90 + (i + 1) * 60 - 3, fill=[MUSTARD, ROSE][i % 2])
    d.ellipse((s * 0.3, s * 0.3, s * 0.7, s * 0.7), fill=hole)
    return im.resize((size, size), Image.LANCZOS)


PEOPLE = [("Seat 1", "B", (150, 110, 40), 56), ("Seat 2", "M", (110, 50, 90), 52), ("Seat 3 · Lily", "L", ROSE, 19),
          ("Seat 4", "K", (60, 70, 110), 61), ("Seat 5", "Z", (190, 140, 40), 47), ("Seat 6", "O", (50, 90, 80), 53)]
assert sum(p[3] for p in PEOPLE) == 288


def check_card(stage):
    w, h = 560, 360 if stage == 0 else 520
    im = layer(w, h)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=26, fill=CARD)
    d.text((40, 34), "THE CHECK", font=f(22), fill=SUB)
    d.text((40, 70), "$288.00", font=f(80), fill=INK)
    d.line((40, 186, w - 40, 186), fill=LINE, width=2)
    d.text((40, 210), "Split evenly, 6 ways", font=f(30, "Medium"), fill=SUB)
    t = "$48 each"
    d.text((w - 40 - d.textlength(t, font=f(32)), 208), t, font=f(32), fill=INK)
    d.text((40, 268), "Easy. Fair?", font=f(26, "Medium"), fill=SUB)
    if stage:
        d.rounded_rectangle((22, 330, w - 22, 492), radius=18, fill=(253, 230, 236))
        d.text((46, 352), "Lily's order", font=f(30, "Medium"), fill=INK)
        d.text((w - 46 - d.textlength("$19", font=f(32)), 350), "$19", font=f(32), fill=INK)
        d.text((46, 410), "Lily pays", font=f(30, "Medium"), fill=INK)
        d.text((w - 46 - d.textlength("$48", font=f(32)), 408), "$48", font=f(32), fill=(200, 50, 80))
        d.text((46, 456), "Salad and a soda", font=f(22, "Regular"), fill=SUB)
    return shadowed(im)[0]


def tablet_card():
    w, h = 600, 470
    im = layer(w, h)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=32, fill=(40, 26, 44))
    d.rounded_rectangle((18, 18, w - 19, h - 19), radius=20, fill=CARD)
    d.text((44, 40), "SERVER TABLET · TABLE 6", font=f(20), fill=SUB)
    d.text((44, 72), "Every item saved to a seat", font=f(30), fill=INK)
    rows = [("B", PEOPLE[0][2], "Seat 1", "Steak frites, 2 margaritas"),
            ("M", PEOPLE[1][2], "Seat 2", "Pasta, mojito, old fashioned"),
            ("L", ROSE, "Seat 3 · Lily", "Caesar salad, soda"),
            ("K", PEOPLE[3][2], "Seat 4", "Ribeye, 2 IPAs")]
    y = 136
    for ini, col, seat, items in rows:
        hl = ini == "L"
        if hl:
            d.rounded_rectangle((32, y - 10, w - 32, y + 66), radius=14, fill=(253, 230, 236), outline=ROSE, width=3)
        im.alpha_composite(chip(ini, col, 44), (46, y + 1))
        d.text((106, y), seat, font=f(24), fill=INK)
        d.text((106, y + 32), items, font=f(21, "Regular"), fill=INK if hl else SUB)
        y += 80
    d.text((44, y + 2), "+ 2 more seats", font=f(20, "Medium"), fill=SUB)
    return shadowed(im)[0]


def seats_card(n_paid):
    w, h = 560, 600
    im = layer(w, h)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=26, fill=CARD)
    d.text((40, 32), "THE CHECK, SPLIT BY SEAT", font=f(22), fill=SUB)
    y = 84
    for i, (seat, ini, col, amt) in enumerate(PEOPLE):
        paid = i < n_paid
        hl = ini == "L"
        if hl:
            d.rounded_rectangle((20, y - 8, w - 20, y + 64), radius=14, fill=(253, 230, 236))
        im.alpha_composite(chip(ini, col, 48), (40, y))
        d.text((104, y + 9), seat, font=f(28, "SemiBold" if not hl else "Bold"), fill=INK)
        a = f"${amt}"
        d.text((w - 170 - d.textlength(a, font=f(30)), y + 8), a, font=f(30), fill=INK)
        if paid:
            d.rounded_rectangle((w - 150, y + 8, w - 40, y + 50), radius=21, fill=(238, 228, 248))
            d.text((w - 133, y + 14), "Paid", font=f(24), fill=PAID)
        y += 84
    return shadowed(im)[0]


def result_card():
    w, h = 620, 250
    im = layer(w, h)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=28, fill=CARD)
    d.text((44, 30), "LILY PAID", font=f(22), fill=SUB)
    d.text((44, 62), "$19", font=f(130), fill=ROSE)
    x = 44 + d.textlength("$19", font=f(130)) + 40
    d.text((x, 118), "not $48", font=f(52), fill=(180, 168, 178))
    tw = d.textlength("$48", font=f(52))
    nx = x + d.textlength("not ", font=f(52))
    d.line((nx - 4, 156, nx + tw + 4, 146), fill=(180, 168, 178), width=6)
    return shadowed(im)[0]


def subtitle(text):
    fnt = f(40, "SemiBold")
    words, lines, cur = text.split(), [], ""
    dd = ImageDraw.Draw(layer(1, 1))
    for w_ in words:
        t = (cur + " " + w_).strip()
        if dd.textlength(t, font=fnt) > 1400 and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = t
    lines.append(cur)
    lw = max(dd.textlength(l, font=fnt) for l in lines)
    im = layer(lw + 64, 56 * len(lines) + 36)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=18, fill=(20, 8, 24, 190))
    for i, l in enumerate(lines):
        d.text(((im.width - dd.textlength(l, font=fnt)) / 2, 16 + i * 56), l, font=fnt, fill=WHITE)
    return im


def title_card(lines_big, small=None, with_logo=False):
    y_, x_ = np.mgrid[0:H, 0:W].astype(np.float32)
    t = np.clip(np.hypot((x_ - W / 2) / W, (y_ - H / 2) / H) * 1.8, 0, 1)
    arr = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        arr[..., i] = PLUM[i] * (1 - t) + PLUM_D[i] * t
    im = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(im)
    y = H / 2 - 90
    if with_logo:
        lg = logo(140)
        word = f(110)
        total = 140 + 30 + d.textlength("SplitSeat", font=word)
        x = (W - total) / 2
        im.paste(lg, (int(x), int(y - 30)), lg)
        d.text((x + 170, y - 30), "Split", font=word, fill=WHITE)
        d.text((x + 170 + d.textlength("Split", font=word), y - 30), "Seat", font=word, fill=MUSTARD)
        y += 150
    for l in lines_big:
        d.text(((W - d.textlength(l, font=f(64))) / 2, y), l, font=f(64), fill=WHITE)
        y += 84
    if small:
        d.text(((W - d.textlength(small, font=f(38, "Medium"))) / 2, y + 10), small, font=f(38, "Medium"),
               fill=(236, 220, 238))
    return im


def O(im, x, y, t, out=None, fade=True, scale=0.8, left=False):
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    px = -10 if left else W - im.width + 10
    py = y if left else max(0, int(y * scale) - 20)
    return dict(im=im, x=px, y=py, t=t, out=out, fade=fade)


def scene_list():
    S = [
        dict(img="lily_s1_wide.jpg", zoom=(1.0, 1.12), focus=(0.47, 0.45),
             lines=["Friday night. Six friends, one table.", "Five of them order cocktails. Lily orders a soda."],
             overlays=[]),
        dict(img="lily_s2_check.jpg", zoom=(1.04, 1.1), focus=(0.4, 0.5),
             lines=["Then the check comes, and someone says, let's just split it.",
                    "That's forty eight dollars each. Lily's order was nineteen."],
             overlays=[O(check_card(0), 1230, 60, 1.0, out="L1"), O(check_card(1), 1230, 60, "L1", fade=False)]),
        dict(img="lily_s3_quiet.jpg", zoom=(1.0, 1.14), focus=(0.48, 0.42),
             lines=["Asking for separate checks feels petty.", "So she hands over her card, and says nothing."],
             overlays=[]),
        dict(title=(["What if nobody had to ask?"], None),
             lines=["What if nobody had to ask?"], overlays=[]),
        dict(img="lily_s4_order.jpg", zoom=(1.08, 1.0), focus=(0.4, 0.45),
             lines=["At a restaurant with SplitSeat, the server's tablet saves every dish and drink to a seat,",
                    "right as it's ordered."],
             overlays=[O(tablet_card(), 1160, 70, 1.2)]),
        dict(img="lily_s5_tap.jpg", zoom=(1.0, 1.1), focus=(0.42, 0.5),
             lines=["When the check comes, it's already split by seat.",
                    "Everyone taps their own card. Nobody has to ask."],
             overlays=[O(seats_card(0), 1220, 40, 0.6, out="L1+0.6"), O(seats_card(1), 1220, 40, "L1+0.6", out="L1+1.0", fade=False),
                       O(seats_card(3), 1220, 40, "L1+1.0", out="L1+1.4", fade=False), O(seats_card(6), 1220, 40, "L1+1.4", fade=False)]),
        dict(img="lily_s6_leave.jpg", zoom=(1.12, 1.02), focus=(0.4, 0.45),
             lines=["Lily pays for what she ordered.", "Nineteen dollars, not forty eight."],
             overlays=[O(result_card(), 0, 560, "L1", scale=0.9, left=True)]),
        dict(title=([], "Pay for your own order, without anyone having to ask.", True),
             lines=["SplitSeat. Pay for your own order, without anyone having to ask."], overlays=[]),
    ]
    return S


_img_cache = {}


def base_image(name):
    if name not in _img_cache:
        im = Image.open(os.path.join(SCENES_DIR, name)).convert("RGB")
        _img_cache[name] = im.resize((int(W * 1.2), int(H * 1.2)), Image.LANCZOS)
    return _img_cache[name]


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def camera(sc, p):
    big = base_image(sc["img"])
    z0, z1 = sc["zoom"]
    z = z0 + (z1 - z0) * smooth(p)
    bw, bh = big.size
    cw, ch = bw / z, bh / z
    fx, fy = sc["focus"]
    cx = min(max(fx * bw, cw / 2), bw - cw / 2)
    cy = min(max(fy * bh, ch / 2), bh - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return big.resize((W, H), Image.BILINEAR, box=box)


_fade = {}


def faded(im, a):
    key = (id(im), round(a, 2))
    if key not in _fade:
        c = im.copy()
        c.putalpha(c.split()[3].point(lambda v: int(v * a)))
        _fade[key] = c
    return _fade[key]


def resolve(v, sc):
    if isinstance(v, str):
        base = sc["line_starts"][1] if v.startswith("L1") else 0
        return base + (float(v.split("+")[1]) if "+" in v else 0)
    return v


def render_scene(sc, t):
    if "title" in sc:
        if "_title" not in sc:
            sc["_title"] = title_card(*sc["title"]).convert("RGBA")
        img = sc["_title"].copy()
        a = ease(t / 0.8)
        if a < 1:
            img = Image.blend(Image.new("RGBA", (W, H), PLUM_D + (255,)), img, a)
    else:
        img = camera(sc, t / sc["dur"]).convert("RGBA")
    for o in sc["overlays"]:
        t0, t1 = resolve(o["t"], sc), resolve(o["out"], sc) if o["out"] is not None else None
        if t < t0 or (t1 is not None and t >= t1):
            continue
        a = ease((t - t0) / 0.5) if o["fade"] else 1.0
        if o["out"] is None:
            a = min(a, 1 - ease((t - (sc["dur"] - 0.75)) / 0.4))
            if a <= 0:
                continue
        dy = int((1 - a) * 30)
        im = o["im"] if a >= 0.999 else faded(o["im"], a)
        img.alpha_composite(im, (o["x"], o["y"] + dy))
    for i, st in enumerate(sc["line_starts"]):
        en = sc["line_starts"][i + 1] if i + 1 < len(sc["line_starts"]) else sc["dur"] - 0.3
        if st <= t < en and "title" not in sc:
            sub = sc["_subs"][i]
            img.alpha_composite(sub, ((W - sub.width) // 2, H - sub.height - 56))
    return img.convert("RGB")


async def tts(text, path):
    import edge_tts
    await edge_tts.Communicate(text, VOICE, rate="-3%").save(path)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]).decode().strip())


def make_music(total, path, sr=48000):
    t = np.arange(int(total * sr)) / sr
    chords = [[196.0, 246.94, 293.66], [164.81, 196.0, 246.94], [130.81, 164.81, 196.0], [146.83, 185.0, 220.0]]
    seg = 4.0
    out = np.zeros_like(t)
    for i in range(int(total / seg) + 1):
        s0 = i * seg
        idx = (t >= s0 - 0.6) & (t < s0 + seg + 1.6)
        tt = t[idx] - s0
        env = np.clip((tt + 0.6) / 1.4, 0, 1) * np.clip((seg + 1.6 - tt) / 1.8, 0, 1)
        for fr in chords[i % 4]:
            out[idx] += env * (np.sin(2 * np.pi * fr * t[idx]) + 0.2 * np.sin(2 * np.pi * fr * 2 * t[idx]))
        for j, fr in enumerate(chords[i % 4]):
            pi = (t >= s0 + j * 0.5) & (t < s0 + j * 0.5 + 1.5)
            tp = t[pi] - s0 - j * 0.5
            out[pi] += 0.6 * np.exp(-tp * 3.5) * np.sin(2 * np.pi * fr * 4 * t[pi])
    out *= np.clip(t / 0.8, 0, 1) * np.clip((total - t) / 2.5, 0, 1)
    out = out / np.max(np.abs(out)) * 0.15
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


def build_timeline(S, with_audio=True):
    clips = []
    LEAD, GAP, TAIL = 0.6, 0.25, 0.9
    start = 0.0
    for si, sc in enumerate(S):
        sc["_subs"] = [subtitle(l) for l in sc["lines"]]
        sc["line_starts"] = []
        t = LEAD if si else 0.3
        for li, line in enumerate(sc["lines"]):
            path = os.path.join(BUILD, f"vo_{si}_{li}.mp3")
            if with_audio and not os.path.exists(path):
                asyncio.run(tts(line, path))
            dur = duration(path) if os.path.exists(path) else 2.5
            sc["line_starts"].append(t)
            clips.append((start + t, path))
            t += dur + GAP
        sc["dur"] = t + TAIL
        sc["start"] = start
        start += sc["dur"]
    return clips, start


def preview():
    S = scene_list()
    build_timeline(S, with_audio=False)
    thumbs = []
    for sc in S:
        thumbs.append(render_scene(sc, sc["dur"] - 0.35).resize((640, 360)))
    sheet = Image.new("RGB", (640 * 4, 360 * 2))
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % 4) * 640, (i // 4) * 360))
    sheet.save(os.path.join(BUILD, "preview.jpg"))
    for i in (1, 4, 5, 6):
        render_scene(S[i], S[i]["dur"] - 0.35).save(os.path.join(BUILD, f"scene{i}.jpg"))


def main():
    S = scene_list()
    clips, total = build_timeline(S)
    total += 0.3
    XF = 0.7
    video = os.path.join(BUILD, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                           "-pix_fmt", "yuv420p", video], stdin=subprocess.PIPE)
    for fi in range(int(total * FPS)):
        gt = fi / FPS
        idx = max(i for i, sc in enumerate(S) if sc["start"] <= gt)
        sc = S[idx]
        lt = gt - sc["start"]
        img = render_scene(sc, lt)
        if idx > 0 and lt < XF:
            prev = S[idx - 1]
            img = Image.blend(render_scene(prev, prev["dur"] - 0.01 + lt), img, smooth(lt / XF))
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()

    music = os.path.join(BUILD, "music.wav")
    make_music(total, music)
    inputs, filters = ["-i", music], []
    for i, (st, path) in enumerate(clips):
        inputs += ["-i", path]
        ms = int(st * 1000)
        filters.append(f"[{i + 1}:a]adelay={ms}|{ms},aresample=48000[v{i}]")
    mix = "".join(f"[v{i}]" for i in range(len(clips)))
    filters.append(f"{mix}amix=inputs={len(clips)}:normalize=0[vo];[vo][0:a]amix=inputs=2:normalize=0[a]")
    audio = os.path.join(BUILD, "audio.m4a")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(filters),
                          "-map", "[a]", "-t", f"{total:.2f}", "-c:a", "aac", "-ac", "2", "-ar", "48000",
                          "-b:a", "192k", audio])
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", audio, "-c:v", "copy", "-c:a", "copy",
                           "-shortest", "-movflags", "+faststart", FINAL])
    print("done", FINAL, round(total, 1), "s")


if __name__ == "__main__":
    preview() if "--preview" in sys.argv else main()
