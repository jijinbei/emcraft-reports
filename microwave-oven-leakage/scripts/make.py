"""Writes the EMCraft scripts that solve the three ovens. The designs put the box of air's corner
at their origin (model/make.py's OFFSET), so a point is written in the oven's frame (mm, the
cavity's front lower left corner at 0) and moved by OFFSET into the model's."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
A, D, H, W, G, T, CW = 330, 330, 210, 45, 2, 40, 130   # the design's parameters (mm)
PER_WAVELENGTH = int(os.environ.get("PER_WAVELENGTH", "4"))   # elements per wavelength at 2.45 GHz
LAYER = 31                           # the matched layer's thickness: a quarter wavelength
OFFSET = [60 + W, 120 + G + T, 60 + W]   # model/make.py's
BOX = [OFFSET[0] + A + CW + 60, OFFSET[1] + D + W + 45, OFFSET[2] + H + W + 60]
move = lambda p: [round(p[i] + OFFSET[i], 6) for i in range(3)]

# 5 cm in front of the door's outer face (y = −g − t): a grid over the door.
Y = -G - T - 50
PROBES = [[x, Y, z] for z in range(-40, 251, 20) for x in range(-40, 461, 30)]


def script(name):
    return [
        # Water at 25 °C, one Debye pole: εs 78.36, ε∞ 5.2, τ 8.27 ps (Kaatze 1989) → 77.2 − j9.2 at 2.45 GHz.
        {"command": "model.material.create", "params": {"name": "water", "eps_r": 5.2, "debye": [{"delta_eps": 73.16, "frequency": 19.24}]}},
        # Borosilicate glass, the turntable: εr 4.6, tan δ 0.005 near 3 GHz (von Hippel 1954, Corning 7740).
        {"command": "model.material.create", "params": {"name": "glass", "eps_r": 4.6, "loss_tangent": 0.005}},
        {"command": "geometry.import", "params": {"path": f"../model/{name}.solidcraft", "region": "box", "open": True,
                                                   "box": BOX, "thickness": LAYER,
                                                   "materials": {"shell": "metal", "door": "metal"}}},
        # The turntable (radius 140 mm, 6 mm thick, 12 mm above the floor) and the load on it:
        # 275 ml of water 85 mm across (IEC 60335-2-25), 2 mm above the plate where the beaker's
        # glass bottom (left out) holds it. The cylinders' bases at their centres.
        {"command": "geometry.inclusion", "params": {"shape": "cylinder", "radius": 140, "length": 6, "at": move([A / 2, D / 2, 12]), "material": "glass"}},
        {"command": "geometry.inclusion", "params": {"shape": "cylinder", "radius": 42.5, "length": 48.5, "at": move([A / 2, D / 2, 20]), "material": "water"}},
        # The magnetron's antenna as a lumped source: an 18 mm probe into the waveguide through its
        # outer broad wall, across the guide (along its electric field), a quarter guide
        # wavelength (λg = 174 mm) above the shorted end.
        {"command": "model.port.lumped", "params": {"name": "feed", "from": move([A + 5 + 43 - 1, 195, 20 + 44]), "to": move([A + 5 + 43 - 19, 195, 20 + 44])}},
        {"command": "mesh.generate", "params": {"per_wavelength": PER_WAVELENGTH, "frequency": 2.45}},
        # Factored whole (direct), its largest blocks compressed to 1e-8 so it fits 30 GB.
        {"command": "solve.frequency", "params": {"frequencies": [2.45], "solver": "direct", "compress": 1e-8}},
        {"command": "results.power", "params": {"frequency": 2.45}},
        {"command": "results.probe", "params": {"frequency": 2.45, "at": [move(p) for p in PROBES]}},
    ] + [
        # |E| on four planes as numbers (scripts/figures.py draws them on a log scale): A across the
        # oven's middle, B level with the feed, C 2 mm before the door, D 5 cm before it.
        {"command": "results.field.export", "params": {"path": f"../results/real/{name}-plane-{tag}.csv", "frequency": 2.45, "plane": plane, "at": at}}
        for tag, plane, at in (("A", "e", OFFSET[0] + A / 2), ("B", "cross", OFFSET[2] + H - 30),
                               ("C", "h", OFFSET[1] - G - T - 2), ("D", "h", OFFSET[1] - G - T - 50))
    ]

for name in ("oven-gap", "oven-choke", "oven-slotted"):
    with open(os.path.join(HERE, name + ".json"), "w") as f:
        json.dump(script(name), f, indent=1)
        f.write("\n")
