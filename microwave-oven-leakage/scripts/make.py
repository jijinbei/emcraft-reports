"""Writes the EMCraft scripts that solve the two ovens. Coordinates are written in the design's
frame (mm) and moved into the model's: `geometry.import` with `margin` puts the box of air's
lower corner at the origin, so the design's point p sits at p − (lowest body corner − margin)."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
W, G, T = 45, 2, 40                  # wall, gap, door thickness (the design's parameters)
PER_WAVELENGTH = int(os.environ.get("PER_WAVELENGTH", "5"))   # elements per wavelength at 2.45 GHz
MARGIN = 90                          # air and layer round the oven
SHIFT = [MARGIN + W, MARGIN + G + T, MARGIN + W]   # −(lowest corner) + margin
move = lambda p: [round(p[i] + SHIFT[i], 6) for i in range(3)]

# 5 cm in front of the door's outer face (y = −g − t): a grid over the door.
Y = -G - T - 50
PROBES = [[x, Y, z] for z in range(-40, 251, 20) for x in range(-40, 371, 30)]

def script(name):
    return [
        # Water at 25 °C, one Debye pole: εs 78.36, ε∞ 5.2, τ 8.27 ps (Kaatze 1989) → 77.2 − j9.2 at 2.45 GHz.
        {"command": "model.material.create", "params": {"name": "water", "eps_r": 5.2, "debye": [{"delta_eps": 73.16, "frequency": 19.24}]}},
        {"command": "geometry.import", "params": {"path": f"../model/{name}.solidcraft", "region": "box", "open": True,
                                                   "margin": MARGIN, "thickness": 31,
                                                   "materials": {"shell": "metal", "door": "metal", "water": "water", "water2": "water"}}},
        # The magnetron's antenna as a lumped source: a 30 mm gap hanging from the ceiling in the
        # oven's middle plane x = a/2, toward the back. The oven is mirror-symmetric about that
        # plane and the gap's current runs in it, so its field is even there: a magnetic wall
        # keeps half the model (the gap holds half its current), the other half its image.
        {"command": "model.port.lumped", "params": {"name": "feed", "from": move([165, 250, 209]), "to": move([165, 250, 179])}},
        {"command": "model.symmetry", "params": {"axis": "x", "kind": "magnetic"}},
        {"command": "mesh.generate", "params": {"per_wavelength": PER_WAVELENGTH, "frequency": 2.45}},
        {"command": "solve.frequency", "params": {"frequencies": [2.45]}},
        {"command": "results.power", "params": {"frequency": 2.45}},
        {"command": "results.probe", "params": {"frequency": 2.45, "at": [move(p) for p in PROBES]}},
    ] + [
        # Pictures of |E| on the three middle planes: the whole field, and clamped low (10 V/m for
        # 1 W in) so the inside saturates and the field leaking past the door shows.
        {"command": "view.field", "params": {"path": f"../results/{name}-{plane}{tag}.png", "frequency": 2.45, "plane": plane,
                                             "component": "|e|", "width": 1100, **clamp}}
        for plane in ("h", "e", "cross") for tag, clamp in (("", {}), ("-leak", {"clamp": 10}))
    ]

for name in ("oven-gap", "oven-choke", "oven-slotted"):
    with open(os.path.join(HERE, name + ".json"), "w") as f:
        json.dump(script(name), f, indent=1)
        f.write("\n")
