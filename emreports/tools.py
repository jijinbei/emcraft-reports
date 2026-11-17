"""The programs a report drives — emcraft-cli, solidcraft-cli, typst — found the one way, and
EMCraft's replies read back."""
import json, os, shutil, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def emcraft():
    """emcraft-cli: $EMCRAFT_CLI, else on the PATH."""
    return os.environ.get("EMCRAFT_CLI") or shutil.which("emcraft-cli") or "emcraft-cli"


def emcraft_version():
    try:
        return subprocess.run([emcraft(), "--version"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def solidcraft(*args, cwd=ROOT):
    """solidcraft-cli on the PATH, else the flatpak io.tangencylabs.solidcraft (given the
    repository's folder)."""
    if shutil.which("solidcraft-cli"):
        command = ["solidcraft-cli", *args]
    else:
        command = ["flatpak", "run", f"--filesystem={ROOT}", "--command=solidcraft-cli", "io.tangencylabs.solidcraft", *args]
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)


def typst(document, pdf):
    subprocess.run(["typst", "compile", "--root", ROOT, document, pdf], check=True)


def replies(text):
    """The JSON objects emcraft-cli printed, in order."""
    dec, i, out = json.JSONDecoder(), 0, []
    while (i := text.find("{", i)) >= 0:
        try:
            obj, j = dec.raw_decode(text, i)
            out.append(obj)
            i = j
        except ValueError:
            i += 1
    return out


def summary(objs):
    """A run's replies in a few numbers: a particle run's output plane, probe frequency, wall
    currents and speeds; a frequency run's unknowns."""
    s = {}
    for o in objs:
        if not isinstance(o, dict):
            continue
        if o.get("outputs"):
            out = o["outputs"][0]
            s.update({"power_w": out.get("power_w"), "efficiency": out.get("efficiency")})
        if isinstance(o.get("walls"), dict):
            s.update({f"current_{k}_a": v.get("current") for k, v in o["walls"].items() if isinstance(v, dict)})
        for key in ("mid_gamma", "time_ns", "particles", "unknowns"):
            if key in o and not isinstance(o[key], (dict, list)):
                s[key] = o[key]
    return {k: v for k, v in s.items() if v is not None}
