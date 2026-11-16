"""Draws the report's schematics as SVG into results/: the three door seals cut across the bottom
rim (choke.svg) and where each field picture's plane lies in the oven (planes.svg). Dimensions
are model/make.py's (mm, the design's frame: the cavity's front lower left corner at 0, the door
at y < 0)."""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "results")
A, D, H, W, G, T, CW = 330, 330, 210, 45, 2, 40, 130
CS, CD, CL = 6, 30, 30            # plain groove: width, depth, distance from the cavity's edge
FS, FL, SW, SP = 8.5, 36, 2.5, 18  # slotted choke: lip from fs to fl, slots sw wide every sp

METAL, METAL_EDGE, AIR, WATER, GLASS, LEAK = "#c3c7cc", "#5b6066", "#ffffff", "#3d7fd9", "#bfe3f2", "#d62728"
GAS = "#d6ecfa"   # the air round the seals: one tint, so a groove or channel reads as air open to the gap
FONT = "font-family='Noto Sans CJK JP, sans-serif'"


class Svg:
    """A drawing in mm: x to the right, z up, `s` pixels a millimetre, the view's corner at (x0, z0)."""

    def __init__(self, x0, z0, width, height, s, dx=0, dy=0):
        self.x0, self.z0, self.w, self.h, self.s, self.dx, self.dy = x0, z0, width, height, s, dx, dy
        self.parts = []

    def p(self, x, z):
        return self.dx + (x - self.x0) * self.s, self.dy + (self.z0 + self.h - z) * self.s

    def rect(self, x1, z1, x2, z2, fill, stroke="none", width=1.0, dash=None):
        (a, b), (c, d) = self.p(min(x1, x2), max(z1, z2)), self.p(max(x1, x2), min(z1, z2))
        extra = f" stroke-dasharray='{dash}'" if dash else ""
        self.parts.append(f"<rect x='{a:.1f}' y='{b:.1f}' width='{c - a:.1f}' height='{d - b:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='{width}'{extra}/>")

    def line(self, pts, colour="black", width=1.5, dash=None, arrow=False):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in (self.p(*q) for q in pts))
        extra = (f" stroke-dasharray='{dash}'" if dash else "") + (" marker-end='url(#arrow)'" if arrow else "")
        self.parts.append(f"<polyline points='{d}' fill='none' stroke='{colour}' stroke-width='{width}'{extra}/>")

    def text(self, x, z, s, size=15, anchor="start", colour="black", weight="normal"):
        a, b = self.p(x, z)
        self.parts.append(f"<text x='{a:.1f}' y='{b:.1f}' font-size='{size}' text-anchor='{anchor}' fill='{colour}' font-weight='{weight}' {FONT}>{s}</text>")

    def label(self, x, z, tx, tz, s, size=15, anchor="start"):
        """A label at (tx, tz) with a thin leader to (x, z)."""
        self.line([(tx, tz + 1), (x, z)], colour="#333333", width=0.8)
        self.text(tx, tz, s, size, anchor)


def document(width, height, parts):
    head = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"
            "<defs><marker id='arrow' viewBox='0 0 10 10' refX='8' refY='5' markerWidth='7' markerHeight='7' orient='auto-start-reverse'>"
            f"<path d='M 0 0 L 10 5 L 0 10 z' fill='{LEAK}'/></marker></defs>"
            f"<rect width='{width}' height='{height}' fill='white'/>")
    return head + "".join(parts) + "</svg>\n"


