"""Writes the BWOs' SolidCraft scripts: the vacuum inside each tube (where the beam and the wave
run) as a body of revolution — its wall r(z) a closed profile on the plane through the axis,
revolved 360° about z. Then `solidcraft-cli run <name>.script.json --save <name>.sc` builds each
design, which EMCraft imports (scripts/make.py). The walls are scripts/make.py's: the Ku-band BWO
of Na et al. (2017) and the S-band design."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import make  # noqa: E402  the walls (r, z in mm)
import solid  # noqa: E402


def design(name, title, wall):
    """model/<name>.script.json: the vacuum inside `wall` (scripts/solid.py)."""
    solid.design(os.path.join(HERE, f"{name}.script.json"), title, wall)


def view(name, title, wall, beam, collector):
    """A SolidCraft design for pictures only: the metal tube round `wall` (4 mm thick beyond its
    widest point) and the beam (radii `beam`, from the cathode to `collector`, mm)."""
    inside = [(r, z) for r, z in wall if r > 0]
    end = max(z for _, z in wall)
    outer = max(r for r, _ in inside) + 4.0
    tube = inside + [(outer, end), (outer, 0.0)]
    ring = [(beam[0], 0.0), (beam[1], 0.0), (beam[1], collector), (beam[0], collector)]

    def feature(fid, profile_points, body):
        points = [{"fixed": True, "id": "origin", "pos": [0.0, 0.0]}]
        points += [{"fixed": True, "id": f"p{i + 1}", "pos": [float(z), float(r)]} for i, (r, z) in enumerate(profile_points)]
        n = len(profile_points)
        curves = [{"a": i + 1, "b": (i + 1) % n + 1, "construction": False, "id": f"l{i + 1}", "type": "line"} for i in range(n)]
        sketch = {"constraints": [], "counters": {"l": n, "p": n, "s": 0}, "curves": curves, "equations": [], "points": points}
        # The axis along x (lying down in the picture), r up: pictures only.
        plane = {"origin": [0.0, 0.0, 0.0], "type": "placed", "x_dir": [1.0, 0.0, 0.0], "y_dir": [0.0, 0.0, 1.0]}
        return [{"command": "timeline.add", "params": {"feature": {"id": fid, "name": f"{body} profile", "plane": plane, "sketch": sketch, "suppressed": False, "type": "sketch"}}},
                {"command": "timeline.add", "params": {"feature": {"angle": "360 deg", "axis": {"axis": "x", "type": "sketch_axis"}, "body_names": [body],
                                                                    "convention": "sketch_normal", "id": fid + 1, "name": body, "operation": "new_body",
                                                                    "profiles": {"type": "all"}, "sketch": fid, "suppressed": False, "type": "revolve"}}}]

    script = {"commands": [{"command": "file.new", "params": {"name": title}}] + feature(1, tube, "tube") + feature(3, ring, "beam")}
    with open(os.path.join(HERE, f"{name}.script.json"), "w") as f:
        json.dump(script, f, indent=1)
        f.write("\n")


def wall_of(script):
    for c in script:
        if c["command"] == "geometry.solid":
            return c["params"]["points"]
    raise ValueError("no wall")


design("ku", "Ku-band BWO (Na et al. 2017)", wall_of(make.ku_collector()))
design("sband", "S-band BWO", wall_of(make.BEST))
view("ku-view", "Ku-band BWO (view)", wall_of(make.ku_collector()), (9.0, 11.0), 140.0)
view("sband-view", "S-band BWO (view)", wall_of(make.BEST), (28.5, 30.5), 290.0)
