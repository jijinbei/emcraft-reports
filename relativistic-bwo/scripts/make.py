"""Writes the BWO study's EMCraft scripts (run from this folder):
- cell.json: one period of the S-band slow-wave structure, its TM01 Bloch dispersion (cold test);
- sband.json: the S-band BWO laid out after Molchanov & Gurnevich (2024)'s rules — period
  D ≈ 0.37 λg, mean radius ≈ 0.29 λg, depth ≈ λg/12 for the TM01 guide wavelength λg at 3.6 GHz —
  with a cut-off neck, an insert, five sinusoidal periods and an output horn; 550 keV, 80 Ω, 2.5 T;
- ku.json: the Ku-band BWO of Na et al. (2017), EMCraft's template relativistic-bwo.
Lengths in mm, frequencies in GHz."""
import json, math, os

import solid

HERE = os.path.dirname(os.path.abspath(__file__))
# Where each scan's tube is written as a SolidCraft design (built by `uv run report`, not kept).
SCAN_DESIGNS = os.path.join(os.path.dirname(HERE), "model", "scan")

# The S-band structure: λg = 127 mm at 3.6 GHz makes the three rules consistent (the TM01 guide
# wavelength in a guide of the structure's outer radius, r0 + h/2).
D, R0, H = 47.0, 36.9, 10.6
NECK, NECK_LEN, INSERT, PERIODS = 30.0, 15.0, 30.0, 5
BEAM = (27.0, 29.0)         # the beam's inner and outer radius
TIME = 60                   # ns
HORN, HORN_LEN, OUT_LEN = 45.0, 60.0, 80.0
RIPPLE_POINTS = 24          # points a period along the wall


def ripple(z0, periods, inner=None):
    """The wall from z0 over `periods` periods, each r(z) = rmax − (rmax − r_in)(1 + cos(2π (z − z0)/D))/2
    between its inner radius r_in and the crest rmax = r0 + h/2: starting and ending at r_in.
    `inner` gives each period's inner radius (default r0 − h/2 for all)."""
    rmax = R0 + H / 2
    inner = inner or [R0 - H / 2] * periods
    depths = [rmax - r_in for r_in in inner]

    def depth(t):
        # Each period's depth at its middle (t = p + 1/2), straight between: the wall stays
        # continuous where the depth changes (a period's own depth at both its ends would step).
        k = min(max(t - 0.5, 0.0), periods - 1.0)
        p = min(int(k), periods - 2) if periods > 1 else 0
        f = k - p
        return depths[p] if periods == 1 else depths[p] * (1 - f) + depths[p + 1] * f

    pts = []
    for n in range(RIPPLE_POINTS * periods + 1):
        t = n / RIPPLE_POINTS
        r = rmax - depth(t) * (1 + math.cos(2 * math.pi * t)) / 2
        pts.append([round(r, 4), round(z0 + D * t, 4)])
    return pts


def cell(period=None):
    """One period (`period`, default D) of the structure, its TM01 Bloch dispersion."""
    d = period or D
    pts = [[0, 0]] + [[round(R0 + H / 2 * math.cos(2 * math.pi * i / RIPPLE_POINTS), 4), round(d * i / RIPPLE_POINTS, 4)] for i in range(RIPPLE_POINTS + 1)] + [[0, d]]
    return [
        {"command": "geometry.solid", "params": {"shape": "revolved", "points": pts, "sides": 64}},
        {"command": "model.port.create", "params": {"name": "1", "end": "start", "modes": 3}},
        {"command": "model.port.create", "params": {"name": "2", "end": "end", "modes": 3}},
        {"command": "solve.revolution.bloch", "params": {"start": 2.6, "stop": 4.6, "points": 41, "m": 0, "modes": 3}},
    ]