def seal(kind, dx, title):
    """The bottom rim cut down the door's middle (x = a/2): y across (outside to the left), z up."""
    v = Svg(-50, -60, 72, 84, 7.0, dx, 50)
    v.rect(-50, -60, 22, 24, GAS)
    v.rect(0, -W, 22, 0, METAL, METAL_EDGE)                 # the cavity's floor and front flange
    v.rect(-50, -W, -G, 24, METAL, METAL_EDGE)              # the door (its outer part cut off at the left)
    if kind == "choke":
        v.rect(-G - CD, -CL - CS / 2, -G + 0.3, -CL + CS / 2, GAS, METAL_EDGE)
        v.rect(-G - 0.4, -CL - CS / 2 + 0.15, -G + 0.6, -CL + CS / 2 - 0.15, GAS)   # open to the gap
        v.label(-G - 20, -CL + CS / 2, -46, -16, "groove (λ/4)", 22)
    if kind == "slotted":
        v.rect(-G - 5, -FL - 4, -G - 1, -FS, GAS, METAL_EDGE)   # the channel behind the lip
        v.rect(-G - 1.3, -FL - 4 + 0.15, -G + 0.6, -FL - 0.15, GAS)  # its mouth to the gap
        v.label(-G - 0.5, -14, -46, -6, "slotted lip", 22)
        v.label(-G - 4.5, -26, -46, -24, "channel", 22)
    # Where the field leaks: down the gap from the cavity's edge to the outside.
    v.line([(-1, 14), (-1, -W - 1), (-9, -W - 10)], colour=LEAK, width=3, dash="7,5", arrow=True)
    v.text(11, 12, "cavity", 26, "middle", weight="bold")
    v.text(-28, 14, "door", 26, "middle", weight="bold")
    v.text(-47, -56, "outside", 26, weight="bold")
    v.text(11, -24, "body", 22, "middle")
    v.label(-1, -50, 3, -55, "gap", 22)
    v.text(-14, 27, title, 26, "middle", weight="bold")
    return v.parts


