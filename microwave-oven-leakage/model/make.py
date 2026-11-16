"""Writes the oven's SolidCraft scripts: `oven-gap` (a plain door over a gap) and `oven-choke`
(the same door with a quarter-wave groove round its rim). Run, then build each design with
`solidcraft-cli run <name>.script.json --save <name>.solidcraft`."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
# name, value in mm, what it is
PARAMS = [
    ("a", 330, "cavity width (x)"), ("d", 330, "cavity depth (y), door at y = 0"),
    ("h", 210, "cavity height (z)"), ("w", 45, "wall, and the flange the door rests on"),
    ("g", 2, "gap between door and flange"), ("t", 40, "door thickness"),
    ("lw", 60, "each water load's side"), ("lh", 38.2, "each water load's height: 137.5 ml, two of them 275 ml"), ("lx", 50, "each water load's centre from the middle plane x = a/2"),
    ("lz", 15, "water load's height above the floor: where a turntable holds it"),
    ("fs", 8.5, "slotted choke: where its channel's shorted end and the lip start, out from the cavity's edge"),
    ("fl", 36, "slotted choke: where the lip ends and the channel opens to the gap"),
    ("cs", 6, "choke groove's width"), ("cl", 30, "choke groove's distance from the cavity's edge: about a quarter wavelength"), ("cd", 30, "choke groove's depth: about a quarter wavelength"),
]

def box(length, width, height, corner, **kw):
    return {"command": "solid.box", "params": {"length": length, "width": width, "height": height, "corner": corner, **kw}}

def ring(s0, s1, y0, y1, name):
    """A rectangular ring round the opening, s0 to s1 out from the cavity's edge, y0 to y1 deep."""
    out = box(f"a + 2*({s1})", f"({y1}) - ({y0})", f"h + 2*({s1})", [f"-({s1})", f"{y0}", f"-({s1})"], operation="new_body", body_name=name)
    inner = box(f"a + 2*({s0})", f"({y1}) - ({y0}) + 2 mm", f"h + 2*({s0})", [f"-({s0})", f"({y0}) - 1 mm", f"-({s0})"], operation="cut", targets=[name])
    return [out, inner]

def slotted_choke():
    """A folded choke with a slotted lip (after Osepchuk et al., US 3,767,884): the door's face
    from `fs` to `fl` out from the cavity's edge is a 1 mm lip; behind it a channel 4 mm deep
    runs from `fs` to `fl + 4 mm`, open to the gap past the lip's end; slots through the lip
    across the path, `sw` wide every `sp` along the rim, make the lip fingers and stop waves
    running round the rim inside the choke."""
    c = ring("fs", "fl + 4 mm", "-g - 5 mm", "-g - 1 mm", "channel") + ring("fl", "fl + 4 mm", "-g - 1 mm", "-g", "mouth")
    c.append({"command": "solid.combine", "params": {"target": "door", "tools": ["channel", "mouth"], "operation": "cut"}})
    # Slots along each side of the rim, centred on the side, none within a slot pitch of a corner.
    a, h, sp, sw, fs, fl = 330, 210, 18, 2.5, 8.5, 36
    slots = []
    for along, length in (("x", a), ("z", h)):
        n = int((length + 2 * fs) // sp) - 1
        first = length / 2 - (n - 1) * sp / 2
        for k in range(n):
            u = first + k * sp - sw / 2
            for side in (0, 1):
                if along == "x":
                    corner = [f"{u}", "-g - 1 mm", f"-fl - 0.5 mm" if side == 0 else "h + fs"]
                    size = (f"{sw}", "1 mm", "fl - fs + 0.5 mm")
                else:
                    corner = [f"-fl - 0.5 mm" if side == 0 else "a + fs", "-g - 1 mm", f"{u}"]
                    size = ("fl - fs + 0.5 mm", "1 mm", f"{sw}")
                slots.append(box(*size, corner, operation="cut", targets=["door"]))
    return c + slots

def script(choke, slotted=False):
    c = [{"command": "file.new", "params": {"name": "Microwave oven" + (" with choke" if choke else "")}}]
    c += [{"command": "parameters.add", "params": {"name": n, "expression": str(v), "unit": "mm", "comment": what}} for n, v, what in PARAMS]
    # The shell: a box with the cavity cut out through its front.
    c.append(box("a + 2*w", "d + w", "h + 2*w", ["-w", "0", "-w"], body_name="shell"))
    c.append(box("a", "d + 1 mm", "h", ["0", "-1 mm", "0"], operation="cut", targets=["shell"]))
    # The door: a plate over the opening and the flange, a gap g in front of it.
    c.append(box("a + 2*w", "t", "h + 2*w", ["-w", "-g - t", "-w"], operation="new_body", body_name="door"))
    if choke:
        # A ring groove cut into the door's inner face, a quarter wavelength out from the cavity's
        # edge along the gap: its shorted end, a quarter wavelength down, shows an open circuit at
        # its mouth, and the gap turns that into a short at the cavity's edge.
        c.append(box("a + 2*cl + cs", "cd", "h + 2*cl + cs", ["-cl - cs/2", "-g - cd", "-cl - cs/2"], operation="new_body", body_name="groove"))
        c.append(box("a + 2*cl - cs", "cd + 2 mm", "h + 2*cl - cs", ["-cl + cs/2", "-g - cd - 1 mm", "-cl + cs/2"], operation="cut", targets=["groove"]))
        c.append({"command": "solid.combine", "params": {"target": "door", "tools": ["groove"], "operation": "cut"}})
    if slotted:
        c += slotted_choke()
    # The load: 275 ml of water (IEC 60335-2-25's leakage test load) in two beakers of 137.5 ml
    # either side of the middle plane x = a/2, held up where a turntable holds them: the oven
    # stays mirror-symmetric about that plane, which then halves the model.
    for name, centre in (("water", "a/2 - lx"), ("water2", "a/2 + lx")):
        c.append(box("lw", "lw", "lh", [f"{centre} - lw/2", "d/2 - lw/2", "lz"], operation="new_body", body_name=name))
    return {"commands": c}

for name, choke, slotted in (("oven-gap", False, False), ("oven-choke", True, False), ("oven-slotted", False, True)):
    with open(os.path.join(HERE, name + ".script.json"), "w") as f:
        json.dump(script(choke, slotted), f, indent=2)
        f.write("\n")
