"""Draws the report's figures into results/: the oven's model (SolidCraft snapshots of
model/oven-view.solidcraft), the three doors in their CAD models, and |E| on the planes A–D
from the CSVs the solves wrote (results/real/). Run from the report's folder after the solves:
python3 scripts/figures.py [model] [doors] [planes]"""
import os, shutil, subprocess, sys
from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL, RESULTS = os.path.join(HERE, "model"), os.path.join(HERE, "results")
FONT = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 64)
CENTRE = [330, 330, 240]   # the cavity's middle in the design's frame (mm)


def solidcraft(*args):
    """solidcraft-cli on PATH, else the flatpak."""
    if shutil.which("solidcraft-cli"):
        cmd = ["solidcraft-cli", *args]
    else:
        cmd = ["flatpak", "run", f"--filesystem={HERE}", "--command=solidcraft-cli", "io.tangencylabs.solidcraft", *args]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def snapshot(out, yaw, pitch, distance, *extra):
    camera = '{"target": %s, "yaw": %s, "pitch": %s, "distance": %s}' % (CENTRE, yaw, pitch, distance)
    solidcraft("snapshot", "--in", os.path.join(MODEL, "oven-view.solidcraft"), "--out", out, "--width", "1400", "--height", "1050",
               "--camera", camera, "--no-grid", "--no-axes", *extra)
    return out


def cropped(path, pad=20):
    """The picture cut to what differs from its background (each row's colour at its left edge:
    SolidCraft's background is a vertical gradient)."""
    im = Image.open(path).convert("RGB")
    bg = im.crop((0, 0, 1, im.height)).resize(im.size)
    diff = ImageChops.difference(im, bg).convert("L").point([0] * 13 + [255] * 243)
    box = diff.getbbox() or (0, 0, *im.size)
    box = (max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, im.width), min(box[3] + pad, im.height))
    return im.crop(box)


def row(images, out, height=700, gap=40):
    """Images side by side at one height, each labelled (a), (b), … in its top left corner."""
    scaled = [im.resize((round(im.width * height / im.height), height)) for im in images]
    width = sum(im.width for im in scaled) + gap * (len(scaled) - 1)
    canvas = Image.new("RGB", (width, height + 90), "white")
    x = 0
    for i, im in enumerate(scaled):
        canvas.paste(im, (x, 90))
        ImageDraw.Draw(canvas).text((x + 10, 0), f"({chr(97 + i)})", fill="black", font=FONT)
        x += im.width + gap
    canvas.save(out)


def model():
    tmp = os.path.join(RESULTS, "model-parts")
    os.makedirs(tmp, exist_ok=True)
    colours = ["--body", "turntable:color=#7fb8d9", "--body", "water:color=#2a6fdb"]
    shots = [
        snapshot(os.path.join(tmp, "outside.png"), -0.45, 0.25, 1500),
        snapshot(os.path.join(tmp, "inside.png"), -0.75, 0.45, 1500, "--body", "shell:opacity=0.18", "--body", "door:opacity=0.3", *colours),
        snapshot(os.path.join(tmp, "section.png"), -0.75, 0.9, 1400, "--section", "z=275", *colours),
    ]
    row([cropped(s) for s in shots], os.path.join(RESULTS, "model.png"))


def door_shot(name, out, camera, section):
    """A snapshot of model/<name>.solidcraft (1000 × 800) cut by `section`."""
    solidcraft("snapshot", "--in", os.path.join(MODEL, f"{name}.solidcraft"), "--out", out, "--width", "1000", "--height", "800",
               "--camera", camera, "--no-grid", "--no-axes", "--section", section)
    return Image.open(out).convert("RGB")


def note(im, text, at, to=None):
    """A label at `at` (pixels), with a leader to `to` when given."""
    d = ImageDraw.Draw(im)
    if to:
        d.line([at, to], fill="black", width=4)
        d.ellipse([to[0] - 7, to[1] - 7, to[0] + 7, to[1] + 7], fill="black")
    d.text(at, text, fill="black", font=SMALL, anchor="mm", stroke_width=6, stroke_fill="white")


