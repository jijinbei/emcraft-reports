"""Draws results/bwo-3d.png: the two BWOs' SolidCraft designs for pictures (model/*-view.sc: the
metal tube and the beam), cut in half along the axis, with what each part is. Run from the
report's folder after model/make.py and the designs are built (run.sh)."""
import os, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(HERE, "results", "model-parts")
FONT = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
S = 1.8  # the labels' places below are on a 1000-pixel-wide picture


def solidcraft(*args):
    if shutil.which("solidcraft-cli"):
        return subprocess.run(["solidcraft-cli", *args], check=True, capture_output=True)
    return subprocess.run(["flatpak", "run", f"--filesystem={HERE}", "--command=solidcraft-cli", "io.tangencylabs.solidcraft", *args],
                          check=True, capture_output=True)


def snapshot(name, target, distance):
    out = os.path.join(PARTS, f"{name}.png")
    camera = f'{{"target": [{target}, 0, 0], "yaw": -0.45, "pitch": 0.35, "distance": {distance}}}'
    solidcraft("snapshot", "--in", os.path.join(HERE, "model", f"{name}.sc"), "--out", out, "--width", "1800", "--height", "700",
               "--camera", camera, "--no-grid", "--no-axes", "--section", "y=0,flip", "--body", "beam:color=#f2a93b")
    return Image.open(out).convert("RGB")


def note(d, font, text, at, to, colour="black"):
    at, to = (at[0] * S, at[1] * S), (to[0] * S, to[1] * S)
    d.line([at, to], fill=colour, width=4)
    d.ellipse([to[0] - 8, to[1] - 8, to[0] + 8, to[1] + 8], fill=colour)
    d.text(at, text, fill=colour, font=font, anchor="mm", stroke_width=6, stroke_fill="white")


def main():
    os.makedirs(PARTS, exist_ok=True)
    font, bold = ImageFont.truetype(FONT, 40), ImageFont.truetype(BOLD, 46)
    red, blue = (200, 60, 30), (40, 80, 200)
    ku = snapshot("ku-view", 90, 190)
    d = ImageDraw.Draw(ku)
    note(d, font, "beam (orange)", (300, 60), (430, 170))
    note(d, font, "rippled wall: slow-wave structure", (470, 330), (450, 222))
    note(d, font, "collector: the beam ends on the wall", (760, 90), (612, 200), red)
    note(d, font, "output", (860, 250), (725, 240), blue)
    note(d, font, "cathode end", (200, 250), (292, 200))
    sb = snapshot("sband-view", 205, 420)
    d = ImageDraw.Draw(sb)
    note(d, font, "beam (orange)", (300, 51), (420, 171))
    note(d, font, "slow-wave structure (5 periods)", (560, 311), (480, 231))
    note(d, font, "collector", (700, 81), (600, 201), red)
    note(d, font, "output horn", (880, 271), (690, 236), blue)
    note(d, font, "cathode end, cut-off neck", (170, 291), (292, 211))
    head = 90
    page = Image.new("RGB", (ku.width, ku.height + sb.height + 2 * head), "white")
    d = ImageDraw.Draw(page)
    d.text((20, head / 2), "(a) Ku band: Na et al. (2017)", fill="black", font=bold, anchor="lm")
    page.paste(ku, (0, head))
    d.text((20, ku.height + head + head / 2), "(b) S band: this design", fill="black", font=bold, anchor="lm")
    page.paste(sb, (0, ku.height + 2 * head))
    page.save(os.path.join(HERE, "results", "bwo-3d.png"))


if __name__ == "__main__":
    main()
