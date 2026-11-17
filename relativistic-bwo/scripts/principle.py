"""Draws the schematic of how a BWO works into results/principle.svg: (a) the structure, the
beam going one way and the backward wave's power the other; (b) the beam bunching where the
wave's E_z slows it; (c) the loop that makes it oscillate without outside feedback."""
import math, os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "principle.svg")
METAL, EDGE, BEAM, RED, BLUE, GREY = "#c3c7cc", "#5b6066", "#f2a93b", "#d62728", "#2b5bc8", "#777777"
FONT = "font-family='Noto Sans, sans-serif'"
W = 1600


def text(x, y, s, size=24, anchor="start", colour="black", weight="normal"):
    size = round(size * 1.4)
    return f"<text x='{x:.1f}' y='{y:.1f}' font-size='{size}' text-anchor='{anchor}' fill='{colour}' font-weight='{weight}' {FONT}>{s}</text>"


def arrow(x0, y0, x1, y1, colour, width=6):
    return f"<line x1='{x0}' y1='{y0}' x2='{x1}' y2='{y1}' stroke='{colour}' stroke-width='{width}' marker-end='url(#head-{colour[1:]})'/>"


def heads():
    return "".join(
        f"<marker id='head-{c[1:]}' viewBox='0 0 10 10' refX='7' refY='5' markerWidth='4' markerHeight='4' orient='auto-start-reverse'>"
        f"<path d='M0,0 L10,5 L0,10 z' fill='{c}'/></marker>" for c in (RED, BLUE, "#000000", GREY))


def structure(y):
    """(a) The tube's upper half: a cut-off neck, the rippled wall, the output; the beam and the
    backward wave's power."""
    out = [text(20, y + 10, "(a) beam one way, the wave's power the other", 24, weight="bold")]
    top, axis = y + 80, y + 270
    x0, x1, ripple0, ripple1 = 60, 1540, 300, 1260
    wall = []
    for i in range(0, 1201):
        x = x0 + (x1 - x0) * i / 1200
        if x < 200:
            r = 45
        elif x < ripple0:
            r = 50
        elif x < ripple1:
            r = 80 - 30 * (1 - math.cos(2 * math.pi * (x - ripple0) / 120)) / 2
        else:
            r = 70
        wall.append((x, axis - 160 + (80 - r)))
    poly = " ".join(f"{a:.1f},{b:.1f}" for a, b in wall)
    out.append(f"<polygon points='{x0},{top} {poly} {x1},{top}' fill='{METAL}' stroke='{EDGE}' stroke-width='2'/>")
    out.append(f"<rect x='{x0}' y='{axis - 118}' width='{1200}' height='14' fill='{BEAM}'/>")
    out.append(arrow(x0 + 20, axis - 70, x0 + 230, axis - 70, "#000000"))
    out.append(text(x0 + 250, axis - 63, "electron beam", 22))
    out.append(arrow(1250, axis - 20, 330, axis - 20, RED, 7))
    out.append(text(790, axis + 18, "backward wave: power flows back to the cathode", 21, "middle", RED))
    out.append(text(x0 + 70, top + 45, "cut-off neck", 20, "middle", colour="#222"))
    out.append(text(780, top - 12, "slow-wave structure (rippled wall)", 22, "middle"))
    out.append(arrow(1300, axis - 40, 1520, axis - 40, BLUE, 7))
    out.append(text(1410, axis - 2, "output", 22, "middle", BLUE))
    return out


def bunching(y):
    """(b) E_z of the wave at one moment, and the electrons at the entrance (even) and further
    on (bunched where E_z slows them)."""
    out = [text(20, y + 10, "(b) the wave's E_z bunches the beam where it slows it", 24, weight="bold")]
    x0, x1, mid = 120, 1500, y + 150
    pts = []
    for i in range(401):
        x = x0 + (x1 - x0) * i / 400
        pts.append((x, mid - 55 * math.sin(2 * math.pi * (x - x0) / 345)))
    for k in range(4):
        # Shade the decelerating half (E_z > 0 slows electrons: their charge is negative).
        a = x0 + 345 * k
        out.append(f"<rect x='{a}' y='{mid - 70}' width='{172.5}' height='140' fill='{RED}' opacity='0.12'/>")
    out.append("<polyline points='" + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f"' fill='none' stroke='{GREY}' stroke-width='3'/>")
    out.append(text(x1 + 10, mid - 40, "E_z", 22, colour=GREY))
    out.append(text(x0 + 86, mid + 62, "slows", 20, "middle", RED))
    out.append(text(x0 + 258, mid + 62, "speeds up", 20, "middle", BLUE))
    even, bunched = mid + 110, mid + 160
    out.append(text(20, even + 6, "entrance", 20))
    out.append(text(20, bunched + 6, "downstream", 20))
    for i in range(130):
        x = x0 + 140 + i * (x1 - x0 - 140) / 129
        out.append(f"<circle cx='{x:.1f}' cy='{even}' r='4' fill='#000'/>")
        phase = ((x - x0) % 345) / 345
        # Pulled towards the middle of the slowing half (phase 0.25).
        shifted = x - 345 / (2 * math.pi) * math.sin(2 * math.pi * (phase - 0.25)) * 0.9
        if shifted > x0 + 130:
            out.append(f"<circle cx='{shifted:.1f}' cy='{bunched}' r='4' fill='#000'/>")
    out.append(text(x1, bunched + 42, "bunched where slowed: energy to the wave", 22, "end", RED))
    return out


def loop(y):
    """(c) The loop: the wave grown downstream comes back, modulates the fresh beam, which bunches
    and grows the wave."""
    out = [text(20, y + 10, "(c) a loop inside the tube: it oscillates by itself", 24, weight="bold")]
    boxes = [(260, "wave grows downstream", RED), (800, "power flows back", RED), (1340, "modulates the fresh beam", "#000"),
             (800, "beam bunches as it goes", "#000")]
    cy = [y + 80, y + 80, y + 80, y + 190]
    for (x, s, c), yy in zip(boxes, cy):
        out.append(f"<rect x='{x - 230}' y='{yy - 30}' width='460' height='56' rx='12' fill='white' stroke='{c}' stroke-width='3'/>")
        out.append(text(x, yy + 7, s, 22, "middle", c))
    out.append(arrow(490, y + 80, 565, y + 80, RED))
    out.append(arrow(1030, y + 80, 1105, y + 80, RED))
    out.append(arrow(1340, y + 106, 1040, y + 175, "#000000"))
    out.append(arrow(570, y + 190, 300, y + 108, "#000000"))
    return out


def main():
    parts = structure(30) + bunching(380) + loop(800)
    height = 1050
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{height}' viewBox='0 0 {W} {height}'><defs>{heads()}</defs>"
           f"<rect width='{W}' height='{height}' fill='white'/>" + "".join(parts) + "</svg>\n")
    with open(OUT, "w") as f:
        f.write(svg)


if __name__ == "__main__":
    main()