def sband(insert=None, beam=None, tag="sband", ends=None, period=None, neck=None, periods=None, field=2.5, inner=None, field_end=None):
    """`ends`: the inner radii of the first and the last period (the terminal corrugations;
    default the others')."""
    global D, NECK, PERIODS
    saved = (D, NECK, PERIODS)
    D, NECK, PERIODS = period or D, neck or NECK, periods or PERIODS
    insert = INSERT if insert is None else insert
    beam = BEAM if beam is None else beam
    rmin = round(R0 - H / 2, 4)
    first, last = ends or (rmin, rmin)
    z = 0.0
    wall = [[0, 0], [NECK, 0], [NECK, NECK_LEN]]
    z = NECK_LEN
    wall += [[first, z], [first, z + insert]]
    z += insert
    wall += ripple(z, PERIODS, inner or [first] + [rmin] * (PERIODS - 2) + [last])[1:]
    z += D * PERIODS
    wall += [[HORN, z + HORN_LEN], [HORN, z + HORN_LEN + OUT_LEN]]
    end = z + HORN_LEN + OUT_LEN
    wall += [[0, end]]
    probe_z = NECK_LEN + insert + D * 2.5
    D, NECK, PERIODS = saved
    return [
        {"command": "geometry.solid", "params": {"shape": "revolved", "points": wall, "sides": 64}},
        {"command": "project.analysis", "params": {"kind": "particles"}},
        {"command": "particles.magnetic", "params": {"b": [0, 0, field], **({"end": field_end, "fall": 10} if field_end else {})}},
        # 550 keV, 80 Ω: 6.875 kA, an annulus 2 mm thick 5.6 mm inside the ripple's crests.
        {"command": "particles.beam", "params": {"face": "z-", "current": 550e3 / 80, "energy": 550e3, "radius": beam[1], "inner": beam[0], "rise": 2000}},
        {"command": "particles.open", "params": {"face": "z+"}},
        {"command": "particles.probe", "params": {"at": [33, 0, probe_z]}},
        {"command": "particles.output", "params": {"at": round(end - 20, 3)}},
        {"command": "solve.particles", "params": {"time": TIME, "cell": 1.5, "axisymmetric": True, "fine": 8}},
        {"command": "results.particles.export", "params": {"path": f"../results/{tag}-history.csv"}},
        {"command": "results.particles.export", "params": {"path": f"../results/{tag}-probes.csv", "what": "probes"}},
        {"command": "results.particles.export", "params": {"path": f"../results/{tag}-phase.csv", "what": "particles"}},
    ]


def ku():
    return [
        {"command": "file.sample", "params": {"name": "relativistic-bwo"}},
        {"command": "particles.output", "params": {"at": 140}},
        {"command": "solve.particles", "params": {"time": 50}},
        {"command": "results.particles.export", "params": {"path": "../results/ku-history.csv"}},
        {"command": "results.particles.export", "params": {"path": "../results/ku-probes.csv", "what": "probes"}},
        {"command": "results.particles.export", "params": {"path": "../results/ku-phase.csv", "what": "particles"}},
    ]


# The scan of the insert's length and the beam's radius (scan-<insert>-<outer radius>.json).
SCAN = [(insert, beam) for insert in (15.0, 30.0, 45.0) for beam in ((24.0, 26.0), (27.0, 29.0))]
scans = [(f"scan-{i:g}-{b[1]:g}", sband(i, b, f"scan-{i:g}-{b[1]:g}")) for i, b in SCAN]
# The terminal corrugations' inner radii (the first period's, the last's), the beam 24–26 mm.
ENDS = [(a, b) for a in (28.0, 30.0, 31.6) for b in (28.0, 30.0, 31.6)]
scans += [(f"ends-{a:g}-{b:g}", sband(30.0, (24.0, 26.0), f"ends-{a:g}-{b:g}", (a, b))) for a, b in ENDS]
# The period against the beam's radius (the beam slowed by its own charge syncs lower), the
# ends 30 mm inside; a beam 28.5–30.5 mm out passes a neck of 31.5 mm (still below TM01's cut-off).
SYNC = [(d, beam) for d in (47.0, 44.0, 41.0) for beam in ((24.0, 26.0), (28.5, 30.5))]
scans += [
    (f"sync-{d:g}-{b[1]:g}", sband(30.0, b, f"sync-{d:g}-{b[1]:g}", (31.6, 31.6) if b[1] > 30 else (30.0, 30.0), d, 31.5 if b[1] > 30 else None))
    for d, b in SYNC
]

# Round the best (D 44 mm, the beam 28.5–30.5 mm): the period against the insert's length.
TUNE = [(d, ins) for d in (42.0, 43.0, 44.0) for ins in (20.0, 30.0, 45.0)]
scans += [(f"tune-{d:g}-{i:g}", sband(i, (28.5, 30.5), f"tune-{d:g}-{i:g}", (31.6, 31.6), d, 31.5)) for d, i in TUNE]

# The number of periods and the guiding field, the period 44 or 45 mm.
MORE = [(d, n, b) for d in (44.0, 45.0) for n in (5, 6) for b in (2.5, 4.0)]
MORE += [(44.0, 4, 2.5), (44.0, 4, 4.0)]
scans += [
    (f"more-{d:g}-{n}-{b:g}", sband(30.0, (28.5, 30.5), f"more-{d:g}-{n}-{b:g}", (31.6, 31.6), d, 31.5, n, b)) for d, n, b in MORE
]

