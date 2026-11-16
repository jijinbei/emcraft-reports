"""Reads a solve's output (results.power, results.probe) and gives the power density 5 cm in
front of the door for 1000 W accepted by the oven (the fields are for 1 W incident at `feed`)."""
import json, sys

P_OVEN = 1000.0  # W the magnetron delivers into the oven

def replies(path):
    text, dec, i, out = open(path).read(), json.JSONDecoder(), 0, []
    while (i := text.find("{", i)) >= 0:
        try:
            obj, j = dec.raw_decode(text, i); out.append(obj); i = j
        except ValueError:
            i += 1
    return out

def leak(path):
    r = replies(path)
    power = next(o for o in r if "reflected" in o and "unaccounted" in o)
    probe = next(o for o in r if "points" in o and o["points"] and "e" in o["points"][0])
    accepted = 1.0 - power["reflected"]
    scale = P_OVEN / accepted          # power scales the fields' products (E×H*) linearly
    c = lambda v: complex(v[0], v[1])
    def s(p):                           # ½ Re(E × H*), W/m², for 1 W incident
        e, h = [c(v) for v in p["e"]], [c(v).conjugate() for v in p["h"]]
        x = e[1] * h[2] - e[2] * h[1]; y = e[2] * h[0] - e[0] * h[2]; z = e[0] * h[1] - e[1] * h[0]
        return 0.5 * (abs(x.real) ** 2 + abs(y.real) ** 2 + abs(z.real) ** 2) ** 0.5
    dens = [s(p) * scale / 10.0 for p in probe["points"]]   # W/m² → mW/cm² (1 mW/cm² = 10 W/m²)
    leak.last = dens
    return {"accepted_per_W": accepted, "max_mW_cm2": max(dens), "mean_mW_cm2": sum(dens) / len(dens), "points": len(dens)}

def densities(path):
    """Power density (mW/cm²) at each probe, keyed by its (x, z) in the design's frame."""
    leak(path)
    xs = list(range(-40, 371, 30)); zs = list(range(-40, 251, 20))
    keys = [(x, z) for z in zs for x in xs]
    return dict(zip(keys, leak.last))

if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(f, json.dumps(leak(f)))
