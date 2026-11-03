from PIL import Image, ImageDraw, ImageFont

A = "storyboard_panels/"
PANELS = [A + f for f in ("splitseat_panel1_today.jpg", "splitseat_panel2_order.jpg",
                          "splitseat_panel3_check.jpg", "splitseat_panel4_tap.jpg")]
GREEN = (79, 127, 92)
DARK = (31, 42, 48)
BODY = (60, 60, 60)
GREY = (120, 120, 120)
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FB if bold else F, size)


def bubble(d, box, tail, text, size=30, fill=(255, 255, 255), color=DARK, bold=True):
    x1, y1, x2, y2 = box
    d.polygon(tail, fill=fill, outline=(200, 200, 200))
    d.rounded_rectangle(box, radius=22, fill=fill, outline=(200, 200, 200), width=2)
    d.polygon(tail, fill=fill)
    lines = text.split("\n")
    f = font(size, bold)
    lh = size + 8
    ty = (y1 + y2) / 2 - lh * len(lines) / 2 + 2
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text(((x1 + x2) / 2 - w / 2, ty), ln, font=f, fill=color)
        ty += lh


def panel1(im):
    d = ImageDraw.Draw(im)
    bubble(d, (560, 40, 1120, 160), [(640, 155), (700, 155), (560, 230)],
           "\u201cShould we just\nsplit it evenly?\u201d", 34)
    d.rounded_rectangle((40, 760, 420, 840), radius=16, fill=(255, 255, 255), outline=(200, 200, 200), width=2)
    d.text((62, 772), "Table of 5", font=font(24), fill=GREY)
    d.text((62, 800), "One total: $124.00", font=font(28, True), fill=DARK)
    return im


def panel2(im):
    d = ImageDraw.Draw(im)
    bubble(d, (40, 690, 560, 840), [(300, 695), (370, 695), (420, 600)],
           "Each dish is saved\nto a seat number", 32, fill=GREEN, color=(255, 255, 255))
    return im


def panel3(im):
    d = ImageDraw.Draw(im)
    x1, y1, x2, y2 = 640, 70, 1110, 830
    d.rounded_rectangle((x1 + 8, y1 + 10, x2 + 8, y2 + 10), radius=18, fill=(215, 210, 200))
    d.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=(255, 255, 255), outline=(190, 190, 190), width=2)
    d.text((x1 + 30, y1 + 28), "Your check, split by seat", font=font(28, True), fill=DARK)
    d.line((x1 + 30, y1 + 78, x2 - 30, y1 + 78), fill=(220, 220, 220), width=2)
    rows = [("Seat 1", "$26.40"), ("Seat 2", "$21.10"), ("Seat 3", "$18.75"),
            ("Seat 4", "$31.20"), ("Seat 5", "$26.55")]
    y = y1 + 100
    for s, amt in rows:
        hl = s == "Seat 2"
        if hl:
            d.rounded_rectangle((x1 + 18, y - 10, x2 - 18, y + 50), radius=10, fill=(229, 239, 232))
        d.text((x1 + 34, y), s, font=font(30, hl), fill=DARK)
        w = d.textlength(amt, font=font(30, True))
        d.text((x2 - 34 - w, y), amt, font=font(30, True), fill=GREEN if hl else DARK)
        y += 78
    d.line((x1 + 30, y - 6, x2 - 30, y - 6), fill=(220, 220, 220), width=2)
    note = ["Shared nachos split only among", "the seats that had them.", "Tax and tip included."]
    y += 14
    for ln in note:
        d.text((x1 + 30, y), ln, font=font(23), fill=GREY)
        y += 32
    return im


def panel4(im):
    d = ImageDraw.Draw(im)
    bubble(d, (40, 40, 560, 230), [(180, 225), (250, 225), (265, 370)],
           "Seat 2 \u00b7 $21.10\nTap to pay", 40, fill=(255, 255, 255), color=GREEN)
    return im


CAPTIONS = [
    ("1  Today", "One total. Someone has to suggest a fairer split."),
    ("2  Order as usual", "The server links each dish to your seat."),
    ("3  The check comes split", "Each seat has its own total, shared items included."),
    ("4  Tap your own card", "Pay just your total. As fast as one card. Nobody asked."),
]


def build(layout):
    pw, ph = 1152, 864
    ims = [fn(Image.open(p).convert("RGB")) for fn, p in zip((panel1, panel2, panel3, panel4), PANELS)]
    cap_h, gap, pad, head = 170, 36, 60, 190
    cols = 4 if layout == "strip" else 2
    rows = 4 // cols
    W = pad * 2 + cols * pw + (cols - 1) * gap
    H = head + rows * (ph + cap_h) + (rows - 1) * gap + pad
    c = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(c)
    d.text((pad, 50), "SplitSeat", font=font(72, True), fill=GREEN)
    tw = d.textlength("SplitSeat", font=font(72, True))
    d.text((pad + tw + 30, 72), "Pay for your own order, without anyone having to ask",
           font=font(48), fill=DARK)
    for i, im in enumerate(ims):
        r, k = divmod(i, cols)
        x = pad + k * (pw + gap)
        y = head + r * (ph + cap_h + gap)
        c.paste(im, (x, y))
        d.rectangle((x, y + ph, x + pw, y + ph + cap_h - 20), fill=(242, 243, 242))
        t, s = CAPTIONS[i]
        d.text((x + 30, y + ph + 24), t, font=font(44, True), fill=GREEN if i else DARK)
        d.text((x + 30, y + ph + 88), s, font=font(32), fill=BODY)
    return c


build("strip").save("/workspace/SplitSeat_Storyboard_Strip.png", optimize=True)
build("grid").save("/workspace/SplitSeat_Storyboard_Grid.png", optimize=True)
print("saved")
