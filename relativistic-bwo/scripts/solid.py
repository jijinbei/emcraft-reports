"""A tube's vacuum as a SolidCraft design: its wall r(z) a closed profile on the plane through the
axis, revolved 360° about z. `solidcraft-cli run <name>.script.json --save <name>.sc` builds it and
EMCraft imports it (`geometry.import`, the body `vacuum` the region's interior)."""
import json


def design(path, title, wall):
    """Writes to `path` the SolidCraft script of `wall`'s points (r, z in mm), from the axis round
    to the axis, as lines on the plane whose x is the global z and y the global x, revolved about
    that x."""
    points = [{"fixed": True, "id": "origin", "pos": [0.0, 0.0]}]
    curves = []
    for i, (r, z) in enumerate(wall):
        points.append({"fixed": True, "id": f"p{i + 1}", "pos": [float(z), float(r)]})
    n = len(wall)
    for i in range(n):
        curves.append({"a": i + 1, "b": (i + 1) % n + 1, "construction": False, "id": f"l{i + 1}", "type": "line"})
    sketch = {"constraints": [], "counters": {"l": n, "p": n, "s": 0}, "curves": curves, "equations": [], "points": points}
    profile = {"id": 1, "name": "profile", "plane": {"origin": [0.0, 0.0, 0.0], "type": "placed", "x_dir": [0.0, 0.0, 1.0], "y_dir": [1.0, 0.0, 0.0]},
               "sketch": sketch, "suppressed": False, "type": "sketch"}
    revolve = {"angle": "360 deg", "axis": {"axis": "x", "type": "sketch_axis"}, "body_names": ["vacuum"], "convention": "sketch_normal", "id": 2,
               "name": "vacuum", "operation": "new_body", "profiles": {"type": "all"}, "sketch": 1, "suppressed": False, "type": "revolve"}
    script = {"commands": [{"command": "file.new", "params": {"name": title}},
                           {"command": "timeline.add", "params": {"feature": profile}},
                           {"command": "timeline.add", "params": {"feature": revolve}}]}
    text = json.dumps(script, indent=1) + "\n"
    # Written only when it changes: its design is built again only then.
    try:
        if open(path).read() == text:
            return
    except OSError:
        pass
    with open(path, "w") as f:
        f.write(text)
