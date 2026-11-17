"""Microwave oven door leakage: the whole oven at 2.45 GHz with three door seals."""
from emreports import Design, Report, Run, Step

OVENS = ("oven-gap", "oven-choke", "oven-slotted")
# The door seal cut out as a two-port (scripts/cell.py): its kinds, widths and lip starts.
CELLS = [f"{k}-{b}-fs{fs}" for k, b, fs in [("groove", 300, 10), ("groove", 80, 10), ("folded", 300, 10), ("folded", 80, 10),
         ("slotted", 300, 10), ("slotted", 80, 10), ("slotted", 300, 8.5), ("slotted", 80, 8.5)]]

REPORT = Report(
    title="Microwave oven door leakage",
    question="Does a household microwave oven's door keep its 2.45 GHz field inside, below 5 mW/cm² at 5 cm?",
    status="v0.1: the whole oven (2.3 million unknowns), three doors, solved with EMCraft v0.1",
    prepare=[Step("model/make.py"), Step("scripts/make.py"), Step("scripts/cell.py", "write")],
    designs=[Design(f"model/{n}.script.json", f"model/{n}.solidcraft") for n in (*OVENS, "oven-view")]
    + [Design(f"scripts/cell/{n}.script.json", f"scripts/cell/{n}.solidcraft") for n in CELLS],
    # Each oven takes about 25 minutes and up to 26 GB of memory: one at a time.
    runs=[Run(n, out=f"results/real/{n}.out") for n in OVENS]
    + [Run(f"cell/{n}", script=f"scripts/cell/{n}.json", out=f"results/cell/{n}.out") for n in CELLS],
    analysis=[Step("scripts/leak.py", *(f"results/real/{n}.out" for n in OVENS)), Step("scripts/cell.py")],
    figures=[Step("scripts/figures.py"), Step("scripts/schematic.py")],
    documents=["report.typ", "report.ja.typ"],
    published="report.typ",
)