# Shallower towards the output (the beam slowed there couples less and turns back less): each
# period's inner radius, the crest 42.2 mm kept; D 44 mm, the beam 28.5–30.5 mm.
TAPERS = {
    "flat": [31.6] * 5,
    "last": [31.6, 31.6, 31.6, 31.6, 34.0],
    "two": [31.6, 31.6, 31.6, 33.0, 35.0],
    "three": [31.6, 31.6, 32.6, 34.0, 36.0],
    "deep": [31.6, 31.6, 31.6, 34.0, 37.0],
}
scans += [(f"taper-{k}", sband(30.0, (28.5, 30.5), f"taper-{k}", None, 44.0, 31.5, 5, 2.5, v)) for k, v in TAPERS.items()]

# A collector: the guiding field falls away past the structure (it ends at 265 mm), the beam
# spreading to the horn's wall before the output plane; flat and tapered structures.
COLLECT = [(k, e) for k in ("flat", "two") for e in (275.0, 290.0, 310.0)]
scans += [
    (f"collect-{k}-{e:g}", sband(30.0, (28.5, 30.5), f"collect-{k}-{e:g}", None, 44.0, 31.5, 5, 2.5, TAPERS[k], e)) for k, e in COLLECT
]

def ku_collector():
    """Na et al.'s Ku-band BWO (the template's structure) with its output guide carried on to
    180 mm, the guiding field falling away past the structure (it ends at 128.75 mm) so the beam
    lands on the wall before the output plane: the plane sees the radiated power alone."""
    # ku-wall.json: the template's wall (r, z in mm), copied from EMCraft's
    # crates/templates/scripts/relativistic-bwo.json — R(z) = (A + B)/2 + (A − B)/2 cos(2πz/C),
    # A 17.1, B 12.9, C 7.5 mm, 14.5 periods from z = 20 mm (Na et al. 2017, §5.1).
    template = json.load(open(os.path.join(HERE, "ku-wall.json")))
    wall = template[:-2] + [[17.1, 180.0], [0, 180.0]]
    return [
        {"command": "geometry.solid", "params": {"shape": "revolved", "points": wall, "sides": 64}},
        {"command": "project.analysis", "params": {"kind": "particles"}},
        {"command": "particles.magnetic", "params": {"b": [0, 0, 5], "end": 140, "fall": 3}},
        {"command": "particles.beam", "params": {"face": "z-", "current": 1500, "energy": 552495.7, "radius": 11, "inner": 9, "rise": 1000}},
        {"command": "particles.open", "params": {"face": "z+"}},
        {"command": "particles.probe", "params": {"at": [12.5, 0, 22]}},
        {"command": "particles.output", "params": {"at": 170}},
        {"command": "solve.particles", "params": {"time": 100, "cell": 0.5, "axisymmetric": True, "fine": 4}},
        {"command": "results.particles.export", "params": {"path": "../results/ku-collector-history.csv"}},
        {"command": "results.particles.export", "params": {"path": "../results/ku-collector-probes.csv", "what": "probes"}},
        {"command": "results.particles.export", "params": {"path": "../results/ku-collector-phase.csv", "what": "particles"}},
    ]


# With the collector at 290 mm: how the structure shallows towards its output, and the period.
TAPERS["mild"] = [31.6, 31.6, 31.6, 32.3, 33.5]
TAPERS["two-deep"] = [31.6, 31.6, 31.6, 33.5, 36.0]
REFINE = [("last", 44.0), ("three", 44.0), ("mild", 44.0), ("two-deep", 44.0), ("two", 43.0), ("two", 45.0)]
scans += [
    (f"refine-{k}-{d:g}", sband(30.0, (28.5, 30.5), f"refine-{k}-{d:g}", None, d, 31.5, 5, 2.5, TAPERS[k], 290.0 + 5 * (d - 44.0)))
    for k, d in REFINE
]

def via_solidcraft(script, design):
    """`script` with its geometry the SolidCraft design model/<design>.sc (the vacuum inside the
    tube, a body of revolution: model/make.py) in place of the wall's points."""
    out = []
    for c in script:
        if c["command"] == "geometry.solid":
            c = {"command": "geometry.import", "params": {"path": f"../model/{design}.sc", "materials": {"vacuum": "interior"}}}
        out.append(c)
    return out