def doors():
    """The three doors in the CAD models: the door's inner face seen from the cavity (the shell cut
    away just behind it, y = 160.5) and the lower rim cut down the middle (x = a/2, outside on the
    left), the same parts labelled as in the schematics: results/doors-cad.png."""
    tmp = os.path.join(RESULTS, "model-parts")
    os.makedirs(tmp, exist_ok=True)
    inner_cam = '{"target": [300,140,210], "yaw": 2.85, "pitch": 0.3, "distance": 950}'
    rim_cam = '{"target": [270,152,88], "yaw": -1.57, "pitch": 0.05, "distance": 170}'
    tops, bottoms = [], []
    for name, _ in NAMES:
        top = door_shot(name, os.path.join(tmp, f"{name}-inner.png"), inner_cam, "y=160.5")
        rim = door_shot(name, os.path.join(tmp, f"{name}-rim.png"), rim_cam, "x=270")
        note(top, "panel", (270, 640), (270, 450))
        note(rim, "door", (430, 360))
        note(rim, "cavity", (780, 120))
        note(rim, "body", (780, 520))
        note(rim, "outside", (150, 700))
        note(rim, "gap", (640, 720), (563, 560))
        if name == "oven-choke":
            note(top, "ring groove", (520, 120), (520, 255))
            note(rim, "groove", (330, 560), (470, 450))
        if name == "oven-slotted":
            note(top, "slots", (420, 120), (420, 260))
            note(rim, "lip, channel", (300, 560), (535, 420))
        tops.append(top.crop((180, 90, 880, 680)))
        bottoms.append(rim.crop((60, 0, 1000, 780)))
    gap, head, side = 40, 90, 0
    width = 3 * 940 + 2 * gap
    canvas = Image.new("RGB", (width, head + 590 + 60 + 780 + 70), "white")
    d = ImageDraw.Draw(canvas)
    for i, ((_, label), top, rim) in enumerate(zip(NAMES, tops, bottoms)):
        x = side + i * (940 + gap)
        d.text((x + 470, head / 2), f"({chr(97 + i)}) {label}", fill="black", font=FONT, anchor="mm")
        canvas.paste(top, (x + 120, head))
        canvas.paste(rim, (x, head + 590 + 60))
    canvas.save(os.path.join(RESULTS, "doors-cad.png"))


# |E| on a log scale, for 1000 W into the oven: blue (weak) through green and yellow to red.
LOW, HIGH = 1.0, 1000.0                       # V/m at the colour bar's ends
LIMIT = (2 * 376.73 * 50.0) ** 0.5            # V/m: 5 mW/cm² (50 W/m²) as a plane wave's peak |E|
STOPS = [(0.0, (40, 50, 150)), (0.25, (40, 150, 220)), (0.5, (90, 200, 110)), (0.75, (245, 210, 60)), (1.0, (200, 35, 30))]
METAL = (150, 150, 155)
P_OVEN = 1000.0
SMALL = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 44)

# Each plane: its CSV columns across and up (0 x, 1 y, 2 z), the span drawn (mm) and its title.
PLANES = {
    "A": (1, 2, (40, 560), (40, 380), "A: vertical section (side view, door on the left)"),
    "B": (0, 1, (40, 620), (40, 560), "B: horizontal section at the feed (top view, door at the bottom)"),
    "C": (0, 2, (40, 620), (40, 380), "C: 2 mm in front of the door (front view)"),
    "D": (0, 2, (40, 620), (40, 380), "D: 5 cm in front of the door (front view)"),
}
# What the front planes look at (x0, z0, x1, z1 in mm, the solve's frame): model/make.py's door,
# its window and the control panel beside it (a 2 mm gap between them).
FRONT = [("door", (60, 60, 480, 360)), ("window", (160, 135, 380, 285)), ("panel", (482, 60, 565, 360))]
OUTLINES = {"C": FRONT, "D": FRONT}
NAMES = (("oven-gap", "no choke"), ("oven-choke", "ring groove"), ("oven-slotted", "slotted choke"))


def colour(v):
    """The colour of |E| = v V/m on the log scale."""
    import math
    t = min(max((math.log10(max(v, 1e-30)) - math.log10(LOW)) / (math.log10(HIGH) - math.log10(LOW)), 0.0), 1.0)
    for (t0, c0), (t1, c1) in zip(STOPS, STOPS[1:]):
        if t <= t1:
            s = (t - t0) / (t1 - t0)
            return tuple(round(a + (b - a) * s) for a, b in zip(c0, c1))
    return STOPS[-1][1]


