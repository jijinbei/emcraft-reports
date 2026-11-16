"""Writes the oven's SolidCraft scripts: `oven-gap` (a plain door over a gap), `oven-choke` (the
same door with a quarter-wave groove round its rim) and `oven-slotted` (a slotted folded choke).
The oven is built as a counter-top one is: the cavity to the left, the control compartment to the
right with the waveguide that feeds the cavity through its right wall, a glass turntable, the
IEC load in a glass beaker on it, a window in the door. Run, then build each design with
`solidcraft-cli run <name>.script.json --save <name>.solidcraft`."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
# name, value in mm, what it is
PARAMS = [
    ("a", 330, "cavity width (x)"), ("d", 330, "cavity depth (y), door at y = 0"),
    ("h", 210, "cavity height (z)"), ("w", 45, "wall, and the flange the door rests on"),
    ("g", 2, "gap between door and flange"), ("t", 40, "door thickness"),
    ("cw", 130, "control compartment's width, right of the cavity (x)"),
    ("gb", 86, "waveguide's broad side (y): TE10 cut off at 1.74 GHz"), ("gn", 43, "waveguide's narrow side (x)"),
    ("gy", 195, "waveguide's centre (y), behind the cavity's middle"), ("gs", 5, "wall between the cavity and the waveguide"),
    ("gz", 20, "waveguide's shorted bottom end (z)"), ("ga", 60, "feed aperture's height (z), at the guide's top end, through the cavity's right wall"),
    ("tr", 140, "turntable's radius"), ("tt", 6, "turntable's thickness"), ("tz", 12, "turntable's height above the floor, on its roller ring"),
    ("br", 42.5, "the load's radius: IEC 60335-2-25's beaker, about 85 mm across"), ("bw", 2, "the beaker's glass bottom, left out: the water stands this high above the plate"), 
    ("lh", 48.5, "water's depth: 275 ml in the beaker"),
    ("ww", 220, "door window's width (x)"), ("wh", 150, "door window's height (z)"), ("wd", 12, "door window's depth into the door's outer face: the screen at its bottom"),
    ("fs", 8.5, "slotted choke: where its channel's shorted end and the lip start, out from the cavity's edge"),
    ("fl", 36, "slotted choke: where the lip ends and the channel opens to the gap"),
    ("cs", 6, "choke groove's width"), ("cl", 30, "choke groove's distance from the cavity's edge: about a quarter wavelength"), ("cd", 30, "choke groove's depth: about a quarter wavelength"),
]

# The design's origin is the corner of EMCraft's box of air; the cavity's front lower left corner
# sits here (mm): 60 mm left of the cabinet, below and above it, 120 mm in front of the door.
OFFSET = (60 + 45, 120 + 2 + 40, 60 + 45)

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

def script(choke, slotted=False, load=False):
    c = [{"command": "file.new", "params": {"name": "Microwave oven" + (" with choke" if choke else "")}}]
    c += [{"command": "parameters.add", "params": {"name": n, "expression": str(v), "unit": "mm", "comment": what}} for n, v, what in PARAMS]
    # The shell: the cabinet's metal, the cavity cut out through its front, the control
    # compartment to its right brought forward flush with the door (a gap g beside the door's edge).
    c.append(box("a + w + cw", "d + w", "h + 2*w", ["-w", "0", "-w"], body_name="shell"))
    c.append(box("a", "d + 1 mm", "h", ["0", "-1 mm", "0"], operation="cut", targets=["shell"]))
    c.append(box("cw - w - g", "g + t", "h + 2*w", ["a + w + g", "-g - t", "-w"], operation="join", targets=["shell"]))
    # The waveguide, up the compartment beside the cavity's right wall: shorted at its bottom, the
    # magnetron's antenna a quarter guide wavelength above that, open into the cavity at its top
    # through an aperture in the wall between them.
    c.append(box("gn", "gb", "h - gz", ["a + gs", "gy - gb/2", "gz"], operation="cut", targets=["shell"]))
    c.append(box("gs + 2 mm", "gb", "ga", ["a - 1 mm", "gy - gb/2", "h - ga"], operation="cut", targets=["shell"]))
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
    # The window: a recess in the door's outer face, its bottom the perforated screen (holes of a
    # millimetre or two, cut off far below 2.45 GHz: metal to the field, see the report).
    c.append(box("ww", "wd + 1 mm", "wh", ["a/2 - ww/2", "-g - t - 1 mm", "h/2 - wh/2"], operation="cut", targets=["door"]))
    if load:
        # The turntable: a glass plate on its roller ring above the floor; the load on it, 275 ml
        # of water (IEC 60335-2-25's leakage test load) where a beaker 85 mm across holds it at
        # the centre. Drawn only: EMCraft places the two as cylinders of its own (scripts/make.py),
        # meshed on their exact surfaces; the beaker's thin glass is left out (EMCraft does not
        # mesh a dielectric inside or against another yet), the water standing its bottom's
        # thickness above the plate.
        c.append({"command": "solid.cylinder", "params": {"radius": "tr", "height": "tt", "base": ["a/2", "d/2", "tz"], "operation": "new_body", "body_name": "turntable"}})
        c.append({"command": "solid.cylinder", "params": {"radius": "br", "height": "lh", "base": ["a/2", "d/2", "tz + tt + bw"], "operation": "new_body", "body_name": "water"}})
    # Into the frame EMCraft's box of air starts at: room round the oven for the air and the
    # layer, most of it in front of the door, where the leak is measured.
    c.append({"command": "solid.move", "params": {"bodies": ["shell", "door"] + (["turntable", "water"] if load else []), "translate": [str(v) for v in OFFSET]}})
    return {"commands": c}

# The three solved; the slotted one again with its load, for the pictures.
for name, choke, slotted, load in (("oven-gap", False, False, False), ("oven-choke", True, False, False),
                                   ("oven-slotted", False, True, False), ("oven-view", False, True, True)):
    with open(os.path.join(HERE, name + ".script.json"), "w") as f:
        json.dump(script(choke, slotted, load), f, indent=2)
        f.write("\n")