def lip(dx, dy):
    """The slotted choke's lip seen from the cavity (the plane y = −g), along the bottom rim."""
    x0, x1 = 112, 200
    v = Svg(x0, -50, x1 - x0, 58, 7.0, dx, dy)
    v.rect(x0, -50, x1, 8, METAL, METAL_EDGE)
    v.rect(x0, -FL - 4, x1, -FL, "#4a4f55")                  # the mouth: the dark of the channel
    n = int((A + 2 * FS) // SP) - 1
    first = A / 2 - (n - 1) * SP / 2
    slots = [first + k * SP for k in range(n) if x0 < first + k * SP < x1]
    for u in slots:
        v.rect(u - SW / 2, -FL, u + SW / 2, -FS, "#4a4f55")
    v.rect(x0, -FS, x1, 8, GAS, METAL_EDGE)
    v.text((x0 + x1) / 2, -2, "cavity side (air)", 20, "middle")
    v.text((slots[1] + slots[2]) / 2, -24, "tooth", 22, "middle", weight="bold")
    v.label(slots[3], -12, slots[3] + 3, -4.5, "slot", 22)
    v.text((x0 + x1) / 2, -46.5, "channel mouth", 22, "middle")
    v.text((x0 + x1) / 2, 14, "(a) slotted lip, from inside", 26, "middle", weight="bold")
    return v.parts


def locator(dx, dy):
    """The oven from the front, the section's place marked."""
    v = Svg(-W - 10, -W - 40, A + W + CW + 20, H + 2 * W + 60, 0.9, dx, dy)
    v.rect(-W, -W, A + W, H + W, METAL, METAL_EDGE)                       # the door
    v.rect(A / 2 - 110, H / 2 - 75, A / 2 + 110, H / 2 + 75, "#9aa0a6", METAL_EDGE)  # its window
    v.rect(A + W + G, -W, A + CW, H + W, "#d9dcdf", METAL_EDGE)           # the control panel
    v.rect(0, 0, A, H, "none", "#333333", 1.5, dash="6,4")                # the cavity behind
    v.line([(A / 2, -W - 15), (A / 2, 25)], colour=LEAK, width=4)
    v.text(A / 2 + 8, -W - 30, "the sections' place", 22, colour=LEAK)
    v.text((A + CW) / 2, H + W + 10, "(b) the oven from the front", 26, "middle", weight="bold")
    return v.parts


def legend(x, y):
    """Swatches: metal, air, the leak's path."""
    out = []
    for i, (fill, name) in enumerate(((METAL, "metal"), (GAS, "air"))):
        out.append(f"<rect x='{x + i * 150}' y='{y}' width='34' height='24' fill='{fill}' stroke='{METAL_EDGE}'/>"
                   f"<text x='{x + i * 150 + 44}' y='{y + 19}' font-size='22' {FONT}>{name}</text>")
    out.append(f"<line x1='{x + 300}' y1='{y + 12}' x2='{x + 350}' y2='{y + 12}' stroke='{LEAK}' stroke-width='3' stroke-dasharray='7,5'/>"
               f"<text x='{x + 360}' y='{y + 19}' font-size='22' {FONT}>leak path</text>")
    return out


def choke():
    parts = []
    for i, (kind, title) in enumerate((("gap", "(a) no choke"), ("choke", "(b) ring groove"), ("slotted", "(c) slotted choke"))):
        parts += seal(kind, 20 + i * 580, title)
    parts += legend(560, 700)
    with open(os.path.join(OUT, "choke.svg"), "w") as f:
        f.write(document(1760, 740, parts))
    # The slotted lip face on, and where the sections lie.
    with open(os.path.join(OUT, "lip.svg"), "w") as f:
        f.write(document(1240, 520, lip(20, 80) + locator(720, 80)))


def planes():
    """Front (x–z) and plan (x–y) views of the oven with the field pictures' planes."""
    parts = []
    front = Svg(-W - 20, -W - 50, A + W + CW + 40, H + 2 * W + 110, 1.4, 10, 20)
    front.rect(-W, -W, A + CW, H + W, METAL, METAL_EDGE)
    front.rect(0, 0, A, H, AIR, METAL_EDGE)
    front.rect(A + 5, 20, A + 48, H, AIR, METAL_EDGE)
    front.rect(A / 2 - 140, 12, A / 2 + 140, 18, GLASS, METAL_EDGE)
    front.rect(A / 2 - 42.5, 20, A / 2 + 42.5, 68.5, WATER, METAL_EDGE)
    front.line([(A + 47, 64), (A + 29, 64)], colour="black", width=4)
    front.text(A + 26, 58, "feed", 20, "end")
    front.text(A + 26, 150, "waveguide", 20, "end")
    front.line([(A / 2, -W - 15), (A / 2, H + W + 15)], colour=LEAK, width=3, dash="9,5")
    front.text(A / 2 + 8, H + W + 25, "A: vertical section (x = a/2)", 22, colour=LEAK)
    front.line([(-W - 15, H - 30), (A + CW + 15, H - 30)], colour="#1f77b4", width=3, dash="9,5")
    front.text(10, H - 24, "B: horizontal section", 22, colour="#1f77b4")
    front.text((A + CW) / 2 - W / 2, -W - 40, "front view (door removed)", 24, "middle", weight="bold")
    parts += front.parts
    plan = Svg(-W - 20, -G - T - 75, A + W + CW + 260, D + W + G + T + 110, 1.4, 760, 20)
    plan.rect(-W, 0, A + CW, D + W, METAL, METAL_EDGE)
    plan.rect(0, 0, A, D, AIR, METAL_EDGE)
    plan.rect(-W, -G - T, A + W, -G, METAL, METAL_EDGE)
    plan.rect(A + W + G, -G - T, A + CW, 0, "#d9dcdf", METAL_EDGE)
    plan.rect(A + 5, 195 - 43, A + 48, 195 + 43, AIR, METAL_EDGE)
    plan.parts.append("<circle cx='%.1f' cy='%.1f' r='%.1f' fill='%s' stroke='%s'/>" % (*plan.p(A / 2, D / 2), 140 * 1.4, GLASS, METAL_EDGE))
    plan.parts.append("<circle cx='%.1f' cy='%.1f' r='%.1f' fill='%s' stroke='%s'/>" % (*plan.p(A / 2, D / 2), 42.5 * 1.4, WATER, METAL_EDGE))
    plan.line([(A / 2, -G - T - 65), (A / 2, D + W + 15)], colour=LEAK, width=3, dash="9,5")
    plan.text(A / 2 - 8, D + W + 12, "A", 22, "end", colour=LEAK)
    for y, name in ((-G - T - 2, "C: 2 mm out"), (-G - T - 50, "D: 5 cm out")):
        plan.line([(-W - 15, y), (A + CW + 15, y)], colour="#2ca02c", width=3, dash="9,5")
        plan.text(A + CW + 22, y - 6, name, 22, colour="#2ca02c")
    plan.text(A / 2, -G - T / 2 - 6, "door", 20, "middle")
    plan.text(A + CW - 40, -G - T / 2 - 6, "panel", 18, "middle")
    plan.text(A + 26, D / 2 + 60, "waveguide", 20, "start")
    plan.text(A + CW, D + W + 12, "top view (roof removed)", 24, "end", weight="bold")
    parts += plan.parts
    with open(os.path.join(OUT, "planes.svg"), "w") as f:
        f.write(document(1760, 790, parts))


if __name__ == "__main__":
    choke()
    planes()
