"""The relativistic BWO study: the Ku-band BWO of Na et al. (2017) checked, an S-band one designed."""
import glob, os

from emreports import Design, Report, Run, Step

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = ["cell-44", "final-ku", "final-sband", "anim-ku-growth", "anim-ku-rf", "anim-sband-growth", "anim-sband-rf"]
# The design study's runs (scripts/make.py writes them): solved with --scans or by name.
SCANS = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(HERE, "scripts", "*.json"))
               if os.path.basename(p)[:-5] not in MAIN and not p.endswith("ku-wall.json"))

# The scripts whose tube is a design of their own (scripts/make.py writes them to model/scan/).
DESIGNED = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(HERE, "scripts", "*.json"))
                  if '"../model/scan/' in open(p).read())

REPORT = Report(
    title="A relativistic backward-wave oscillator",
    question="Does EMCraft's r–z particle simulation reproduce a published relativistic BWO, and can it design one from rules of thumb?",
    status="Ku band 15.32 GHz against 15.575 GHz published; S band designed, 3.40 GHz, 0.64 GW, 17 %",
    prepare=[Step("scripts/make.py"), Step("model/make.py")],
    designs=[Design(f"model/{n}.script.json", f"model/{n}.sc") for n in ("ku", "sband", "ku-view", "sband-view")]
    + [Design(f"model/scan/{n}.script.json", f"model/scan/{n}.sc") for n in DESIGNED],
    runs=[Run(n) for n in MAIN] + [Run(n, scan=True) for n in SCANS],
    figures=[Step("scripts/principle.py"), Step("scripts/views.py"),
             Step("scripts/figures.py", "dispersion", "sections", "evolution", "animations", "maps", "final-ku", "final-sband")],
    documents=["report.typ", "report.ja.typ"],
    published="report.typ",
)
