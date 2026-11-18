"""Draws the BWO study's figures into results/ from the CSVs the runs wrote (PIL only): the output
power over time, the probe's spectrum and the particles' phase space, for each run named.
Run from the report's folder after the runs: python3 scripts/figures.py [ku] [sband]"""
import cmath, csv, json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, "results")
FONT = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
BIG, SMALL = ImageFont.truetype(FONT, 40), ImageFont.truetype(FONT, 32)
BLUE, RED, GREY = (35, 90, 200), (210, 40, 40), (150, 150, 150)


def rows(name):
    with open(os.path.join(RESULTS, name)) as f:
        r = list(csv.reader(f))
    return r[0], [[float(x) for x in row] for row in r[1:]]


def ticks(lo, hi, n=5):
    """Round tick values between lo and hi."""
    step = 10 ** math.floor(math.log10((hi - lo) / n))
    for m in (1, 2, 5, 10):
        if (hi - lo) / (step * m) <= n:
            step *= m
            break
    t = math.ceil(lo / step) * step
    out = []
    while t <= hi + 1e-9 * step:
        out.append(round(t, 10))
        t += step
    return out


class Axes:
    """A chart 1400 × 900: data coordinates to pixels, its frame, ticks and labels."""

    def __init__(self, x, y, xlabel, ylabel, title=""):
        self.im = Image.new("RGB", (1400, 900), "white")
        self.d = ImageDraw.Draw(self.im)
        self.box = (190, 90, 1350, 760)
        self.x, self.y = x, y
        l, t, r, b = self.box
        self.d.rectangle(self.box, outline="black", width=3)
        for v in ticks(*x):
            px = self.px(v, y[0])[0]
            self.d.line([(px, b), (px, b + 14)], fill="black", width=3)
            self.d.text((px, b + 20), f"{v:g}", fill="black", font=SMALL, anchor="mt")
        for v in ticks(*y):
            py = self.px(x[0], v)[1]
            self.d.line([(l - 14, py), (l, py)], fill="black", width=3)
            self.d.text((l - 20, py), f"{v:g}", fill="black", font=SMALL, anchor="rm")
        self.d.text(((l + r) / 2, b + 75), xlabel, fill="black", font=BIG, anchor="mt")
        lab = Image.new("RGBA", (700, 60), (255, 255, 255, 0))
        ImageDraw.Draw(lab).text((350, 30), ylabel, fill="black", font=BIG, anchor="mm")
        self.im.paste(lab.rotate(90, expand=True), (10, (t + b) // 2 - 350), lab.rotate(90, expand=True))
        if title:
            self.d.text(((l + r) / 2, 40), title, fill="black", font=BIG, anchor="mm")

    def px(self, x, y):
        l, t, r, b = self.box
        return (l + (x - self.x[0]) / (self.x[1] - self.x[0]) * (r - l), b - (y - self.y[0]) / (self.y[1] - self.y[0]) * (b - t))

    def line(self, xs, ys, colour, width=4):
        pts = [self.px(a, b) for a, b in zip(xs, ys) if self.x[0] <= a <= self.x[1]]
        l, t, r, b = self.box
        pts = [(a, min(max(c, t), b)) for a, c in pts]
        if len(pts) > 1:
            self.d.line(pts, fill=colour, width=width)

    def dots(self, xs, ys, colour, r=2):
        l, t, rr, b = self.box
        for a, c in zip(xs, ys):
            x, y = self.px(a, c)
            if l <= x <= rr and t <= y <= b:
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=colour)

    def legend(self, items):
        l, t, r, b = self.box
        for i, (label, colour) in enumerate(items):
            y = t + 30 + i * 50
            self.d.line([(r - 420, y), (r - 360, y)], fill=colour, width=6)
            self.d.text((r - 345, y), label, fill="black", font=SMALL, anchor="lm")

    def save(self, name):
        self.im.save(os.path.join(RESULTS, name))


def window_mean(t, p, width):
    """p averaged over windows `width` wide: (window centres, means)."""
    out_t, out_p, k = [], [], 0
    while k * width < t[-1]:
        sel = [b for a, b in zip(t, p) if k * width <= a < (k + 1) * width]
        if sel:
            out_t.append((k + 0.5) * width)
            out_p.append(sum(sel) / len(sel))
        k += 1
    return out_t, out_p


def power(run, steady):
    """The output power over time (GW, 0.5 ns means): through the plane, and less the beam's own
    steady field's power (`steady`, W) where that is not negligible (no collector)."""
    _, d = rows(f"{run}-history.csv")
    t, p = [r[0] for r in d], [r[5] / 1e9 for r in d]
    tw, pw = window_mean(t, p, 0.5)
    # The scale from 5 ns on: the beam's head entering makes a brief surge before it.
    top = max(x for a, x in zip(tw, pw) if a > 5) * 1.4
    ax = Axes((0, t[-1]), (0, top), "time (ns)", "output power (GW)")
    if steady > 0.01 * max(pw):
        ax.line(tw, pw, GREY)
        ax.line(tw, [x - steady / 1e9 for x in pw], RED)
        ax.legend([("through the plane", GREY), ("less the beam's own field", RED)])
    else:
        ax.line(tw, pw, RED)
        ax.legend([("through the output plane", RED)])
    ax.d.text((ax.px(0.3, top)[0] + 10, ax.box[1] + 120), "beam head\n(off scale)", fill=GREY, font=SMALL, anchor="la")
    ax.save(f"{run}-power.png")


def spectrum(run, f_lo, f_hi):
    """The probe's E_z over the run's second half, its amplitude spectrum (normalised, dB)."""
    _, d = rows(f"{run}-probes.csv")
    half = d[len(d) // 2:]
    t = [r[0] * 1e-9 for r in half]
    ez = [r[3] for r in half]
    mean = sum(ez) / len(ez)
    ez = [e - mean for e in ez]
    n = len(ez)
    # A Hann window, then the transform at each frequency asked.
    w = [0.5 - 0.5 * math.cos(2 * math.pi * k / (n - 1)) for k in range(n)]
    fs = [f_lo + (f_hi - f_lo) * k / 600 for k in range(601)]
    amp = [abs(sum(wk * e * cmath.exp(-2j * math.pi * f * 1e9 * tk) for wk, e, tk in zip(w, ez, t))) for f in fs]
    peak = max(amp)
    db = [20 * math.log10(max(a / peak, 1e-6)) for a in amp]
    ax = Axes((f_lo, f_hi), (-60, 5), "frequency (GHz)", "spectrum of the probe's Ez (dB)")
    ax.line(fs, db, BLUE)
    f_peak = fs[amp.index(peak)]
    ax.d.text((ax.px(f_peak, 0)[0] + 15, ax.box[1] + 20), f"{f_peak:.2f} GHz", fill=BLUE, font=BIG, anchor="lt")
    ax.save(f"{run}-spectrum.png")
    return f_peak


def phase(run):
    """The particles at the end: their kinetic energy against z."""
    name = f"{run}-phase.csv" if os.path.exists(os.path.join(RESULTS, f"{run}-phase.csv")) else f"{run}-particles.csv"
    _, d = rows(name)
    z = [r[2] for r in d]
    e = [r[6] / 1e3 for r in d]
    ax = Axes((0, max(z)), (0, max(e) * 1.1), "z (mm)", "kinetic energy (keV)")
    ax.dots(z, e, BLUE)
    ax.save(f"{run}-phase.png")


def dispersion(cell="cell.out", name="sband-dispersion.png"):
    """The S-band cell's TM01 band (results/cell.out: its Bloch phase per period against the
    frequency) with the beam lines that meet its −1 harmonic, ψ = 360° − 2πfD/v, for 550 keV and
    for a beam slowed by its own charge to 0.8c."""
    import json
    text = open(os.path.join(RESULTS, cell)).read()
    reply = json.loads(text[text.index('{\n  "m": 0'):text.index("\n}\n", text.index('{\n  "m": 0')) + 2])
    pts = [(p["phase"], p["frequency"]) for p in reply["points"] if 0.5 < p["phase"] < 179.5]
    d = reply["period"] * 1e-3
    ax = Axes((0, 180), (2.8, 4.4), "phase per period ψ (degrees)", "frequency (GHz)")
    ax.line([p for p, _ in pts], [f for _, f in pts], BLUE, 6)
    c = 299_792_458.0
    for beta, colour, label in ((0.8763, RED, "550 keV beam"), (0.80, GREY, "slowed to 0.8c")):
        fs = [2.8 + 0.01 * k for k in range(161)]
        ax.line([360 - 360 * f * 1e9 * d / (beta * c) for f in fs], fs, colour)
    ax.legend([(f"TM01 band, D = {reply['period']:g} mm", BLUE), ("550 keV beam", RED), ("beam slowed to 0.8c", GREY)])
    ax.save(name)


METAL, EDGE = (195, 199, 204), (91, 96, 102)
SCRIPTS = os.path.join(HERE, "scripts")


def wall_of(script):
    """The revolved wall's points (r, z in mm) of a run's script (scripts/<script>.json): its
    points, or those of the SolidCraft design it imports (model/<design>.script.json's profile)."""
    for c in json.load(open(os.path.join(SCRIPTS, f"{script}.json"))):
        if c["command"] == "geometry.solid":
            return c["params"]["points"]
        if c["command"] == "geometry.import":
            design = os.path.splitext(os.path.basename(c["params"]["path"]))[0]
            model = json.load(open(os.path.join(HERE, "model", f"{design}.script.json")))
            sketch = model["commands"][1]["params"]["feature"]["sketch"]
            return [[p["pos"][1], p["pos"][0]] for p in sketch["points"] if p["id"] != "origin"]
    return []


class Section:
    """The r–z half-plane of a body of revolution, `width` pixels for z from 0 to `zmax` and r
    from 0 to `rmax` (mm): the metal beyond the wall grey."""

    def __init__(self, wall, zmax, rmax, width=2400, top=60, bottom=90, left=110):
        self.zmax, self.rmax = zmax, rmax
        self.s = (width - left - 40) / zmax
        self.l, self.t = left, top
        self.w, self.h = width, int(rmax * self.s) + top + bottom
        self.im = Image.new("RGB", (self.w, self.h), "white")
        self.d = ImageDraw.Draw(self.im)
        self.wall = [(r, z) for r, z in wall if 0 < r or z > 0]
        self.metal()

    def px(self, z, r):
        return (self.l + z * self.s, self.t + (self.rmax - r) * self.s)

    def metal(self):
        inside = [self.px(z, r) for r, z in self.wall if z <= self.zmax + 1e-9 and r > 0]
        poly = inside + [self.px(self.zmax, self.rmax), self.px(0, self.rmax)]
        self.d.polygon(poly, fill=METAL)
        self.d.line(inside, fill=EDGE, width=3)

    def frame(self, step=25):
        l, t = self.px(0, self.rmax)
        r, b = self.px(self.zmax, 0)
        self.d.rectangle([l, t, r, b], outline="black", width=2)
        for z in range(0, int(self.zmax) + 1, step):
            x, _ = self.px(z, 0)
            self.d.line([(x, b), (x, b + 10)], fill="black", width=2)
            self.d.text((x, b + 14), f"{z}", fill="black", font=SMALL, anchor="mt")
        for rr in range(0, int(self.rmax) + 1, 10 if self.rmax < 60 else 20):
            _, y = self.px(0, rr)
            self.d.text((l - 12, y), f"{rr}", fill="black", font=SMALL, anchor="rm")
        self.d.text(((l + r) / 2, b + 50), "z (mm)", fill="black", font=SMALL, anchor="mt")
        self.d.text((l - 70, t - 30), "r (mm)", fill="black", font=SMALL, anchor="lm")

    def note(self, text, at, to=None, colour="black"):
        if to:
            a, b = self.px(*at), self.px(*to)
            self.d.line([a, b], fill=colour, width=3)
            self.d.ellipse([b[0] - 6, b[1] - 6, b[0] + 6, b[1] + 6], fill=colour)
        self.d.text(self.px(*at), text, fill=colour, font=SMALL, anchor="mm", stroke_width=5, stroke_fill="white")

    def save(self, name):
        self.im.save(os.path.join(RESULTS, name))


def sections():
    """The two BWOs' cross-sections, their parts named."""
    ku = Section(wall_of("final-ku"), 180, 22)
    ku.d.rectangle([*ku.px(0, 11), *ku.px(140, 9)], fill=(255, 205, 120))
    ku.frame()
    ku.note("drift tube", (10, 18), (10, 12.9))
    ku.note("rippled wall: 14.5 periods of 7.5 mm, r 12.9–17.1 mm", (75, 20.5), (75, 17.1))
    ku.note("output guide", (160, 20.5), (160, 17.1))
    ku.note("beam 550 kV, 1.5 kA, r 9–11 mm, 5 T", (60, 5), (60, 10))
    ku.note("field ends: the collector", (140, 4), (140, 9), RED)
    x, _ = ku.px(170, 0)
    ku.d.line([ku.px(170, 0), ku.px(170, 17.1)], fill=BLUE, width=4)
    ku.note("output plane", (170, 6), None, BLUE)
    ku.save("ku-section.png")
    sb = Section(wall_of("final-sband"), 405, 50)
    sb.d.rectangle([*sb.px(0, 30.5), *sb.px(290, 28.5)], fill=(255, 205, 120))
    sb.frame(50)
    sb.note("cut-off neck, r 31.5", (40, 21), (8, 31.5))
    sb.note("insert", (40, 40), (30, 31.6))
    sb.note("slow-wave structure: 5 periods of 44 mm", (130, 47), (120, 42.2))
    sb.note("last two shallower", (240, 47), (225, 38))
    sb.note("output horn", (330, 47), (300, 38))
    sb.note("beam 550 kV, 6.9 kA, r 28.5–30.5 mm, 2.5 T", (130, 14), (130, 29.5))
    sb.note("field ends: the collector", (290, 14), (290, 28.5), RED)
    sb.d.line([sb.px(395, 0), sb.px(395, 45)], fill=BLUE, width=4)
    sb.note("output plane", (395, 8), None, BLUE)
    sb.save("sband-section.png")


def diverging(t):
    """Blue (−1) through white (0) to red (+1)."""
    t = max(-1.0, min(1.0, t))
    if t < 0:
        return tuple(round(255 + (c - 255) * -t) for c in (40, 80, 200))
    return tuple(round(255 + (c - 255) * t) for c in (210, 40, 40))


def panel(m, f, script, zmax, rmax, vmax=None, width=2400, notes=False):
    """E_z on the r–z plane (`m`: the map's rows of one moment) with its electrons (`f`) over it:
    blue negative, red positive, scaled to `vmax` (default the moment's 98th percentile)."""
    t = m[0][1]
    vmax = vmax or sorted(abs(r[4]) for r in m)[int(0.98 * (len(m) - 1))] or 1.0
    sec = Section(wall_of(script), zmax, rmax, width=width, top=50, bottom=20)
    rs, zs = sorted({r[2] for r in m}), sorted({r[3] for r in m})
    dr = (rs[1] - rs[0]) if len(rs) > 1 else 1
    dz = (zs[1] - zs[0]) if len(zs) > 1 else 1
    for _, _, r, z, ez in m:
        if z <= zmax:
            sec.d.rectangle([sec.px(z - dz / 2, r + dr / 2), sec.px(z + dz / 2, r - dr / 2)], fill=diverging(ez / vmax))
    sec.metal()
    for row in f:
        if row[4] <= zmax:
            x, y = sec.px(row[4], math.hypot(row[2], row[3]))
            sec.d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill="black")
    sec.d.text((sec.l, 25), f"t = {t:.2f} ns", fill="black", font=BIG, anchor="lm")
    colour_bar(sec.d, sec.w - 40, 25, vmax)
    if notes:
        def arrow(z0, z1, r, colour):
            (x0, y), (x1, _) = sec.px(z0, r), sec.px(z1, r)
            sec.d.line([(x0, y), (x1, y)], fill=colour, width=8)
            head = 22 if x1 > x0 else -22
            sec.d.polygon([(x1 + head, y), (x1, y - 16), (x1, y + 16)], fill=colour)
        y_note = 0.13 * rmax
        sec.d.text(sec.px(0.02 * zmax, y_note), "beam", fill="black", font=BIG, anchor="lm", stroke_width=6, stroke_fill="white")
        arrow(0.10 * zmax, 0.18 * zmax, y_note, "black")
        arrow(0.62 * zmax, 0.30 * zmax, y_note, RED)
        sec.d.text(sec.px(0.64 * zmax, y_note), "backward wave: power flows back", fill=RED, font=SMALL, anchor="lm", stroke_width=6, stroke_fill="white")
    return sec.im


def nice(v):
    """`v` rounded to two significant figures."""
    return float(f"{v:.2g}")


def colour_bar(d, right, y, vmax, length=420, height=22):
    """The colour scale of E_z, its right end at `right`, centred on `y`: −vmax blue through 0
    white to +vmax red, in MV/m, and what the dots are."""
    text = "dots: electrons"
    x = right - d.textlength(text, font=SMALL)
    d.text((x, y), text, fill="black", font=SMALL, anchor="lm")
    hi = f"+{nice(vmax / 1e6):g} MV/m"
    x -= 40 + d.textlength(hi, font=SMALL)
    d.text((x, y), hi, fill="black", font=SMALL, anchor="lm")
    x1, x0 = x - 12, x - 12 - length
    for k in range(length):
        d.line([(x0 + k, y - height / 2), (x0 + k, y + height / 2)], fill=diverging(2 * k / (length - 1) - 1))
    d.rectangle([x0, y - height / 2, x1, y + height / 2], outline="black", width=1)
    mid = (x0 + x1) / 2
    d.line([(mid, y - height / 2 - 5), (mid, y + height / 2 + 5)], fill="black", width=2)
    d.text((x0 - 12, y), f"-{nice(vmax / 1e6):g}", fill="black", font=SMALL, anchor="rm")
    d.text((x0 - 12 - d.textlength(f"-{nice(vmax / 1e6):g}", font=SMALL) - 16, y), "E_z", fill="black", font=SMALL, anchor="rm")


def shared_scale(kept):
    """One colour scale for moments `kept`: the 98th percentile of |E_z| over all of them, so
    the field's growth shows as its colour deepening."""
    values = sorted(abs(r[4]) for m, _ in kept for r in m)
    return nice(values[int(0.98 * (len(values) - 1))]) or 1.0


def moments(tag):
    """The maps' and the particles' rows of a run (results/<tag>-maps.csv, -frames.csv), by moment."""
    _, maps = rows(f"{tag}-maps.csv")
    _, frames = rows(f"{tag}-frames.csv")
    by_map, by_frame = {}, {}
    for r in maps:
        by_map.setdefault(int(r[0]), []).append(r)
    for r in frames:
        by_frame.setdefault(int(r[0]), []).append(r)
    return [(by_map[k], by_frame.get(k, [])) for k in sorted(by_map)]


def evolution(tag, script, zmax, rmax, picks):
    """E_z on the r–z plane with the electrons over it at the moments `picks` (indices into the
    run's moments), stacked down the page, all on one colour scale."""
    kept = [mf for k, mf in enumerate(moments(f"final-{tag}")) if k in picks]
    vmax = shared_scale(kept)
    panels = [panel(m, f, script, zmax, rmax, vmax) for m, f in kept]
    if panels:
        canvas = Image.new("RGB", (panels[0].width, sum(p.height for p in panels)), "white")
        y = 0
        for p in panels:
            canvas.paste(p, (0, y))
            y += p.height
        canvas.save(os.path.join(RESULTS, f"{tag}-evolution.png"))


def animate(tag, script, zmax, rmax, fps):
    """An animation of a run's moments (results/anim-<tag>-*.csv) as results/<tag>.mp4 and
    .gif: one colour scale for all its frames (the 98th percentile over them), so the field's
    growth shows."""
    import subprocess, tempfile
    kept = moments(f"anim-{tag}")
    vmax = shared_scale(kept)
    with tempfile.TemporaryDirectory() as tmp:
        for k, (m, f) in enumerate(kept):
            im = panel(m, f, script, zmax, rmax, vmax, width=1920, notes=True)
            im = im.resize((im.width // 2 * 2, im.height // 2 * 2))
            im.save(os.path.join(tmp, f"{k:04d}.png"))
        frames = os.path.join(tmp, "%04d.png")
        mp4 = os.path.join(RESULTS, f"{tag}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", frames, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4], check=True)
        gif = os.path.join(RESULTS, f"{tag}.gif")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", frames, "-vf",
                        "scale=960:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse", "-loop", "0", gif], check=True)