def accepted(name):
    """The power the oven takes for 1 W incident at the feed (results.power in the solve's output)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import leak
    return next(o for o in leak.replies(os.path.join(RESULTS, "real", f"{name}.out")) if "reflected" in o and "unaccounted" in o)["reflected"]


def plane(name, tag, px=2.0):
    """|E| (V/m, for 1000 W into the oven) on plane `tag` drawn at `px` pixels per mm; points the
    mesh leaves out (metal) grey."""
    import csv, math
    across, up, (u0, u1), (v0, v1), _ = PLANES[tag]
    scale = math.sqrt(P_OVEN / (1.0 - accepted(name)))
    points = {}
    with open(os.path.join(RESULTS, "real", f"{name}-plane-{tag}.csv")) as f:
        rows = csv.reader(f)
        next(rows)
        for r in rows:
            x = [float(c) for c in r]
            e = math.sqrt(sum(x[3 + i] ** 2 for i in range(6)))
            points[(x[across], x[up])] = e * scale
    us, vs = sorted({k[0] for k in points}), sorted({k[1] for k in points})
    step = min(b - a for a, b in zip(us, us[1:]) if b - a > 1e-9)
    grid = {(round((u - us[0]) / step), round((v - vs[0]) / step)): e for (u, v), e in points.items()}
    w, h = round((u1 - u0) * px), round((v1 - v0) * px)
    im = Image.new("RGB", (w, h), METAL)
    pix = im.load()
    for i in range(w):
        a = round((u0 + (i + 0.5) / px - us[0]) / step)
        for j in range(h):
            e = grid.get((a, round((v1 - (j + 0.5) / px - vs[0]) / step)))
            if e is not None:
                pix[i, j] = colour(e)
    if tag in OUTLINES:
        d = ImageDraw.Draw(im)
        for label, (x0, z0, x1, z1) in OUTLINES[tag]:
            d.rectangle([(x0 - u0) * px, (v1 - z1) * px, (x1 - u0) * px, (v1 - z0) * px], outline="black", width=4)
            d.text((((x0 + x1) / 2 - u0) * px, (v1 - z1) * px + 8), label, fill="black", font=SMALL, anchor="mt")
    return im


def colour_bar(height):
    """The log colour bar (V/m) with the 5 mW/cm² mark."""
    import math
    bar = Image.new("RGB", (330, height), "white")
    d = ImageDraw.Draw(bar)
    top, bottom = 30, height - 30
    lg = lambda v: bottom - (math.log10(v) - math.log10(LOW)) / (math.log10(HIGH) - math.log10(LOW)) * (bottom - top)
    for y in range(top, bottom):
        v = 10 ** (math.log10(LOW) + (bottom - y) / (bottom - top) * (math.log10(HIGH) - math.log10(LOW)))
        d.line([(0, y), (60, y)], fill=colour(v))
    for v in (1, 10, 100, 1000):
        d.line([(60, lg(v)), (75, lg(v))], fill="black", width=3)
        d.text((85, lg(v)), f"{v}", fill="black", font=SMALL, anchor="lm")
    y = lg(LIMIT)
    d.line([(0, y), (75, y)], fill="black", width=5)
    d.text((85, y), "limit", fill="black", font=SMALL, anchor="lm")
    return bar


def plane_figure(tag):
    """Plane `tag` for the three doors side by side, one shared colour bar: results/plane-<tag>.png."""
    if not all(os.path.exists(os.path.join(RESULTS, "real", f"{n}-plane-{tag}.csv")) for n, _ in NAMES):
        return
    shots = [(plane(n, tag), label) for n, label in NAMES]
    gap, head, left = 40, 80, 110
    w = left + sum(im.width for im, _ in shots) + gap * len(shots) + 330
    h = shots[0][0].height + head + 140
    canvas = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(canvas)
    _, _, (u0, u1), (v0, v1), _ = PLANES[tag]
    px = shots[0][0].width / (u1 - u0)
    for v in range(100 * (int(v0) // 100 + 1), int(v1) + 1, 100):    # the up axis (mm), left
        y = head + (v1 - v) * px
        d.line([(left - 15, y), (left, y)], fill="black", width=3)
        d.text((left - 20, y), f"{v}", fill="black", font=SMALL, anchor="rm")
    x = left
    for im, label in shots:
        canvas.paste(im, (x, head))
        d.rectangle([x, head, x + im.width - 1, head + im.height - 1], outline="black", width=2)
        for u in range(100 * (int(u0) // 100 + 1), int(u1) + 1, 100):    # the across axis (mm)
            ux = x + (u - u0) * px
            d.line([(ux, head + im.height), (ux, head + im.height + 15)], fill="black", width=3)
            d.text((ux, head + im.height + 18), f"{u}", fill="black", font=SMALL, anchor="mt")
        d.text((x + im.width / 2, head / 2), label, fill="black", font=FONT, anchor="mm")
        x += im.width + gap
    canvas.paste(colour_bar(shots[0][0].height + 60), (x, head - 30))
    d.text((x + 20, h - 40), "|E| (V/m)", fill="black", font=SMALL, anchor="lm")
    d.text((left, h - 40), "mm", fill="black", font=SMALL, anchor="lm")
    canvas.save(os.path.join(RESULTS, f"plane-{tag}.png"))


if __name__ == "__main__":
    what = sys.argv[1:] or ["model", "doors", "planes"]
    if "model" in what:
        model()
    if "doors" in what:
        doors()
    if "planes" in what:
        for tag in PLANES:
            plane_figure(tag)