def final(script, tag):
    """`script` kept at 30 moments along the run, its exports named for the final runs."""
    out = []
    for c in script:
        c = json.loads(json.dumps(c))
        if c["command"] == "solve.particles":
            c["params"]["frames"] = 30
        if c["command"] == "results.particles.export":
            what = c["params"].get("what", "history")
            c["params"]["path"] = f"../results/final-{tag}-{what}.csv"
        out.append(c)
    for what in ("frames", "maps"):
        out.append({"command": "results.particles.export", "params": {"path": f"../results/final-{tag}-{what}.csv", "what": what}})
    return out


def animation(script, tag, count, start=None):
    """`script` keeping `count` moments (from `start` ns, else over the whole run), only their
    particles and fields written: the frames of an animation."""
    out = [json.loads(json.dumps(c)) for c in script if c["command"] != "results.particles.export"]
    for c in out:
        if c["command"] == "solve.particles":
            c["params"]["frames"] = count
            if start is not None:
                c["params"]["frames_from"] = start
    for what in ("frames", "maps"):
        out.append({"command": "results.particles.export", "params": {"path": f"../results/anim-{tag}-{what}.csv", "what": what}})
    return out


# Maps about the final design, each point a whole 60 ns run on a GPU (some 50 s): the period
# against the beam's radius (the beam 2 mm thick, the collector moving with the structure's end),
# and the last two periods' inner radii (the others 31.6 mm, the crest 42.2 mm).
MAP_PERIODS = (41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0)
MAP_BEAMS = (27.0, 28.0, 29.0, 30.0, 30.5, 31.0)
scans += [
    (f"map-{d:g}-{b:g}", sband(30.0, (b - 2.0, b), f"map-{d:g}-{b:g}", None, d, 31.5, 5, 2.5, TAPERS["two"], 290.0 + 5 * (d - 44.0)))
    for d in MAP_PERIODS for b in MAP_BEAMS
]
MAP_FOURTH = (31.6, 32.3, 33.0, 33.7, 34.4)
MAP_FIFTH = (33.0, 34.0, 35.0, 36.0, 37.0)
scans += [
    (f"shallow-{a:g}-{b:g}", sband(30.0, (28.5, 30.5), f"shallow-{a:g}-{b:g}", None, 44.0, 31.5, 5, 2.5, [31.6, 31.6, 31.6, a, b], 290.0))
    for a in MAP_FOURTH for b in MAP_FIFTH
]

# The final runs the report draws: Na et al.'s Ku band with a collector, and the S band's best
# design (the last two periods shallower, D 44 mm, the collector at 290 mm).
scans += [
    ("final-ku", final(via_solidcraft(ku_collector(), "ku"), "ku")),
    ("final-sband", final(via_solidcraft(sband(30.0, (28.5, 30.5), "x", None, 44.0, 31.5, 5, 2.5, TAPERS["two"], 290.0), "sband"), "sband")),
]
# The animations' runs: the S band growing (60 moments over its 60 ns) and in its steady
# oscillation (58–60 ns: some 7 periods), the Ku band's steady oscillation (99.4–100 ns).
BEST = sband(30.0, (28.5, 30.5), "x", None, 44.0, 31.5, 5, 2.5, TAPERS["two"], 290.0)
scans += [
    ("anim-sband-growth", animation(via_solidcraft(BEST, "sband"), "sband-growth", 60)),
    ("anim-sband-rf", animation(via_solidcraft(BEST, "sband"), "sband-rf", 60, 58.0)),
    ("anim-ku-rf", animation(via_solidcraft(ku_collector(), "ku"), "ku-rf", 60, 99.4)),
    ("anim-ku-growth", animation(via_solidcraft(ku_collector(), "ku"), "ku-growth", 50)),
]

def designed(name, script):
    """`script` with its wall drawn by its own SolidCraft design (model/scan/<name>.sc) and, a
    particle run of the design study (not the final runs), solved on a GPU (CUDA, double precision)."""
    out = []
    for c in script:
        if c["command"] == "geometry.solid":
            solid.design(os.path.join(SCAN_DESIGNS, f"{name}.script.json"), name, c["params"]["points"])
            c = {"command": "geometry.import", "params": {"path": f"../model/scan/{name}.sc", "materials": {"vacuum": "interior"}}}
        elif c["command"] == "solve.particles" and not name.startswith(("final-", "anim-")):
            c = {"command": c["command"], "params": {**c["params"], "device": "cuda", "precision": "double"}}
        out.append(c)
    return out


os.makedirs(SCAN_DESIGNS, exist_ok=True)
for name, script in (("cell", cell()), ("cell-44", cell(44.0)), ("sband", sband()), ("ku", ku()), ("ku-collector", ku_collector()), *scans):
    with open(os.path.join(HERE, name + ".json"), "w") as f:
        json.dump(designed(name, script), f, indent=1)
        f.write("\n")