def steady_of(run):
    """The output plane's steady power (W) from the run's reply (results/<run>.out)."""
    text = open(os.path.join(RESULTS, f"{run}.out")).read()
    i = text.index('"steady_w"')
    return float(text[i:].split(":")[1].split(",")[0].split("}")[0])


if __name__ == "__main__":
    asked = sys.argv[1:] or ["dispersion", "sections", "evolution", "final-ku", "final-sband"]
    if "dispersion" in asked:
        dispersion("cell-44.out", "sband-dispersion.png")
    if "sections" in asked:
        sections()
    if "animations" in asked:
        animate("sband-growth", "final-sband", 405, 50, 8)
        animate("sband-rf", "final-sband", 405, 50, 12)
        animate("ku-rf", "final-ku", 180, 22, 12)
        animate("ku-growth", "final-ku", 180, 22, 6)
    if "evolution" in asked:
        evolution("ku", "final-ku", 180, 22, [5, 9, 13, 17, 23, 29])
        evolution("sband", "final-sband", 405, 50, [5, 9, 13, 17, 23, 29])
    for run in [a for a in asked if a not in ("dispersion", "sections", "evolution", "animations")]:
        if not os.path.exists(os.path.join(RESULTS, f"{run}-history.csv")):
            continue
        power(run, steady_of(run))
        lo, hi = (13, 17) if "ku" in run else (2.5, 4.5)
        print(run, "peak", spectrum(run, lo, hi), "GHz")
        phase(run)
