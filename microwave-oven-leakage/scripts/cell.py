"""The door seal cut out as a two-port: a 2 mm gap between the door and the oven's flange,
running from the cavity (port 1) out past the choke (port 2), b wide along the door's rim with
conducting walls there — so the wave in the gap goes as sin(πy/b) along the rim, as the oven's
gap field varies round the door (b = 300 mm nearly uniform, b = 80 mm strongly varying).

Builds each cell in SolidCraft, solves it with EMCraft and writes results/cell/<name>.out;
prints |S21| (dB) at 2.45 GHz and the notch. A plain groove's |S21| is checked against the
series-stub transmission line (the reference, computed here independently)."""
import json, math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "cell")
WORK = os.path.join(HERE, "cell")
EMCRAFT = os.environ.get("EMCRAFT_CLI", "emcraft-cli")
SOLIDCRAFT = ["flatpak", "run", f"--filesystem={WORK}", "--command=solidcraft-cli", "io.tangencylabs.solidcraft"]
C0 = 299792458.0

def box(l, w, h, c, **kw):
    return {"command": "solid.box", "params": {"length": str(l), "width": str(w), "height": str(h), "corner": [str(v) for v in c], **kw}}

def cell(kind, b, fs=10):
    """`groove`: a 6 mm × 30 mm groove in the door 40 mm out; `folded`: a 1 mm lip from fs to 36 mm
    with a 4 mm channel behind it from fs to 40 mm, open past the lip's end; `slotted`: that lip
    cut into fingers by 2.5 mm slots every 18 mm (after Osepchuk et al., US 3,767,884)."""
    c = [{"command": "file.new", "params": {"name": f"{kind} {b}"}}, box(2, b, 86, [0, 0, 0], body_name="air")]
    if kind == "groove":
        c.append(box(30, b, 6, [2, 0, 40], operation="join", targets=["air"]))
    else:
        c.append(box(1, b, 4, [2, 0, 36], operation="join", targets=["air"]))
        c.append(box(4, b, 40 - fs, [3, 0, fs], operation="join", targets=["air"]))
        if kind == "slotted":
            c += [box(1, 2.5, 36 - fs, [2, y - 1.25, fs], operation="join", targets=["air"]) for y in range(9, b - 2, 18)]
    return {"commands": c}

def s21(path):
    text, dec, i, objs = open(path).read(), json.JSONDecoder(), 0, []
    while (i := text.find("{", i)) >= 0:
        try:
            o, j = dec.raw_decode(text, i); objs.append(o); i = j
        except ValueError:
            i += 1
    sp = [o for o in objs if "points" in o and o["points"] and "s21" in o["points"][0]][-1]
    return [(p["frequency"], p["s21"]["db"]) for p in sp["points"]]

def stub(f_ghz, b, depth=0.030, gap=0.002, width=0.006):
    """|S21| (dB) of a series shorted stub on the gap's line: the groove, `width` wide and `depth`
    deep, its impedance width/gap times the gap's, both lines' wave going as sin(πy/b)
    (β² = k² − (π/b)²); S21 = 2Z₀/(2Z₀ + jZ_g tan βd) (Pozar, Microwave Engineering, §2.3, §4.3)."""
    k = 2 * math.pi * f_ghz * 1e9 / C0
    beta = math.sqrt(k * k - (math.pi / b) ** 2)
    z = 1j * (width / gap) * math.tan(beta * depth)
    return 20 * math.log10(abs(2 / (2 + z)))

CASES = [("groove", 300, 10), ("groove", 80, 10), ("folded", 300, 10), ("folded", 80, 10),
         ("slotted", 300, 10), ("slotted", 80, 10), ("slotted", 300, 8.5), ("slotted", 80, 8.5)]

if __name__ == "__main__":
    os.makedirs(WORK, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    for kind, b, fs in CASES:
        name = f"{kind}-{b}-fs{fs}"
        design = os.path.join(WORK, name + ".solidcraft")
        json.dump(cell(kind, b, fs), open(os.path.join(WORK, name + ".script.json"), "w"), indent=1)
        subprocess.run(SOLIDCRAFT + ["run", os.path.join(WORK, name + ".script.json"), "--save", design], check=True, capture_output=True)
        run = [{"command": "geometry.import", "params": {"path": name + ".solidcraft", "region": "air"}},
               {"command": "mesh.generate", "params": {"size": 5}},
               {"command": "model.port.create", "params": {"name": "1", "end": "start"}},
               {"command": "model.port.create", "params": {"name": "2", "end": "end"}},
               {"command": "solve.frequency", "params": {"start": 2.0, "stop": 3.4, "points": 29, "order": 2}},
               {"command": "results.sparameters", "params": {}}]
        json.dump(run, open(os.path.join(WORK, name + ".json"), "w"))
        out = os.path.join(OUT, name + ".out")
        with open(out, "w") as f:
            subprocess.run([EMCRAFT, "run", name + ".json"], cwd=WORK, stdout=f, stderr=subprocess.STDOUT, check=True)
        rows = s21(out)
        at = min(rows, key=lambda r: abs(r[0] - 2.45))[1]
        notch = min(rows, key=lambda r: r[1])
        ref = "" if kind != "groove" else f"  stub model at 2.45: {stub(2.45, b / 1000):6.1f} dB"
        print(f"{name:20s} |S21| at 2.45 GHz {at:6.1f} dB, notch {notch[1]:6.1f} dB at {notch[0]:.2f} GHz{ref}", flush=True)
